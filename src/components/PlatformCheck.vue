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
        <router-link :to="getBackUrl()" class="flex items-center justify-center px-2 sm:px-3 py-1.5 sm:py-2 rounded-md bg-gundam-blue text-white hover:bg-gundam-blue/80 transition-colors">
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
                <h3 class="text-sm font-medium mb-3">判断依据:</h3>
                <div class="space-y-4">
                  <div v-for="(reason, window) in result.explanation.analysis_details.selection_reasons" :key="window" class="space-y-2">
                    <div class="flex items-center gap-2 mb-2">
                      <span class="font-medium text-primary text-base">{{ window }}天窗口</span>
                      <span class="text-xs px-2 py-0.5 rounded-full bg-primary/20 text-primary">
                        符合平台期
                      </span>
                    </div>
                    
                    <!-- 解析并格式化选择理由 -->
                    <div class="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                      <!-- 价格相关 -->
                      <div v-if="reason.includes('价格区间')" class="flex items-start gap-2">
                        <i class="fas fa-chart-line text-primary mt-0.5"></i>
                        <div>
                          <span class="text-muted-foreground">价格区间:</span>
                          <span class="ml-1 font-medium">{{ extractValue(reason, '价格区间') }}</span>
                        </div>
                      </div>
                      
                      <!-- 均线相关 -->
                      <div v-if="reason.includes('均线收敛')" class="flex items-start gap-2">
                        <i class="fas fa-wave-square text-primary mt-0.5"></i>
                        <div>
                          <span class="text-muted-foreground">均线收敛:</span>
                          <span class="ml-1 font-medium">{{ extractValue(reason, '均线收敛') }}</span>
                        </div>
                      </div>
                      
                      <!-- 波动率 -->
                      <div v-if="reason.includes('波动率')" class="flex items-start gap-2">
                        <i class="fas fa-chart-area text-primary mt-0.5"></i>
                        <div>
                          <span class="text-muted-foreground">波动率:</span>
                          <span class="ml-1 font-medium">{{ extractValue(reason, '波动率') }}</span>
                        </div>
                      </div>
                      
                      <!-- 箱体质量 -->
                      <div v-if="reason.includes('箱体质量')" class="flex items-start gap-2">
                        <i class="fas fa-cube text-primary mt-0.5"></i>
                        <div>
                          <span class="text-muted-foreground">箱体质量:</span>
                          <span class="ml-1 font-medium">{{ extractValue(reason, '箱体质量') }}</span>
                        </div>
                      </div>
                      
                      <!-- 低位判断 -->
                      <div v-if="reason.includes('低位')" class="flex items-start gap-2 sm:col-span-2">
                        <i class="fas fa-map-marker-alt text-primary mt-0.5"></i>
                        <div class="flex-1">
                          <span class="text-muted-foreground">低位判断:</span>
                          <span class="ml-1">{{ extractLowPositionInfo(reason) }}</span>
                        </div>
                      </div>
                      
                      <!-- 快速下跌 -->
                      <div v-if="reason.includes('快速下跌')" class="flex items-start gap-2 sm:col-span-2">
                        <i class="fas fa-arrow-down text-primary mt-0.5"></i>
                        <div class="flex-1">
                          <span class="text-muted-foreground">快速下跌:</span>
                          <span class="ml-1">{{ extractRapidDeclineInfo(reason) }}</span>
                        </div>
                      </div>
                      
                      <!-- 标准模式 -->
                      <div v-if="reason.includes('标准模式')" class="flex items-start gap-2 sm:col-span-2">
                        <i class="fas fa-check-double text-primary mt-0.5"></i>
                        <div class="flex-1">
                          <span class="text-muted-foreground">模式:</span>
                          <span class="ml-1 font-medium">{{ extractTextValue(reason, '标准模式') }}</span>
                        </div>
                      </div>
                      
                      <!-- 突破前兆 -->
                      <div v-if="reason.includes('突破前兆')" class="flex items-start gap-2 sm:col-span-2">
                        <i class="fas fa-bolt text-amber-500 mt-0.5"></i>
                        <div class="flex-1">
                          <span class="text-muted-foreground">突破前兆:</span>
                          <span class="ml-1 font-medium text-amber-600 dark:text-amber-400">{{ extractBreakthroughInfo(reason) }}</span>
                        </div>
                      </div>
                    </div>
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
              <div v-if="result.explanation.breakthrough_signal.has_signal" class="mt-4 p-4 bg-muted/30 rounded-md">
                <h3 class="text-sm font-medium mb-3">技术指标详情:</h3>
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <!-- MACD -->
                  <div v-if="result.explanation.breakthrough_signal.details.MACD" class="p-3 rounded-md" :class="[
                    result.explanation.breakthrough_signal.signals.MACD ? 'bg-amber-500/10 border border-amber-500/20' : 'bg-muted/30'
                  ]">
                    <div class="flex items-center justify-between mb-2">
                      <span class="font-medium">MACD</span>
                      <i :class="[
                        'fas',
                        result.explanation.breakthrough_signal.signals.MACD ? 'fa-check-circle text-amber-500' : 'fa-times-circle text-gray-400'
                      ]"></i>
                    </div>
                    <div class="space-y-1 text-xs">
                      <div>
                        <span class="text-muted-foreground">状态:</span>
                        <span :class="result.explanation.breakthrough_signal.signals.MACD ? 'text-amber-600 dark:text-amber-400' : 'text-gray-600 dark:text-gray-400'">
                          {{ result.explanation.breakthrough_signal.details.MACD.status }}
                        </span>
                      </div>
                      <div v-if="result.explanation.breakthrough_signal.details.MACD.current_macd !== undefined">
                        <span class="text-muted-foreground">MACD值:</span>
                        <span class="font-medium">{{ result.explanation.breakthrough_signal.details.MACD.current_macd }}</span>
                      </div>
                      <div v-if="result.explanation.breakthrough_signal.details.MACD.current_signal !== undefined">
                        <span class="text-muted-foreground">信号线:</span>
                        <span class="font-medium">{{ result.explanation.breakthrough_signal.details.MACD.current_signal }}</span>
                      </div>
                      <div class="flex items-center gap-2 mt-2 pt-2 border-t border-border/50">
                        <span :class="result.explanation.breakthrough_signal.details.MACD.crossover ? 'text-green-600 dark:text-green-400' : 'text-gray-500'">
                          <i :class="result.explanation.breakthrough_signal.details.MACD.crossover ? 'fas fa-check' : 'fas fa-times'"></i>
                          金叉
                        </span>
                        <span :class="result.explanation.breakthrough_signal.details.MACD.macd_increasing ? 'text-green-600 dark:text-green-400' : 'text-gray-500'">
                          <i :class="result.explanation.breakthrough_signal.details.MACD.macd_increasing ? 'fas fa-check' : 'fas fa-times'"></i>
                          MACD上升
                        </span>
                        <span :class="result.explanation.breakthrough_signal.details.MACD.histogram_increasing ? 'text-green-600 dark:text-green-400' : 'text-gray-500'">
                          <i :class="result.explanation.breakthrough_signal.details.MACD.histogram_increasing ? 'fas fa-check' : 'fas fa-times'"></i>
                          柱状图上升
                        </span>
                      </div>
                      <div class="text-xs text-muted-foreground italic mt-1">
                        说明: MACD金叉或MACD与柱状图同时上升时产生突破信号
                      </div>
                    </div>
                  </div>

                  <!-- RSI -->
                  <div v-if="result.explanation.breakthrough_signal.details.RSI" class="p-3 rounded-md" :class="[
                    result.explanation.breakthrough_signal.signals.RSI ? 'bg-amber-500/10 border border-amber-500/20' : 'bg-muted/30'
                  ]">
                    <div class="flex items-center justify-between mb-2">
                      <span class="font-medium">RSI</span>
                      <i :class="[
                        'fas',
                        result.explanation.breakthrough_signal.signals.RSI ? 'fa-check-circle text-amber-500' : 'fa-times-circle text-gray-400'
                      ]"></i>
                    </div>
                    <div class="space-y-1 text-xs">
                      <div>
                        <span class="text-muted-foreground">状态:</span>
                        <span :class="result.explanation.breakthrough_signal.signals.RSI ? 'text-amber-600 dark:text-amber-400' : 'text-gray-600 dark:text-gray-400'">
                          {{ result.explanation.breakthrough_signal.details.RSI.status }}
                        </span>
                      </div>
                      <div v-if="result.explanation.breakthrough_signal.details.RSI.current_rsi !== undefined">
                        <span class="text-muted-foreground">RSI值:</span>
                        <span class="font-medium">{{ result.explanation.breakthrough_signal.details.RSI.current_rsi }}</span>
                        <span class="text-xs ml-1">
                          (超卖: &lt;30, 超买: &gt;70)
                        </span>
                      </div>
                      <div v-if="result.explanation.breakthrough_signal.details.RSI.rsi_increasing !== undefined" class="mt-2 pt-2 border-t border-border/50">
                        <span :class="result.explanation.breakthrough_signal.details.RSI.rsi_increasing ? 'text-green-600 dark:text-green-400' : 'text-gray-500'">
                          <i :class="result.explanation.breakthrough_signal.details.RSI.rsi_increasing ? 'fas fa-check' : 'fas fa-times'"></i>
                          RSI上升
                        </span>
                      </div>
                      <div class="text-xs text-muted-foreground italic mt-1">
                        说明: RSI从超卖区域（&lt;30）上升或持续上升时产生突破信号
                      </div>
                    </div>
                  </div>

                  <!-- KDJ -->
                  <div v-if="result.explanation.breakthrough_signal.details.KDJ" class="p-3 rounded-md" :class="[
                    result.explanation.breakthrough_signal.signals.KDJ ? 'bg-amber-500/10 border border-amber-500/20' : 'bg-muted/30'
                  ]">
                    <div class="flex items-center justify-between mb-2">
                      <span class="font-medium">KDJ</span>
                      <i :class="[
                        'fas',
                        result.explanation.breakthrough_signal.signals.KDJ ? 'fa-check-circle text-amber-500' : 'fa-times-circle text-gray-400'
                      ]"></i>
                    </div>
                    <div class="space-y-1 text-xs">
                      <div>
                        <span class="text-muted-foreground">状态:</span>
                        <span :class="result.explanation.breakthrough_signal.signals.KDJ ? 'text-amber-600 dark:text-amber-400' : 'text-gray-600 dark:text-gray-400'">
                          {{ result.explanation.breakthrough_signal.details.KDJ.status }}
                        </span>
                      </div>
                      <div v-if="result.explanation.breakthrough_signal.details.KDJ.current_k !== undefined" class="flex gap-3">
                        <div>
                          <span class="text-muted-foreground">K:</span>
                          <span class="font-medium">{{ result.explanation.breakthrough_signal.details.KDJ.current_k }}</span>
                        </div>
                        <div>
                          <span class="text-muted-foreground">D:</span>
                          <span class="font-medium">{{ result.explanation.breakthrough_signal.details.KDJ.current_d }}</span>
                        </div>
                        <div>
                          <span class="text-muted-foreground">J:</span>
                          <span class="font-medium">{{ result.explanation.breakthrough_signal.details.KDJ.current_j }}</span>
                        </div>
                      </div>
                      <div class="flex items-center gap-2 mt-2 pt-2 border-t border-border/50">
                        <span :class="result.explanation.breakthrough_signal.details.KDJ.golden_cross ? 'text-green-600 dark:text-green-400' : 'text-gray-500'">
                          <i :class="result.explanation.breakthrough_signal.details.KDJ.golden_cross ? 'fas fa-check' : 'fas fa-times'"></i>
                          K线上穿D线
                        </span>
                        <span :class="result.explanation.breakthrough_signal.details.KDJ.k_increasing && result.explanation.breakthrough_signal.details.KDJ.j_increasing ? 'text-green-600 dark:text-green-400' : 'text-gray-500'">
                          <i :class="result.explanation.breakthrough_signal.details.KDJ.k_increasing && result.explanation.breakthrough_signal.details.KDJ.j_increasing ? 'fas fa-check' : 'fas fa-times'"></i>
                          K、J上升
                        </span>
                      </div>
                      <div class="text-xs text-muted-foreground italic mt-1">
                        说明: K线上穿D线（金叉）或K、J线同时上升时产生突破信号
                      </div>
                    </div>
                  </div>

                  <!-- 布林带 -->
                  <div v-if="result.explanation.breakthrough_signal.details.布林带" class="p-3 rounded-md" :class="[
                    result.explanation.breakthrough_signal.signals.布林带 ? 'bg-amber-500/10 border border-amber-500/20' : 'bg-muted/30'
                  ]">
                    <div class="flex items-center justify-between mb-2">
                      <span class="font-medium">布林带</span>
                      <i :class="[
                        'fas',
                        result.explanation.breakthrough_signal.signals.布林带 ? 'fa-check-circle text-amber-500' : 'fa-times-circle text-gray-400'
                      ]"></i>
                    </div>
                    <div class="space-y-1 text-xs">
                      <div>
                        <span class="text-muted-foreground">状态:</span>
                        <span :class="result.explanation.breakthrough_signal.signals.布林带 ? 'text-amber-600 dark:text-amber-400' : 'text-gray-600 dark:text-gray-400'">
                          {{ result.explanation.breakthrough_signal.details.布林带.status }}
                        </span>
                      </div>
                      <div v-if="result.explanation.breakthrough_signal.details.布林带.current_bandwidth !== undefined" class="flex gap-3">
                        <div>
                          <span class="text-muted-foreground">带宽:</span>
                          <span class="font-medium">{{ result.explanation.breakthrough_signal.details.布林带.current_bandwidth }}</span>
                        </div>
                        <div v-if="result.explanation.breakthrough_signal.details.布林带.bandwidth_change !== undefined">
                          <span class="text-muted-foreground">带宽变化:</span>
                          <span :class="result.explanation.breakthrough_signal.details.布林带.bandwidth_expanding ? 'text-green-600 dark:text-green-400' : 'text-gray-500'">
                            {{ result.explanation.breakthrough_signal.details.布林带.bandwidth_change > 0 ? '+' : '' }}{{ result.explanation.breakthrough_signal.details.布林带.bandwidth_change }}
                          </span>
                        </div>
                      </div>
                      <div class="flex items-center gap-2 mt-2 pt-2 border-t border-border/50">
                        <span :class="result.explanation.breakthrough_signal.details.布林带.close_to_upper ? 'text-green-600 dark:text-green-400' : 'text-gray-500'">
                          <i :class="result.explanation.breakthrough_signal.details.布林带.close_to_upper ? 'fas fa-check' : 'fas fa-times'"></i>
                          接近上轨
                        </span>
                        <span :class="result.explanation.breakthrough_signal.details.布林带.bandwidth_expanding ? 'text-green-600 dark:text-green-400' : 'text-gray-500'">
                          <i :class="result.explanation.breakthrough_signal.details.布林带.bandwidth_expanding ? 'fas fa-check' : 'fas fa-times'"></i>
                          带宽扩张
                        </span>
                        <span :class="result.explanation.breakthrough_signal.details.布林带.above_middle && result.explanation.breakthrough_signal.details.布林带.price_increasing ? 'text-green-600 dark:text-green-400' : 'text-gray-500'">
                          <i :class="result.explanation.breakthrough_signal.details.布林带.above_middle && result.explanation.breakthrough_signal.details.布林带.price_increasing ? 'fas fa-check' : 'fas fa-times'"></i>
                          价格上升
                        </span>
                      </div>
                      <div class="text-xs text-muted-foreground italic mt-1">
                        说明: 价格突破布林带上轨时产生突破信号
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
                  :markLines="generateMarkLines(result)"
                  :supportLevels="getSupportLevels(result)"
                  :resistanceLevels="getResistanceLevels(result)"
                  @daySelect="handleDaySelect"
                  class="rounded-md overflow-hidden"
                />
              </div>
              
              <!-- 选中日期数据显示 -->
              <div v-if="selectedDay" class="mt-4 p-4 bg-muted/30 rounded-md">
                <h3 class="text-sm font-medium mb-2 flex items-center">
                  <i class="fas fa-calendar-day mr-2 text-primary"></i>
                  选中日期数据: {{ selectedDay.date }}
                </h3>
                <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 text-sm">
                  <div>
                    <span class="text-muted-foreground">开盘:</span>
                    <span class="ml-2 font-medium">{{ selectedDay.open }}</span>
                  </div>
                  <div>
                    <span class="text-muted-foreground">收盘:</span>
                    <span class="ml-2 font-medium" :class="selectedDay.close >= selectedDay.open ? 'text-red-600 dark:text-red-400' : 'text-blue-600 dark:text-blue-400'">
                      {{ selectedDay.close }}
                    </span>
                  </div>
                  <div>
                    <span class="text-muted-foreground">最高:</span>
                    <span class="ml-2 font-medium">{{ selectedDay.high }}</span>
                  </div>
                  <div>
                    <span class="text-muted-foreground">最低:</span>
                    <span class="ml-2 font-medium">{{ selectedDay.low }}</span>
                  </div>
                  <!-- 涨幅显示 -->
                  <div class="sm:col-span-2">
                    <span class="text-muted-foreground">单日涨幅:</span>
                    <template v-if="hasValidChangePercent">
                      <span class="ml-2 font-medium font-semibold" :class="selectedDay.changePercent >= 0 ? 'text-red-600 dark:text-red-400' : 'text-blue-600 dark:text-blue-400'">
                        {{ selectedDay.changePercent >= 0 ? '+' : '' }}{{ formatChangePercent(selectedDay.changePercent) }}%
                      </span>
                      <span v-if="hasValidChange" class="ml-1 text-xs" :class="selectedDay.changePercent >= 0 ? 'text-red-600 dark:text-red-400' : 'text-blue-600 dark:text-blue-400'">
                        ({{ selectedDay.change >= 0 ? '+' : '' }}{{ formatChange(selectedDay.change) }})
                      </span>
                    </template>
                    <span v-else class="ml-2 text-gray-500 dark:text-gray-400">暂无数据</span>
                  </div>
                  <div v-if="selectedDay.volume" class="sm:col-span-2">
                    <span class="text-muted-foreground">成交量:</span>
                    <span class="ml-2 font-medium">{{ selectedDay.volume }}</span>
                  </div>
                </div>
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
import { ref, onMounted, computed, provide } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import axios from 'axios'
import KlineChart from './KlineChart.vue'
import ThemeToggle from './ThemeToggle.vue'

const router = useRouter()
const route = useRoute()
const stockCode = ref('')
const loading = ref(false)
const error = ref(null)
const result = ref(null)
const isDarkMode = ref(false)
const selectedDay = ref(null)

// 计算属性：检查是否有有效的涨幅百分比
const hasValidChangePercent = computed(() => {
  if (!selectedDay.value) return false
  const cp = selectedDay.value.changePercent
  return cp !== undefined && cp !== null && !isNaN(cp) && cp !== ''
})

// 计算属性：检查是否有有效的涨跌金额
const hasValidChange = computed(() => {
  if (!selectedDay.value) return false
  const c = selectedDay.value.change
  return c !== undefined && c !== null && !isNaN(c) && c !== ''
})

// 格式化涨幅百分比
function formatChangePercent(value) {
  const num = Number(value)
  return isNaN(num) ? '0.00' : num.toFixed(2)
}

// 格式化涨跌金额
function formatChange(value) {
  const num = Number(value)
  return isNaN(num) ? '0.00' : num.toFixed(2)
}

// 辅助函数：从选择理由中提取值（用于数字值）
function extractValue(reason, key) {
  // 匹配 "价格区间0.20" 或 "价格区间: 0.20" 格式
  const regex = new RegExp(`${key}[：:]?\\s*([\\d.]+)`)
  const match = reason.match(regex)
  return match ? match[1].trim() : ''
}

// 提取文本值（用于标准模式等）
function extractTextValue(reason, key) {
  // 匹配 "标准模式: 低位+快速下跌后形成平台期" 格式
  const regex = new RegExp(`${key}[：:]?\\s*([^,，]+)`)
  const match = reason.match(regex)
  return match ? match[1].trim() : ''
}

// 提取低位判断信息
function extractLowPositionInfo(reason) {
  const declineMatch = reason.match(/从高点下跌([\d.]+)%/)
  const dateMatch = reason.match(/高点日期([\d-]+)/)
  const parts = []
  if (declineMatch) {
    parts.push(`从高点下跌${declineMatch[1]}%`)
  }
  if (dateMatch) {
    parts.push(`高点日期: ${dateMatch[1]}`)
  }
  return parts.length > 0 ? parts.join('，') : ''
}

// 提取快速下跌信息
function extractRapidDeclineInfo(reason) {
  const match = reason.match(/快速下跌[：:]?\s*([\d.]+)%\s*\(([^)]+)\)/)
  if (match) {
    return `${match[1]}% (${match[2]})`
  }
  return ''
}

// 提取突破前兆信息
function extractBreakthroughInfo(reason) {
  const match = reason.match(/突破前兆[：:]?\s*(\d+)个指标\s*\(([^)]+)\)/)
  if (match) {
    return `${match[1]}个指标 (${match[2]})`
  }
  return ''
}

// 生成标记线数据（与首页相同的方法）
function generateMarkLines(result) {
  if (!result) return [];
  
  // 首先检查后端是否直接提供了标记线数据
  if (result.mark_lines && result.mark_lines.length > 0) {
    return result.mark_lines;
  }

  const markLines = [];

  // 如果有突破确认分析，添加突破标记
  if (result.explanation && result.explanation.breakthrough_confirmation && result.explanation.breakthrough_confirmation.details) {
    const details = result.explanation.breakthrough_confirmation.details;
    if (details.breakthrough_date) {
      markLines.push({
        date: details.breakthrough_date,
        text: '突破',
        color: '#10b981' // 绿色
      });
    }
  }

  // 如果有平台期窗口信息，可以添加平台期开始标记
  if (result.platform_windows && result.platform_windows.length > 0) {
    // 这里可以根据实际数据结构添加平台期开始日期标记
    // 如果后端提供了平台期开始日期，可以添加
  }

  return markLines;
}

// 获取支撑位数据（与首页相同的方法）
function getSupportLevels(result) {
  if (!result) return [];

  // 检查是否有箱体分析结果
  if (result.box_analysis && result.box_analysis.support_levels) {
    return result.box_analysis.support_levels;
  }

  // 检查explanation中是否有箱体分析
  if (result.explanation && result.explanation.analysis_details) {
    // 尝试从分析详情中获取支撑位
    // 根据实际数据结构调整
  }

  return [];
}

// 获取阻力位数据（与首页相同的方法）
function getResistanceLevels(result) {
  if (!result) return [];

  // 检查是否有箱体分析结果
  if (result.box_analysis && result.box_analysis.resistance_levels) {
    return result.box_analysis.resistance_levels;
  }

  // 检查explanation中是否有箱体分析
  if (result.explanation && result.explanation.analysis_details) {
    // 尝试从分析详情中获取阻力位
    // 根据实际数据结构调整
  }

  return [];
}

// 处理日期选择事件
function handleDaySelect(dayData) {
  console.log('handleDaySelect 接收到数据:', dayData);
  console.log('result.value:', result.value);
  console.log('kline_data 长度:', result.value?.kline_data?.length);
  
  // 计算单日涨幅（相对于前一日收盘价）
  let changePercent = null;
  let change = null;
  
  // 优先使用后端提供的 pctChg 字段
  if (dayData.pctChg !== undefined && dayData.pctChg !== null && !isNaN(dayData.pctChg)) {
    changePercent = Number(dayData.pctChg);
    console.log('使用 pctChg:', changePercent);
    // 如果有前一日收盘价，计算涨跌金额
    if (dayData.preclose !== undefined && dayData.preclose !== null && !isNaN(dayData.preclose)) {
      change = dayData.close - dayData.preclose;
      console.log('使用 preclose 计算 change:', change);
    }
  }
  
  // 如果没有 pctChg 或计算失败，尝试从前一日数据计算
  if ((changePercent === null || isNaN(changePercent)) && result.value && result.value.kline_data && dayData.index > 0) {
    console.log('尝试从前一日数据计算涨幅, index:', dayData.index);
    const prevDay = result.value.kline_data[dayData.index - 1];
    console.log('前一日数据:', prevDay);
    if (prevDay && prevDay.close !== undefined && prevDay.close !== null) {
      // 计算涨幅 = (当日收盘价 - 前一日收盘价) / 前一日收盘价 * 100%
      change = dayData.close - prevDay.close;
      changePercent = (change / prevDay.close) * 100;
      console.log('计算得到的涨幅:', changePercent, '涨跌金额:', change);
    }
  }
  
  // 如果还是没有，尝试从 index=0 的情况（第一天，可能没有前一天数据）
  if ((changePercent === null || isNaN(changePercent)) && dayData.index === 0) {
    console.log('第一天数据，无法计算涨幅');
  }
  
  selectedDay.value = {
    ...dayData,
    changePercent: changePercent,
    change: change
  };
  
  console.log('最终 selectedDay.value:', selectedDay.value);
  console.log('changePercent 类型:', typeof changePercent, '值:', changePercent);
  console.log('changePercent 是否为 null:', changePercent === null);
  console.log('changePercent 是否为 undefined:', changePercent === undefined);
  console.log('changePercent 是否为 NaN:', isNaN(changePercent));
}

async function checkStock() {
  if (!stockCode.value.trim()) {
    error.value = '请输入股票代码'
    return
  }

  loading.value = true
  error.value = null
  result.value = null
  selectedDay.value = null

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

// 切换暗色模式
function toggleDarkMode() {
  isDarkMode.value = !isDarkMode.value
  if (isDarkMode.value) {
    document.documentElement.classList.add('dark')
    localStorage.setItem('theme', 'dark')
  } else {
    document.documentElement.classList.remove('dark')
    localStorage.setItem('theme', 'light')
  }
}

// 获取返回URL
function getBackUrl() {
  // 如果是从扫描页面跳转过来的，返回时添加查询参数以恢复状态
  if (route.query.from === 'scan') {
    return {
      path: '/platform/',
      query: { from: 'check' }
    }
  }
  return '/platform/'
}

// 提供 isDarkMode 和 toggleDarkMode 给子组件
provide('isDarkMode', isDarkMode)
provide('toggleDarkMode', toggleDarkMode)

onMounted(() => {
  // 检查本地存储中的主题设置
  const savedTheme = localStorage.getItem('theme')
  if (savedTheme === 'dark' || (!savedTheme && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
    isDarkMode.value = true
    document.documentElement.classList.add('dark')
  }
  
  // 检查URL查询参数中是否有股票代码
  if (route.query.code) {
    stockCode.value = String(route.query.code)
    // 自动执行检查
    checkStock()
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

