<template>
  <div class="space-y-4">
    <!-- 扫描日期 -->
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
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4 mb-4">
      <!-- 窗口期设置 -->
      <div>
        <ParameterLabel for-id="windows" parameter-id="windows" @show-tutorial="$emit('show-tutorial', 'windows')">
          窗口期设置
        </ParameterLabel>
        <div class="flex flex-col space-y-2">
          <!-- 预设选项 -->
          <div class="flex flex-wrap gap-2">
            <button v-for="preset in windowPresets" :key="preset.name" @click="selectWindowPreset(preset.value)"
              :class="[
                'px-2 py-1 text-xs rounded-md transition-colors',
                localConfig.windowsInput === preset.value
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-muted hover:bg-muted/80 text-muted-foreground'
              ]">
              {{ preset.name }}
            </button>
            <button @click="showCustomWindowInput = true" :class="[
              'px-2 py-1 text-xs rounded-md transition-colors',
              !isUsingPreset
                ? 'bg-primary text-primary-foreground'
                : 'bg-muted hover:bg-muted/80 text-muted-foreground'
            ]">
              自定义
            </button>
          </div>

          <!-- 自定义输入 -->
          <div v-if="showCustomWindowInput" class="flex items-center space-x-2">
            <input v-model="localConfig.windowsInput" class="input flex-grow" id="windows" type="text"
              placeholder="例如: 30,60,90">
            <button @click="validateCustomWindows" class="btn btn-primary text-xs py-1 px-2">
              确认
            </button>
          </div>

          <!-- 当前选择的窗口期显示 -->
          <div v-if="!showCustomWindowInput" class="text-xs text-muted-foreground">
            当前窗口期:
            <span v-for="(window, index) in parsedWindows" :key="window" class="font-medium">
              {{ window }}天{{ index < parsedWindows.length - 1 ? '、' : '' }} </span>
          </div>
        </div>
      </div>
      <div>
        <ParameterLabel for-id="expectedCount" parameter-id="expected_count"
          @show-tutorial="$emit('show-tutorial', 'expected_count')">
          期望股票数量
        </ParameterLabel>
        <input v-model.number="localConfig.expected_count" class="input" id="expectedCount" type="number" min="1"
          max="100" placeholder="例如: 10">
      </div>
      <div class="flex flex-wrap items-end gap-4">
        <label for="useVolumeAnalysis"
          class="flex items-center space-x-2 cursor-pointer hover:opacity-80 transition-opacity p-1 rounded-md hover:bg-muted/30">
          <input type="checkbox" v-model="localConfig.use_volume_analysis" id="useVolumeAnalysis" class="checkbox">
          <ParameterLabel for-id="useVolumeAnalysis" parameter-id="use_volume_analysis"
            @show-tutorial="$emit('show-tutorial', 'use_volume_analysis')">
            <span class="text-sm font-medium">启用成交量分析</span>
          </ParameterLabel>
        </label>
        <label for="useBreakthroughPrediction"
          class="flex items-center space-x-2 cursor-pointer hover:opacity-80 transition-opacity p-1 rounded-md hover:bg-muted/30">
          <input type="checkbox" v-model="localConfig.use_breakthrough_prediction" id="useBreakthroughPrediction"
            class="checkbox">
          <ParameterLabel for-id="useBreakthroughPrediction" parameter-id="use_breakthrough_prediction"
            @show-tutorial="$emit('show-tutorial', 'use_breakthrough_prediction')">
            <span class="text-sm font-medium">启用突破前兆识别</span>
          </ParameterLabel>
        </label>
        <label for="useBreakthroughConfirmation"
          class="flex items-center space-x-2 cursor-pointer hover:opacity-80 transition-opacity p-1 rounded-md hover:bg-muted/30">
          <input type="checkbox" v-model="localConfig.use_breakthrough_confirmation" id="useBreakthroughConfirmation"
            class="checkbox">
          <ParameterLabel for-id="useBreakthroughConfirmation" parameter-id="use_breakthrough_confirmation"
            @show-tutorial="$emit('show-tutorial', 'use_breakthrough_confirmation')">
            <span class="text-sm font-medium">启用突破确认</span>
          </ParameterLabel>
        </label>
        <label for="useLowPosition"
          class="flex items-center space-x-2 cursor-pointer hover:opacity-80 transition-opacity p-1 rounded-md hover:bg-muted/30">
          <input type="checkbox" v-model="localConfig.use_low_position" id="useLowPosition" class="checkbox">
          <ParameterLabel for-id="useLowPosition" parameter-id="use_low_position"
            @show-tutorial="$emit('show-tutorial', 'use_low_position')">
            <span class="text-sm font-medium">启用低位判断</span>
          </ParameterLabel>
        </label>
        <label for="useWindowWeights"
          class="flex items-center space-x-2 cursor-pointer hover:opacity-80 transition-opacity p-1 rounded-md hover:bg-muted/30">
          <input type="checkbox" v-model="localConfig.use_window_weights" id="useWindowWeights" class="checkbox">
          <ParameterLabel for-id="useWindowWeights" parameter-id="use_window_weights"
            @show-tutorial="$emit('show-tutorial', 'use_window_weights')">
            <span class="text-sm font-medium">启用窗口权重</span>
          </ParameterLabel>
        </label>
      </div>
    </div>

    <!-- 价格参数 -->
    <div class="mb-4">
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
    <div class="mb-4" v-if="localConfig.use_volume_analysis">
      <h3 class="text-sm font-medium mb-2 flex items-center">
        <i class="fas fa-chart-bar mr-1 text-primary"></i>
        成交量参数
      </h3>
      <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 sm:gap-4">
        <div>
          <ParameterLabel for-id="volumeChangeThreshold" parameter-id="volume_change_threshold"
            @show-tutorial="$emit('show-tutorial', 'volume_change_threshold')">
            成交量变化阈值
          </ParameterLabel>
          <input v-model.number="localConfig.volume_change_threshold" class="input" id="volumeChangeThreshold"
            type="number" step="0.05" placeholder="例如: 0.8">
          <p class="text-xs text-muted-foreground mt-1">平台期内成交量变化的最大比例</p>
        </div>
        <div>
          <ParameterLabel for-id="volumeStabilityThreshold" parameter-id="volume_stability_threshold"
            @show-tutorial="$emit('show-tutorial', 'volume_stability_threshold')">
            成交量稳定性阈值
          </ParameterLabel>
          <input v-model.number="localConfig.volume_stability_threshold" class="input" id="volumeStabilityThreshold"
            type="number" step="0.05" placeholder="例如: 0.5">
          <p class="text-xs text-muted-foreground mt-1">平台期内成交量波动的最大程度</p>
        </div>
        <div>
          <ParameterLabel for-id="volumeIncreaseThreshold" parameter-id="volume_increase_threshold"
            @show-tutorial="$emit('show-tutorial', 'volume_increase_threshold')">
            成交量突破阈值
          </ParameterLabel>
          <input v-model.number="localConfig.volume_increase_threshold" class="input" id="volumeIncreaseThreshold"
            type="number" step="0.1" placeholder="例如: 1.5">
          <p class="text-xs text-muted-foreground mt-1">识别为突破的最小成交量放大倍数</p>
        </div>
      </div>
    </div>

    <!-- 换手率参数 -->
    <div class="mb-4">
      <h3 class="text-sm font-medium mb-2 flex items-center">
        <i class="fas fa-exchange-alt mr-1 text-primary"></i>
        换手率参数
      </h3>
      <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 sm:gap-4">
        <div>
          <ParameterLabel for-id="maxTurnoverRate" parameter-id="max_turnover_rate"
            @show-tutorial="$emit('show-tutorial', 'max_turnover_rate')">
            最大换手率 (%)
          </ParameterLabel>
          <input v-model.number="localConfig.max_turnover_rate" class="input" id="maxTurnoverRate" type="number"
            step="0.1" min="0" placeholder="例如: 3.0">
          <p class="text-xs text-muted-foreground mt-1">
            平台期平均换手率不超过此值
          </p>
        </div>
        <div>
          <div class="flex items-center justify-between">
            <ParameterLabel for-id="allowTurnoverSpikes" parameter-id="allow_turnover_spikes"
              @show-tutorial="$emit('show-tutorial', 'allow_turnover_spikes')">
              允许异常放量
            </ParameterLabel>
            <label for="allowTurnoverSpikes" class="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" v-model="localConfig.allow_turnover_spikes" id="allowTurnoverSpikes"
                class="sr-only peer">
              <div
                class="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-secondary">
              </div>
            </label>
          </div>
          <p class="text-xs text-muted-foreground mt-1">
            是否允许偶尔的异常放量
          </p>
        </div>
      </div>
    </div>

    <!-- 相对强度参数 -->
    <div class="mb-4">
      <h3 class="text-sm font-medium mb-2 flex items-center">
        <i class="fas fa-chart-area mr-1 text-primary"></i>
        相对强度参数
      </h3>
      <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 sm:gap-4">
        <div>
          <div class="flex items-center justify-between">
            <ParameterLabel for-id="checkRelativeStrength" parameter-id="check_relative_strength"
              @show-tutorial="$emit('show-tutorial', 'check_relative_strength')">
              启用相对大盘强度检查
            </ParameterLabel>
            <label for="checkRelativeStrength" class="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" v-model="localConfig.check_relative_strength" id="checkRelativeStrength"
                class="sr-only peer">
              <div
                class="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-primary">
              </div>
            </label>
          </div>
          <p class="text-xs text-muted-foreground mt-1">
            启用相对大盘强度检查，计算并保存相对强度值。可通过阈值设置是否作为筛选条件
          </p>
        </div>
        <div v-if="localConfig.check_relative_strength">
          <ParameterLabel for-id="outperformIndexThreshold" parameter-id="outperform_index_threshold"
            @show-tutorial="$emit('show-tutorial', 'outperform_index_threshold')">
            相对强度阈值
          </ParameterLabel>
          <input 
            :value="localConfig.outperform_index_threshold === null ? '' : localConfig.outperform_index_threshold"
            @input="handleOutperformIndexThresholdInput($event)"
            class="input" 
            id="outperformIndexThreshold"
            type="number" 
            step="0.01" 
            placeholder="留空表示不过滤">
          <p class="text-xs text-muted-foreground mt-1">
            相对强度需大于此值。留空表示不过滤（计算并保存相对强度值，但不作为筛选条件）
          </p>
        </div>
      </div>
    </div>

    <!-- 位置参数 -->
    <div class="mb-4" v-if="localConfig.use_low_position">
      <h3 class="text-sm font-medium mb-2 flex items-center">
        <i class="fas fa-map-marker-alt mr-1 text-primary"></i>
        位置参数
      </h3>
      <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 sm:gap-4">
        <div>
          <ParameterLabel for-id="highPointLookbackDays" parameter-id="high_point_lookback_days"
            @show-tutorial="$emit('show-tutorial', 'high_point_lookback_days')">
            高点查找时间范围 (天)
          </ParameterLabel>
          <input v-model.number="localConfig.high_point_lookback_days" class="input" id="highPointLookbackDays"
            type="number" step="1" min="30" placeholder="例如: 365">
        </div>
        <div>
          <ParameterLabel for-id="declinePeriodDays" parameter-id="decline_period_days"
            @show-tutorial="$emit('show-tutorial', 'decline_period_days')">
            下跌时间范围 (天)
          </ParameterLabel>
          <input v-model.number="localConfig.decline_period_days" class="input" id="declinePeriodDays" type="number"
            step="1" min="30" placeholder="例如: 180">
        </div>
        <div>
          <ParameterLabel for-id="declineThreshold" parameter-id="decline_threshold"
            @show-tutorial="$emit('show-tutorial', 'decline_threshold')">
            下跌幅度阈值
          </ParameterLabel>
          <input v-model.number="localConfig.decline_threshold" class="input" id="declineThreshold" type="number"
            step="0.05" min="0.1" max="0.9" placeholder="例如: 0.3">
          <p class="text-xs text-muted-foreground mt-1">从高点下跌的最小百分比 (0.3 = 30%)</p>
        </div>
      </div>
    </div>

    <!-- 快速下跌判断参数 -->
    <div class="mb-4" v-if="localConfig.use_low_position">
      <h3 class="text-sm font-medium mb-2 flex items-center">
        <i class="fas fa-bolt mr-1 text-primary"></i>
        快速下跌判断
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
                class="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-primary">
              </div>
            </label>
          </div>
          <p class="text-xs text-muted-foreground mt-1">识别类似安记食品的快速下跌后形成平台期的股票</p>
        </div>
        <!-- 只有在启用快速下跌判断时才显示这些参数 -->
        <div v-if="localConfig.use_rapid_decline_detection">
          <ParameterLabel for-id="rapidDeclineDays" parameter-id="rapid_decline_days"
            @show-tutorial="$emit('show-tutorial', 'rapid_decline_days')">
            快速下跌时间窗口 (天)
          </ParameterLabel>
          <input v-model.number="localConfig.rapid_decline_days" class="input" id="rapidDeclineDays" type="number"
            step="1" min="10" max="60" placeholder="例如: 30">
          <p class="text-xs text-muted-foreground mt-1">定义快速下跌的时间窗口</p>
        </div>
        <div v-if="localConfig.use_rapid_decline_detection">
          <ParameterLabel for-id="rapidDeclineThreshold" parameter-id="rapid_decline_threshold"
            @show-tutorial="$emit('show-tutorial', 'rapid_decline_threshold')">
            快速下跌幅度阈值
          </ParameterLabel>
          <input v-model.number="localConfig.rapid_decline_threshold" class="input" id="rapidDeclineThreshold"
            type="number" step="0.05" min="0.05" max="0.5" placeholder="例如: 0.15">
          <p class="text-xs text-muted-foreground mt-1">快速下跌的最小百分比 (0.15 = 15%)</p>
        </div>
      </div>
    </div>

    <!-- 突破确认参数 -->
    <div class="mb-4" v-if="localConfig.use_breakthrough_confirmation">
      <h3 class="text-sm font-medium mb-2 flex items-center">
        <i class="fas fa-check-circle mr-1 text-primary"></i>
        突破确认参数
      </h3>
      <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 sm:gap-4">
        <div>
          <ParameterLabel for-id="breakthroughConfirmationDays" parameter-id="breakthrough_confirmation_days"
            @show-tutorial="$emit('show-tutorial', 'breakthrough_confirmation_days')">
            确认天数
          </ParameterLabel>
          <input v-model.number="localConfig.breakthrough_confirmation_days" class="input"
            id="breakthroughConfirmationDays" type="number" step="1" min="1" max="5" placeholder="例如: 1">
          <p class="text-xs text-muted-foreground mt-1">突破后需要多少天确认</p>
        </div>
      </div>
    </div>

    <!-- 箱体检测参数 -->
    <div class="mb-4">
      <h3 class="text-sm font-medium mb-2 flex items-center">
        <i class="fas fa-cube mr-1 text-primary"></i>
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
              <input type="checkbox" v-model="localConfig.use_box_detection" id="useBoxDetection" class="sr-only peer">
              <div
                class="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-primary">
              </div>
            </label>
          </div>
          <p class="text-xs text-muted-foreground mt-1">启用更精确的箱体形态检测</p>
        </div>
        <div v-if="localConfig.use_box_detection">
          <ParameterLabel for-id="boxQualityThreshold" parameter-id="box_quality_threshold"
            @show-tutorial="$emit('show-tutorial', 'box_quality_threshold')">
            箱体质量阈值
          </ParameterLabel>
          <input v-model.number="localConfig.box_quality_threshold" class="input" id="boxQualityThreshold"
            type="number" step="0.01" min="0.1" max="1.0" placeholder="例如: 0.94">
          <p class="text-xs text-muted-foreground mt-1">箱体形态的最低质量要求 (0.6 = 60%)</p>
        </div>
      </div>
    </div>

    <!-- 基本面筛选参数 -->
    <div class="mb-4">
      <h3 class="text-sm font-medium mb-2 flex items-center">
        <i class="fas fa-chart-pie mr-1 text-secondary"></i>
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
          <p class="text-xs text-muted-foreground mt-1">要求位于行业前X%（0.3 = 前30%）</p>
        </div>

        <div v-if="localConfig.use_fundamental_filter">
          <ParameterLabel for-id="roePercentile" parameter-id="roe_percentile"
            @show-tutorial="$emit('show-tutorial', 'roe_percentile')">
            ROE百分位
          </ParameterLabel>
          <input v-model.number="localConfig.roe_percentile" class="input" id="roePercentile" type="number" step="0.05"
            min="0.1" max="0.9" placeholder="例如: 0.3">
          <p class="text-xs text-muted-foreground mt-1">要求位于行业前X%（0.3 = 前30%）</p>
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
          <p class="text-xs text-muted-foreground mt-1">要求不在行业前X%最高估值（0.7 = 后70%）</p>
        </div>

        <div v-if="localConfig.use_fundamental_filter">
          <ParameterLabel for-id="pbPercentile" parameter-id="pb_percentile"
            @show-tutorial="$emit('show-tutorial', 'pb_percentile')">
            PB百分位
          </ParameterLabel>
          <input v-model.number="localConfig.pb_percentile" class="input" id="pbPercentile" type="number" step="0.05"
            min="0.1" max="0.9" placeholder="例如: 0.7">
          <p class="text-xs text-muted-foreground mt-1">要求不在行业前X%最高估值（0.7 = 后70%）</p>
        </div>

        <div v-if="localConfig.use_fundamental_filter">
          <ParameterLabel for-id="fundamentalYearsToCheck" parameter-id="fundamental_years_to_check"
            @show-tutorial="$emit('show-tutorial', 'fundamental_years_to_check')">
            检查年数
          </ParameterLabel>
          <input v-model.number="localConfig.fundamental_years_to_check" class="input" id="fundamentalYearsToCheck"
            type="number" step="1" min="1" max="5" placeholder="例如: 3">
          <p class="text-xs text-muted-foreground mt-1">连续增长的年数要求（默认3年）</p>
        </div>
      </div>
    </div>

    <!-- 窗口权重设置 -->
    <div class="mb-4" v-if="localConfig.use_window_weights">
      <h3 class="text-sm font-medium mb-2 flex items-center">
        <i class="fas fa-balance-scale mr-1 text-primary"></i>
        窗口权重设置
      </h3>
      <div class="bg-muted/30 p-3 rounded-md mb-3">
        <p class="text-xs text-muted-foreground mb-2">
          为不同的窗口期分配权重，权重总和将自动归一化。权重越高，该窗口期的分析结果对最终评分的影响越大。
        </p>
        <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 sm:gap-4">
          <div v-for="window in parsedWindows" :key="window" class="flex items-center space-x-2">
            <label class="text-sm font-medium whitespace-nowrap">{{ window }}天:</label>
            <input v-model.number="localWindowWeights[window]" type="range" min="0" max="10" step="1" class="flex-grow"
              @input="handleWindowWeightChange(window, $event.target.value)">
            <span class="text-sm">{{ localWindowWeights[window] || 0 }}</span>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 系统设置 -->
    <div class="mb-6">
      <h3 class="text-sm font-medium mb-3 flex items-center">
        <i class="fas fa-cog mr-2 text-primary"></i>
        系统设置
      </h3>
      <div class="bg-muted/30 p-4 rounded-md space-y-3">
        <div class="flex items-center space-x-2">
          <input
            type="checkbox"
            id="useScanCache"
            v-model="localConfig.use_scan_cache"
            class="checkbox"
          />
          <label for="useScanCache" class="text-sm cursor-pointer">
            <i class="fas fa-database mr-1 text-primary"></i>
            使用扫描结果缓存
          </label>
        </div>
        <p class="text-xs text-muted-foreground ml-6">
          开启后，相同参数的扫描结果会从缓存中读取，提高扫描速度。关闭后会重新从数据中筛选，不使用缓存。
        </p>
        <div class="flex items-center space-x-2 mt-4">
          <input
            type="checkbox"
            id="useLocalDatabaseFirst"
            v-model="localConfig.use_local_database_first"
            class="checkbox"
          />
          <label for="useLocalDatabaseFirst" class="text-sm cursor-pointer">
            <i class="fas fa-server mr-1 text-primary"></i>
            优先使用本地数据库
          </label>
        </div>
        <p class="text-xs text-muted-foreground ml-6">
          开启后，优先从本地数据库读取数据，减少API请求。关闭后，所有数据都从网络API获取并更新本地数据库。
        </p>
        <div class="mt-4">
          <label for="maxStockCount" class="block text-sm font-medium mb-2">
            <i class="fas fa-list-ol mr-1 text-primary"></i>
            扫描股票数量
          </label>
          <input
            id="maxStockCount"
            v-model.number="localConfig.max_stock_count"
            type="number"
            step="1"
            min="1"
            class="input w-full"
            placeholder="留空表示全量扫描"
          />
          <p class="text-xs text-muted-foreground mt-1">
            限制扫描的股票数量，留空或0表示扫描全部股票。输入数字后，将只扫描前N只股票。
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
// 默认配置对象（内部使用，需要在模块作用域中定义以便 defineProps 引用）
function getDefaultScanConfig() {
  return  {
    // 扫描日期
    scan_date: new Date().toISOString().split('T')[0], // 扫描日期，默认为今天
    
    // 基本参数
    windowsInput: '30,60,90', // 中期窗口期设置（默认）
    expected_count: 30, // 期望返回的股票数量，默认为30

    // 价格参数
    box_threshold: 0.3, // 箱体阈值
    ma_diff_threshold: 0.03, // 均线粘合度阈值
    volatility_threshold: 0.03, // 波动率阈值

    // 成交量参数
    use_volume_analysis: true, // 是否启用成交量分析
    volume_change_threshold: 0.5, // 成交量变化阈值
    volume_stability_threshold: 0.5, // 成交量稳定性阈值
    volume_increase_threshold: 1.5, // 成交量突破阈值

    // 技术指标参数
    use_technical_indicators: false, // 是否启用技术指标
    use_breakthrough_prediction: true, // 是否启用突破前兆识别

    // 位置参数
    use_low_position: true, // 是否启用低位判断
    high_point_lookback_days: 365, // 高点查找时间范围
    decline_period_days: 180, // 下跌时间范围
    decline_threshold: 0.3, // 下跌阈值

    // 快速下跌判断参数
    use_rapid_decline_detection: true, // 是否启用快速下跌判断
    rapid_decline_days: 30, // 快速下跌窗口
    rapid_decline_threshold: 0.15, // 快速下跌阈值

    // 突破确认参数
    use_breakthrough_confirmation: true, // 是否启用突破确认
    breakthrough_confirmation_days: 1, // 确认天数，默认为1天，这样启用时不需要手动修改

    // 箱体检测参数
    use_box_detection: true, // 是否启用箱体检测
    box_quality_threshold: 0.94, // 箱体质量阈值

    // todo: 新增的因子
    // 进入平台期后的筹码与分布参数 (新增)
    // use_chip_distribution: true,
    // cost_concentration_threshold: 0.15, // 90%筹码集中度小于15%
    // avg_cost_divergence: 0.05, // 当前价格偏离平均成本不超过5%

    // // 进入平台期后的布林带特征参数 (新增)
    // use_boll_analysis: true,
    // boll_bandwidth_threshold: 0.10, // 布林带开口收窄至10%以内

    // 进入平台期后的换手率参数 (新增)
    max_turnover_rate: 5.0, // 平台期平均换手率不超过
    allow_turnover_spikes: true, // 是否允许偶尔的异常放量

    // 进入平台期后的相对强度参数 (新增)
    check_relative_strength: true, // 启用相对大盘强度检查（计算并保存相对强度值）
    outperform_index_threshold: null, // 相对强度阈值，null表示不过滤（计算并保存但不作为筛选条件）
    // todo end

    // 基本面筛选参数
    use_fundamental_filter: false, // 是否启用基本面筛选
    revenue_growth_percentile: 0.3, // 营收增长率行业百分位
    profit_growth_percentile: 0.3, // 净利润增长率行业百分位
    roe_percentile: 0.3, // ROE行业百分位
    liability_percentile: 0.3, // 资产负债率行业百分位
    pe_percentile: 0.7, // PE行业百分位
    pb_percentile: 0.7, // PB行业百分位
    fundamental_years_to_check: 3, // 检查连续增长的年数

    // 窗口权重参数
    use_window_weights: true, // 是否使用窗口权重
    window_weights: {}, // 窗口权重
    
    // 系统设置
    use_scan_cache: false, // 是否使用扫描结果缓存，默认为关闭
    max_stock_count: null, // 扫描股票数量限制，null或0表示全量扫描
    use_local_database_first: true // 优先使用本地数据库数据，默认为开启
  }
}
</script>

<script setup>
import { ref, watch, computed, nextTick, onMounted } from 'vue'
import ParameterLabel from './parameter-help/ParameterLabel.vue'

// 默认配置对象（内部使用）
const defaultScanConfig = getDefaultScanConfig()

const props = defineProps({
  config: {
    type: Object,
    required: false,
    default: () => getDefaultScanConfig()
  },
  showScanDate: {
    type: Boolean,
    default: true
  },
  windowWeights: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['update:config', 'show-tutorial', 'update-window-weights'])

// 窗口期预设
const windowPresets = [
  { name: '标准', value: '80,100,120' },
  { name: '短期', value: '10,20,30' },
  { name: '中期', value: '30,60,90' },
  { name: '长期', value: '60,120,180' },
  { name: '混合', value: '30,60,120' }
]

// 自定义窗口期相关
const showCustomWindowInput = ref(false)
const isUsingPreset = computed(() => {
  return windowPresets.some(preset => preset.value === localConfig.value.windowsInput)
})

// Computed property to parse windows input string into an array of numbers
const parsedWindows = computed(() => {
  // 添加安全检查，确保 windowsInput 存在且有效
  const windowsInput = localConfig.value?.windowsInput || defaultScanConfig.windowsInput || '30,60,90'
  const windows = windowsInput
    .split(',')
    .map(w => parseInt(w.trim(), 10))
    .filter(w => !isNaN(w) && w > 0)

  // 如果解析结果为空，返回默认值
  if (windows.length === 0) {
    return [30, 60, 90]
  }

  // Initialize window weights if needed
  windows.forEach(window => {
    if (localWindowWeights.value[window] === undefined) {
      localWindowWeights.value[window] = 5 // Default weight
    }
  })

  return windows
})

const localWindowWeights = ref({ ...props.windowWeights })

watch(() => props.windowWeights, (newWeights) => {
  // 同步父组件的 windowWeights 到本地
  localWindowWeights.value = { ...newWeights }
  // 确保所有窗口期都有权重
  parsedWindows.value.forEach(window => {
    if (localWindowWeights.value[window] === undefined) {
      localWindowWeights.value[window] = 5 // Default weight
    }
  })
}, { deep: true })

// 选择窗口期预设
function selectWindowPreset(presetValue) {
  localConfig.value.windowsInput = presetValue
  showCustomWindowInput.value = false

  // 重新初始化窗口权重
  parsedWindows.value.forEach(window => {
    if (localWindowWeights.value[window] === undefined) {
      localWindowWeights.value[window] = 5 // Default weight
    }
  })

  // 更新窗口权重
  updateWindowWeights()
}

// 验证自定义窗口期
function validateCustomWindows() {
  const windows = localConfig.value.windowsInput
    .split(',')
    .map(w => parseInt(w.trim(), 10))
    .filter(w => !isNaN(w) && w > 0)

  if (windows.length === 0) {
    // 如果没有有效的窗口期，恢复为默认值
    localConfig.value.windowsInput = '30,60,90'
    alert('请输入有效的窗口期，例如: 30,60,90')
  } else {
    // 格式化输入
    localConfig.value.windowsInput = windows.join(',')
    showCustomWindowInput.value = false

    // 重新初始化窗口权重
    windows.forEach(window => {
      if (localWindowWeights.value[window] === undefined) {
        localWindowWeights.value[window] = 5 // Default weight
      }
    })

    // 更新窗口权重
    updateWindowWeights()
  }
}

// Update window weights and config
function updateWindowWeights(window, value) {
  // 如果提供了特定窗口的值，更新它
  if (window !== undefined && value !== undefined) {
    localWindowWeights.value[window] = parseInt(value, 10)
  }

  // Update config.window_weights with normalized values
  const weights = {}
  let total = 0

  // Calculate total
  for (const [key, val] of Object.entries(localWindowWeights.value)) {
    if (parsedWindows.value.includes(parseInt(key, 10))) {
      total += val
    }
  }

  // Normalize weights
  if (total > 0) {
    for (const [key, val] of Object.entries(localWindowWeights.value)) {
      if (parsedWindows.value.includes(parseInt(key, 10))) {
        weights[key] = val / total
      }
    }
  }

  // Update config
  localConfig.value.window_weights = weights
  
  // Emit update event
  emit('update-window-weights', window, value)
}

const handleWindowWeightChange = (window, value) => {
  updateWindowWeights(window, value)
}

// 处理相对强度阈值输入，支持设置为 null（不过滤）
const handleOutperformIndexThresholdInput = (event) => {
  const value = event.target.value
  if (value === '' || value === null || value === undefined) {
    localConfig.value.outperform_index_threshold = null
  } else {
    const numValue = parseFloat(value)
    if (!isNaN(numValue)) {
      localConfig.value.outperform_index_threshold = numValue
    }
  }
}

const maxDate = computed(() => {
  const today = new Date()
  return today.toISOString().split('T')[0]
})

// 合并默认配置和传入的配置
const localConfig = ref({ ...defaultScanConfig, ...props.config })
const isUpdatingFromProps = ref(false)
const isInitialized = ref(false)
const isEmittingInitialConfig = ref(false)

watch(() => props.config, (newConfig) => {
  // 如果正在 emit 初始配置，忽略这次更新（避免循环）
  if (isEmittingInitialConfig.value) {
    return
  }
  
  isUpdatingFromProps.value = true
  // 合并默认配置和新的配置，确保所有字段都有值
  localConfig.value = { ...defaultScanConfig, ...newConfig }
  // Use nextTick to ensure the flag is reset after all watchers have run
  nextTick(() => {
    isUpdatingFromProps.value = false
  })
}, { deep: true })

watch(localConfig, (newConfig) => {
  // Only emit if the change didn't come from props and component is initialized
  // This prevents recursive updates during initialization
  if (!isUpdatingFromProps.value && isInitialized.value && !isEmittingInitialConfig.value) {
    emit('update:config', newConfig)
  }
}, { deep: true })

// 组件挂载后，如果父组件没有传入配置，emit 默认配置（仅一次）
onMounted(() => {
  isInitialized.value = true
  // 检查父组件是否传入了有效的配置
  const hasValidConfig = props.config && Object.keys(props.config).length > 0
  // 如果父组件没有传入配置，emit 默认配置
  if (!hasValidConfig) {
    // 使用 nextTick 确保在下一个 tick 中执行，避免与 watch 冲突
    nextTick(() => {
      if (!isUpdatingFromProps.value) {
        isEmittingInitialConfig.value = true
        emit('update:config', { ...localConfig.value })
        // 在下一个 tick 重置标志
        nextTick(() => {
          isEmittingInitialConfig.value = false
        })
      }
    })
  }
})

watch(() => parsedWindows.value, (newWindows) => {
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
  // 更新窗口权重
  updateWindowWeights()
}, { immediate: true })

// 暴露 parsedWindows 给父组件
defineExpose({
  parsedWindows
})
</script>

