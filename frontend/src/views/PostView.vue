<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api, type Comment, type Post } from '@/api'
import { auth, toast } from '@/stores'

const route = useRoute()
const router = useRouter()

const post = ref<Post | null>(null)
const comments = ref<Comment[]>([])
const related = ref<Post[]>([])
const loading = ref(true)
const error = ref('')
const commentText = ref('')
const submitting = ref(false)
const likeBusy = ref(false)

async function load() {
  loading.value = true
  error.value = ''
  try {
    const data = await api.post(Number(route.params.id))
    post.value = data.post
    comments.value = data.comments
    related.value = data.related
  } catch (err: any) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

async function toggleLike() {
  if (!auth.user) {
    toast('登录后才能点赞', 'err')
    router.push('/login')
    return
  }
  if (likeBusy.value || !post.value) return
  likeBusy.value = true
  try {
    const result = await api.like(post.value.id)
    post.value.liked = result.liked
    post.value.like_count = result.like_count
  } catch (err: any) {
    toast(err.message, 'err')
  } finally {
    likeBusy.value = false
  }
}

async function addComment() {
  if (!auth.user) {
    toast('登录后才能评论', 'err')
    router.push('/login')
    return
  }
  const content = commentText.value.trim()
  if (!content || !post.value) return
  submitting.value = true
  try {
    const data = await api.addComment(post.value.id, content)
    comments.value.push(data)
    commentText.value = ''
    toast('评论成功')
  } catch (err: any) {
    toast(err.message, 'err')
  } finally {
    submitting.value = false
  }
}

function goUser(id: number) {
  if (auth.user && auth.user.id === id) router.push('/me')
  else router.push('/user/' + id)
}

function fmt(iso: string) {
  return new Date(iso).toLocaleString('zh-CN', {
    month: 'numeric',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

onMounted(load)
watch(() => route.params.id, load)
</script>

<template>
  <main class="mx-auto max-w-[1000px] px-5 pb-24 pt-6">
    <button class="btn btn-sm mb-4" @click="router.push('/')">← 返回社区</button>

    <div v-if="loading" class="card space-y-3 p-6">
      <div class="skeleton h-7 w-3/5" />
      <div class="skeleton h-4 w-full" />
      <div class="skeleton h-4 w-11/12" />
    </div>

    <div v-else-if="error" class="card">
      <div class="flex flex-col items-center gap-2 py-16 text-slate-500">
        <div class="text-3xl">🫥</div>
        <p class="text-sm">{{ error }}</p>
      </div>
    </div>

    <template v-else-if="post">
      <article class="card p-7">
        <div class="mb-5 flex items-center gap-3 border-b border-slate-200 pb-4 dark:border-slate-800">
          <button class="grid h-11 w-11 place-items-center rounded-full border border-slate-200 bg-slate-50 text-xl dark:border-slate-800 dark:bg-slate-800" @click="goUser(post.author.id)">
            {{ post.author.avatar }}
          </button>
          <div class="min-w-0 flex-1">
            <div class="text-sm font-bold">{{ post.author.nickname }}</div>
            <div class="text-xs text-slate-400">{{ fmt(post.created_at) }} · {{ post.author.major || '未填写专业' }}</div>
          </div>
          <span class="rounded-full bg-brand-50 px-2.5 py-1 text-[11.5px] font-semibold text-brand-700 dark:bg-brand-700/20 dark:text-brand-300">
            {{ post.category_icon }} {{ post.category_name }}
          </span>
        </div>

        <h1 class="mb-3 text-2xl font-extrabold leading-snug tracking-tight">{{ post.title }}</h1>
        <div v-if="post.tags.length" class="mb-4 flex flex-wrap gap-1.5">
          <span v-for="tag in post.tags" :key="tag" class="tag"># {{ tag }}</span>
        </div>

        <div class="whitespace-pre-wrap text-[15.5px] leading-[1.9]">{{ post.content }}</div>

        <div class="mt-6 flex flex-wrap items-center gap-4 border-t border-dashed border-slate-200 pt-4 dark:border-slate-800">
          <button class="btn btn-sm" :class="{ 'btn-primary': post.liked }" @click="toggleLike">
            {{ post.liked ? '❤️ 已赞' : '🤍 点赞' }} {{ post.like_count }}
          </button>
          <span class="metric">💬 {{ comments.length }} 条评论</span>
          <span class="metric">👀 {{ post.views }}</span>
          <span class="metric ml-auto">🔥 热度 {{ post.heat }}</span>
        </div>
      </article>

      <section class="card mt-4 p-6">
        <div class="mb-3 text-sm font-bold">💬 评论（{{ comments.length }}）</div>

        <div class="mb-4 flex gap-2">
          <input v-model="commentText" class="input flex-1" maxlength="500" placeholder="友善交流，说说你的想法…" @keyup.enter="addComment" />
          <button class="btn btn-primary btn-sm" :disabled="submitting || !commentText.trim()" @click="addComment">
            {{ submitting ? '发送中…' : '发送' }}
          </button>
        </div>

        <div v-if="!comments.length" class="flex flex-col items-center gap-1 py-8 text-slate-400">
          <div class="text-2xl">🌿</div>
          <p class="text-sm">还没有评论，来做第一个回应的人</p>
        </div>

        <div v-for="comment in comments" :key="comment.id" class="flex gap-3 border-b border-slate-100 py-3.5 last:border-0 dark:border-slate-800">
          <div class="grid h-8 w-8 shrink-0 place-items-center rounded-full border border-slate-200 bg-slate-50 text-sm dark:border-slate-800 dark:bg-slate-800">
            {{ comment.author.avatar }}
          </div>
          <div class="min-w-0 flex-1">
            <div class="flex items-center justify-between">
              <span class="text-[13px] font-semibold">{{ comment.author.nickname }}</span>
              <span class="text-[11px] text-slate-400">{{ fmt(comment.created_at) }}</span>
            </div>
            <div class="mt-0.5 text-sm text-slate-600 dark:text-slate-300">{{ comment.content }}</div>
          </div>
        </div>
      </section>

      <section v-if="related.length" class="card mt-4 p-6">
        <div class="mb-2.5 text-sm font-bold">🔗 相关帖子</div>
        <ul class="space-y-1">
          <li
            v-for="item in related"
            :key="item.id"
            class="cursor-pointer rounded-lg px-2 py-2 text-[13px] hover:bg-slate-50 dark:hover:bg-slate-800"
            @click="router.push('/post/' + item.id)"
          >
            📌 {{ item.title }}
          </li>
        </ul>
      </section>
    </template>
  </main>
</template>
