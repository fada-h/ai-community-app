<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { login, register, toast, auth } from '@/stores'

const route = useRoute()
const router = useRouter()

const mode = ref<'login' | 'register'>('login')
const loading = ref(false)
const error = ref('')
const form = reactive({ username: '', password: '', nickname: '' })

async function submit() {
  error.value = ''
  if (!form.username.trim() || !form.password) {
    error.value = '请填写用户名和密码'
    return
  }
  loading.value = true
  try {
    if (mode.value === 'login') {
      await login(form.username.trim(), form.password)
      toast('欢迎回来 🌿')
    } else {
      await register({
        username: form.username.trim(),
        password: form.password,
        nickname: form.nickname.trim() || form.username.trim(),
      })
      toast('注册成功，欢迎加入青禾')
    }
    const redirect = (route.query.redirect as string) || '/'
    router.push(redirect)
  } catch (err: any) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

function useDemo() {
  form.username = 'linxiaoman'
  form.password = '123456'
  mode.value = 'login'
}
</script>

<template>
  <main class="mx-auto max-w-[440px] px-5 pb-24 pt-10">
    <section v-if="!auth.user" class="card space-y-4 p-7">
      <div class="text-center">
        <div class="mx-auto mb-2 grid h-11 w-11 place-items-center rounded-xl bg-gradient-to-br from-brand-700 to-brand-500 text-xl text-white">🌱</div>
        <h1 class="text-xl font-extrabold tracking-tight">欢迎来到青禾</h1>
        <p class="text-xs text-slate-400">一个更懂你的 AI 校园社区</p>
      </div>

      <div class="flex justify-center gap-2">
        <button class="chip" :class="{ 'chip-active': mode === 'login' }" @click="mode = 'login'">登录</button>
        <button class="chip" :class="{ 'chip-active': mode === 'register' }" @click="mode = 'register'">注册</button>
      </div>

      <div class="space-y-1.5">
        <label class="field-label">用户名</label>
        <input v-model="form.username" class="input" placeholder="字母、数字或下划线" @keyup.enter="submit" />
      </div>
      <div v-if="mode === 'register'" class="space-y-1.5">
        <label class="field-label">昵称</label>
        <input v-model="form.nickname" class="input" placeholder="别人怎么称呼你" @keyup.enter="submit" />
      </div>
      <div class="space-y-1.5">
        <label class="field-label">密码</label>
        <input v-model="form.password" type="password" class="input" placeholder="至少 6 位" @keyup.enter="submit" />
      </div>

      <div v-if="error" class="text-xs text-rose-500">{{ error }}</div>

      <button class="btn btn-primary w-full" :disabled="loading" @click="submit">
        {{ loading ? '请稍候…' : mode === 'login' ? '登录' : '注册并登录' }}
      </button>

      <div class="flex items-center justify-between">
        <span class="hint">演示账号：linxiaoman / 123456</span>
        <button class="btn btn-sm btn-ghost" @click="useDemo">一键填入</button>
      </div>
    </section>

    <section v-else class="card space-y-3 p-7 text-center">
      <div class="text-3xl">{{ auth.user.avatar }}</div>
      <div class="text-sm font-bold">你已经登录为 {{ auth.user.nickname }}</div>
      <button class="btn btn-primary" @click="router.push('/')">回到社区</button>
    </section>
  </main>
</template>
