<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api, type User } from '@/api'
import { websocketUrl } from '@/api/client'
import { auth } from '@/stores'

interface Conversation {
  user: User
  last_message: string
  last_at: string
  unread: number
  online: boolean
}

interface Message {
  id: number
  sender_id: number
  receiver_id: number
  content: string
  created_at: string
}

const router = useRouter()
const conversations = ref<Conversation[]>([])
const activePeer = ref<Conversation | null>(null)
const messages = ref<Message[]>([])
const input = ref('')
const loading = ref(true)
const scroller = ref<HTMLElement | null>(null)

let socket: WebSocket | null = null
let heartbeat: number | undefined

function scrollToBottom() {
  nextTick(() => {
    if (scroller.value) scroller.value.scrollTop = scroller.value.scrollHeight
  })
}

async function loadConversations() {
  try {
    conversations.value = await api.conversations()
  } catch {
    conversations.value = []
  } finally {
    loading.value = false
  }
}

async function openPeer(conversation: Conversation) {
  activePeer.value = conversation
  try {
    messages.value = await api.messages(conversation.user.id)
    conversation.unread = 0
    scrollToBottom()
  } catch {
    messages.value = []
  }
}

async function send() {
  const content = input.value.trim()
  if (!content || !activePeer.value) return
  input.value = ''
  try {
    const message = await api.sendMessage(activePeer.value.user.id, content)
    messages.value.push(message as Message)
    scrollToBottom()
    await loadConversations()
  } catch {
    input.value = content
  }
}

function connect() {
  if (!auth.token) return
  try {
    socket = new WebSocket(websocketUrl())
    socket.onmessage = (event) => {
      const data = JSON.parse(event.data)
      if (data.type !== 'message') return
      if (activePeer.value && (data.sender_id === activePeer.value.user.id || data.receiver_id === activePeer.value.user.id)) {
        if (!messages.value.some((item) => item.id === data.id)) {
          messages.value.push(data)
          scrollToBottom()
        }
      }
      loadConversations()
    }
  } catch {
    /* WebSocket 失败时仍可用 REST 轮询 */
  }
  heartbeat = window.setInterval(() => {
    if (socket?.readyState === WebSocket.OPEN) socket.send('ping')
  }, 25000)
}

onMounted(async () => {
  await loadConversations()
  connect()
})

onBeforeUnmount(() => {
  if (heartbeat) clearInterval(heartbeat)
  socket?.close()
})

function fmt(iso: string) {
  return new Date(iso).toLocaleString('zh-CN', { month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}
</script>

<template>
  <main class="mx-auto max-w-[1000px] px-5 pb-24 pt-6">
    <div class="grid gap-4 md:grid-cols-[280px_minmax(0,1fr)]">
      <section class="card overflow-hidden">
        <div class="border-b border-slate-200 px-4 py-3 text-sm font-bold dark:border-slate-800">💬 会话</div>
        <div v-if="loading" class="p-4"><div class="skeleton h-10" /></div>
        <div v-else-if="!conversations.length" class="p-6 text-center text-xs text-slate-400">
          还没有会话，去别人的主页或帖子里发起聊天吧
        </div>
        <ul v-else>
          <li
            v-for="item in conversations"
            :key="item.user.id"
            class="flex cursor-pointer items-center gap-2.5 border-b border-slate-100 px-4 py-3 last:border-0 hover:bg-slate-50 dark:border-slate-800 dark:hover:bg-slate-800/60"
            :class="{ 'bg-brand-50 dark:bg-brand-700/20': activePeer?.user.id === item.user.id }"
            @click="openPeer(item)"
          >
            <div class="grid h-9 w-9 place-items-center rounded-full border border-slate-200 bg-slate-50 text-base dark:border-slate-800 dark:bg-slate-800">
              {{ item.user.avatar }}
            </div>
            <div class="min-w-0 flex-1">
              <div class="flex items-center gap-1.5">
                <span class="truncate text-[13px] font-semibold">{{ item.user.nickname }}</span>
                <span v-if="item.online" class="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                <span v-if="item.unread" class="ml-auto rounded-full bg-rose-500 px-1.5 text-[10px] font-bold text-white">{{ item.unread }}</span>
              </div>
              <div class="truncate text-[11.5px] text-slate-400">{{ item.last_message }}</div>
            </div>
          </li>
        </ul>
      </section>

      <section class="card flex min-h-[520px] flex-col overflow-hidden">
        <div class="flex items-center gap-2 border-b border-slate-200 px-4 py-3 dark:border-slate-800">
          <span class="text-sm font-bold">{{ activePeer ? activePeer.user.avatar + ' ' + activePeer.user.nickname : '私信' }}</span>
          <span v-if="activePeer?.online" class="rounded-full bg-emerald-100 px-2 py-0.5 text-[10px] font-semibold text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-300">在线</span>
        </div>

        <div v-if="!activePeer" class="flex flex-1 flex-col items-center justify-center gap-2 text-slate-400">
          <div class="text-3xl">💬</div>
          <p class="text-sm">选择一个会话开始聊天</p>
        </div>

        <template v-else>
          <div ref="scroller" class="flex-1 space-y-3 overflow-y-auto p-4">
            <div
              v-for="message in messages"
              :key="message.id"
              class="flex"
              :class="{ 'justify-end': message.sender_id === auth.user?.id }"
            >
              <div
                class="max-w-[76%] whitespace-pre-wrap rounded-2xl px-3.5 py-2 text-[13.5px]"
                :class="
                  message.sender_id === auth.user?.id
                    ? 'rounded-br-md bg-gradient-to-br from-brand-700 to-brand-500 text-white'
                    : 'rounded-bl-md border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-800'
                "
              >
                {{ message.content }}
                <div class="mt-1 text-[10px] opacity-60">{{ fmt(message.created_at) }}</div>
              </div>
            </div>
          </div>

          <div class="flex gap-2 border-t border-slate-200 p-3 dark:border-slate-800">
            <input v-model="input" class="input flex-1" placeholder="输入消息，回车发送" @keyup.enter="send" />
            <button class="btn btn-primary" :disabled="!input.trim()" @click="send">发送</button>
          </div>
        </template>
      </section>
    </div>
  </main>
</template>
