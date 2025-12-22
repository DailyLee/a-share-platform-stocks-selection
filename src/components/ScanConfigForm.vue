<template>
  <div class="space-y-4">
    <!-- 扫描日期（仅在单次扫描时显示） -->
    <div v-if="showScanDate">
      <label class="block text-sm font-medium mb-2">
        <i class="fas fa-calendar-alt mr-1 text-primary"></i>
        扫描日期
      </label>
      <input
        v-model="localConfig.scan_date"
        type="date"
        class="input w-full"
        :max="maxDate"
      />
      <p class="text-xs text-muted-foreground mt-1">
        设置扫描的截止日期，默认为今天
      </p>
    </div>

    <!-- 基本参数 -->
    <div>
      <h3 class="text-sm font-medium mb-2 flex items-center">
        <i class="fas fa-cog mr-1 text-primary"></i>
        基本参数
      </h3>
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
        <div>
          <ParameterLabel for-id="windowsInput" parameter-id="windows"
            @show-tutorial="$emit('show-tutorial', 'windows')">
            窗口期设置
          </ParameterLabel>
          <input
            v-model="localConfig.windowsInput"
            class="input"
            id="windowsInput"
            placeholder="例如: 30,60,90"
          />
          <p class="text-xs text-muted-foreground mt-1">
            用逗号分隔的窗口期天数，例如：30,60,90
          </p>
        </div>
        <div>
          <ParameterLabel for-id="expectedCount" parameter-id="expected_count"
            @show-tutorial="$emit('show-tutorial', 'expected_count')">
            期望返回数量
          </ParameterLabel>
          <input
            v-model.number="localConfig.expected_count"
            class="input"
            id="expectedCount"
            type="number"
            min="1"
            placeholder="例如: 10"
          />
          <p class="text-xs text-muted-foreground mt-1">
            期望返回的股票数量
          </p>
        </div>
      </div>
    </div>

    <!-- 价格参数 -->
    <div>
      <h3 class="text-sm font-medium mb-2 flex items-center">
        <i class="fas fa-chart-line mr-1 text-primary"></i>
        价格参数
      </h3>
      <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 sm:gap-4">
        <div>
          <ParameterLabel for-id="boxThreshold" parameter-id="box_threshold"
            @show-tutorial="$emit('show-tutorial', 'box_threshold')">
            振幅阈值 (%)
          </ParameterLabel>
          <input v-model.number="localConfig.box_threshold" class="input" id="boxThreshold" type="number" step="0.01"
            placeholder="例如: 0.3">
        </div>
        <div>
          <ParameterLabel for-id="maDiffThreshold" parameter-id="ma_diff_threshold"
            @show-tutorial="$emit('show-tutorial', 'ma_diff_threshold')">
            均线粘合度 (%)
          </ParameterLabel>
          <input v-model.number="localConfig.ma_diff_threshold" class="input" id="maDiffThreshold" type="number"
            step="0.005" placeholder="例如: 0.03">
        </div>
        <div>
          <ParameterLabel for-id="volatilityThreshold" parameter-id="volatility_threshold"
            @show-tutorial="$emit('show-tutorial', 'volatility_threshold')">
            波动率阈值 (%)
          </ParameterLabel>
          <input v-model.number="localConfig.volatility_threshold" class="input" id="volatilityThreshold" type="number"
            step="0.005" placeholder="例如: 0.03">
        </div>
      </div>
    </div>

    <!-- 成交量参数 -->
    <div>
      <h3 class="text-sm font-medium mb-2 flex items-center">
        <i class="fas fa-chart-bar mr-1 text-primary"></i>
        成交量参数
      </h3>
      <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 sm:gap-4">
        <div>
          <div class="flex items-center justify-between">
            <ParameterLabel for-id="useVolumeAnalysis" parameter-id="use_volume_analysis"
              @show-tutorial="$emit('show-tutorial', 'use_volume_analysis')">
              启用成交量分析
            </ParameterLabel>
            <label for="useVolumeAnalysis" class="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" v-model="localConfig.use_volume_analysis" id="useVolumeAnalysis"
                class="sr-only peer">
              <div
                class="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-secondary">
              </div>
            </label>
          </div>
        </div>
        <div v-if="localConfig.use_volume_analysis">
          <ParameterLabel for-id="volumeChangeThreshold" parameter-id="volume_change_threshold"
            @show-tutorial="$emit('show-tutorial', 'volume_change_threshold')">
            成交量变化阈值
          </ParameterLabel>
          <input v-model.number="localConfig.volume_change_threshold" class="input" id="volumeChangeThreshold"
            type="number" step="0.1" placeholder="例如: 0.5">
        </div>
        <div v-if="localConfig.use_volume_analysis">
          <ParameterLabel for-id="volumeStabilityThreshold" parameter-id="volume_stability_threshold"
            @show-tutorial="$emit('show-tutorial', 'volume_stability_threshold')">
            成交量稳定性阈值
          </ParameterLabel>
          <input v-model.number="localConfig.volume_stability_threshold" class="input" id="volumeStabilityThreshold"
            type="number" step="0.1" placeholder="例如: 0.5">
        </div>
        <div v-if="localConfig.use_volume_analysis">
          <ParameterLabel for-id="volumeIncreaseThreshold" parameter-id="volume_increase_threshold"
            @show-tutorial="$emit('show-tutorial', 'volume_increase_threshold')">
            成交量突破阈值
          </ParameterLabel>
          <input v-model.number="localConfig.volume_increase_threshold" class="input" id="volumeIncreaseThreshold"
            type="number" step="0.1" placeholder="例如: 1.5">
        </div>
      </div>
    </div>

    <!-- 位置参数 -->
    <div>
      <h3 class="text-sm font-medium mb-2 flex items-center">
        <i class="fas fa-map-marker-alt mr-1 text-primary"></i>
        位置参数
      </h3>
      <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 sm:gap-4">
        <div>
          <div class="flex items-center justify-between">
            <ParameterLabel for-id="useLowPosition" parameter-id="use_low_position"
              @show-tutorial="$emit('show-tutorial', 'use_low_position')">
              启用低位判断
            </ParameterLabel>
            <label for="useLowPosition" class="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" v-model="localConfig.use_low_position" id="useLowPosition"
                class="sr-only peer">
              <div
                class="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-secondary">
              </div>
            </label>
          </div>
        </div>
        <div v-if="localConfig.use_low_position">
          <ParameterLabel for-id="highPointLookbackDays" parameter-id="high_point_lookback_days"
            @show-tutorial="$emit('show-tutorial', 'high_point_lookback_days')">
            高点查找时间范围（天）
          </ParameterLabel>
          <input v-model.number="localConfig.high_point_lookback_days" class="input" id="highPointLookbackDays"
            type="number" min="1" placeholder="例如: 365">
        </div>
        <div v-if="localConfig.use_low_position">
          <ParameterLabel for-id="declinePeriodDays" parameter-id="decline_period_days"
            @show-tutorial="$emit('show-tutorial', 'decline_period_days')">
            下跌时间范围（天）
          </ParameterLabel>
          <input v-model.number="localConfig.decline_period_days" class="input" id="declinePeriodDays" type="number"
            min="1" placeholder="例如: 180">
        </div>
        <div v-if="localConfig.use_low_position">
          <ParameterLabel for-id="declineThreshold" parameter-id="decline_threshold"
            @show-tutorial="$emit('show-tutorial', 'decline_threshold')">
            下跌阈值 (%)
          </ParameterLabel>
          <input v-model.number="localConfig.decline_threshold" class="input" id="declineThreshold" type="number"
            step="0.01" placeholder="例如: 0.3">
        </div>
      </div>
    </div>

    <!-- 快速下跌判断参数 -->
    <div>
      <h3 class="text-sm font-medium mb-2 flex items-center">
        <i class="fas fa-arrow-down mr-1 text-primary"></i>
        快速下跌判断参数
      </h3>
      <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 sm:gap-4">
        <div>
          <div class="flex items-center justify-between">
            <ParameterLabel for-id="useRapidDeclineDetection" parameter-id="use_rapid_decline_detection"
              @show-tutorial="$emit('show-tutorial', 'use_rapid_decline_detection')">
              启用快速下跌判断
            </ParameterLabel>
            <label for="useRapidDeclineDetection" class="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" v-model="localConfig.use_rapid_decline_detection" id="useRapidDeclineDetection"
                class="sr-only peer">
              <div
                class="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-secondary">
              </div>
            </label>
          </div>
        </div>
        <div v-if="localConfig.use_rapid_decline_detection">
          <ParameterLabel for-id="rapidDeclineDays" parameter-id="rapid_decline_days"
            @show-tutorial="$emit('show-tutorial', 'rapid_decline_days')">
            快速下跌窗口（天）
          </ParameterLabel>
          <input v-model.number="localConfig.rapid_decline_days" class="input" id="rapidDeclineDays" type="number"
            min="1" placeholder="例如: 30">
        </div>
        <div v-if="localConfig.use_rapid_decline_detection">
          <ParameterLabel for-id="rapidDeclineThreshold" parameter-id="rapid_decline_threshold"
            @show-tutorial="$emit('show-tutorial', 'rapid_decline_threshold')">
            快速下跌阈值 (%)
          </ParameterLabel>
          <input v-model.number="localConfig.rapid_decline_threshold" class="input" id="rapidDeclineThreshold"
            type="number" step="0.01" placeholder="例如: 0.15">
        </div>
      </div>
    </div>

    <!-- 突破确认参数 -->
    <div>
      <h3 class="text-sm font-medium mb-2 flex items-center">
        <i class="fas fa-check-circle mr-1 text-primary"></i>
        突破确认参数
      </h3>
      <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 sm:gap-4">
        <div>
          <div class="flex items-center justify-between">
            <ParameterLabel for-id="useBreakthroughConfirmation" parameter-id="use_breakthrough_confirmation"
              @show-tutorial="$emit('show-tutorial', 'use_breakthrough_confirmation')">
              启用突破确认
            </ParameterLabel>
            <label for="useBreakthroughConfirmation" class="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" v-model="localConfig.use_breakthrough_confirmation" id="useBreakthroughConfirmation"
                class="sr-only peer">
              <div
                class="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-secondary">
              </div>
            </label>
          </div>
        </div>
        <div v-if="localConfig.use_breakthrough_confirmation">
          <ParameterLabel for-id="breakthroughConfirmationDays" parameter-id="breakthrough_confirmation_days"
            @show-tutorial="$emit('show-tutorial', 'breakthrough_confirmation_days')">
            确认天数
          </ParameterLabel>
          <input v-model.number="localConfig.breakthrough_confirmation_days" class="input" id="breakthroughConfirmationDays"
            type="number" min="1" placeholder="例如: 1">
        </div>
      </div>
    </div>

    <!-- 箱体检测参数 -->
    <div>
      <h3 class="text-sm font-medium mb-2 flex items-center">
        <i class="fas fa-square mr-1 text-primary"></i>
        箱体检测参数
      </h3>
      <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 sm:gap-4">
        <div>
          <div class="flex items-center justify-between">
            <ParameterLabel for-id="useBoxDetection" parameter-id="use_box_detection"
              @show-tutorial="$emit('show-tutorial', 'use_box_detection')">
              启用箱体检测
            </ParameterLabel>
            <label for="useBoxDetection" class="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" v-model="localConfig.use_box_detection" id="useBoxDetection"
                class="sr-only peer">
              <div
                class="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-secondary">
              </div>
            </label>
          </div>
        </div>
        <div v-if="localConfig.use_box_detection">
          <ParameterLabel for-id="boxQualityThreshold" parameter-id="box_quality_threshold"
            @show-tutorial="$emit('show-tutorial', 'box_quality_threshold')">
            箱体质量阈值
          </ParameterLabel>
          <input v-model.number="localConfig.box_quality_threshold" class="input" id="boxQualityThreshold" type="number"
            step="0.1" min="0" max="1" placeholder="例如: 0.9">
        </div>
      </div>
    </div>

    <!-- 基本面筛选参数 -->
    <div>
      <h3 class="text-sm font-medium mb-2 flex items-center">
        <i class="fas fa-chart-pie mr-1 text-primary"></i>
        基本面筛选参数
      </h3>
      <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 sm:gap-4">
        <div>
          <div class="flex items-center justify-between">
            <ParameterLabel for-id="useFundamentalFilter" parameter-id="use_fundamental_filter"
              @show-tutorial="$emit('show-tutorial', 'use_fundamental_filter')">
              启用基本面筛选
            </ParameterLabel>
            <label for="useFundamentalFilter" class="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" v-model="localConfig.use_fundamental_filter" id="useFundamentalFilter"
                class="sr-only peer">
              <div
                class="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-secondary">
              </div>
            </label>
          </div>
          <p class="text-xs text-muted-foreground mt-1">启用基于财务指标的基本面筛选</p>
        </div>

        <div v-if="localConfig.use_fundamental_filter">
          <ParameterLabel for-id="revenueGrowthPercentile" parameter-id="revenue_growth_percentile"
            @show-tutorial="$emit('show-tutorial', 'revenue_growth_percentile')">
            营收增长率百分位
          </ParameterLabel>
          <input v-model.number="localConfig.revenue_growth_percentile" class="input" id="revenueGrowthPercentile"
            type="number" step="0.05" min="0.1" max="0.9" placeholder="例如: 0.3">
          <p class="text-xs text-muted-foreground mt-1">要求位于行业前X%（0.3 = 前30%）</p>
        </div>

        <div v-if="localConfig.use_fundamental_filter">
          <ParameterLabel for-id="profitGrowthPercentile" parameter-id="profit_growth_percentile"
            @show-tutorial="$emit('show-tutorial', 'profit_growth_percentile')">
            净利润增长率百分位
          </ParameterLabel>
          <input v-model.number="localConfig.profit_growth_percentile" class="input" id="profitGrowthPercentile"
            type="number" step="0.05" min="0.1" max="0.9" placeholder="例如: 0.3">
        </div>

        <div v-if="localConfig.use_fundamental_filter">
          <ParameterLabel for-id="roePercentile" parameter-id="roe_percentile"
            @show-tutorial="$emit('show-tutorial', 'roe_percentile')">
            ROE百分位
          </ParameterLabel>
          <input v-model.number="localConfig.roe_percentile" class="input" id="roePercentile" type="number" step="0.05"
            min="0.1" max="0.9" placeholder="例如: 0.3">
        </div>

        <div v-if="localConfig.use_fundamental_filter">
          <ParameterLabel for-id="liabilityPercentile" parameter-id="liability_percentile"
            @show-tutorial="$emit('show-tutorial', 'liability_percentile')">
            资产负债率百分位
          </ParameterLabel>
          <input v-model.number="localConfig.liability_percentile" class="input" id="liabilityPercentile" type="number"
            step="0.05" min="0.1" max="0.9" placeholder="例如: 0.3">
          <p class="text-xs text-muted-foreground mt-1">要求位于行业后X%（0.3 = 后30%）</p>
        </div>

        <div v-if="localConfig.use_fundamental_filter">
          <ParameterLabel for-id="pePercentile" parameter-id="pe_percentile"
            @show-tutorial="$emit('show-tutorial', 'pe_percentile')">
            PE百分位
          </ParameterLabel>
          <input v-model.number="localConfig.pe_percentile" class="input" id="pePercentile" type="number" step="0.05"
            min="0.1" max="0.9" placeholder="例如: 0.7">
          <p class="text-xs text-muted-foreground mt-1">要求不在行业前X%最高估值（0.7 = 前30%）</p>
        </div>

        <div v-if="localConfig.use_fundamental_filter">
          <ParameterLabel for-id="pbPercentile" parameter-id="pb_percentile"
            @show-tutorial="$emit('show-tutorial', 'pb_percentile')">
            PB百分位
          </ParameterLabel>
          <input v-model.number="localConfig.pb_percentile" class="input" id="pbPercentile" type="number" step="0.05"
            min="0.1" max="0.9" placeholder="例如: 0.7">
        </div>

        <div v-if="localConfig.use_fundamental_filter">
          <ParameterLabel for-id="fundamentalYearsToCheck" parameter-id="fundamental_years_to_check"
            @show-tutorial="$emit('show-tutorial', 'fundamental_years_to_check')">
            检查连续增长的年数
          </ParameterLabel>
          <input v-model.number="localConfig.fundamental_years_to_check" class="input" id="fundamentalYearsToCheck"
            type="number" min="1" max="5" placeholder="例如: 3">
        </div>
      </div>
    </div>

    <!-- 窗口权重参数 -->
    <div>
      <h3 class="text-sm font-medium mb-2 flex items-center">
        <i class="fas fa-balance-scale mr-1 text-primary"></i>
        窗口权重参数
      </h3>
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
        <div>
          <div class="flex items-center justify-between">
            <ParameterLabel for-id="useWindowWeights" parameter-id="use_window_weights"
              @show-tutorial="$emit('show-tutorial', 'use_window_weights')">
              启用窗口权重
            </ParameterLabel>
            <label for="useWindowWeights" class="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" v-model="localConfig.use_window_weights" id="useWindowWeights"
                class="sr-only peer">
              <div
                class="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-secondary">
              </div>
            </label>
          </div>
        </div>
      </div>
      
      <!-- 窗口权重设置 -->
      <div v-if="localConfig.use_window_weights && parsedWindows && parsedWindows.length > 0" class="mt-4">
        <div class="bg-muted/30 p-3 rounded-md">
          <p class="text-xs text-muted-foreground mb-2">
            为不同的窗口期分配权重，权重总和将自动归一化。权重越高，该窗口期的分析结果对最终评分的影响越大。
          </p>
          <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 sm:gap-4">
            <div v-for="window in parsedWindows" :key="window" class="flex items-center space-x-2">
              <label class="text-sm font-medium whitespace-nowrap">{{ window }}天:</label>
              <input 
                :value="localWindowWeights[window] || 0" 
                type="range" 
                min="0" 
                max="10" 
                step="1" 
                class="flex-grow"
                @input="handleWindowWeightChange(window, $event.target.value)"
              >
              <span class="text-sm">{{ localWindowWeights[window] || 0 }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 系统设置 -->
    <div>
      <h3 class="text-sm font-medium mb-2 flex items-center">
        <i class="fas fa-tools mr-1 text-primary"></i>
        系统设置
      </h3>
      <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 sm:gap-4">
        <div>
          <div class="flex items-center justify-between">
            <label class="text-sm font-medium">使用扫描缓存</label>
            <label class="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" v-model="localConfig.use_scan_cache"
                class="sr-only peer">
              <div
                class="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-secondary">
              </div>
            </label>
          </div>
        </div>
        <div>
          <label class="block text-sm font-medium mb-2">最大股票数量限制</label>
          <input v-model.number="localConfig.max_stock_count" class="input" type="number" min="0"
            placeholder="0或空表示全量扫描">
        </div>
        <div>
          <div class="flex items-center justify-between">
            <label class="text-sm font-medium">优先使用本地数据库</label>
            <label class="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" v-model="localConfig.use_local_database_first"
                class="sr-only peer">
              <div
                class="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-secondary">
              </div>
            </label>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed, nextTick } from 'vue'
import ParameterLabel from './parameter-help/ParameterLabel.vue'

const props = defineProps({
  config: {
    type: Object,
    required: true
  },
  showScanDate: {
    type: Boolean,
    default: true
  },
  windowWeights: {
    type: Object,
    default: () => ({})
  },
  parsedWindows: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['update:config', 'show-tutorial', 'update-window-weights'])

const localWindowWeights = ref({ ...props.windowWeights })

watch(() => props.windowWeights, (newWeights) => {
  localWindowWeights.value = { ...newWeights }
}, { deep: true })

const handleWindowWeightChange = (window, value) => {
  localWindowWeights.value[window] = parseInt(value, 10)
  emit('update-window-weights', window, value)
}

const maxDate = computed(() => {
  const today = new Date()
  return today.toISOString().split('T')[0]
})

const localConfig = ref({ ...props.config })
const isUpdatingFromProps = ref(false)

watch(() => props.config, (newConfig) => {
  isUpdatingFromProps.value = true
  localConfig.value = { ...newConfig }
  // Use nextTick to ensure the flag is reset after all watchers have run
  nextTick(() => {
    isUpdatingFromProps.value = false
  })
}, { deep: true })

watch(localConfig, (newConfig) => {
  // Only emit if the change didn't come from props
  if (!isUpdatingFromProps.value) {
    emit('update:config', newConfig)
  }
}, { deep: true })

watch(() => props.parsedWindows, (newWindows) => {
  // 当窗口期变化时，初始化新窗口的权重
  newWindows.forEach(window => {
    if (localWindowWeights.value[window] === undefined) {
      localWindowWeights.value[window] = 5 // 默认权重
    }
  })
  // 移除不在窗口列表中的权重
  Object.keys(localWindowWeights.value).forEach(key => {
    if (!newWindows.includes(parseInt(key, 10))) {
      delete localWindowWeights.value[key]
    }
  })
}, { immediate: true })
</script>

