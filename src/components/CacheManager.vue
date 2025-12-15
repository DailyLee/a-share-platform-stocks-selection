<template>
  <div class="min-h-screen bg-background text-foreground">
    <!-- 顶部导航栏 -->
    <header class="bg-card border-b border-border p-4 flex justify-between items-center sticky top-0 z-30">
      <div class="flex items-center">
        <img src="/gundam-logo.svg" alt="Gundam Logo" class="w-8 h-8 mr-2" />
        <h1 class="text-xl font-semibold">缓存管理</h1>
      </div>

      <div class="flex items-center space-x-2 sm:space-x-3">
        <!-- 返回首页 -->
        <router-link to="/platform/" class="flex items-center justify-center px-2 sm:px-3 py-1.5 sm:py-2 rounded-md bg-gundam-blue text-white hover:bg-gundam-blue/80 transition-colors">
          <i class="fas fa-arrow-left mr-1 sm:mr-2"></i>
          <span class="hidden sm:inline">返回</span>
        </router-link>

        <!-- 主题切换 -->
        <ThemeToggle />
      </div>
    </header>

    <!-- 主内容区 -->
    <main class="p-4 sm:p-6 md:p-8">
      <div class="max-w-4xl mx-auto">
        <!-- 操作卡片 -->
        <div class="card p-4 sm:p-6 mb-6">
          <h2 class="text-lg font-semibold mb-4 flex items-center">
            <i class="fas fa-cog mr-2 text-primary"></i>
            缓存操作
          </h2>
          <div class="flex flex-col sm:flex-row gap-4">
            <button
              @click="refreshStats"
              :disabled="loading"
              class="btn btn-primary flex items-center justify-center px-4 sm:px-6 py-2 h-10"
            >
              <i class="fas fa-sync-alt mr-2" :class="{ 'fa-spin': loading }"></i>
              刷新统计
            </button>
            <button
              @click="showClearConfirm = true"
              :disabled="loading || clearing"
              class="btn bg-destructive hover:bg-destructive/80 text-destructive-foreground flex items-center justify-center px-4 sm:px-6 py-2 h-10"
            >
              <i class="fas fa-trash-alt mr-2"></i>
              清除所有缓存
            </button>
          </div>
        </div>

        <!-- 错误提示 -->
        <transition name="fade">
          <div v-if="error" class="bg-destructive/10 border border-destructive text-destructive px-4 py-3 rounded-md mb-6" role="alert">
            <div class="flex items-center">
              <i class="fas fa-exclamation-circle mr-2"></i>
              <strong class="font-bold">错误:</strong>
              <span class="ml-2">{{ error }}</span>
            </div>
          </div>
        </transition>

        <!-- 成功提示 -->
        <transition name="fade">
          <div v-if="successMessage" class="bg-green-500/10 border border-green-500 text-green-700 dark:text-green-400 px-4 py-3 rounded-md mb-6" role="alert">
            <div class="flex items-center">
              <i class="fas fa-check-circle mr-2"></i>
              <span>{{ successMessage }}</span>
            </div>
          </div>
        </transition>

        <!-- 缓存统计卡片 -->
        <div v-if="stats" class="space-y-6">
          <!-- 总体统计 -->
          <div class="card p-4 sm:p-6">
            <h2 class="text-lg font-semibold mb-4 flex items-center">
              <i class="fas fa-chart-bar mr-2 text-primary"></i>
              缓存统计
            </h2>
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              <!-- 缓存命中率 -->
              <div class="bg-muted/30 p-4 rounded-lg">
                <div class="flex items-center justify-between mb-2">
                  <span class="text-sm text-muted-foreground">缓存命中率</span>
                  <i class="fas fa-bullseye text-primary"></i>
                </div>
                <div class="text-2xl font-bold text-primary">
                  {{ stats.cache_stats.hit_rate }}%
                </div>
                <div class="text-xs text-muted-foreground mt-1">
                  {{ stats.cache_stats.hits }} 次命中 / {{ stats.cache_stats.total_requests }} 次请求
                </div>
              </div>

              <!-- 缓存大小 -->
              <div class="bg-muted/30 p-4 rounded-lg">
                <div class="flex items-center justify-between mb-2">
                  <span class="text-sm text-muted-foreground">缓存条目数</span>
                  <i class="fas fa-database text-primary"></i>
                </div>
                <div class="text-2xl font-bold text-primary">
                  {{ stats.cache_stats.size }}
                </div>
                <div class="text-xs text-muted-foreground mt-1">
                  <span v-if="stats.cache_stats.file_cache_size !== undefined">
                    文件: {{ stats.cache_stats.file_cache_size }} / 
                    内存: {{ stats.cache_stats.memory_cache_size }}
                  </span>
                  <span v-else>当前缓存的条目数量</span>
                </div>
              </div>

              <!-- 总请求数 -->
              <div class="bg-muted/30 p-4 rounded-lg">
                <div class="flex items-center justify-between mb-2">
                  <span class="text-sm text-muted-foreground">总请求数</span>
                  <i class="fas fa-chart-line text-primary"></i>
                </div>
                <div class="text-2xl font-bold text-primary">
                  {{ stats.cache_stats.total_requests }}
                </div>
                <div class="text-xs text-muted-foreground mt-1">
                  累计请求次数
                </div>
              </div>
            </div>
          </div>

          <!-- 详细统计 -->
          <div class="card p-4 sm:p-6">
            <h2 class="text-lg font-semibold mb-4 flex items-center">
              <i class="fas fa-info-circle mr-2 text-primary"></i>
              详细统计
            </h2>
            <div class="space-y-4">
              <!-- 命中次数 -->
              <div class="flex items-center justify-between p-3 bg-muted/30 rounded-lg">
                <div class="flex items-center">
                  <i class="fas fa-check-circle text-green-500 mr-3"></i>
                  <span class="font-medium">缓存命中次数</span>
                </div>
                <span class="text-lg font-semibold text-green-500">{{ stats.cache_stats.hits }}</span>
              </div>

              <!-- 未命中次数 -->
              <div class="flex items-center justify-between p-3 bg-muted/30 rounded-lg">
                <div class="flex items-center">
                  <i class="fas fa-times-circle text-orange-500 mr-3"></i>
                  <span class="font-medium">缓存未命中次数</span>
                </div>
                <span class="text-lg font-semibold text-orange-500">{{ stats.cache_stats.misses }}</span>
              </div>

              <!-- 过期清理次数 -->
              <div class="flex items-center justify-between p-3 bg-muted/30 rounded-lg">
                <div class="flex items-center">
                  <i class="fas fa-broom text-blue-500 mr-3"></i>
                  <span class="font-medium">过期条目清理次数</span>
                </div>
                <span class="text-lg font-semibold text-blue-500">{{ stats.cache_stats.evictions }}</span>
              </div>

              <!-- 本次清理的过期条目 -->
              <div v-if="stats.expired_entries_cleaned > 0" class="flex items-center justify-between p-3 bg-muted/30 rounded-lg">
                <div class="flex items-center">
                  <i class="fas fa-trash text-red-500 mr-3"></i>
                  <span class="font-medium">本次清理的过期条目</span>
                </div>
                <span class="text-lg font-semibold text-red-500">{{ stats.expired_entries_cleaned }}</span>
              </div>

              <!-- 文件读取次数 -->
              <div v-if="stats.cache_stats.file_reads !== undefined" class="flex items-center justify-between p-3 bg-muted/30 rounded-lg">
                <div class="flex items-center">
                  <i class="fas fa-file-alt text-purple-500 mr-3"></i>
                  <span class="font-medium">文件读取次数</span>
                </div>
                <span class="text-lg font-semibold text-purple-500">{{ stats.cache_stats.file_reads }}</span>
              </div>

              <!-- 文件写入次数 -->
              <div v-if="stats.cache_stats.file_writes !== undefined" class="flex items-center justify-between p-3 bg-muted/30 rounded-lg">
                <div class="flex items-center">
                  <i class="fas fa-save text-indigo-500 mr-3"></i>
                  <span class="font-medium">文件写入次数</span>
                </div>
                <span class="text-lg font-semibold text-indigo-500">{{ stats.cache_stats.file_writes }}</span>
              </div>
            </div>
          </div>

          <!-- 缓存说明 -->
          <div class="card p-4 sm:p-6">
            <h2 class="text-lg font-semibold mb-4 flex items-center">
              <i class="fas fa-question-circle mr-2 text-primary"></i>
              缓存说明
            </h2>
            <div class="space-y-3 text-sm text-muted-foreground">
              <div class="flex items-start">
                <i class="fas fa-circle text-primary mr-2 mt-1 text-xs"></i>
                <div>
                  <span class="font-medium text-foreground">存储方式:</span> 缓存数据以JSON文件形式存储在服务器的 <code class="px-1 py-0.5 bg-muted rounded text-xs">cache/</code> 目录中，支持持久化和跨进程共享
                </div>
              </div>
              <div class="flex items-start">
                <i class="fas fa-circle text-primary mr-2 mt-1 text-xs"></i>
                <div>
                  <span class="font-medium text-foreground">有效期:</span> 由于数据来自昨天，所有缓存条目在<strong class="text-foreground">当天都有效</strong>（直到当天23:59:59），跨天后自动失效
                </div>
              </div>
              <div class="flex items-start">
                <i class="fas fa-circle text-primary mr-2 mt-1 text-xs"></i>
                <div>
                  <span class="font-medium text-foreground">股票基本信息:</span> 当天有效，因为股票基本信息变化不频繁
                </div>
              </div>
              <div class="flex items-start">
                <i class="fas fa-circle text-primary mr-2 mt-1 text-xs"></i>
                <div>
                  <span class="font-medium text-foreground">行业数据:</span> 当天有效，因为行业分类数据变化不频繁
                </div>
              </div>
              <div class="flex items-start">
                <i class="fas fa-circle text-primary mr-2 mt-1 text-xs"></i>
                <div>
                  <span class="font-medium text-foreground">K线数据:</span> 当天有效，基于股票代码和日期范围缓存
                </div>
              </div>
              <div class="flex items-start">
                <i class="fas fa-circle text-primary mr-2 mt-1 text-xs"></i>
                <div>
                  <span class="font-medium text-foreground">自动清理:</span> 过期条目（跨天或过期）会在查询时自动清理，无需手动操作
                </div>
              </div>
              <div class="flex items-start">
                <i class="fas fa-circle text-primary mr-2 mt-1 text-xs"></i>
                <div>
                  <span class="font-medium text-foreground">服务器重启:</span> 文件缓存会保留，服务器重启后仍可使用（当天有效）
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 加载状态 -->
        <div v-else-if="loading" class="card p-8 text-center">
          <i class="fas fa-spinner fa-spin text-4xl text-primary mb-4"></i>
          <p class="text-muted-foreground">正在加载缓存统计...</p>
        </div>

        <!-- 空状态 -->
        <div v-else class="card p-8 text-center">
          <i class="fas fa-database text-4xl text-muted-foreground mb-4"></i>
          <p class="text-muted-foreground">暂无缓存数据，请点击"刷新统计"按钮</p>
        </div>
      </div>
    </main>

    <!-- 清除确认对话框 -->
    <transition name="fade">
      <div v-if="showClearConfirm" class="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
        <div class="bg-card rounded-lg shadow-xl max-w-md w-full p-6">
          <h3 class="text-lg font-semibold mb-4 flex items-center">
            <i class="fas fa-exclamation-triangle text-yellow-500 mr-2"></i>
            确认清除缓存
          </h3>
          <p class="text-muted-foreground mb-6">
            确定要清除所有缓存吗？这将删除所有已缓存的JSON文件（包括内存和文件缓存），下次请求将重新从数据源获取并缓存。
          </p>
          <div class="flex gap-3 justify-end">
            <button
              @click="showClearConfirm = false"
              :disabled="clearing"
              class="btn bg-muted hover:bg-muted/80 text-muted-foreground px-4 py-2 h-10"
            >
              取消
            </button>
            <button
              @click="clearCache"
              :disabled="clearing"
              class="btn bg-destructive hover:bg-destructive/80 text-destructive-foreground px-4 py-2 h-10 flex items-center justify-center"
            >
              <i class="fas fa-spinner fa-spin mr-2" v-if="clearing"></i>
              {{ clearing ? '清除中...' : '确认清除' }}
            </button>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import ThemeToggle from './ThemeToggle.vue'

const stats = ref(null)
const loading = ref(false)
const clearing = ref(false)
const error = ref(null)
const successMessage = ref(null)
const showClearConfirm = ref(false)

// 获取缓存统计
const refreshStats = async () => {
  loading.value = true
  error.value = null
  successMessage.value = null

  try {
    const response = await axios.get('/platform/api/cache/stats')
    stats.value = response.data
  } catch (err) {
    error.value = err.response?.data?.detail || err.message || '获取缓存统计失败'
    console.error('Error fetching cache stats:', err)
  } finally {
    loading.value = false
  }
}

// 清除缓存
const clearCache = async () => {
  clearing.value = true
  error.value = null
  successMessage.value = null

  try {
    const response = await axios.post('/platform/api/cache/clear')
    successMessage.value = response.data.message || '缓存已成功清除'
    showClearConfirm.value = false
    
    // 清除后刷新统计
    await refreshStats()
  } catch (err) {
    error.value = err.response?.data?.detail || err.message || '清除缓存失败'
    console.error('Error clearing cache:', err)
  } finally {
    clearing.value = false
  }
}

// 组件挂载时自动加载统计
onMounted(() => {
  refreshStats()
})
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>

