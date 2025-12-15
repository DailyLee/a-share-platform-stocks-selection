<template>
  <div class="min-h-screen bg-background text-foreground">
    <!-- 顶部导航栏 -->
    <header class="bg-card border-b border-border p-4 flex justify-between items-center sticky top-0 z-30">
      <div class="flex items-center">
        <img src="/gundam-logo.svg" alt="Gundam Logo" class="w-8 h-8 mr-2" />
        <h1 class="text-xl font-semibold">股票平台期检查</h1>
      </div>

      <div class="flex items-center space-x-2 sm:space-x-3">
        <!-- 返回首页 -->
        <router-link to="/platform/" class="flex items-center justify-center px-2 sm:px-3 py-1.5 sm:py-2 rounded-md bg-gundam-blue text-white hover:bg-gundam-blue/80 transition-colors">
          <i class="fas fa-home mr-1 sm:mr-2"></i>
          <span class="hidden sm:inline">返回首页</span>
        </router-link>

        <!-- 主题切换 -->
        <ThemeToggle />
      </div>
    </header>

    <!-- 主内容区 -->
    <main class="p-4 sm:p-6 md:p-8">
      <div class="max-w-4xl mx-auto">
        <!-- 输入卡片 -->
        <div class="card p-4 sm:p-6 mb-6">
          <h2 class="text-lg font-semibold mb-4 flex items-center">
            <i class="fas fa-search mr-2 text-primary"></i>
            输入股票代码
          </h2>
          <div class="flex flex-col sm:flex-row gap-4 sm:items-start">
            <div class="flex-grow">
              <input
                v-model="stockCode"
                @keyup.enter="checkStock"
                class="input w-full"
                type="text"
                placeholder="例如: sh.600000 或 sz.000001"
                :disabled="loading"
              />
              <p class="text-xs text-muted-foreground mt-2">
                请输入完整的股票代码，如：sh.600000（上海）或 sz.000001（深圳）
              </p>
            </div>
            <button
              @click="checkStock"
              :disabled="loading || !stockCode.trim()"
              class="btn btn-primary h-10 px-4 sm:px-6 whitespace-nowrap w-full sm:w-auto"
            >
              <i class="fas fa-search mr-2" v-if="!loading"></i>
              <i class="fas fa-spinner fa-spin mr-2" v-if="loading"></i>
              {{ loading ? '分析中...' : '开始分析' }}
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

        <!-- 分析结果 -->
        <transition name="slide-up">
          <div v-if="result" class="space-y-6">
            <!-- 基本信息卡片 -->
            <div class="card p-4 sm:p-6">
              <h2 class="text-lg font-semibold mb-4 flex items-center">
                <i class="fas fa-info-circle mr-2 text-primary"></i>
                基本信息
              </h2>
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <span class="text-sm text-muted-foreground">股票代码:</span>
                  <p class="text-lg font-semibold">{{ result.code }}</p>
                </div>
                <div>
                  <span class="text-sm text-muted-foreground">股票名称:</span>
                  <p class="text-lg font-semibold">{{ result.name }}</p>
                </div>
              </div>
            </div>

            <!-- 平台期判断卡片 -->
            <div class="card p-4 sm:p-6">
              <h2 class="text-lg font-semibold mb-4 flex items-center">
                <i class="fas fa-chart-area mr-2 text-primary"></i>
                平台期判断
              </h2>
              <div class="flex items-center space-x-4 mb-4">
                <div :class="[
                  'px-4 py-2 rounded-lg font-semibold',
                  result.is_platform ? 'bg-green-500/20 text-green-700 dark:text-green-400' : 'bg-red-500/20 text-red-700 dark:text-red-400'
                ]">
                  <i :class="[
                    'fas mr-2',
                    result.is_platform ? 'fa-check-circle' : 'fa-times-circle'
                  ]"></i>
                  {{ result.explanation.platform_status }}
                </div>
                <div v-if="result.platform_windows.length > 0" class="text-sm text-muted-foreground">
                  符合平台期的窗口: {{ result.platform_windows.join('天、') }}天
                </div>
              </div>
              
              <!-- 详细解释 -->
              <div v-if="result.explanation.analysis_details.selection_reasons" class="mt-4 p-4 bg-muted/30 rounded-md">
                <h3 class="text-sm font-medium mb-2">判断依据:</h3>
                <div class="space-y-2">
                  <div v-for="(reason, window) in result.explanation.analysis_details.selection_reasons" :key="window" class="text-sm">
                    <span class="font-medium text-primary">{{ window }}天窗口:</span>
                    <span class="ml-2">{{ reason }}</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- 突破预兆卡片 -->
            <div class="card p-4 sm:p-6">
              <h2 class="text-lg font-semibold mb-4 flex items-center">
                <i class="fas fa-bolt mr-2 text-primary"></i>
                突破预兆
              </h2>
              <div class="flex items-center space-x-4 mb-4">
                <div :class="[
                  'px-4 py-2 rounded-lg font-semibold',
                  result.has_breakthrough_signal ? 'bg-amber-500/20 text-amber-700 dark:text-amber-400' : 'bg-gray-500/20 text-gray-700 dark:text-gray-400'
                ]">
                  <i :class="[
                    'fas mr-2',
                    result.has_breakthrough_signal ? 'fa-bolt' : 'fa-minus-circle'
                  ]"></i>
                  {{ result.has_breakthrough_signal ? '有突破预兆' : '无突破预兆' }}
                </div>
                <div v-if="result.has_breakthrough_signal" class="text-sm text-muted-foreground">
                  {{ result.explanation.breakthrough_signal.signal_count }}个技术指标显示突破信号
                </div>
              </div>

              <!-- 技术指标详情 -->
              <div v-if="result.explanation.breakthrough_signal.has_signal" class="mt-4">
                <h3 class="text-sm font-medium mb-2">技术指标详情:</h3>
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div v-for="(hasSignal, indicator) in result.explanation.breakthrough_signal.signals" :key="indicator" :class="[
                    'p-3 rounded-md',
                    hasSignal ? 'bg-amber-500/10 border border-amber-500/20' : 'bg-muted/30'
                  ]">
                    <div class="flex items-center justify-between">
                      <span class="font-medium">{{ indicator }}</span>
                      <i :class="[
                        'fas',
                        hasSignal ? 'fa-check-circle text-amber-500' : 'fa-times-circle text-gray-400'
                      ]"></i>
                    </div>
                    <div v-if="result.explanation.breakthrough_signal.details[indicator]" class="mt-2 text-xs text-muted-foreground">
                      <div v-for="(value, key) in result.explanation.breakthrough_signal.details[indicator]" :key="key">
                        <span class="font-medium">{{ key }}:</span> {{ value }}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 突破确认卡片 -->
            <div class="card p-4 sm:p-6">
              <h2 class="text-lg font-semibold mb-4 flex items-center">
                <i class="fas fa-check-circle mr-2 text-primary"></i>
                突破确认
              </h2>
              <div class="flex items-center space-x-4 mb-4">
                <div :class="[
                  'px-4 py-2 rounded-lg font-semibold',
                  result.has_breakthrough_confirmation ? 'bg-green-500/20 text-green-700 dark:text-green-400' : 'bg-gray-500/20 text-gray-700 dark:text-gray-400'
                ]">
                  <i :class="[
                    'fas mr-2',
                    result.has_breakthrough_confirmation ? 'fa-check-double' : 'fa-times-circle'
                  ]"></i>
                  {{ result.has_breakthrough_confirmation ? '突破已确认' : '突破未确认' }}
                </div>
              </div>

              <!-- 确认详情 -->
              <div v-if="result.explanation.breakthrough_confirmation.details" class="mt-4 p-4 bg-muted/30 rounded-md">
                <h3 class="text-sm font-medium mb-2">检测详情:</h3>
                <div class="space-y-2 text-sm">
                  <div v-if="result.explanation.breakthrough_confirmation.details.breakthrough_date">
                    <span class="font-medium">检测日期:</span>
                    {{ result.explanation.breakthrough_confirmation.details.breakthrough_date }}
                  </div>
                  <div v-if="result.explanation.breakthrough_confirmation.details.breakthrough_close">
                    <span class="font-medium">当日收盘价:</span>
                    {{ result.explanation.breakthrough_confirmation.details.breakthrough_close }}
                  </div>
                  <div v-if="result.explanation.breakthrough_confirmation.details.breakthrough_volume_increase !== undefined">
                    <span class="font-medium">成交量放大:</span>
                    <span :class="result.explanation.breakthrough_confirmation.details.volume_increase_met ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'">
                      {{ result.explanation.breakthrough_confirmation.details.breakthrough_volume_increase }}倍
                      <span class="text-xs ml-1">
                        (要求: {{ result.explanation.breakthrough_confirmation.details.volume_increase_required || 1.5 }}倍,
                        {{ result.explanation.breakthrough_confirmation.details.volume_increase_met ? '✓ 满足' : '✗ 不满足' }})
                      </span>
                    </span>
                  </div>
                  <div v-if="result.explanation.breakthrough_confirmation.details.breakthrough_price_change_pct !== undefined">
                    <span class="font-medium">价格上涨:</span>
                    <span :class="result.explanation.breakthrough_confirmation.details.price_increase_met ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'">
                      {{ result.explanation.breakthrough_confirmation.details.breakthrough_price_change_pct }}%
                      <span class="text-xs ml-1">
                        (要求: {{ (result.explanation.breakthrough_confirmation.details.price_increase_required || 0.02) * 100 }}%,
                        {{ result.explanation.breakthrough_confirmation.details.price_increase_met ? '✓ 满足' : '✗ 不满足' }})
                      </span>
                    </span>
                  </div>
                  <div v-if="result.explanation.breakthrough_confirmation.details.confirmation_details && result.explanation.breakthrough_confirmation.has_breakthrough">
                    <span class="font-medium">确认天数详情:</span>
                    <div class="mt-1 ml-4">
                      <div v-for="(detail, index) in result.explanation.breakthrough_confirmation.details.confirmation_details" :key="index" class="text-xs">
                        {{ detail.date }}: 
                        <span :class="detail.confirmed ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'">
                          {{ detail.confirmed ? '已确认' : '未确认' }}
                        </span>
                        (收盘价: {{ detail.close }})
                      </div>
                    </div>
                  </div>
                  <div v-if="!result.explanation.breakthrough_confirmation.has_breakthrough" class="text-xs text-amber-600 dark:text-amber-400 mt-2 italic">
                    说明: 检测到价格波动，但未满足突破条件（成交量放大或价格上涨不满足要求）
                  </div>
                </div>
              </div>
            </div>

            <!-- K线图卡片 -->
            <div class="card p-4 sm:p-6">
              <h2 class="text-lg font-semibold mb-4 flex items-center">
                <i class="fas fa-chart-line mr-2 text-primary"></i>
                K线图
              </h2>
              <div class="w-full">
                <KlineChart
                  :klineData="result.kline_data"
                  height="400px"
                  width="100%"
                  :title="`${result.name} (${result.code})`"
                  :isDarkMode="isDarkMode"
                  :markLines="result.mark_lines || []"
                  class="rounded-md overflow-hidden"
                />
              </div>
            </div>

            <!-- 财务分析卡片 -->
            <div class="card p-4 sm:p-6">
              <h2 class="text-lg font-semibold mb-4 flex items-center">
                <i class="fas fa-chart-pie mr-2 text-primary"></i>
                财务分析
              </h2>
              <div v-if="result.fundamental_analysis" class="space-y-4">
                <!-- 成长能力 -->
                <div>
                  <h3 class="text-sm font-medium mb-2 flex items-center">
                    <i class="fas fa-arrow-trend-up mr-2 text-primary"></i>
                    成长能力
                  </h3>
                  <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div class="p-3 bg-muted/30 rounded-md">
                      <div class="text-xs text-muted-foreground mb-1">营收增长率（近3年平均）</div>
                      <div class="flex items-center justify-between">
                        <span class="text-lg font-semibold">
                          {{ result.fundamental_analysis.avg_revenue_growth !== null && result.fundamental_analysis.avg_revenue_growth !== undefined 
                            ? (result.fundamental_analysis.avg_revenue_growth > 1 
                              ? result.fundamental_analysis.avg_revenue_growth.toFixed(2) + '%' 
                              : (result.fundamental_analysis.avg_revenue_growth * 100).toFixed(2) + '%')
                            : '暂无数据' }}
                        </span>
                        <span v-if="result.fundamental_analysis.revenue_growth_consistent" class="text-xs px-2 py-0.5 rounded-full bg-green-500/20 text-green-700 dark:text-green-400">
                          连续增长
                        </span>
                        <span v-else-if="result.fundamental_analysis.avg_revenue_growth !== null" class="text-xs px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-700 dark:text-amber-400">
                          不连续
                        </span>
                      </div>
                    </div>
                    <div class="p-3 bg-muted/30 rounded-md">
                      <div class="text-xs text-muted-foreground mb-1">净利润增长率（近3年平均）</div>
                      <div class="flex items-center justify-between">
                        <span class="text-lg font-semibold">
                          {{ result.fundamental_analysis.avg_profit_growth !== null && result.fundamental_analysis.avg_profit_growth !== undefined 
                            ? (result.fundamental_analysis.avg_profit_growth > 1 
                              ? result.fundamental_analysis.avg_profit_growth.toFixed(2) + '%' 
                              : (result.fundamental_analysis.avg_profit_growth * 100).toFixed(2) + '%')
                            : '暂无数据' }}
                        </span>
                        <span v-if="result.fundamental_analysis.profit_growth_consistent" class="text-xs px-2 py-0.5 rounded-full bg-green-500/20 text-green-700 dark:text-green-400">
                          连续增长
                        </span>
                        <span v-else-if="result.fundamental_analysis.avg_profit_growth !== null" class="text-xs px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-700 dark:text-amber-400">
                          不连续
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- 盈利能力 -->
                <div>
                  <h3 class="text-sm font-medium mb-2 flex items-center">
                    <i class="fas fa-coins mr-2 text-primary"></i>
                    盈利能力
                  </h3>
                  <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div class="p-3 bg-muted/30 rounded-md">
                      <div class="text-xs text-muted-foreground mb-1">ROE（净资产收益率，近3年平均）</div>
                      <div class="flex items-center justify-between">
                        <span class="text-lg font-semibold">
                          {{ result.fundamental_analysis.avg_roe !== null && result.fundamental_analysis.avg_roe !== undefined 
                            ? (result.fundamental_analysis.avg_roe > 1 
                              ? result.fundamental_analysis.avg_roe.toFixed(2) + '%' 
                              : (result.fundamental_analysis.avg_roe * 100).toFixed(2) + '%')
                            : '暂无数据' }}
                        </span>
                        <span v-if="result.fundamental_analysis.roe_consistent" class="text-xs px-2 py-0.5 rounded-full bg-green-500/20 text-green-700 dark:text-green-400">
                          稳定
                        </span>
                        <span v-else-if="result.fundamental_analysis.avg_roe !== null" class="text-xs px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-700 dark:text-amber-400">
                          不稳定
                        </span>
                      </div>
                    </div>
                    <div class="p-3 bg-muted/30 rounded-md">
                      <div class="text-xs text-muted-foreground mb-1">资产负债率（近3年平均）</div>
                      <div class="flex items-center justify-between">
                        <span class="text-lg font-semibold">
                          {{ result.fundamental_analysis.avg_liability_ratio !== null && result.fundamental_analysis.avg_liability_ratio !== undefined 
                            ? (result.fundamental_analysis.avg_liability_ratio * 100).toFixed(2) + '%' 
                            : '暂无数据' }}
                        </span>
                        <span v-if="result.fundamental_analysis.liability_ratio_consistent" class="text-xs px-2 py-0.5 rounded-full bg-green-500/20 text-green-700 dark:text-green-400">
                          稳定
                        </span>
                        <span v-else-if="result.fundamental_analysis.avg_liability_ratio !== null" class="text-xs px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-700 dark:text-amber-400">
                          不稳定
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- 估值指标 -->
                <div>
                  <h3 class="text-sm font-medium mb-2 flex items-center">
                    <i class="fas fa-calculator mr-2 text-primary"></i>
                    估值指标
                  </h3>
                  <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div class="p-3 bg-muted/30 rounded-md">
                      <div class="text-xs text-muted-foreground mb-1">PE（市盈率TTM）</div>
                      <div class="text-lg font-semibold">
                        {{ result.fundamental_analysis.pe_ttm !== null && result.fundamental_analysis.pe_ttm !== undefined 
                          ? result.fundamental_analysis.pe_ttm.toFixed(2) 
                          : '暂无数据' }}
                      </div>
                    </div>
                    <div class="p-3 bg-muted/30 rounded-md">
                      <div class="text-xs text-muted-foreground mb-1">PB（市净率MRQ）</div>
                      <div class="text-lg font-semibold">
                        {{ result.fundamental_analysis.pb_mrq !== null && result.fundamental_analysis.pb_mrq !== undefined 
                          ? result.fundamental_analysis.pb_mrq.toFixed(2) 
                          : '暂无数据' }}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              <div v-else class="text-center py-8 text-muted-foreground">
                <i class="fas fa-info-circle text-2xl mb-2 opacity-50"></i>
                <p>暂无财务分析数据</p>
              </div>
            </div>
          </div>
        </transition>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import KlineChart from './KlineChart.vue'
import ThemeToggle from './ThemeToggle.vue'

const router = useRouter()
const stockCode = ref('')
const loading = ref(false)
const error = ref(null)
const result = ref(null)
const isDarkMode = ref(false)

async function checkStock() {
  if (!stockCode.value.trim()) {
    error.value = '请输入股票代码'
    return
  }

  loading.value = true
  error.value = null
  result.value = null

  try {
    const response = await axios.post('/platform/api/platform/check', {
      code: stockCode.value.trim()
    })

    result.value = response.data
  } catch (e) {
    console.error('Error checking stock:', e)
    if (e.response && e.response.data) {
      error.value = e.response.data.detail || e.response.data.message || '分析失败'
    } else {
      error.value = e.message || '网络错误，请稍后重试'
    }
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  // 检查本地存储中的主题设置
  const savedTheme = localStorage.getItem('theme')
  if (savedTheme === 'dark' || (!savedTheme && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
    isDarkMode.value = true
    document.documentElement.classList.add('dark')
  }
})
</script>

<style scoped>
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}

.slide-up-enter-active {
  transition: all 0.3s ease-out;
}
.slide-up-enter-from {
  opacity: 0;
  transform: translateY(20px);
}
</style>

