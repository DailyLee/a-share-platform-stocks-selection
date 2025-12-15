import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'

const routes = [
  {
    path: '/platform/',
    name: 'Home',
    component: App,
    meta: { keepAlive: true }
  },
  {
    path: '/platform/check',
    name: 'PlatformCheck',
    component: () => import('./components/PlatformCheck.vue'),
    meta: { keepAlive: true }
  },
  {
    path: '/platform',
    redirect: '/platform/'
  },
  {
    path: '/',
    redirect: '/platform/'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router

