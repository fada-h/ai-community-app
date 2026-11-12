<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { api } from '@/api'
import { auth, toast, ui } from '@/stores'

defineProps<{ open: boolean }>()
const emit = defineEmits<{ (e: 'close'): void; (e: 'created'): void }>()

const categories = [
  { id: 'study', name: '学习互助', icon: '📚' },
  { id: 'club', name: '社团活动', icon: '🎭' },
  { id: 'market', name: '二手闲置', icon: '🛍️' },
  { id: 'lost', name: '失物招领', icon: '🔍' },
  { id: 'life', name: '校园生活', icon: '☕' },
]

const form = reactive({ title: '', content: '', category: 'life', tags: '' })
const publishing = ref(false)
const error = ref('')
const aiLoading = ref(false)
const aiResult = ref<any>(null)
const aiError = ref('')

const tagList = computed(() =>
  form.tags
    .split(/[,，、\s]+/)
    .map((tag) => tag.trim())
    .filter(Boolean)
    .slice(0, 6),
)

async function runAi() {
  if (form.content.trim().length < 5) {
    toast('先写几句正文，AI 才有素材哦', 'err')
    return
  }
  aiLoading.value = true
  aiError.value = ''
  aiResult.value = null
  try {
    aiResult.value = await api.aiWrite(form.content.trim())
  } catch (err: any) {
    aiError.value = err.message
  } finally {
    aiLoading.value = false
  }
}

function applyAi() {
  if (!aiResult.value) return
  if (!form.title.trim() && aiResult.value.title) form.title = aiResult.value.title
  form.content = aiResult.value.content || form.content
  if (aiResult.value.category) form.category = aiResult.value.category
  if (aiResult.value.tags?.length) form.tags = aiResult.value.tags.join('，')
  aiResult.value = null
  toast('已应用 AI 建议，你可以继续修改')
}

async function publish() {
  error.value = ''
  if (!auth.user) {
    error.value = '请先登录'
    return
  }
  if (form.title.trim().length < 2) {
    error.value = '标题至少 2 个字'
    return
  }
  if (form.content.trim().length < 5) {
    error.value = '正文至少 5 个字'
    return
  }
  publishing.value = true
  try {
    await api.createPost({
      title: form.title.trim(),
      content: form.content.trim(),
      category: form.category,
      tags: tagList.value,
    })
    toast('发布成功 🎉')
    form.title = ''
    form.content = ''
    form.tags = ''
    form.category = 'life'
    ui.version += 1
    emit('created')
    emit('close')
  } catch (err: any) {
    error.value = err.message
  } finally {
    publishing.value = false
  }
}
</script>

<template>
  <div
    v-if="open"
    class="fixed inset-0 z-[60] grid place-items-center bg-slate-950/55 p-5 backdrop-blur-sm"
    @click.self="emit('close')"
  >
    <div class="card flex max-h-[88vh] w-full max-w-2xl flex-col overflow-hidden">
      <div class="flex items-center gap-3 border-b border-slate-200 px-6 py-4 dark:border-slate-800">
        <div class="flex-1">
          <div class="text-[15px] font-bold">✍️ 发布帖子</div>
          <div class="text-xs text-slate-400">真实表达最重要，AI 只是帮你把话说得更清楚</div>
        </div>
        <button class="btn btn-ghost btn-sm h-8 w-8 px-0" @click="emit('close')">✕</button>
      </div>

      <div class="flex-1 space-y-4 overflow-y-auto px-6 py-5">
        <div class="space-y-1.5">
          <label class="field-label">标题</label>
          <input v-model="form.title" class="input" maxlength="80" placeholder="一句话说清你想聊什么" />
        </div>

        <div class="space-y-1.5">
          <label class="field-label">正文</label>
          <textarea
            v-model="form.content"
            class="input min-h-[120px] resize-y leading-relaxed"
            maxlength="4000"
            placeholder="例如：想找一起自习的同学，时间地点、对搭子的期待…"
          />
          <div class="flex items-center justify-between">
            <span class="hint">{{ form.content.length }} / 4000</span>
            <button class="btn btn-sm btn-ai" :disabled="aiLoading" @click="runAi">
              <span v-if="aiLoading" class="typing mr-1 flex gap-1"><span /><span /><span /></span>
              <span v-else>✨</span>
              {{ aiLoading ? 'AI 思考中…' : 'AI 帮我润色' }}
            </button>
          </div>
        </div>

        <div class="grid gap-3 sm:grid-cols-2">
          <div class="space-y-1.5">
            <label class="field-label">分类</label>
            <select v-model="form.category" class="input">
              <option v-for="item in categories" :key="item.id" :value="item.id">
                {{ item.icon }} {{ item.name }}
              </option>
            </select>
          </div>
          <div class="space-y-1.5">
            <label class="field-label">标签（逗号分隔，最多 6 个）</label>
            <input v-model="form.tags" class="input" placeholder="考研，自习，图书馆" />
          </div>
        </div>

        <div v-if="tagList.length" class="flex flex-wrap gap-1.5">
          <span v-for="tag in tagList" :key="tag" class="tag"># {{ tag }}</span>
        </div>

        <div v-if="aiError" class="notice">⚠️ {{ aiError }}</div>

        <div v-if="aiResult" class="ai-panel space-y-3">
          <div class="flex items-center gap-2 text-sm font-bold">
            <span class="h-2 w-2 rounded-full bg-ai-500" />
            AI 写作助手
            <span class="ai-chip">{{ aiResult.mode === 'cloud' ? 'DeepSeek' : '本地引擎' }}</span>
          </div>

          <div v-if="aiResult.title" class="rounded-xl border border-dashed border-ai-300 bg-white px-3.5 py-2.5 text-[13.5px] dark:bg-slate-900">
            <strong>建议标题：</strong>{{ aiResult.title }}
          </div>
          <div class="whitespace-pre-wrap rounded-xl border border-dashed border-ai-300 bg-white px-3.5 py-2.5 text-[13.5px] dark:bg-slate-900">
            <strong>润色后的正文：</strong>
            {{ aiResult.content }}
          </div>

          <div class="flex flex-wrap gap-1.5">
            <span class="ai-chip">推荐分类：{{ aiResult.category_name }}</span>
            <span v-for="tag in aiResult.tags" :key="tag" class="ai-chip"># {{ tag }}</span>
          </div>

          <div v-if="aiResult.issues.length" class="text-xs text-slate-500">
            <div class="font-medium">发现的问题：</div>
            <div v-for="issue in aiResult.issues" :key="issue">· {{ issue }}</div>
          </div>
          <div v-if="aiResult.summary" class="text-xs text-slate-500">摘要：{{ aiResult.summary }}</div>

          <div :class="aiResult.safety.safe ? 'ok-note' : 'notice'">
            {{ aiResult.safety.safe ? '✅ ' : '⚠️ ' }}{{ aiResult.safety.message }}
          </div>

          <div class="flex items-center gap-2">
            <button class="btn btn-sm btn-primary" @click="applyAi">应用到正文</button>
            <button class="btn btn-sm btn-ghost" @click="aiResult = null">忽略建议</button>
            <span class="ml-auto text-xs text-slate-400">AI 建议不会自动发布</span>
          </div>
        </div>

        <div v-if="error" class="text-xs text-rose-500">{{ error }}</div>
      </div>

      <div class="flex justify-end gap-2 border-t border-slate-200 px-6 py-4 dark:border-slate-800">
        <button class="btn" @click="emit('close')">取消</button>
        <button class="btn btn-primary" :disabled="publishing" @click="publish">
          <span v-if="publishing" class="typing mr-1 flex gap-1"><span /><span /><span /></span>
          {{ publishing ? '发布中…' : '发布帖子' }}
        </button>
      </div>
    </div>
  </div>
</template>
