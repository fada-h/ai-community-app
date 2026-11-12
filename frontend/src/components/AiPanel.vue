<script setup lang="ts">
import { nextTick, ref } from 'vue'
import { streamChat } from '@/api/client'

defineProps<{ compact?: boolean }>()

interface ChatMessage {
  id: number
  role: 'me' | 'ai'
  text: string
  meta?: any
  pending?: boolean
  error?: boolean
}

const DEFAULT_SUGGESTIONS = [
  '图书馆几点关门？',
  '校园卡丢了怎么办？',
  '奖学金什么时候申请？',
  '校园网连不上怎么办？',
]

let seq = 0
const messages = ref<ChatMessage[]>([])
const input = ref('')
const streaming = ref(false)
const errorText = ref('')
const suggestions = ref<string[]>([...DEFAULT_SUGGESTIONS])
const scroller = ref<HTMLElement | null>(null)
const lastQuestion = ref('')

function scrollToBottom() {
  nextTick(() => {
    if (scroller.value) scroller.value.scrollTop = scroller.value.scrollHeight
  })
}

async function send(text?: string) {
  const question = (text ?? input.value).trim()
  if (!question || streaming.value) return

  input.value = ''
  errorText.value = ''
  lastQuestion.value = question

  // 带着最近几轮对话一起发，追问才能接得上
  const history = messages.value
    .filter((item) => item.text && !item.error)
    .slice(-8)
    .map((item) => ({
      role: item.role === 'me' ? 'user' : 'assistant',
      content: item.text,
    }))

  messages.value.push({ id: ++seq, role: 'me', text: question })
  const target: ChatMessage = { id: ++seq, role: 'ai', text: '', pending: true }
  messages.value.push(target)
  streaming.value = true
  scrollToBottom()

  await streamChat(
    question,
    {
      onMeta(meta) {
        target.meta = meta
        if (meta.suggestions?.length) suggestions.value = meta.suggestions.slice(0, 4)
        target.pending = false
        scrollToBottom()
      },
      onDelta(chunk) {
        target.text += chunk
        target.pending = false
        scrollToBottom()
      },
      onDone() {
        target.pending = false
        streaming.value = false
        scrollToBottom()
      },
      onError(error) {
        target.pending = false
        target.error = true
        target.text = target.text || '抱歉，这次没有连接上 AI 服务。'
        errorText.value = error.message
        streaming.value = false
        scrollToBottom()
      },
    },
    history,
  )
}

function retry(message: ChatMessage) {
  if (streaming.value) return
  const index = messages.value.findIndex((item) => item.id === message.id)
  if (index >= 0) messages.value.splice(index, 1)
  send(lastQuestion.value || message.text)
}

function reset() {
  messages.value = []
  errorText.value = ''
  suggestions.value = [...DEFAULT_SUGGESTIONS]
}

defineExpose({ reset })
</script>

<template>
  <div class="card space-y-4 p-5">
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-2.5">
        <div class="grid h-8 w-8 place-items-center rounded-lg bg-gradient-to-br from-ai-600 to-fuchsia-500 text-sm text-white">✨</div>
        <div>
          <div class="text-sm font-bold">青禾 AI 助手</div>
          <div class="text-[11.5px] text-slate-400">
            {{ messages.length ? '正在对话' : '校园事务问答 · 断网也能用' }}
          </div>
        </div>
      </div>
      <button v-if="messages.length" class="btn btn-sm btn-ghost" @click="reset">清空</button>
    </div>

    <div v-if="!messages.length" class="ai-panel space-y-3">
      <div class="text-sm font-bold">我可以帮你</div>
      <p class="m-0 text-xs text-slate-500">
        查校园事务（图书馆 / 食堂 / 教务 / 宿舍 / 奖学金…）、解释社区规则、帮你梳理发帖思路。
      </p>
      <div class="flex flex-wrap gap-2">
        <button
          v-for="item in suggestions"
          :key="item"
          class="rounded-full border border-ai-300 bg-white px-3 py-1.5 text-[12.5px] text-slate-600 transition hover:-translate-y-px hover:border-ai-500 hover:text-ai-600 dark:bg-slate-900"
          @click="send(item)"
        >
          {{ item }}
        </button>
      </div>
    </div>

    <div
      v-else
      ref="scroller"
      class="space-y-3.5 overflow-y-auto pr-1"
      :style="{ maxHeight: compact ? '300px' : '440px' }"
    >
      <div
        v-for="message in messages"
        :key="message.id"
        class="flex gap-2.5"
        :class="{ 'flex-row-reverse': message.role === 'me' }"
      >
        <div
          v-if="message.role === 'ai'"
          class="grid h-7 w-7 shrink-0 place-items-center rounded-full bg-ai-100 text-xs dark:bg-ai-500/20"
        >
          ✨
        </div>
        <div class="min-w-0 max-w-[80%]">
          <div
            class="whitespace-pre-wrap break-words rounded-2xl px-3.5 py-2.5 text-[13.5px] leading-relaxed"
            :class="
              message.role === 'ai'
                ? 'rounded-tl-md border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900'
                : 'rounded-tr-md bg-gradient-to-br from-brand-700 to-brand-500 text-white'
            "
          >
            {{ message.text }}
            <span v-if="message.pending" class="typing ml-1 flex gap-1"><span /><span /><span /></span>
          </div>
          <div v-if="message.role === 'ai'" class="mt-1.5 flex flex-wrap items-center gap-1.5 text-[11px] text-slate-400">
            <span v-if="message.meta?.mode">{{ message.meta.mode === 'cloud' ? 'DeepSeek' : '本地引擎' }}</span>
            <span v-if="message.meta?.kind === 'knowledge' && message.meta?.confidence">
              · 置信度 {{ Math.round(message.meta.confidence * 100) }}%
            </span>
            <span
              v-for="source in message.meta?.sources || []"
              :key="source"
              class="rounded-full border border-slate-200 px-2 py-0.5 dark:border-slate-700"
              >📎 {{ source }}</span
            >
            <button v-if="message.error" class="text-ai-500 underline" @click="retry(message)">↻ 重试</button>
          </div>
        </div>
      </div>
    </div>

    <div v-if="errorText" class="notice">⚠️ {{ errorText }}</div>

    <div v-if="messages.length" class="flex flex-wrap gap-2">
      <button
        v-for="item in suggestions"
        :key="item"
        class="rounded-full border border-ai-300 bg-white px-3 py-1 text-[12px] text-slate-600 transition hover:border-ai-500 hover:text-ai-600 dark:bg-slate-900"
        @click="send(item)"
      >
        {{ item }}
      </button>
    </div>

    <div class="flex gap-2">
      <input
        v-model="input"
        class="input flex-1"
        :placeholder="streaming ? 'AI 正在回答…' : '问我任何校园问题，回车发送'"
        :disabled="streaming"
        @keyup.enter="send()"
      />
      <button class="btn btn-ai" :disabled="streaming || !input.trim()" @click="send()">
        {{ streaming ? '…' : '发送' }}
      </button>
    </div>
    <div class="text-center text-[11px] text-slate-400">AI 生成内容仅供参考，重要信息请以学校官方通知为准。</div>
  </div>
</template>
