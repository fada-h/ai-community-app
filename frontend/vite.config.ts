import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// 前端 5173；/api 与 /ws 代理到 FastAPI 8000，避免跨域与额外配置
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    host: '127.0.0.1',
    port: 5173,
    watch: {
      // 忽略编辑器/工具产生的临时目录，避免 Windows 上 EBUSY 监听错误
      ignored: ['**/*.tmpdir/**', '**/.tailwind.config.js.*'],
    },
    proxy: {
      '/api': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/ws': { target: 'ws://127.0.0.1:8000', ws: true, changeOrigin: true },
    },
  },
})
