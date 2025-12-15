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

