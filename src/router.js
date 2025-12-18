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
    path: '/platform/backtest',
    name: 'Backtest',
    component: () => import('./components/Backtest.vue'),
    meta: { keepAlive: false }
  },
  {
    path: '/platform/cache',
    name: 'CacheManager',
    component: () => import('./components/CacheManager.vue'),
    meta: { keepAlive: false }
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
  routes,
  scrollBehavior(to, from, savedPosition) {
    // 如果有保存的位置（比如浏览器前进/后退），则使用保存的位置
    if (savedPosition) {
      return savedPosition
    }
    // 否则立即滚动到顶部（无动画）
    return { top: 0 }
  }
})

export default router

