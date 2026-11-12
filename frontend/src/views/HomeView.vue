<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { api, type Meta, type Post } from '@/api'
import PostCard from '@/components/PostCard.vue'
import { auth, toast, ui } from '@/stores'

const router = useRouter()
const meta = ref<Meta | null>(null)
const posts = ref<Post[]>([])
const hot = ref<Post[]>([])
const loading = ref(true)
const error = ref('')
const category = ref('all')
const sort = ref<'latest' | 'hot'>('latest')

const categories = computed(() => meta.value?.categories || [])
const stats = computed(() => meta.value?.stats)

async function load() {
  loading.value = true
  error.value = ''
  try {
    const [feed, hotFeed, metaData] = await Promise.all([
      api.posts({ category: category.value, sort: sort.value, q: ui.search, limit: 30 }),
      api.posts({ sort: 'hot', limit: 5 }),
      api.meta(),
    ])
    posts.value = feed.items
    hot.value = hotFeed.items
    meta.value = metaData
  } catch (err: any) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

function openComposer() {
  if (!auth.user) {
    toast('登录后才能发帖', 'err')
    router.push('/login')
    return
  }
  ui.composerOpen = true
}

function pickCategory(id: string) {
  category.value = id
  load()
}

function clearSearch() {
  ui.search = ''
  load()
}

onMounted(load)
watch(() => ui.version, load)
watch(() => ui.search, load)
watch(sort, load)
</script>

<template>
  <main class="mx-auto max-w-[1200px] px-5 pb-24 pt-6">
    <div class="grid items-start gap-6 lg:grid-cols-[200px_minmax(0,1fr)_300px]">
      <!-- 左：导航 -->
      <aside class="sticky top-[88px] hidden space-y-4 lg:block">
        <nav class="space-y-1">
          <router-link to="/" class="flex items-center gap-2.5 rounded-xl px-3.5 py-2.5 text-sm font-semibold text-brand-700 bg-brand-50 dark:bg-brand-700/20 dark:text-brand-300">
            <span>🏠</span> 社区首页
          </router-link>
          <router-link to="/ai" class="flex items-center gap-2.5 rounded-xl px-3.5 py-2.5 text-sm font-semibold text-slate-600 hover:bg-white dark:text-slate-300 dark:hover:bg-slate-900">
            <span>✨</span> AI 助手
            <span class="ml-auto rounded-full bg-ai-100 px-1.5 text-[10px] font-bold text-ai-600 dark:bg-ai-500/20 dark:text-ai-400">AI</span>
          </router-link>
          <router-link to="/messages" class="flex items-center gap-2.5 rounded-xl px-3.5 py-2.5 text-sm font-semibold text-slate-600 hover:bg-white dark:text-slate-300 dark:hover:bg-slate-900">
            <span>💬</span> 私信
          </router-link>
          <router-link to="/me" class="flex items-center gap-2.5 rounded-xl px-3.5 py-2.5 text-sm font-semibold text-slate-600 hover:bg-white dark:text-slate-300 dark:hover:bg-slate-900">
            <span>👤</span> 个人主页
          </router-link>
        </nav>
        <button class="btn btn-primary w-full" @click="openComposer">✍️ 发布帖子</button>
        <div class="rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
          <div class="mb-1.5 text-xs font-bold">🌱 关于青禾</div>
          <p class="text-[12px] leading-relaxed text-slate-500">
            一个更懂你的校园社区。AI 帮你查事务、润色文字、找同频的同学，但不会替你发言。
          </p>
        </div>
      </aside>

      <!-- 中：信息流 -->
      <div class="min-w-0 space-y-5">
        <section
          class="relative overflow-hidden rounded-3xl bg-gradient-to-br from-brand-700 via-brand-800 to-slate-900 p-7 text-brand-50 shadow-soft"
        >
          <h1 class="text-2xl font-extrabold leading-tight tracking-tight sm:text-[30px]">
            让每一次校园连接，<br />都被 AI 温柔接住。
          </h1>
          <p class="mt-2 max-w-lg text-sm text-brand-100/80">
            青禾把「校园问答、发帖助手、搭子匹配」放进同一个社区。你不用再翻十个群，也不必独自摸索。
          </p>
          <div class="mt-5 flex flex-wrap gap-2.5">
            <button class="btn btn-ai" @click="router.push('/ai')">✨ 问问青禾 AI</button>
            <button class="btn border-white/25 bg-white/10 text-white hover:bg-white/20" @click="openComposer">
              ✍️ 发一条帖子
            </button>
          </div>
          <div class="mt-5 flex flex-wrap gap-2 text-[11.5px] text-brand-100/80">
            <span class="rounded-full border border-white/20 bg-white/10 px-2.5 py-1">📚 学习互助</span>
            <span class="rounded-full border border-white/20 bg-white/10 px-2.5 py-1">🎭 社团活动</span>
            <span class="rounded-full border border-white/20 bg-white/10 px-2.5 py-1">🛍️ 二手闲置</span>
            <span class="rounded-full border border-white/20 bg-white/10 px-2.5 py-1">🔍 失物招领</span>
            <span class="rounded-full border border-white/20 bg-white/10 px-2.5 py-1">☕ 校园生活</span>
          </div>
        </section>

        <section class="card space-y-3 p-4">
          <div class="flex flex-wrap items-center justify-between gap-3">
            <div class="flex flex-wrap gap-2">
              <button class="chip" :class="{ 'chip-active': category === 'all' }" @click="pickCategory('all')">🌐 全部</button>
              <button
                v-for="item in categories"
                :key="item.id"
                class="chip"
                :class="{ 'chip-active': category === item.id }"
                @click="pickCategory(item.id)"
              >
                {{ item.icon }} {{ item.name }}
              </button>
            </div>
            <div class="flex gap-2">
              <button class="btn btn-sm" :class="{ 'btn-primary': sort === 'latest' }" @click="sort = 'latest'">最新</button>
              <button class="btn btn-sm" :class="{ 'btn-primary': sort === 'hot' }" @click="sort = 'hot'">最热</button>
            </div>
          </div>

          <div v-if="ui.search" class="notice flex items-center justify-between">
            <span>搜索「{{ ui.search }}」共 {{ posts.length }} 条</span>
            <button class="underline" @click="clearSearch">清除</button>
          </div>
        </section>

        <div v-if="loading" class="space-y-3.5">
          <div v-for="n in 3" :key="n" class="card space-y-2.5 p-5">
            <div class="skeleton h-4 w-2/5" />
            <div class="skeleton h-5 w-4/5" />
            <div class="skeleton h-3.5 w-full" />
            <div class="skeleton h-3.5 w-3/5" />
          </div>
        </div>

        <div v-else-if="error" class="card">
          <div class="flex flex-col items-center gap-2 py-12 text-slate-500">
            <div class="text-3xl">😵</div>
            <p class="text-sm">{{ error }}</p>
            <button class="btn btn-sm" @click="load">重新加载</button>
          </div>
        </div>

        <div v-else-if="!posts.length" class="card">
          <div class="flex flex-col items-center gap-2 py-12 text-slate-500">
            <div class="text-3xl">🌾</div>
            <p class="text-sm">这里还很安静，来做第一个发帖的人吧</p>
            <button class="btn btn-sm btn-primary" @click="openComposer">发布帖子</button>
          </div>
        </div>

        <div v-else class="space-y-3.5">
          <PostCard v-for="(post, index) in posts" :key="post.id" :post="post" :index="index" />
        </div>
      </div>

      <!-- 右：数据与热门 -->
      <aside class="sticky top-[88px] hidden space-y-4 lg:block">
        <section class="card p-4">
          <div class="mb-2 flex items-center justify-between">
            <div class="text-sm font-bold">📊 社区数据</div>
            <span class="text-[11px] text-slate-400">实时</span>
          </div>
          <div class="space-y-1.5 text-[13px] text-slate-600 dark:text-slate-300">
            <div class="flex justify-between"><span>注册同学</span><b>{{ stats?.users || 0 }}</b></div>
            <div class="flex justify-between"><span>校园帖子</span><b>{{ stats?.posts || 0 }}</b></div>
            <div class="flex justify-between"><span>互动评论</span><b>{{ stats?.comments || 0 }}</b></div>
            <div class="flex justify-between"><span>AI 调用次数</span><b>{{ stats?.ai_calls || 0 }}</b></div>
          </div>
        </section>

        <section class="ai-panel space-y-2">
          <div class="flex items-center gap-2 text-sm font-bold"><span class="h-2 w-2 rounded-full bg-ai-500" /> 青禾 AI</div>
          <p class="m-0 text-xs text-slate-500">校园事务问答、帖子润色、搭子匹配，一处搞定。</p>
          <button class="btn btn-sm btn-ai" @click="router.push('/ai')">和 AI 聊聊 →</button>
        </section>

        <section v-if="hot.length" class="card p-4">
          <div class="mb-2 text-sm font-bold">🔥 热门话题</div>
          <ul class="space-y-1">
            <li
              v-for="(post, index) in hot"
              :key="post.id"
              class="flex cursor-pointer gap-2 rounded-lg px-1.5 py-1.5 text-[12.5px] leading-snug hover:bg-slate-50 dark:hover:bg-slate-800"
              @click="router.push('/post/' + post.id)"
            >
              <span class="text-slate-400">{{ index + 1 }}</span>
              <span class="line-clamp-2">{{ post.title }}</span>
            </li>
          </ul>
        </section>

        <section class="rounded-2xl border border-slate-200 bg-white p-4 text-[12px] text-slate-500 dark:border-slate-800 dark:bg-slate-900">
          <div class="mb-1 text-xs font-bold text-slate-700 dark:text-slate-200">赛题对应</div>
          传智杯 · AI Web 赛道：场景设计 + AI 集成 + 界面工程。智慧校园方向作品。
        </section>
      </aside>
    </div>
  </main>
</template>
