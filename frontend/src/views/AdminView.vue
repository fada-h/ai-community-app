<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { api, type Post, type User } from '@/api'
import { toast } from '@/stores'

const loading = ref(true)
const totals = ref({ users: 0, posts: 0, comments: 0, ai_calls: 0 })
const recentPosts = ref<Post[]>([])
const users = ref<(User & { post_count: number })[]>([])

async function load() {
  loading.value = true
  try {
    const [overview, userList] = await Promise.all([api.adminOverview(), api.adminUsers()])
    totals.value = overview.totals
    recentPosts.value = overview.recent_posts
    users.value = userList
  } catch (err: any) {
    toast(err.message, 'err')
  } finally {
    loading.value = false
  }
}

async function removePost(post: Post) {
  if (!confirm('确定删除《' + post.title + '》吗？')) return
  try {
    await api.adminDeletePost(post.id)
    recentPosts.value = recentPosts.value.filter((item) => item.id !== post.id)
    totals.value.posts -= 1
    toast('已删除')
  } catch (err: any) {
    toast(err.message, 'err')
  }
}

async function toggleAdmin(user: User) {
  try {
    const result = await api.adminToggleAdmin(user.id)
    const target = users.value.find((item) => item.id === user.id)
    if (target) target.is_admin = result.is_admin
    toast(result.is_admin ? '已设为管理员' : '已取消管理员')
  } catch (err: any) {
    toast(err.message, 'err')
  }
}

onMounted(load)
</script>

<template>
  <main class="mx-auto max-w-[1100px] px-5 pb-24 pt-6">
    <div class="mb-5 flex items-center justify-between">
      <div>
        <h1 class="text-xl font-extrabold tracking-tight">🛠️ 后台管理</h1>
        <p class="text-xs text-slate-400">内容审核与用户管理（仅管理员可见）</p>
      </div>
      <button class="btn btn-sm" @click="load">刷新</button>
    </div>

    <div class="grid grid-cols-2 gap-3 sm:grid-cols-4">
      <div class="card p-4">
        <div class="text-xs text-slate-400">注册用户</div>
        <div class="text-2xl font-extrabold">{{ totals.users }}</div>
      </div>
      <div class="card p-4">
        <div class="text-xs text-slate-400">帖子总数</div>
        <div class="text-2xl font-extrabold">{{ totals.posts }}</div>
      </div>
      <div class="card p-4">
        <div class="text-xs text-slate-400">评论总数</div>
        <div class="text-2xl font-extrabold">{{ totals.comments }}</div>
      </div>
      <div class="card p-4">
        <div class="text-xs text-slate-400">AI 调用</div>
        <div class="text-2xl font-extrabold">{{ totals.ai_calls }}</div>
      </div>
    </div>

    <section class="card mt-4 overflow-hidden">
      <div class="border-b border-slate-200 px-4 py-3 text-sm font-bold dark:border-slate-800">最新帖子</div>
      <div v-if="loading" class="p-4"><div class="skeleton h-20" /></div>
      <table v-else class="w-full text-left text-[13px]">
        <thead class="bg-slate-50 text-[11px] uppercase tracking-wide text-slate-400 dark:bg-slate-800/50">
          <tr>
            <th class="px-4 py-2 font-medium">标题</th>
            <th class="px-4 py-2 font-medium">作者</th>
            <th class="px-4 py-2 font-medium">分类</th>
            <th class="px-4 py-2 font-medium">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="post in recentPosts" :key="post.id" class="border-t border-slate-100 dark:border-slate-800">
            <td class="max-w-[380px] truncate px-4 py-2.5">{{ post.title }}</td>
            <td class="px-4 py-2.5">{{ post.author.nickname }}</td>
            <td class="px-4 py-2.5">{{ post.category_icon }} {{ post.category_name }}</td>
            <td class="px-4 py-2.5">
              <button class="text-xs text-rose-500 hover:underline" @click="removePost(post)">删除</button>
            </td>
          </tr>
        </tbody>
      </table>
    </section>

    <section class="card mt-4 overflow-hidden">
      <div class="border-b border-slate-200 px-4 py-3 text-sm font-bold dark:border-slate-800">用户</div>
      <table class="w-full text-left text-[13px]">
        <thead class="bg-slate-50 text-[11px] uppercase tracking-wide text-slate-400 dark:bg-slate-800/50">
          <tr>
            <th class="px-4 py-2 font-medium">用户</th>
            <th class="px-4 py-2 font-medium">专业</th>
            <th class="px-4 py-2 font-medium">帖子数</th>
            <th class="px-4 py-2 font-medium">角色</th>
            <th class="px-4 py-2 font-medium">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in users" :key="user.id" class="border-t border-slate-100 dark:border-slate-800">
            <td class="px-4 py-2.5">{{ user.avatar }} {{ user.nickname }}</td>
            <td class="px-4 py-2.5 text-slate-500">{{ user.major || '—' }}</td>
            <td class="px-4 py-2.5">{{ user.post_count }}</td>
            <td class="px-4 py-2.5">
              <span v-if="user.is_admin" class="rounded-full bg-ai-100 px-2 py-0.5 text-[10px] font-bold text-ai-600 dark:bg-ai-500/20 dark:text-ai-400">管理员</span>
              <span v-else class="text-slate-400">普通用户</span>
            </td>
            <td class="px-4 py-2.5">
              <button class="text-xs text-brand-700 hover:underline dark:text-brand-400" @click="toggleAdmin(user)">
                {{ user.is_admin ? '取消管理员' : '设为管理员' }}
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </section>
  </main>
</template>
