<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api, type Post, type User } from '@/api'
import PostCard from '@/components/PostCard.vue'
import { auth, setUser, toast } from '@/stores'

const route = useRoute()
const router = useRouter()

const user = ref<User | null>(null)
const posts = ref<Post[]>([])
const loading = ref(true)
const error = ref('')
const editing = ref(false)
const saving = ref(false)
const matches = ref<{ user: User; score: number; reason: string }[] | null>(null)
const matchMessage = ref('')
const matchLoading = ref(false)

const form = reactive({ nickname: '', major: '', grade: '', bio: '', avatar: '', tags: '' })

const isSelf = computed(() => Boolean(auth.user && user.value && auth.user.id === user.value.id))

function targetId(): number {
  return route.name === 'me' ? auth.user?.id || 0 : Number(route.params.id)
}

async function load() {
  const id = targetId()
  if (!id) {
    loading.value = false
    error.value = '请先登录'
    return
  }
  loading.value = true
  error.value = ''
  try {
    const data = await api.user(id)
    user.value = data.user
    posts.value = data.posts
    Object.assign(form, {
      nickname: data.user.nickname,
      major: data.user.major,
      grade: data.user.grade,
      bio: data.user.bio,
      avatar: data.user.avatar,
      tags: (data.user.tags || []).join('，'),
    })
  } catch (err: any) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

async function save() {
  saving.value = true
  try {
    const updated = await api.updateMe({
      nickname: form.nickname,
      major: form.major,
      grade: form.grade,
      bio: form.bio,
      avatar: form.avatar,
      tags: form.tags.split(/[,，、\s]+/).map((tag) => tag.trim()).filter(Boolean).slice(0, 8),
    })
    user.value = updated
    setUser(updated)
    editing.value = false
    toast('资料已更新')
  } catch (err: any) {
    toast(err.message, 'err')
  } finally {
    saving.value = false
  }
}

async function runMatch() {
  matchLoading.value = true
  matches.value = null
  try {
    const result = await api.aiMatch()
    matches.value = result.matches
    matchMessage.value = result.message
  } catch (err: any) {
    toast(err.message, 'err')
  } finally {
    matchLoading.value = false
  }
}

function goUser(id: number) {
  if (auth.user && auth.user.id === id) router.push('/me')
  else router.push('/user/' + id)
}

onMounted(load)
watch(() => route.params.id, load)
watch(() => route.name, load)
</script>

<template>
  <main class="mx-auto max-w-[1000px] px-5 pb-24 pt-6">
    <div v-if="loading" class="card p-6"><div class="skeleton h-20" /></div>

    <div v-else-if="error" class="card">
      <div class="flex flex-col items-center gap-2 py-16 text-slate-500">
        <div class="text-3xl">🔒</div>
        <p class="text-sm">{{ error }}</p>
        <button class="btn btn-sm btn-primary" @click="router.push('/login')">去登录</button>
      </div>
    </div>

    <template v-else-if="user">
      <section class="card p-6">
        <div class="flex flex-wrap items-center gap-4">
          <div class="grid h-[72px] w-[72px] place-items-center rounded-3xl border border-slate-200 bg-slate-50 text-4xl dark:border-slate-800 dark:bg-slate-800">
            {{ user.avatar }}
          </div>
          <div class="min-w-0 flex-1">
            <div class="text-xl font-extrabold tracking-tight">{{ user.nickname }}</div>
            <div class="text-xs text-slate-400">
              {{ user.major || '未填写专业' }}<span v-if="user.grade"> · {{ user.grade }}</span>
              <span> · 加入于 {{ new Date(user.created_at).toLocaleDateString('zh-CN') }}</span>
            </div>
            <div v-if="user.tags.length" class="mt-2 flex flex-wrap gap-1.5">
              <span v-for="tag in user.tags" :key="tag" class="tag"># {{ tag }}</span>
            </div>
          </div>
          <button v-if="isSelf" class="btn btn-sm" @click="editing = !editing">
            {{ editing ? '收起编辑' : '✏️ 编辑资料' }}
          </button>
        </div>
        <p class="mt-3 text-sm text-slate-600 dark:text-slate-300">{{ user.bio || '这个人很神秘，还没有写简介。' }}</p>
      </section>

      <section v-if="isSelf && editing" class="card mt-4 space-y-4 p-6">
        <div class="text-sm font-bold">编辑资料</div>
        <div class="grid gap-3 sm:grid-cols-2">
          <div class="space-y-1.5"><label class="field-label">昵称</label><input v-model="form.nickname" class="input" maxlength="20" /></div>
          <div class="space-y-1.5"><label class="field-label">头像（一个 emoji）</label><input v-model="form.avatar" class="input" maxlength="4" /></div>
          <div class="space-y-1.5"><label class="field-label">专业</label><input v-model="form.major" class="input" maxlength="50" placeholder="计算机科学与技术" /></div>
          <div class="space-y-1.5"><label class="field-label">年级</label><input v-model="form.grade" class="input" maxlength="16" placeholder="大三" /></div>
        </div>
        <div class="space-y-1.5">
          <label class="field-label">一句话简介</label>
          <textarea v-model="form.bio" class="input min-h-[80px]" maxlength="300" />
        </div>
        <div class="space-y-1.5">
          <label class="field-label">兴趣标签（逗号分隔，最多 8 个）</label>
          <input v-model="form.tags" class="input" placeholder="考研，摄影，羽毛球" />
          <span class="hint">标签越具体，AI 搭子匹配越准。</span>
        </div>
        <div class="flex justify-end gap-2">
          <button class="btn" @click="editing = false">取消</button>
          <button class="btn btn-primary" :disabled="saving" @click="save">{{ saving ? '保存中…' : '保存' }}</button>
        </div>
      </section>

      <section v-if="isSelf" class="card mt-4 p-6">
        <div class="flex flex-wrap items-center justify-between gap-3">
          <div>
            <div class="text-sm font-bold">🤝 AI 搭子匹配</div>
            <div class="text-xs text-slate-400">依据你的兴趣标签和简介，找出兴趣相投的同学</div>
          </div>
          <button class="btn btn-ai" :disabled="matchLoading" @click="runMatch">
            <span v-if="matchLoading" class="typing mr-1 flex gap-1"><span /><span /><span /></span>
            {{ matchLoading ? '匹配中…' : '开始匹配' }}
          </button>
        </div>

        <div v-if="matches" class="mt-4 space-y-3">
          <p class="text-xs text-slate-500">{{ matchMessage }}</p>
          <div v-for="item in matches" :key="item.user.id" class="ai-panel space-y-2">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <div class="grid h-8 w-8 place-items-center rounded-full bg-ai-100 text-sm dark:bg-ai-500/20">{{ item.user.avatar }}</div>
                <div>
                  <div class="text-[13px] font-semibold">{{ item.user.nickname }}</div>
                  <div class="text-[11px] text-slate-400">{{ item.user.major }} {{ item.user.grade }}</div>
                </div>
              </div>
              <span class="ai-chip">匹配度 {{ Math.round(item.score * 100) }}%</span>
            </div>
            <p class="m-0 text-xs text-slate-600 dark:text-slate-300">{{ item.reason }}</p>
            <div class="flex flex-wrap gap-1.5">
              <span v-for="tag in item.user.tags" :key="tag" class="tag"># {{ tag }}</span>
            </div>
            <button class="btn btn-sm" @click="goUser(item.user.id)">看看 TA 的主页</button>
          </div>
          <p class="hint">匹配理由由 AI 生成，仅供参考。</p>
        </div>
      </section>

      <section class="card mt-4 p-6">
        <div class="mb-3 text-sm font-bold">📝 {{ isSelf ? '我' : 'TA' }}的帖子（{{ posts.length }}）</div>
        <div v-if="!posts.length" class="flex flex-col items-center gap-1 py-8 text-slate-400">
          <div class="text-2xl">🌱</div>
          <p class="text-sm">还没有发布过帖子</p>
        </div>
        <div v-else class="space-y-3">
          <PostCard v-for="(post, index) in posts" :key="post.id" :post="post" :index="index" />
        </div>
      </section>
    </template>
  </main>
</template>
