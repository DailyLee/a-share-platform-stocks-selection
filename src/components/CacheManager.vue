<template>
  <div class="min-h-screen bg-background text-foreground">
    <!-- 顶部导航栏 -->
    <header class="bg-card border-b border-border p-4 flex justify-between items-center sticky top-0 z-30">
      <div class="flex items-center">
        <img src="/gundam-logo.svg" alt="Gundam Logo" class="w-8 h-8 mr-2" />
        <h1 class="text-xl font-semibold">数据库管理</h1>
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
              数据库操作
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
              数据库统计
            </h2>
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              <!-- 股票数量 -->
              <div class="bg-muted/30 p-4 rounded-lg">
                <div class="flex items-center justify-between mb-2">
                  <span class="text-sm text-muted-foreground">股票数量</span>
                  <i class="fas fa-chart-line text-primary"></i>
                </div>
                <div class="text-2xl font-bold text-primary">
                  {{ stats.stock_count }}
                </div>
                <div class="text-xs text-muted-foreground mt-1">
                  基本信息记录数
                </div>
              </div>

              <!-- K线记录数 -->
              <div class="bg-muted/30 p-4 rounded-lg">
                <div class="flex items-center justify-between mb-2">
                  <span class="text-sm text-muted-foreground">K线记录数</span>
                  <i class="fas fa-database text-primary"></i>
                </div>
                <div class="text-2xl font-bold text-primary">
                  {{ stats.kline_records }}
                </div>
                <div class="text-xs text-muted-foreground mt-1">
                  历史K线数据记录
                </div>
              </div>

              <!-- 有数据的股票数 -->
              <div class="bg-muted/30 p-4 rounded-lg">
                <div class="flex items-center justify-between mb-2">
                  <span class="text-sm text-muted-foreground">有数据的股票</span>
                  <i class="fas fa-check-circle text-primary"></i>
                </div>
                <div class="text-2xl font-bold text-primary">
                  {{ stats.stocks_with_data }}
                </div>
                <div class="text-xs text-muted-foreground mt-1">
                  已存储K线数据的股票数
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
              <!-- 行业数据记录数 -->
              <div class="flex items-center justify-between p-3 bg-muted/30 rounded-lg">
                <div class="flex items-center">
                  <i class="fas fa-industry text-green-500 mr-3"></i>
                  <span class="font-medium">行业数据记录数</span>
                </div>
                <span class="text-lg font-semibold text-green-500">{{ stats.industry_count }}</span>
              </div>

              <!-- 日期范围 -->
              <div v-if="stats.date_range && stats.date_range.min_date" class="flex items-center justify-between p-3 bg-muted/30 rounded-lg">
                <div class="flex items-center">
                  <i class="fas fa-calendar text-blue-500 mr-3"></i>
                  <span class="font-medium">数据日期范围</span>
                </div>
                <div class="text-right">
                  <div class="text-sm font-semibold text-blue-500">{{ stats.date_range.min_date }}</div>
                  <div class="text-xs text-muted-foreground">至</div>
                  <div class="text-sm font-semibold text-blue-500">{{ stats.date_range.max_date }}</div>
                </div>
              </div>
            </div>
          </div>

          <!-- 数据库说明 -->
          <div class="card p-4 sm:p-6">
            <h2 class="text-lg font-semibold mb-4 flex items-center">
              <i class="fas fa-question-circle mr-2 text-primary"></i>
              数据库说明
            </h2>
            <div class="space-y-3 text-sm text-muted-foreground">
              <div class="flex items-start">
                <i class="fas fa-circle text-primary mr-2 mt-1 text-xs"></i>
                <div>
                  <span class="font-medium text-foreground">存储方式:</span> 历史股票数据存储在SQLite数据库中，位于服务器的 <code class="px-1 py-0.5 bg-muted rounded text-xs">data/stocks.db</code> 文件
                </div>
              </div>
              <div class="flex items-start">
                <i class="fas fa-circle text-primary mr-2 mt-1 text-xs"></i>
                <div>
                  <span class="font-medium text-foreground">数据持久化:</span> 所有历史数据永久保存，不会自动过期或删除
                </div>
              </div>
              <div class="flex items-start">
                <i class="fas fa-circle text-primary mr-2 mt-1 text-xs"></i>
                <div>
                  <span class="font-medium text-foreground">首次访问:</span> 如果数据库为空，系统会在首次访问时自动从API获取并构建历史数据
                </div>
              </div>
              <div class="flex items-start">
                <i class="fas fa-circle text-primary mr-2 mt-1 text-xs"></i>
                <div>
                  <span class="font-medium text-foreground">查询策略:</span> 优先从本地数据库获取数据，如果缺失则从API获取差量数据并更新到数据库
                </div>
              </div>
              <div class="flex items-start">
                <i class="fas fa-circle text-primary mr-2 mt-1 text-xs"></i>
                <div>
                  <span class="font-medium text-foreground">线程安全:</span> 数据库操作是线程安全的，支持多线程并发访问
                </div>
              </div>
              <div class="flex items-start">
                <i class="fas fa-circle text-primary mr-2 mt-1 text-xs"></i>
                <div>
                  <span class="font-medium text-foreground">数据更新:</span> 当获取的数据本地数据库缺失时，系统会自动从API获取差量数据并更新到数据库
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 加载状态 -->
        <div v-else-if="loading" class="card p-8 text-center">
          <i class="fas fa-spinner fa-spin text-4xl text-primary mb-4"></i>
          <p class="text-muted-foreground">正在加载数据库统计...</p>
        </div>

        <!-- 空状态 -->
        <div v-else class="card p-8 text-center">
          <i class="fas fa-database text-4xl text-muted-foreground mb-4"></i>
          <p class="text-muted-foreground">暂无数据库数据，请点击"刷新统计"按钮</p>
        </div>
      </div>
    </main>

  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import ThemeToggle from './ThemeToggle.vue'

const stats = ref(null)
const loading = ref(false)
const error = ref(null)
const successMessage = ref(null)

// 获取数据库统计
const refreshStats = async () => {
  loading.value = true
  error.value = null
  successMessage.value = null

  try {
    const response = await axios.get('/platform/api/database/stats')
    stats.value = response.data
  } catch (err) {
    error.value = err.response?.data?.detail || err.message || '获取数据库统计失败'
    console.error('Error fetching database stats:', err)
  } finally {
    loading.value = false
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

