<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { auth, ui, toggleTheme, logout, toast } from '@/stores'

const router = useRouter()
const keyword = ref('')
const menuOpen = ref(false)

function search() {
  ui.search = keyword.value.trim()
  if (router.currentRoute.value.name !== 'home') router.push('/')
}

function openComposer() {
  if (!auth.user) {
    toast('登录后才能发帖哦', 'err')
    router.push('/login')
    return
  }
  ui.composerOpen = true
}

function go(path: string) {
  menuOpen.value = false
  router.push(path)
}

function signOut() {
  logout()
  menuOpen.value = false
  toast('已退出登录')
  router.push('/')
}
</script>

<template>
  <header
    class="sticky top-0 z-40 h-16 border-b border-slate-200 bg-slate-50/80 backdrop-blur-md dark:border-slate-800 dark:bg-slate-950/80"
  >
    <div class="mx-auto flex h-full max-w-[1200px] items-center gap-4 px-5">
      <a class="flex shrink-0 items-center gap-2.5" href="#" @click.prevent="go('/')">
        <span
          class="grid h-9 w-9 place-items-center rounded-xl bg-gradient-to-br from-brand-700 to-brand-500 text-lg text-white shadow-[0_6px_16px_rgba(15,118,110,.35)]"
          >🌱</span
        >
        <span class="leading-tight">
          <span class="block text-[17px] font-extrabold tracking-tight">青禾</span>
          <span class="block text-[11px] font-semibold tracking-widest text-slate-400">AI 校园社区</span>
        </span>
      </a>

      <div class="relative hidden max-w-[420px] flex-1 sm:block">
        <span class="absolute left-3.5 top-1/2 -translate-y-1/2 text-sm text-slate-400">🔍</span>
        <input
          v-model="keyword"
          class="input h-9 rounded-full py-0 pl-10"
          placeholder="搜索帖子、话题、同学…"
          @keyup.enter="search"
        />
      </div>

      <div class="ml-auto flex items-center gap-2">
        <button class="btn btn-sm hidden sm:inline-flex" @click="openComposer">✍️ 发帖</button>
        <button class="btn btn-sm btn-ai" @click="go('/ai')">✨ AI 助手</button>
        <button
          class="btn btn-sm btn-ghost h-9 w-9 px-0"
          :title="ui.theme === 'dark' ? '切换到浅色' : '切换到深色'"
          @click="toggleTheme"
        >
          {{ ui.theme === 'dark' ? '☀️' : '🌙' }}
        </button>

        <template v-if="auth.user">
          <button class="btn btn-sm btn-ghost h-9 w-9 px-0" title="私信" @click="go('/messages')">💬</button>
          <div class="relative">
            <button
              class="grid h-9 w-9 place-items-center rounded-xl border border-slate-200 text-base dark:border-slate-800"
              @click="menuOpen = !menuOpen"
            >
              {{ auth.user.avatar }}
            </button>
            <div
              v-if="menuOpen"
              class="card absolute right-0 top-11 z-50 w-44 p-1.5"
              @mouseleave="menuOpen = false"
            >
              <button class="btn btn-ghost btn-sm w-full justify-start" @click="go('/me')">👤 个人主页</button>
              <button class="btn btn-ghost btn-sm w-full justify-start" @click="go('/messages')">💬 私信</button>
              <button
                v-if="auth.user.is_admin"
                class="btn btn-ghost btn-sm w-full justify-start"
                @click="go('/admin')"
              >
                🛠️ 后台管理
              </button>
              <button class="btn btn-ghost btn-sm w-full justify-start" @click="signOut">🚪 退出登录</button>
            </div>
          </div>
        </template>
        <template v-else>
          <button class="btn btn-sm btn-primary" @click="go('/login')">登录</button>
        </template>
      </div>
    </div>
  </header>
</template>
