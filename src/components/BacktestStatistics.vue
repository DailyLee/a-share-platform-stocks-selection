<template>
    <div class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-2 sm:p-4">
      <div class="bg-card border border-border rounded-lg shadow-lg max-w-5xl w-full max-h-[95vh] sm:max-h-[90vh] flex flex-col overflow-hidden" @click.stop>
        <!-- 对话框头部 -->
        <div class="p-3 sm:p-6 border-b border-border flex justify-between items-center flex-shrink-0">
          <h2 class="text-base sm:text-lg font-semibold flex items-center">
            <i class="fas fa-chart-bar mr-2 text-primary"></i>
            数据统计
          </h2>
          <button
            @click="$emit('close')"
            class="text-muted-foreground hover:text-foreground transition-colors"
          >
            <i class="fas fa-times text-xl"></i>
          </button>
        </div>
  
        <!-- 筛选条件 -->
        <div class="p-2 sm:p-3 border-b border-border flex-shrink-0 overflow-y-auto max-h-[35vh] sm:max-h-[40vh]">
          <div class="flex justify-between items-center mb-2">
            <div class="flex items-center space-x-2">
              <button
                @click="statisticsFiltersExpanded = !statisticsFiltersExpanded"
                class="text-muted-foreground hover:text-foreground transition-colors"
                title="收起/展开筛选条件"
              >
                <i :class="statisticsFiltersExpanded ? 'fas fa-chevron-down' : 'fas fa-chevron-right'"></i>
              </button>
              <h3 class="text-sm font-semibold flex items-center">
                <i class="fas fa-filter mr-1 text-primary"></i>
                筛选条件
              </h3>
            </div>
            <div class="flex items-center gap-2">
              <button
                v-if="allStocksDataLoaded"
                @click="calculateStatistics"
                class="px-3 py-1 rounded-md bg-primary text-primary-foreground hover:bg-primary/80 transition-colors text-xs"
                :disabled="statisticsLoading"
              >
                <i v-if="statisticsLoading" class="fas fa-spinner fa-spin mr-1"></i>
                <i v-else class="fas fa-filter mr-1"></i>
                {{ statisticsLoading ? '筛选中...' : '筛选' }}
              </button>
              <button
                @click="loadAllData(true)"
                class="px-3 py-1 rounded-md bg-primary text-primary-foreground hover:bg-primary/80 transition-colors text-xs"
                :disabled="dataLoading"
              >
                <i v-if="dataLoading" class="fas fa-spinner fa-spin mr-1"></i>
                <i v-else-if="allStocksDataLoaded" class="fas fa-sync-alt mr-1"></i>
                <i v-else class="fas fa-download mr-1"></i>
                {{ dataLoading ? '加载中...' : (allStocksDataLoaded ? '重新加载' : '加载数据') }}
              </button>
            </div>
          </div>
          <div v-show="statisticsFiltersExpanded" class="grid grid-cols-1 sm:grid-cols-2 gap-2">
            <!-- 平台期 -->
            <div>
              <label class="block text-xs font-medium mb-1">平台期</label>
              <div class="flex flex-wrap gap-1.5">
                <label 
                  v-for="period in Array.from(allStockAttributes.platformPeriods).sort((a, b) => a - b)" 
                  :key="period"
                  class="flex items-center cursor-pointer px-1.5 py-0.5 rounded border border-border hover:bg-muted/30 transition-colors"
                >
                  <input
                    type="checkbox"
                    :value="period"
                    v-model="statisticsFilters.platformPeriods"
                    class="checkbox mr-1"
                  />
                  <span class="text-xs">{{ period }}天</span>
                </label>
                <p v-if="allStockAttributes.platformPeriods.size === 0" class="text-xs text-muted-foreground">暂无数据</p>
              </div>
            </div>
  
            <!-- 突破前兆 -->
            <div>
              <label class="block text-xs font-medium mb-1">突破前兆</label>
              <div class="space-y-2">
                <!-- MACD -->
                <div class="flex items-center gap-2">
                  <span class="text-xs w-12">MACD:</span>
                  <label class="flex items-center cursor-pointer px-1.5 py-0.5 rounded border border-border hover:bg-muted/30 transition-colors">
                    <input
                      type="checkbox"
                      v-model="statisticsFilters.breakthroughMACD.include"
                      @change="handleBreakthroughSignalChange"
                      class="checkbox mr-1"
                    />
                    <span class="text-xs whitespace-nowrap">包含</span>
                  </label>
                  <label class="flex items-center cursor-pointer px-1.5 py-0.5 rounded border border-border hover:bg-muted/30 transition-colors">
                    <input
                      type="checkbox"
                      v-model="statisticsFilters.breakthroughMACD.exclude"
                      @change="handleBreakthroughExcludeChange('MACD')"
                      class="checkbox mr-1"
                    />
                    <span class="text-xs whitespace-nowrap">不包含</span>
                  </label>
                </div>
                <!-- RSI -->
                <div class="flex items-center gap-2">
                  <span class="text-xs w-12">RSI:</span>
                  <label class="flex items-center cursor-pointer px-1.5 py-0.5 rounded border border-border hover:bg-muted/30 transition-colors">
                    <input
                      type="checkbox"
                      v-model="statisticsFilters.breakthroughRSI.include"
                      @change="handleBreakthroughSignalChange"
                      class="checkbox mr-1"
                    />
                    <span class="text-xs whitespace-nowrap">包含</span>
                  </label>
                  <label class="flex items-center cursor-pointer px-1.5 py-0.5 rounded border border-border hover:bg-muted/30 transition-colors">
                    <input
                      type="checkbox"
                      v-model="statisticsFilters.breakthroughRSI.exclude"
                      @change="handleBreakthroughExcludeChange('RSI')"
                      class="checkbox mr-1"
                    />
                    <span class="text-xs whitespace-nowrap">不包含</span>
                  </label>
                </div>
                <!-- KDJ -->
                <div class="flex items-center gap-2">
                  <span class="text-xs w-12">KDJ:</span>
                  <label class="flex items-center cursor-pointer px-1.5 py-0.5 rounded border border-border hover:bg-muted/30 transition-colors">
                    <input
                      type="checkbox"
                      v-model="statisticsFilters.breakthroughKDJ.include"
                      @change="handleBreakthroughSignalChange"
                      class="checkbox mr-1"
                    />
                    <span class="text-xs whitespace-nowrap">包含</span>
                  </label>
                  <label class="flex items-center cursor-pointer px-1.5 py-0.5 rounded border border-border hover:bg-muted/30 transition-colors">
                    <input
                      type="checkbox"
                      v-model="statisticsFilters.breakthroughKDJ.exclude"
                      @change="handleBreakthroughExcludeChange('KDJ')"
                      class="checkbox mr-1"
                    />
                    <span class="text-xs whitespace-nowrap">不包含</span>
                  </label>
                </div>
                <!-- 布林带 -->
                <div class="flex items-center gap-2">
                  <span class="text-xs w-12">布林带:</span>
                  <label class="flex items-center cursor-pointer px-1.5 py-0.5 rounded border border-border hover:bg-muted/30 transition-colors">
                    <input
                      type="checkbox"
                      v-model="statisticsFilters.breakthroughBollinger.include"
                      @change="handleBreakthroughSignalChange"
                      class="checkbox mr-1"
                    />
                    <span class="text-xs whitespace-nowrap">包含</span>
                  </label>
                  <label class="flex items-center cursor-pointer px-1.5 py-0.5 rounded border border-border hover:bg-muted/30 transition-colors">
                    <input
                      type="checkbox"
                      v-model="statisticsFilters.breakthroughBollinger.exclude"
                      @change="handleBreakthroughExcludeChange('Bollinger')"
                      class="checkbox mr-1"
                    />
                    <span class="text-xs whitespace-nowrap">不包含</span>
                  </label>
                </div>
                <!-- 无突破前兆 -->
                <div class="flex items-center gap-2">
                  <label class="flex items-center cursor-pointer px-1.5 py-0.5 rounded border border-border hover:bg-muted/30 transition-colors">
                    <input
                      type="checkbox"
                      v-model="statisticsFilters.breakthroughNone"
                      @change="handleBreakthroughNoneChange"
                      class="checkbox mr-1"
                    />
                    <span class="text-xs whitespace-nowrap">无突破前兆</span>
                  </label>
                </div>
              </div>
            </div>
  
            <!-- 确认突破 -->
            <div>
              <label class="block text-xs font-medium mb-1">确认突破</label>
              <select
                v-model="statisticsFilters.breakthroughConfirmation"
                class="input w-full text-xs py-1"
              >
                <option :value="null">不筛选</option>
                <option :value="true">是（已确认突破）</option>
                <option :value="false">否（未确认突破）</option>
              </select>
            </div>
  
            <!-- 最小箱体质量 -->
            <div>
              <label class="block text-xs font-medium mb-1">最小箱体质量</label>
              <input
                type="number"
                v-model.number="statisticsFilters.boxQualityThreshold"
                step="0.01"
                :min="allStockAttributes.minBoxQuality"
                :max="allStockAttributes.maxBoxQuality"
                class="input w-full text-xs py-1"
              />
              <p class="text-xs text-muted-foreground mt-0.5">
                范围: {{ allStockAttributes.minBoxQuality.toFixed(2) }} - {{ allStockAttributes.maxBoxQuality.toFixed(2) }}
              </p>
            </div>
  
            <!-- 行业信息 -->
            <div>
              <label class="block text-xs font-medium mb-1">行业信息</label>
              <div class="max-h-24 overflow-y-auto border border-border rounded p-1.5">
                <label 
                  v-for="industry in Array.from(allStockAttributes.industries).sort()" 
                  :key="industry"
                  class="flex items-center cursor-pointer mb-0.5 px-1.5 py-0.5 rounded hover:bg-muted/30 transition-colors"
                >
                  <input
                    type="checkbox"
                    :value="industry"
                    v-model="statisticsFilters.industries"
                    class="checkbox mr-1.5"
                  />
                  <span class="text-xs">{{ industry || '未知行业' }}</span>
                </label>
                <p v-if="allStockAttributes.industries.size === 0" class="text-xs text-muted-foreground text-center py-1">暂无数据</p>
              </div>
            </div>
          </div>
        </div>
  
        <!-- 统计结果 -->
        <div class="flex-1 flex flex-col overflow-hidden p-2 sm:p-3 min-h-0">
          <h3 class="text-sm font-semibold mb-2 flex items-center flex-shrink-0">
            <i class="fas fa-calculator mr-1 text-primary"></i>
            统计结果
          </h3>
          <div v-if="statisticsLoading" class="text-center py-4 flex-shrink-0">
            <i class="fas fa-spinner fa-spin text-xl mb-2 text-primary"></i>
            <p class="text-muted-foreground text-sm">计算中...</p>
          </div>
          <div v-else-if="statisticsError" class="text-center py-4 flex-shrink-0">
            <i class="fas fa-exclamation-triangle text-xl mb-2 text-destructive"></i>
            <p class="text-destructive text-sm">{{ statisticsError }}</p>
          </div>
          <div v-else-if="statisticsResult" class="flex flex-col flex-1 min-h-0 overflow-y-auto">
            <div class="space-y-1.5 flex-shrink-0">
              <div class="grid grid-cols-3 gap-1.5">
                <div class="p-1.5 sm:p-2 bg-muted/30 rounded-md">
                  <div class="text-xs text-muted-foreground mb-0.5 whitespace-nowrap">总记录数</div>
                  <div class="text-base sm:text-lg font-bold">{{ statisticsResult.totalRecords }}</div>
                </div>
                <div class="p-1.5 sm:p-2 bg-muted/30 rounded-md">
                  <div class="text-xs text-muted-foreground mb-0.5 whitespace-nowrap">盈利股票数</div>
                  <div class="text-base sm:text-lg font-bold text-red-600 dark:text-red-400">{{ statisticsResult.profitableRecords }}</div>
                </div>
                <div class="p-1.5 sm:p-2 bg-muted/30 rounded-md">
                  <div class="text-xs text-muted-foreground mb-0.5 whitespace-nowrap">亏损股票数</div>
                  <div class="text-base sm:text-lg font-bold text-blue-600 dark:text-blue-400">{{ statisticsResult.lossRecords }}</div>
                </div>
              </div>
              <div class="grid grid-cols-3 gap-1.5">
                <div class="p-1.5 sm:p-2 bg-muted/30 rounded-md">
                  <div class="text-xs text-muted-foreground mb-0.5 whitespace-nowrap">整体胜率</div>
                  <div class="text-base sm:text-lg font-bold" :class="statisticsResult.winRate >= 50 ? 'text-red-600 dark:text-red-400' : 'text-blue-600 dark:text-blue-400'">
                    {{ formatPercent(statisticsResult.winRate) }}%
                  </div>
                </div>
                <div class="p-1.5 sm:p-2 bg-muted/30 rounded-md">
                  <div class="text-xs text-muted-foreground mb-0.5 whitespace-nowrap">整体收益率</div>
                  <div class="text-base sm:text-lg font-bold" :class="statisticsResult.totalReturnRate >= 0 ? 'text-red-600 dark:text-red-400' : 'text-blue-600 dark:text-blue-400'">
                    {{ statisticsResult.totalReturnRate >= 0 ? '+' : '' }}{{ formatPercent(statisticsResult.totalReturnRate) }}%
                  </div>
                </div>
                <div class="p-1.5 sm:p-2 bg-muted/30 rounded-md">
                  <div class="text-xs text-muted-foreground mb-0.5 whitespace-nowrap">整体收益额</div>
                  <div class="text-base sm:text-lg font-bold truncate" :class="statisticsResult.totalProfit >= 0 ? 'text-red-600 dark:text-red-400' : 'text-blue-600 dark:text-blue-400'">
                    {{ statisticsResult.totalProfit >= 0 ? '+' : '' }}¥{{ formatNumber(statisticsResult.totalProfit) }}
                  </div>
                </div>
              </div>
              <div class="p-1.5 sm:p-2 bg-muted/30 rounded-md">
                <div class="text-xs text-muted-foreground mb-0.5 whitespace-nowrap">总投入资金</div>
                <div class="text-sm sm:text-base font-bold truncate">¥{{ formatNumber(statisticsResult.totalInvestment) }}</div>
              </div>
            </div>
  
            <!-- 筛选出的股票详情 -->
            <div v-if="statisticsResult.filteredRecords && statisticsResult.filteredRecords.length > 0" class="mt-2 flex-shrink-0">
              <div class="flex items-center justify-between mb-2">
                <h4 class="text-xs sm:text-sm font-semibold flex items-center">
                  <i class="fas fa-list mr-1 text-primary"></i>
                  股票详情
                </h4>
                <button
                  @click="showStockDetails = !showStockDetails"
                  class="px-3 py-1 rounded-md bg-secondary text-secondary-foreground hover:bg-secondary/80 transition-colors text-xs"
                >
                  <i :class="[showStockDetails ? 'fas fa-chevron-up' : 'fas fa-chevron-down', 'mr-1']"></i>
                  {{ showStockDetails ? '收起' : '展开' }}
                </button>
              </div>
              <div v-show="showStockDetails" class="space-y-2 sm:space-y-4 -mx-2 sm:mx-0 px-2 sm:px-0">
                <div 
                  v-for="(record, index) in statisticsResult.filteredRecords" 
                  :key="index"
                  class="border border-border rounded-md overflow-hidden"
                >
                  <div class="bg-muted/50 p-2 sm:p-3 border-b border-border">
                    <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-1 sm:gap-0">
                      <span class="text-xs sm:text-sm font-medium">扫描日期: {{ record.scanDate }}</span>
                      <span class="text-xs text-muted-foreground">共 {{ record.stocks ? record.stocks.length : 0 }} 只股票</span>
                    </div>
                  </div>
                  <div v-if="record.stocks && record.stocks.length > 0" class="overflow-x-auto -mx-2 sm:mx-0">
                    <table class="w-full text-xs sm:text-sm">
                      <thead>
                        <tr class="border-b border-border bg-muted/30">
                          <th class="text-left p-2 sm:p-3 font-medium sticky left-0 bg-muted/30 z-10">股票代码</th>
                          <th class="text-left p-2 sm:p-3 font-medium sticky left-[100px] sm:left-[120px] bg-muted/30 z-10">股票名称</th>
                          <th class="text-left p-2 sm:p-3 font-medium">行业</th>
                          <th class="text-left p-2 sm:p-3 font-medium">平台期(天)</th>
                          <th class="text-left p-2 sm:p-3 font-medium">突破前兆</th>
                          <th class="text-left p-2 sm:p-3 font-medium">确认突破</th>
                          <th class="text-left p-2 sm:p-3 font-medium">箱体质量</th>
                          <th class="text-left p-2 sm:p-3 font-medium">收益率</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr 
                          v-for="(stock, stockIndex) in record.stocks" 
                          :key="stockIndex"
                          class="border-b border-border/50 hover:bg-muted/30 transition-colors"
                        >
                          <td class="p-2 sm:p-3 font-mono sticky left-0 bg-background z-10 text-xs sm:text-sm">{{ stock.code }}</td>
                          <td class="p-2 sm:p-3 sticky left-[100px] sm:left-[120px] bg-background z-10 text-xs sm:text-sm">{{ stock.name }}</td>
                          <td class="p-2 sm:p-3 text-muted-foreground text-xs sm:text-sm">{{ stock.industry || '-' }}</td>
                          <td class="p-2 sm:p-3">
                            <span v-if="stock.platformPeriods && stock.platformPeriods.length > 0" class="inline-flex items-center gap-1">
                              <span v-for="(period, idx) in stock.platformPeriods" :key="idx" class="px-2 py-1 rounded bg-blue-100 text-blue-800 text-xs">
                                {{ period }}天
                              </span>
                            </span>
                            <span v-else class="text-muted-foreground">-</span>
                          </td>
                          <td class="p-2 sm:p-3">
                            <span v-if="stock.breakthroughSignals && stock.breakthroughSignals.length > 0" class="inline-flex items-center gap-1 flex-wrap">
                              <span v-for="(signal, idx) in stock.breakthroughSignals" :key="idx" class="px-1.5 sm:px-2 py-0.5 sm:py-1 rounded bg-green-100 text-green-800 text-xs">
                                {{ signal }}
                              </span>
                            </span>
                            <span v-else class="text-muted-foreground text-xs sm:text-sm">-</span>
                          </td>
                          <td class="p-2 sm:p-3">
                            <span v-if="stock.hasBreakthroughConfirmation !== undefined && stock.hasBreakthroughConfirmation !== null">
                              <span v-if="stock.hasBreakthroughConfirmation" class="px-1.5 sm:px-2 py-0.5 sm:py-1 rounded bg-purple-100 text-purple-800 text-xs">是</span>
                              <span v-else class="px-1.5 sm:px-2 py-0.5 sm:py-1 rounded bg-gray-100 text-gray-800 text-xs">否</span>
                            </span>
                            <span v-else class="text-muted-foreground text-xs sm:text-sm">-</span>
                          </td>
                          <td class="p-2 sm:p-3">
                            <span v-if="stock.boxQuality !== null && stock.boxQuality !== undefined" class="px-1.5 sm:px-2 py-0.5 sm:py-1 rounded bg-orange-100 text-orange-800 text-xs">
                              {{ stock.boxQuality.toFixed(3) }}
                            </span>
                            <span v-else class="text-muted-foreground text-xs" title="该股票在扫描时未启用箱体检测或不是基本平台期，因此没有箱体质量数据">-</span>
                          </td>
                          <td class="p-2 sm:p-3 text-xs sm:text-sm">
                            <span v-if="stock.returnRate !== null && stock.returnRate !== undefined" 
                                  :class="[
                                    'px-1.5 sm:px-2 py-0.5 sm:py-1 rounded text-xs font-medium',
                                    stock.returnRate >= 0 
                                      ? 'bg-green-100 text-green-800' 
                                      : 'bg-red-100 text-red-800'
                                  ]">
                              {{ stock.returnRate >= 0 ? '+' : '' }}{{ stock.returnRate.toFixed(2) }}%
                            </span>
                            <span v-else class="text-muted-foreground text-xs sm:text-sm">-</span>
                          </td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                  <div v-else class="p-4 text-center text-muted-foreground">
                    该记录中没有股票信息
                  </div>
                </div>
              </div>
            </div>
            
            <!-- 加载全量数据按钮 -->
            <div v-if="statisticsResult && hasFiltersApplied()" class="mt-4 flex justify-center flex-shrink-0">
              <button
                @click="loadAllDataWithoutFilters"
                class="px-4 py-2 rounded-md bg-secondary text-secondary-foreground hover:bg-secondary/80 transition-colors text-sm"
                :disabled="statisticsLoading"
              >
                <i class="fas fa-list-ul mr-2"></i>
                加载全量数据（不筛选）
              </button>
            </div>
          </div>
          <div v-else-if="!allStocksDataLoaded" class="text-center py-8 flex-shrink-0">
            <i class="fas fa-info-circle text-2xl mb-2 text-muted-foreground"></i>
            <p class="text-muted-foreground text-sm">请先加载数据</p>
          </div>
        </div>
  
        <!-- 对话框底部 -->
        <div class="p-4 sm:p-6 border-t border-border flex justify-end">
          <button
            @click="$emit('close')"
            class="px-4 py-2 rounded-md bg-primary text-primary-foreground hover:bg-primary/80 transition-colors text-sm"
          >
            关闭
          </button>
        </div>
      </div>
    </div>
  </template>
  
  <script setup>
  import { ref, watch } from 'vue'
  import axios from 'axios'
  
  const props = defineProps({
    // 回测历史记录列表（简化版，只包含id、backtestDate、statDate等基本信息）
    historyRecords: {
      type: Array,
      required: true,
      default: () => []
    }
  })
  
  const emit = defineEmits(['close'])
  
  // 数据统计相关
  const statisticsLoading = ref(false)
  const statisticsError = ref(null)
  const statisticsResult = ref(null)
  const statisticsFiltersExpanded = ref(true) // 筛选条件区域是否展开
  const statisticsFilters = ref({
    platformPeriods: [], // 选中的平台期，如[30, 60, 90]
    breakthroughMACD: { include: false, exclude: false }, // 包含/不包含MACD
    breakthroughRSI: { include: false, exclude: false }, // 包含/不包含RSI
    breakthroughKDJ: { include: false, exclude: false }, // 包含/不包含KDJ
    breakthroughBollinger: { include: false, exclude: false }, // 包含/不包含布林带
    breakthroughNone: false, // 是否筛选完全没有突破前兆的股票
    breakthroughConfirmation: null, // true/false/null (null表示不筛选)
    boxQualityThreshold: 0,
    industries: [] // 选中的行业列表
  })
  
  // 所有股票的属性集合（用于筛选条件选项）
  const allStockAttributes = ref({
    platformPeriods: new Set(), // 所有出现的平台期
    industries: new Set(), // 所有行业
    minBoxQuality: 1, // 最小箱体质量
    maxBoxQuality: 0 // 最大箱体质量
  })
  
  // 完整数据缓存（不筛选的完整数据）
  const allStocksData = ref(null) // 存储所有股票的完整数据
  const allStocksDataLoaded = ref(false) // 是否已加载完整数据
  const dataLoading = ref(false) // 数据加载状态
  const showStockDetails = ref(false) // 是否显示股票详情
  
  // 缓存相关
  let scanHistoryCache = null
  let scanHistoryDetailsCache = new Map() // key: record.id, value: record data with scannedStocks
  let backtestRecordsCache = new Map() // key: record.id, value: record data
  let cachedBacktestHistoryIds = null // 缓存的回测历史记录ID列表
  
  // 检查回测历史记录是否发生变化
  function hasBacktestHistoryChanged() {
    const currentIds = props.historyRecords.map(r => r.id).sort().join(',')
    if (cachedBacktestHistoryIds !== currentIds) {
      cachedBacktestHistoryIds = currentIds
      return true
    }
    return false
  }
  
  // 获取扫描历史记录（用于查找扫描配置）
  async function loadScanHistoryForStatistics() {
    if (scanHistoryCache) {
      return scanHistoryCache
    }
    try {
      const response = await axios.get('/platform/api/scan/history')
      if (response.data.success) {
        scanHistoryCache = response.data.data || []
        return scanHistoryCache
      }
    } catch (e) {
      console.warn('加载扫描历史记录失败:', e)
    }
    return []
  }
  
  // 获取扫描历史记录详情（带缓存）
  async function getScanHistoryDetail(recordId) {
    // 如果缓存中有，直接返回
    if (scanHistoryDetailsCache.has(recordId)) {
      return scanHistoryDetailsCache.get(recordId)
    }
    
    // 否则从API获取
    try {
      const response = await axios.get(`/platform/api/scan/history/${recordId}`)
      if (response.data.success && response.data.data) {
        const detail = response.data.data
        // 存入缓存
        scanHistoryDetailsCache.set(recordId, detail)
        return detail
      }
    } catch (e) {
      console.warn(`获取扫描历史记录 ${recordId} 详情失败:`, e)
    }
    return null
  }
  
  // 处理突破前兆信号变化（当选择"包含"时，取消对应的"不包含"选项和"无突破前兆"选项）
  function handleBreakthroughSignalChange() {
    // 检查每个指标，如果选择了"包含"，则取消对应的"不包含"
    if (statisticsFilters.value.breakthroughMACD.include) {
      statisticsFilters.value.breakthroughMACD.exclude = false
    }
    if (statisticsFilters.value.breakthroughRSI.include) {
      statisticsFilters.value.breakthroughRSI.exclude = false
    }
    if (statisticsFilters.value.breakthroughKDJ.include) {
      statisticsFilters.value.breakthroughKDJ.exclude = false
    }
    if (statisticsFilters.value.breakthroughBollinger.include) {
      statisticsFilters.value.breakthroughBollinger.exclude = false
    }
    
    // 如果选择了任何"包含"选项，取消"无突破前兆"
    if (statisticsFilters.value.breakthroughMACD.include || 
        statisticsFilters.value.breakthroughRSI.include || 
        statisticsFilters.value.breakthroughKDJ.include || 
        statisticsFilters.value.breakthroughBollinger.include) {
      statisticsFilters.value.breakthroughNone = false
    }
  }
  
  // 处理"不包含"选项变化（当选择"不包含"时，取消对应的"包含"选项和"无突破前兆"选项）
  function handleBreakthroughExcludeChange(signalType) {
    const signalMap = {
      'MACD': 'breakthroughMACD',
      'RSI': 'breakthroughRSI',
      'KDJ': 'breakthroughKDJ',
      'Bollinger': 'breakthroughBollinger'
    }
    const filterKey = signalMap[signalType]
    if (filterKey && statisticsFilters.value[filterKey].exclude) {
      // 如果选择了"不包含"，则取消"包含"选项
      statisticsFilters.value[filterKey].include = false
    }
    
    // 如果选择了任何"不包含"选项，取消"无突破前兆"
    if (statisticsFilters.value.breakthroughMACD.exclude || 
        statisticsFilters.value.breakthroughRSI.exclude || 
        statisticsFilters.value.breakthroughKDJ.exclude || 
        statisticsFilters.value.breakthroughBollinger.exclude) {
      statisticsFilters.value.breakthroughNone = false
    }
  }
  
  // 处理"无突破前兆"选项变化（当选择"无突破前兆"时，取消所有具体信号选项）
  function handleBreakthroughNoneChange() {
    if (statisticsFilters.value.breakthroughNone) {
      statisticsFilters.value.breakthroughMACD = { include: false, exclude: false }
      statisticsFilters.value.breakthroughRSI = { include: false, exclude: false }
      statisticsFilters.value.breakthroughKDJ = { include: false, exclude: false }
      statisticsFilters.value.breakthroughBollinger = { include: false, exclude: false }
    }
  }
  
  // 格式化数字
  function formatNumber(num, decimals = 0) {
    if (num === null || num === undefined) return '0'
    return Number(num).toFixed(decimals).replace(/\B(?=(\d{3})+(?!\d))/g, ',')
  }
  
  // 格式化百分比
  function formatPercent(num) {
    if (num === null || num === undefined) return '0.00'
    return Number(num).toFixed(2)
  }
  
  // 加载完整数据（只在进入时或历史记录变化时调用）
  async function loadAllData(forceReload = false) {
    dataLoading.value = true
    statisticsError.value = null

    try {
      // 使用传入的历史记录
      const historyToUse = props.historyRecords
      
      if (historyToUse.length === 0) {
        statisticsError.value = '没有回测历史记录'
        dataLoading.value = false
        return
      }

      // 如果强制重新加载，清除相关缓存
      if (forceReload) {
        scanHistoryCache = null
        scanHistoryDetailsCache.clear()
        backtestRecordsCache.clear()
        cachedBacktestHistoryIds = null
      }

      // 加载扫描历史记录（用于查找扫描配置和股票详细信息）
      const scanHistory = await loadScanHistoryForStatistics()
      
      // 对于没有完整股票数据的扫描历史记录，尝试获取详情（使用缓存）
      for (let i = 0; i < scanHistory.length; i++) {
        const record = scanHistory[i]
        if (!record.scannedStocks || record.scannedStocks.length === 0) {
          // 使用缓存函数获取详情
          const detail = await getScanHistoryDetail(record.id)
          if (detail) {
            scanHistory[i] = detail
          }
        }
      }

      // 检查回测历史记录是否发生变化
      const historyChanged = hasBacktestHistoryChanged()
      
      // 获取完整的回测历史记录详情（使用缓存）
      const fullRecords = []
      for (const record of historyToUse) {
        // 如果强制重新加载，或者缓存中没有，或者历史记录已变化，则从API获取
        if (forceReload || !historyChanged || !backtestRecordsCache.has(record.id)) {
          // 从API获取
          try {
            const response = await axios.get(`/platform/api/backtest/history/${record.id}`)
            if (response.data.success) {
              const recordData = response.data.data
              // 存入缓存
              backtestRecordsCache.set(record.id, recordData)
              fullRecords.push(recordData)
            }
          } catch (e) {
            console.warn(`获取回测记录 ${record.id} 详情失败:`, e)
          }
        } else {
          // 使用缓存
          fullRecords.push(backtestRecordsCache.get(record.id))
        }
      }

      if (fullRecords.length === 0) {
        statisticsError.value = '无法获取回测历史记录详情'
        dataLoading.value = false
        return
      }

      // 处理数据并存储到 allStocksData
      const processedData = processAllStocksData(fullRecords, scanHistory)
      allStocksData.value = processedData
      allStocksDataLoaded.value = true
      
      // 自动计算统计数据（不筛选，显示全量数据）
      calculateStatistics()
    } catch (e) {
      console.error('加载数据失败:', e)
      statisticsError.value = '加载数据失败: ' + (e.response?.data?.detail || e.message)
    } finally {
      dataLoading.value = false
    }
  }
  
  // 处理所有股票数据（提取并组织数据）
  function processAllStocksData(fullRecords, scanHistory) {
      // 按扫描日期分组，每个扫描日期选第一条记录
      const recordsByDate = {}
      fullRecords.forEach(record => {
        const scanDate = record.config.backtest_date
        if (!scanDate) return
        
        if (!recordsByDate[scanDate]) {
          recordsByDate[scanDate] = []
        }
        recordsByDate[scanDate].push(record)
      })

      // 每个扫描日期选第一条记录
      const selectedRecords = []
      Object.keys(recordsByDate).sort().forEach(date => {
        const records = recordsByDate[date]
        if (records.length > 0) {
          // 按创建时间排序，选第一条
          records.sort((a, b) => {
            const timeA = new Date(a.createdAt || 0).getTime()
            const timeB = new Date(b.createdAt || 0).getTime()
            return timeA - timeB
          })
          selectedRecords.push(records[0])
        }
      })

      // 收集所有股票的属性
      const allStocks = []
      selectedRecords.forEach(record => {
        const config = record.config || {}
        const scanDate = config.backtest_date
        
        // 尝试从扫描历史记录中获取股票的详细信息
        let scanHistoryRecord = null
        if (scanDate) {
          scanHistoryRecord = scanHistory.find(sh => sh.scanDate === scanDate)
          // 如果列表中没有完整数据，尝试获取详情
          if (scanHistoryRecord && (!scanHistoryRecord.scannedStocks || scanHistoryRecord.scannedStocks.length === 0)) {
            // 需要获取详情，但这里先跳过，因为需要异步调用
            scanHistoryRecord = null
          }
        }
        
        // 从config中获取股票列表
        if (config.selected_stocks && Array.isArray(config.selected_stocks)) {
          config.selected_stocks.forEach(stock => {
            // 尝试从扫描历史记录中获取该股票的详细信息
            let stockDetails = null
            if (scanHistoryRecord && scanHistoryRecord.scannedStocks) {
              stockDetails = scanHistoryRecord.scannedStocks.find(s => s.code === stock.code)
            }
            
            allStocks.push({
              ...stock,
              // 合并扫描历史记录中的详细信息
              platform_windows: stockDetails?.platform_windows || stock.platform_windows,
              selection_reasons: stockDetails?.selection_reasons || stock.selection_reasons,
              breakthrough_prediction: stockDetails?.breakthrough_prediction || stock.breakthrough_prediction,
              has_breakthrough_confirmation: stockDetails?.has_breakthrough_confirmation !== undefined 
                ? stockDetails.has_breakthrough_confirmation 
                : stock.has_breakthrough_confirmation,
              details: stockDetails?.details || stock.details,
              box_analysis: stockDetails?.box_analysis || stock.box_analysis,
              industry: stockDetails?.industry || stock.industry || '',
              scanDate: scanDate,
              record: record
            })
          })
        }
        // 如果没有selected_stocks，尝试从result中提取
        else if (record.result && record.result.buyRecords) {
          record.result.buyRecords.forEach(buyRecord => {
            // 尝试从扫描历史记录中获取该股票的详细信息
            let stockDetails = null
            if (scanHistoryRecord && scanHistoryRecord.scannedStocks) {
              stockDetails = scanHistoryRecord.scannedStocks.find(s => s.code === buyRecord.code)
            }
            
            allStocks.push({
              code: buyRecord.code || '',
              name: buyRecord.name || '',
              industry: stockDetails?.industry || '',
              platform_windows: stockDetails?.platform_windows,
              selection_reasons: stockDetails?.selection_reasons,
              breakthrough_prediction: stockDetails?.breakthrough_prediction,
              has_breakthrough_confirmation: stockDetails?.has_breakthrough_confirmation,
              details: stockDetails?.details,
              box_analysis: stockDetails?.box_analysis,
              scanDate: scanDate,
              record: record
            })
          })
        }
      })

      // 收集所有股票的属性值（用于筛选条件选项）
      const platformPeriodsSet = new Set()
      const industriesSet = new Set()
      const boxQualities = []

      allStocks.forEach(stock => {
        // 收集平台期
        if (stock.selection_reasons) {
          Object.keys(stock.selection_reasons).forEach(key => {
            const period = parseInt(key)
            if (!isNaN(period)) {
              platformPeriodsSet.add(period)
            }
          })
        }
        if (stock.platform_windows && Array.isArray(stock.platform_windows)) {
          stock.platform_windows.forEach(period => {
            platformPeriodsSet.add(period)
          })
        }

        // 收集行业
        if (stock.industry) {
          industriesSet.add(stock.industry)
        }

        // 收集箱体质量
        // 首先检查股票对象上的 box_analysis
        if (stock.box_analysis && typeof stock.box_analysis === 'object') {
          if (stock.box_analysis.box_quality !== undefined) {
            const quality = stock.box_analysis.box_quality
            if (typeof quality === 'number' && !isNaN(quality)) {
              boxQualities.push(quality)
            }
          }
        }
        // 然后检查 details 中每个窗口的 box_analysis
        if (stock.details && typeof stock.details === 'object') {
          Object.values(stock.details).forEach(windowDetail => {
            if (windowDetail && typeof windowDetail === 'object') {
              if (windowDetail.box_analysis && typeof windowDetail.box_analysis === 'object' && windowDetail.box_analysis.box_quality !== undefined) {
                const quality = windowDetail.box_analysis.box_quality
                if (typeof quality === 'number' && !isNaN(quality)) {
                  boxQualities.push(quality)
                }
              }
              if (windowDetail.box_quality !== undefined) {
                const quality = windowDetail.box_quality
                if (typeof quality === 'number' && !isNaN(quality)) {
                  boxQualities.push(quality)
                }
              }
            }
          })
        }
      })

      // 更新属性集合
      allStockAttributes.value.platformPeriods = platformPeriodsSet
      allStockAttributes.value.industries = industriesSet
      if (boxQualities.length > 0) {
        allStockAttributes.value.minBoxQuality = Math.min(...boxQualities)
        allStockAttributes.value.maxBoxQuality = Math.max(...boxQualities)
        // 最小箱体质量默认值保持为0，不自动设置
      }
      
      return {
        allStocks,
        selectedRecords
      }
  }
  
  // 检查是否有筛选条件被应用
  function hasFiltersApplied() {
    const filters = statisticsFilters.value
    return (
      filters.platformPeriods.length > 0 ||
      filters.breakthroughMACD.include ||
      filters.breakthroughMACD.exclude ||
      filters.breakthroughRSI.include ||
      filters.breakthroughRSI.exclude ||
      filters.breakthroughKDJ.include ||
      filters.breakthroughKDJ.exclude ||
      filters.breakthroughBollinger.include ||
      filters.breakthroughBollinger.exclude ||
      filters.breakthroughNone ||
      filters.breakthroughConfirmation !== null ||
      filters.boxQualityThreshold > 0 ||
      filters.industries.length > 0
    )
  }
  
  // 加载全量数据（不应用筛选条件）
  function loadAllDataWithoutFilters() {
    // 临时保存当前筛选条件
    const currentFilters = JSON.parse(JSON.stringify(statisticsFilters.value))
    
    // 清空所有筛选条件
    statisticsFilters.value = {
      platformPeriods: [],
      breakthroughMACD: { include: false, exclude: false },
      breakthroughRSI: { include: false, exclude: false },
      breakthroughKDJ: { include: false, exclude: false },
      breakthroughBollinger: { include: false, exclude: false },
      breakthroughNone: false,
      breakthroughConfirmation: null,
      boxQualityThreshold: 0,
      industries: []
    }
    
    // 计算统计数据（不筛选）
    calculateStatistics()
    
    // 注意：不恢复筛选条件，让用户看到全量数据
    // 如果用户想再次筛选，可以重新设置筛选条件并点击"筛选"按钮
  }
  
  // 计算统计数据（只进行本地筛选，不请求API）
  function calculateStatistics() {
    if (!allStocksData.value) {
      statisticsError.value = '请先加载数据'
      return
    }
    
    statisticsLoading.value = true
    statisticsError.value = null

    try {
      const { allStocks, selectedRecords } = allStocksData.value
      
      // 根据股票属性筛选股票（本地筛选）
      const filteredStocks = allStocks.filter(stock => {
        // 平台期筛选
        if (statisticsFilters.value.platformPeriods.length > 0) {
          const stockPlatformPeriods = []
          // 从 platform_windows 中收集平台期
          if (stock.platform_windows && Array.isArray(stock.platform_windows)) {
            stockPlatformPeriods.push(...stock.platform_windows)
          }
          // 从 selection_reasons 的键中收集平台期（一个股票可能同时满足多个平台期条件）
          if (stock.selection_reasons) {
            Object.keys(stock.selection_reasons).forEach(key => {
              const period = parseInt(key)
              if (!isNaN(period)) {
                stockPlatformPeriods.push(period)
              }
            })
          }
          
          // 去重，确保每个平台期只出现一次
          const uniqueStockPlatformPeriods = [...new Set(stockPlatformPeriods)]
          
          // 检查股票是否有任何一个选中的平台期（使用 OR 逻辑：只要有一个匹配就通过）
          const hasMatchingPeriod = statisticsFilters.value.platformPeriods.some(period => 
            uniqueStockPlatformPeriods.includes(period)
          )
          if (!hasMatchingPeriod) {
            return false
          }
        }

        // 突破前兆筛选
        const hasBreakthroughFilter = statisticsFilters.value.breakthroughMACD.include || 
                                      statisticsFilters.value.breakthroughMACD.exclude ||
                                      statisticsFilters.value.breakthroughRSI.include || 
                                      statisticsFilters.value.breakthroughRSI.exclude ||
                                      statisticsFilters.value.breakthroughKDJ.include || 
                                      statisticsFilters.value.breakthroughKDJ.exclude ||
                                      statisticsFilters.value.breakthroughBollinger.include || 
                                      statisticsFilters.value.breakthroughBollinger.exclude ||
                                      statisticsFilters.value.breakthroughNone
        
        if (hasBreakthroughFilter) {
          const breakthroughPrediction = stock.breakthrough_prediction
          const signals = breakthroughPrediction?.signals || {}
          
          // 如果用户选择了"无突破前兆"
          if (statisticsFilters.value.breakthroughNone) {
            // 检查股票是否完全没有突破前兆数据，或者所有信号都为false
            if (!breakthroughPrediction || !signals || Object.keys(signals).length === 0) {
              // 没有数据，视为无突破前兆，通过筛选
              // 继续其他筛选
            } else {
              // 检查所有信号是否都为false
              const allSignalsFalse = ['MACD', 'RSI', 'KDJ', '布林带'].every(signal => {
                const signalValue = signals[signal]
                // 检查信号值是否为false或falsy值
                if (signalValue === false || signalValue === 0) {
                  return true
                }
                if (typeof signalValue === 'string') {
                  return signalValue.toLowerCase() === 'false'
                }
                return false
              })
              if (!allSignalsFalse) {
                // 有任何一个信号为true，排除该股票
                return false
              }
            }
          } 
          // 处理包含和不包含的逻辑
          else {
            // 检查"包含"逻辑
            const includeSignals = []
            if (statisticsFilters.value.breakthroughMACD.include) includeSignals.push('MACD')
            if (statisticsFilters.value.breakthroughRSI.include) includeSignals.push('RSI')
            if (statisticsFilters.value.breakthroughKDJ.include) includeSignals.push('KDJ')
            if (statisticsFilters.value.breakthroughBollinger.include) includeSignals.push('布林带')

            // 检查"不包含"逻辑
            const excludeSignals = []
            if (statisticsFilters.value.breakthroughMACD.exclude) excludeSignals.push('MACD')
            if (statisticsFilters.value.breakthroughRSI.exclude) excludeSignals.push('RSI')
            if (statisticsFilters.value.breakthroughKDJ.exclude) excludeSignals.push('KDJ')
            if (statisticsFilters.value.breakthroughBollinger.exclude) excludeSignals.push('布林带')

            // 如果有任何筛选条件，需要检查股票数据
            if (includeSignals.length > 0 || excludeSignals.length > 0) {
              // 如果股票没有突破前兆数据
              if (!breakthroughPrediction || !signals || Object.keys(signals).length === 0) {
                // 如果有"包含"条件，没有数据则排除
                if (includeSignals.length > 0) {
                  return false
                }
                // 如果有"不包含"条件，没有数据则通过（因为没有该指标）
                // 继续其他筛选
              } else {
                // 检查"包含"逻辑：必须同时具备所有选中的信号
                if (includeSignals.length > 0) {
                  const hasAllMatchingSignals = includeSignals.every(signal => {
                    const signalValue = signals[signal]
                    // 检查信号值是否为true或truthy值
                    // 支持：true, 1, 'True', 'true', 'TRUE'
                    if (signalValue === true || signalValue === 1) {
                      return true
                    }
                    if (typeof signalValue === 'string') {
                      return signalValue.toLowerCase() === 'true'
                    }
                    if (typeof signalValue === 'boolean') {
                      return signalValue === true
                    }
                    return false
                  })
                  if (!hasAllMatchingSignals) {
                    return false
                  }
                }

                // 检查"不包含"逻辑：必须不包含所有选中的信号
                if (excludeSignals.length > 0) {
                  const hasAnyExcludedSignal = excludeSignals.some(signal => {
                    const signalValue = signals[signal]
                    // 检查信号值是否为true或truthy值
                    // 如果信号为true，则不符合"不包含"条件
                    if (signalValue === true || signalValue === 1) {
                      return true
                    }
                    if (typeof signalValue === 'string') {
                      return signalValue.toLowerCase() === 'true'
                    }
                    if (typeof signalValue === 'boolean') {
                      return signalValue === true
                    }
                    return false
                  })
                  if (hasAnyExcludedSignal) {
                    // 如果股票包含任何一个被排除的信号，则排除该股票
                    return false
                  }
                }
              }
            }
          }
        }

        // 确认突破筛选
        if (statisticsFilters.value.breakthroughConfirmation !== null) {
          // 如果用户选择了确认突破筛选，但股票没有确认突破数据，应该排除该股票
          if (stock.has_breakthrough_confirmation === undefined || stock.has_breakthrough_confirmation === null) {
            // 没有数据，排除股票（因为用户明确选择了筛选条件）
            return false
          } else {
            // 检查确认突破值是否为true（支持布尔值、数字1、字符串'True'等）
            const isConfirmationTrue = (value) => {
              if (value === true || value === 1) return true
              if (typeof value === 'string') return value.toLowerCase() === 'true'
              if (typeof value === 'boolean') return value === true
              return false
            }
            
            const hasConfirmation = isConfirmationTrue(stock.has_breakthrough_confirmation)
            // statisticsFilters.value.breakthroughConfirmation 是布尔值 true/false
            if (statisticsFilters.value.breakthroughConfirmation !== hasConfirmation) {
              return false
            }
          }
        }

        // 行业筛选
        if (statisticsFilters.value.industries.length > 0) {
          const stockIndustry = stock.industry
          // 如果用户选择了行业筛选，但股票没有行业数据，应该排除该股票
          if (!stockIndustry || stockIndustry === '' || stockIndustry === '未知行业') {
            // 没有行业数据，排除股票（因为用户明确选择了筛选条件）
            return false
          } else {
            if (!statisticsFilters.value.industries.includes(stockIndustry)) {
              return false
            }
          }
        }

        // 箱体质量筛选
        if (statisticsFilters.value.boxQualityThreshold > 0) {
          let stockBoxQuality = 0
          let hasBoxQualityData = false
          
          // 首先检查股票对象上的 box_analysis
          if (stock.box_analysis && typeof stock.box_analysis === 'object') {
            if (stock.box_analysis.box_quality !== undefined) {
              const quality = stock.box_analysis.box_quality
              if (typeof quality === 'number' && !isNaN(quality)) {
                stockBoxQuality = Math.max(stockBoxQuality, quality)
                hasBoxQualityData = true
              }
            }
          }
          
          // 然后检查 details 中每个窗口的 box_analysis
          if (stock.details && typeof stock.details === 'object') {
            Object.values(stock.details).forEach(windowDetail => {
              if (windowDetail && typeof windowDetail === 'object') {
                if (windowDetail.box_analysis && typeof windowDetail.box_analysis === 'object' && windowDetail.box_analysis.box_quality !== undefined) {
                  const quality = windowDetail.box_analysis.box_quality
                  if (typeof quality === 'number' && !isNaN(quality)) {
                    stockBoxQuality = Math.max(stockBoxQuality, quality)
                    hasBoxQualityData = true
                  }
                }
                if (windowDetail.box_quality !== undefined) {
                  const quality = windowDetail.box_quality
                  if (typeof quality === 'number' && !isNaN(quality)) {
                    stockBoxQuality = Math.max(stockBoxQuality, quality)
                    hasBoxQualityData = true
                  }
                }
              }
            })
          }
          
          // 如果用户选择了箱体质量筛选，但股票没有箱体质量数据，应该排除该股票
          if (!hasBoxQualityData) {
            // 没有数据，排除股票（因为用户明确选择了筛选条件）
            return false
          } else {
            if (stockBoxQuality < statisticsFilters.value.boxQualityThreshold) {
              return false
            }
          }
        }

        return true
      })

      // 根据筛选后的股票，筛选记录（记录必须包含至少一只筛选后的股票）
      const filteredRecords = selectedRecords.filter(record => {
        const config = record.config || {}
        const recordStocks = []
        
        if (config.selected_stocks && Array.isArray(config.selected_stocks)) {
          recordStocks.push(...config.selected_stocks)
        } else if (record.result && record.result.buyRecords) {
          record.result.buyRecords.forEach(buyRecord => {
            recordStocks.push({
              code: buyRecord.code || '',
              name: buyRecord.name || ''
            })
          })
        }

        // 检查记录中是否有筛选后的股票
        return filteredStocks.some(filteredStock => 
          recordStocks.some(recordStock => recordStock.code === filteredStock.code)
        )
      })

      // 计算统计数据并保存记录详情
      let totalRecords = filteredRecords.length
      let profitableStocks = 0  // 盈利股票数
      let lossStocks = 0  // 亏损股票数
      
      // 每次回测都是独立的，所以需要分别计算每次回测的收益率
      const recordReturns = [] // 存储每次回测的收益率和投入资金
      let totalInvestment = 0  // 所有回测的总投入资金（用于显示）
      let totalProfit = 0  // 所有回测的总收益（用于显示）

      const recordDetails = []

      filteredRecords.forEach(record => {
        const config = record.config || {}
        const result = record.result || {}
        
        // 获取该记录中筛选后的股票代码列表
        const filteredStockCodes = new Set()
        filteredStocks.forEach(filteredStock => {
          if (filteredStock.record === record) {
            filteredStockCodes.add(filteredStock.code)
          }
        })

        // 从stockDetails中获取筛选后股票的收益数据
        const stockDetails = result.stockDetails || []
        const filteredStockDetails = stockDetails.filter(detail => 
          filteredStockCodes.has(detail.code)
        )

        // 重新计算筛选后股票的统计数据（本次回测）
        let recordInvestment = 0
        let recordProfit = 0
        
        filteredStockDetails.forEach(detail => {
          const buyAmount = detail.buyAmount || 0
          recordInvestment += buyAmount
          recordProfit += (detail.profit || 0)
          
          // 统计盈利和亏损股票数
          if (detail.profit > 0) {
            profitableStocks++
          } else if (detail.profit < 0) {
            lossStocks++
          }
        })

        // 计算本次回测的收益率
        let recordReturnRate = 0
        if (recordInvestment > 0) {
          recordReturnRate = (recordProfit / recordInvestment) * 100
        }
        
        // 保存本次回测的数据（用于后续计算整体收益率）
        recordReturns.push({
          investment: recordInvestment,
          profit: recordProfit,
          returnRate: recordReturnRate
        })

        // 累计总投入和总收益（用于显示）
        totalInvestment += recordInvestment
        totalProfit += recordProfit

        // 保存记录详情（只包含筛选后的股票信息）
        const stocks = []
        const recordStocks = []
        
        // 从config中获取股票列表
        if (config.selected_stocks && Array.isArray(config.selected_stocks)) {
          recordStocks.push(...config.selected_stocks)
        }
        // 如果没有selected_stocks，尝试从result中提取
        else if (result.buyRecords) {
          result.buyRecords.forEach(buyRecord => {
            recordStocks.push({
              code: buyRecord.code || '',
              name: buyRecord.name || '',
              industry: ''
            })
          })
        }

        // 只保存筛选后的股票（包含筛选条件信息）
        filteredStocks.forEach(filteredStock => {
          if (filteredStock.record === record) {
            const matchingStock = recordStocks.find(rs => rs.code === filteredStock.code)
            if (matchingStock) {
              // 从stockDetails中获取该股票的收益率
              const stockDetail = filteredStockDetails.find(detail => detail.code === filteredStock.code)
              const returnRate = stockDetail?.returnRate !== undefined ? stockDetail.returnRate : null
              
              // 提取平台期信息
              const platformPeriods = []
              if (filteredStock.platform_windows && Array.isArray(filteredStock.platform_windows)) {
                platformPeriods.push(...filteredStock.platform_windows)
              }
              if (filteredStock.selection_reasons) {
                Object.keys(filteredStock.selection_reasons).forEach(key => {
                  const period = parseInt(key)
                  if (!isNaN(period)) {
                    platformPeriods.push(period)
                  }
                })
              }
              const uniquePlatformPeriods = [...new Set(platformPeriods)].sort((a, b) => a - b)
              
              // 提取突破前兆信息
              const breakthroughSignals = []
              const breakthroughPrediction = filteredStock.breakthrough_prediction
              if (breakthroughPrediction && breakthroughPrediction.signals) {
                const signals = breakthroughPrediction.signals
                // 检查信号值是否为true（支持布尔值、数字1、字符串'True'等）
                const isSignalTrue = (value) => {
                  if (value === true || value === 1) return true
                  if (typeof value === 'string') return value.toLowerCase() === 'true'
                  return false
                }
                if (isSignalTrue(signals.MACD)) breakthroughSignals.push('MACD')
                if (isSignalTrue(signals.RSI)) breakthroughSignals.push('RSI')
                if (isSignalTrue(signals.KDJ)) breakthroughSignals.push('KDJ')
                if (isSignalTrue(signals['布林带'])) breakthroughSignals.push('布林带')
              }
              
              // 提取确认突破信息
              // 检查确认突破值是否为true（支持布尔值、数字1、字符串'True'等）
              const isConfirmationTrue = (value) => {
                if (value === true || value === 1) return true
                if (typeof value === 'string') return value.toLowerCase() === 'true'
                if (typeof value === 'boolean') return value === true
                return false
              }
              const hasBreakthroughConfirmation = isConfirmationTrue(filteredStock.has_breakthrough_confirmation)
              
              // 提取箱体质量信息
              let boxQuality = null
              // 首先检查股票对象上的 box_analysis
              if (filteredStock.box_analysis && typeof filteredStock.box_analysis === 'object') {
                if (filteredStock.box_analysis.box_quality !== undefined) {
                  const quality = filteredStock.box_analysis.box_quality
                  if (typeof quality === 'number' && !isNaN(quality)) {
                    boxQuality = quality
                  }
                }
              }
              // 然后检查 details 中每个窗口的 box_analysis
              if (filteredStock.details && typeof filteredStock.details === 'object') {
                Object.values(filteredStock.details).forEach(windowDetail => {
                  if (windowDetail && typeof windowDetail === 'object') {
                    if (windowDetail.box_analysis && typeof windowDetail.box_analysis === 'object' && windowDetail.box_analysis.box_quality !== undefined) {
                      const quality = windowDetail.box_analysis.box_quality
                      if (typeof quality === 'number' && !isNaN(quality)) {
                        if (boxQuality === null || quality > boxQuality) {
                          boxQuality = quality
                        }
                      }
                    }
                    if (windowDetail.box_quality !== undefined) {
                      const quality = windowDetail.box_quality
                      if (typeof quality === 'number' && !isNaN(quality)) {
                        if (boxQuality === null || quality > boxQuality) {
                          boxQuality = quality
                        }
                      }
                    }
                  }
                })
              }
              
              stocks.push({
                code: filteredStock.code || '',
                name: filteredStock.name || '',
                industry: filteredStock.industry || matchingStock.industry || '',
                platformPeriods: uniquePlatformPeriods,
                breakthroughSignals: breakthroughSignals,
                hasBreakthroughConfirmation: hasBreakthroughConfirmation,
                boxQuality: boxQuality,
                returnRate: returnRate
              })
            }
          }
        })

        recordDetails.push({
          scanDate: config.backtest_date || '',
          stocks: stocks
        })
      })

      // 计算整体收益率
      // 因为每次回测都是独立的，所以整体收益率应该用复利方式计算
      // 或者用加权平均的方式计算
      let totalReturnRate = 0
      if (recordReturns.length > 0) {
        // 方法1：复利计算（更准确）
        // 总收益率 = (1 + r1/100) * (1 + r2/100) * ... * (1 + rn/100) - 1
        let compoundReturn = 1
        recordReturns.forEach(r => {
          if (r.investment > 0) {
            compoundReturn *= (1 + r.returnRate / 100)
          }
        })
        totalReturnRate = (compoundReturn - 1) * 100
        
        // 方法2：加权平均（按投入资金加权）
        // 如果总投入为0，则使用简单平均
        if (totalInvestment > 0) {
          let weightedSum = 0
          recordReturns.forEach(r => {
            if (r.investment > 0) {
              weightedSum += r.returnRate * (r.investment / totalInvestment)
            }
          })
          totalReturnRate = weightedSum
        } else {
          // 如果总投入为0，使用简单平均
          const avgReturn = recordReturns.reduce((sum, r) => sum + r.returnRate, 0) / recordReturns.length
          totalReturnRate = avgReturn
        }
      }

      // 计算胜率（基于股票数量）
      const totalStocks = profitableStocks + lossStocks
      const winRate = totalStocks > 0 ? (profitableStocks / totalStocks) * 100 : 0

      statisticsResult.value = {
        totalRecords,
        profitableRecords: profitableStocks,  // 使用盈利股票数
        lossRecords: lossStocks,  // 使用亏损股票数
        winRate,
        totalInvestment,
        totalProfit,
        totalReturnRate,
        filteredRecords: recordDetails
      }
    } catch (e) {
      console.error('计算统计数据失败:', e)
      statisticsError.value = '计算统计数据失败: ' + (e.response?.data?.detail || e.message)
    } finally {
      statisticsLoading.value = false
    }
  }

  // 监听历史记录变化，自动加载完整数据
  watch(() => props.historyRecords, async (newRecords) => {
    if (newRecords && newRecords.length > 0) {
      // 检查历史记录是否变化
      const historyChanged = hasBacktestHistoryChanged()
      if (historyChanged || !allStocksDataLoaded.value) {
        // 历史记录变化或未加载数据，自动加载
        await loadAllData()
      }
      // 注意：不自动筛选，需要用户点击"筛选"按钮
    } else {
      // 清空数据
      allStocksData.value = null
      allStocksDataLoaded.value = false
      statisticsResult.value = null
    }
  }, { immediate: true })
  
  // 注意：移除了筛选条件的自动监听，改为手动点击"筛选"按钮触发
</script>