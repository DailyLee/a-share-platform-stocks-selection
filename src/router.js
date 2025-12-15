import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'

const routes = [
  {
    path: '/platform/',
    name: 'Home',
    component: App
  },
  {
    path: '/platform/check',
    name: 'PlatformCheck',
    component: () => import('./components/PlatformCheck.vue')
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

