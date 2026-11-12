<script setup lang="ts">
import { ui } from '@/stores'
</script>

<template>
  <div class="pointer-events-none fixed bottom-5 right-5 z-[80] flex flex-col gap-2.5">
    <div
      v-for="item in ui.toasts"
      :key="item.id"
      class="pointer-events-auto min-w-[220px] max-w-[340px] rounded-xl border border-slate-200 bg-white px-4 py-3 text-[13.5px] shadow-lift dark:border-slate-800 dark:bg-slate-900"
      :class="item.type === 'err' ? 'border-l-4 border-l-rose-500' : 'border-l-4 border-l-emerald-500'"
    >
      {{ item.message }}
    </div>
  </div>
</template>
