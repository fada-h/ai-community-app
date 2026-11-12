import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import { bootstrap } from './stores'
import './style.css'

bootstrap()
  .catch(() => {})
  .finally(() => {
    const app = createApp(App)
    app.use(router)
    app.mount('#app')
  })
