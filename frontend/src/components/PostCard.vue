<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import type { Post } from '@/api'
import { api } from '@/api'
import { auth, toast } from '@/stores'

const props = defineProps<{ post: Post; index?: number }>()
const router = useRouter()

const liked = ref(props.post.liked)
const likeCount = ref(props.post.like_count)
const busy = ref(false)

const delay = computed(() => ({ animationDelay: (props.index || 0) * 30 + 'ms' }))

async function toggleLike(event: MouseEvent) {
  event.stopPropagation()
  if (!auth.user) {
    toast('登录后才能点赞', 'err')
    router.push('/login')
    return
  }
  if (busy.value) return
  busy.value = true
  try {
    const result = await api.like(props.post.id)
    liked.value = result.liked
    likeCount.value = result.like_count
  } catch (error: any) {
    toast(error.message, 'err')
  } finally {
    busy.value = false
  }
}

function open() {
  router.push('/post/' + props.post.id)
}
</script>

<template>
  <article
    class="card fade-up cursor-pointer p-5 transition hover:-translate-y-0.5 hover:shadow-lift"
    :style="delay"
    @click="open"
  >
    <div class="mb-3 flex items-center gap-2.5">
      <div class="grid h-9 w-9 place-items-center rounded-full border border-slate-200 bg-slate-50 text-lg dark:border-slate-800 dark:bg-slate-800">
        {{ post.author.avatar }}
      </div>
      <div class="min-w-0 flex-1">
        <div class="truncate text-sm font-semibold">{{ post.author.nickname }}</div>
        <div class="text-[11.5px] text-slate-400">
          {{ new Date(post.created_at).toLocaleString('zh-CN', { month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit' }) }}
          <span v-if="post.author.major"> · {{ post.author.major }}</span>
        </div>
      </div>
      <span class="rounded-full bg-brand-50 px-2.5 py-0.5 text-[11.5px] font-semibold text-brand-700 dark:bg-brand-700/20 dark:text-brand-300">
        {{ post.category_icon }} {{ post.category_name }}
      </span>
    </div>

    <h3 class="mb-1.5 text-[17px] font-bold leading-snug tracking-tight">{{ post.title }}</h3>
    <p class="line-clamp-2 text-[13.5px] leading-relaxed text-slate-500 dark:text-slate-400">
      {{ post.summary }}
    </p>

    <div v-if="post.tags.length" class="mt-3 flex flex-wrap gap-1.5">
      <span v-for="tag in post.tags" :key="tag" class="tag"># {{ tag }}</span>
    </div>

    <div class="mt-3.5 flex items-center gap-4 border-t border-dashed border-slate-200 pt-3 dark:border-slate-800">
      <button class="metric hover:text-rose-500" :class="{ 'font-bold text-rose-500': liked }" @click="toggleLike">
        {{ liked ? '❤️' : '🤍' }} {{ likeCount }}
      </button>
      <span class="metric">💬 {{ post.comment_count }}</span>
      <span class="metric">👀 {{ post.views }}</span>
      <span class="metric ml-auto">🔥 热度 {{ post.heat }}</span>
    </div>
  </article>
</template>
