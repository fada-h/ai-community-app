<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { api } from '@/api'
import AiPanel from '@/components/AiPanel.vue'

const logs = ref<{ id: number; kind: string; input: string; mode: string; chars: number }[]>([])
const aiMode = ref('local')

async function load() {
  try {
    logs.value = (await api.aiLogs()).slice(0, 6)
    const meta = await api.meta()
    aiMode.value = meta.ai.mode
  } catch {
    /* 未登录也能看助手，只是没有记录 */
  }
}

const capabilities = [
  { icon: '🏫', title: '校园事务问答', desc: '图书馆、食堂、教务、宿舍、奖学金等 26 类问题' },
  { icon: '✍️', title: '发帖写作助手', desc: '润色正文、推荐分类与标签、生成摘要、检测违规内容' },
  { icon: '🤝', title: '搭子匹配', desc: '根据兴趣标签与简介，找出同频的同学并给出理由' },
]

onMounted(load)
</script>

<template>
  <main class="mx-auto max-w-[1100px] px-5 pb-24 pt-6">
    <div class="grid items-start gap-6 lg:grid-cols-[minmax(0,1fr)_320px]">
      <AiPanel />

      <aside class="space-y-4">
        <section class="card p-4">
          <div class="mb-3 text-sm font-bold">✨ AI 能做什么</div>
          <div class="space-y-3">
            <div v-for="item in capabilities" :key="item.title" class="flex gap-2.5">
              <span class="text-base">{{ item.icon }}</span>
              <div>
                <div class="text-[13px] font-semibold">{{ item.title }}</div>
                <div class="text-[11.5px] text-slate-400">{{ item.desc }}</div>
              </div>
            </div>
          </div>
        </section>

        <section class="rounded-2xl border border-slate-200 bg-white p-4 text-[12px] dark:border-slate-800 dark:bg-slate-900">
          <div class="mb-1 text-xs font-bold">🧠 当前 AI 模式</div>
          <p v-if="aiMode === 'cloud'" class="text-slate-500">
            已连接 DeepSeek 云端模型，回答由大模型生成。
          </p>
          <p v-else class="text-slate-500">
            正在使用「青禾本地引擎」：基于内置校园知识库的检索增强问答，无需联网即可运行。
            在 backend/.env 配置 <code class="rounded bg-slate-100 px-1 dark:bg-slate-800">DEEPSEEK_API_KEY</code> 后会自动切换云端。
          </p>
        </section>

        <section v-if="logs.length" class="card p-4">
          <div class="mb-2 text-sm font-bold">最近 AI 调用</div>
          <div v-for="log in logs" :key="log.id" class="border-b border-slate-100 py-1.5 last:border-0 dark:border-slate-800">
            <div class="text-[12px]">
              {{ log.kind === 'chat' ? '💬' : log.kind === 'write' ? '✍️' : '🤝' }} {{ log.input }}
            </div>
            <div class="text-[11px] text-slate-400">{{ log.mode === 'cloud' ? '云端' : '本地' }} · {{ log.chars }} 字</div>
          </div>
        </section>

        <section class="rounded-2xl border border-slate-200 bg-white p-4 text-[12px] text-slate-500 dark:border-slate-800 dark:bg-slate-900">
          <div class="mb-1 text-xs font-bold">⚠️ 使用边界</div>
          AI 只提供建议，不会自动发帖、评论或私信；所有内容都需要你确认后才会进入社区。
        </section>
      </aside>
    </div>
  </main>
</template>
