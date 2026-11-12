<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import NavBar from '@/components/NavBar.vue'
import Composer from '@/components/Composer.vue'
import ToastHost from '@/components/ToastHost.vue'
import { ui } from '@/stores'

const route = useRoute()
const router = useRouter()
const showFab = computed(() => route.name !== 'ai' && route.name !== 'login')
</script>

<template>
  <div class="min-h-screen">
    <NavBar />
    <router-view />

    <Composer :open="ui.composerOpen" @close="ui.composerOpen = false" @created="ui.version++" />

    <button
      v-if="showFab"
      class="fixed bottom-6 right-6 z-50 inline-flex h-12 items-center gap-2 rounded-full bg-gradient-to-br from-ai-600 to-fuchsia-500 px-5 text-sm font-bold text-white shadow-[0_12px_30px_rgba(124,58,237,.4)] transition hover:-translate-y-0.5"
      @click="router.push('/ai')"
    >
      ✨ 问问青禾
    </button>

    <ToastHost />
  </div>
</template>
