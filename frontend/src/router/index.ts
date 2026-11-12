import { createRouter, createWebHistory } from 'vue-router'
import { auth } from '@/stores'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'home', component: () => import('@/views/HomeView.vue') },
    { path: '/post/:id', name: 'post', component: () => import('@/views/PostView.vue') },
    { path: '/ai', name: 'ai', component: () => import('@/views/AiView.vue') },
    { path: '/login', name: 'login', component: () => import('@/views/LoginView.vue') },
    { path: '/me', name: 'me', component: () => import('@/views/ProfileView.vue'), meta: { auth: true } },
    { path: '/user/:id', name: 'user', component: () => import('@/views/ProfileView.vue') },
    { path: '/messages', name: 'messages', component: () => import('@/views/MessagesView.vue'), meta: { auth: true } },
    { path: '/admin', name: 'admin', component: () => import('@/views/AdminView.vue'), meta: { auth: true, admin: true } },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
  scrollBehavior: () => ({ top: 0 }),
})

router.beforeEach((to) => {
  if (to.meta.auth && !auth.user) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  if (to.meta.admin && !auth.user?.is_admin) {
    return { name: 'home' }
  }
  return true
})

export default router
