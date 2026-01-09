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
                :disabled="dataLoading"
              >
                <i :class="statisticsFiltersExpanded ? 'fas fa-chevron-down' : 'fas fa-chevron-right'"></i>
              </button>
              <h3 class="text-sm font-semibold flex items-center">
                <i class="fas fa-filter mr-1 text-primary"></i>
                筛选条件
                <span v-if="dataLoading" class="ml-2 text-xs text-muted-foreground">
                  <i class="fas fa-spinner fa-spin mr-1"></i>
                  加载中...
                </span>
              </h3>
            </div>
          </div>
          <div v-if="dataLoading" class="text-center py-4">
            <i class="fas fa-spinner fa-spin text-2xl mb-2 text-primary"></i>
            <p class="text-muted-foreground text-sm">正在加载数据...</p>
          </div>
          <div v-else v-show="statisticsFiltersExpanded" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
            <!-- ========== 第一组：基础筛选（平台期相关） ========== -->
            <!-- 平台期 -->
            <div>
              <label class="block text-xs font-medium mb-1">平台期</label>
              <div class="flex flex-wrap gap-1">
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
  
            <!-- 行业信息 -->
            <div>
              <label class="block text-xs font-medium mb-1">行业信息</label>
              <div class="max-h-20 overflow-y-auto border border-border rounded p-1">
                <label 
                  v-for="industry in Array.from(allStockAttributes.industries).sort()" 
                  :key="industry"
                  class="flex items-center cursor-pointer mb-0.5 px-1 py-0.5 rounded hover:bg-muted/30 transition-colors"
                >
                  <input
                    type="checkbox"
                    :value="industry"
                    v-model="statisticsFilters.industries"
                    class="checkbox mr-1"
                  />
                  <span class="text-xs">{{ industry || '未知行业' }}</span>
                </label>
                <p v-if="allStockAttributes.industries.size === 0" class="text-xs text-muted-foreground text-center py-1">暂无数据</p>
              </div>
            </div>

            <!-- 板块筛选 -->
            <div>
              <label class="block text-xs font-medium mb-1">板块</label>
              <div class="flex flex-wrap gap-1">
                <label 
                  class="flex items-center cursor-pointer px-1.5 py-0.5 rounded border border-border hover:bg-muted/30 transition-colors"
                  :class="statisticsFilters.boards.includes('创业板') ? 'bg-primary/20 border-primary' : ''"
                >
                  <input
                    type="checkbox"
                    value="创业板"
                    v-model="statisticsFilters.boards"
                    class="checkbox mr-1"
                  />
                  <span class="text-xs">创业板</span>
                </label>
                <label 
                  class="flex items-center cursor-pointer px-1.5 py-0.5 rounded border border-border hover:bg-muted/30 transition-colors"
                  :class="statisticsFilters.boards.includes('科创板') ? 'bg-primary/20 border-primary' : ''"
                >
                  <input
                    type="checkbox"
                    value="科创板"
                    v-model="statisticsFilters.boards"
                    class="checkbox mr-1"
                  />
                  <span class="text-xs">科创板</span>
                </label>
                <label 
                  class="flex items-center cursor-pointer px-1.5 py-0.5 rounded border border-border hover:bg-muted/30 transition-colors"
                  :class="statisticsFilters.boards.includes('主板') ? 'bg-primary/20 border-primary' : ''"
                >
                  <input
                    type="checkbox"
                    value="主板"
                    v-model="statisticsFilters.boards"
                    class="checkbox mr-1"
                  />
                  <span class="text-xs">主板</span>
                </label>
              </div>
            </div>

            <!-- ========== 第二组：突破相关 ========== -->
            <!-- 突破前兆 -->
            <div class="sm:col-span-2 lg:col-span-1">
              <label class="block text-xs font-medium mb-1">突破前兆</label>
              <div class="grid grid-cols-2 gap-1.5">
                <!-- MACD -->
                <div class="flex items-center gap-1">
                  <span class="text-xs w-10 flex-shrink-0">MACD:</span>
                  <label class="flex items-center cursor-pointer px-1 py-0.5 rounded border border-border hover:bg-muted/30 transition-colors flex-1">
                    <input
                      type="checkbox"
                      v-model="statisticsFilters.breakthroughMACD.include"
                      @change="handleBreakthroughSignalChange"
                      class="checkbox mr-0.5"
                    />
                    <span class="text-xs">含</span>
                  </label>
                  <label class="flex items-center cursor-pointer px-1 py-0.5 rounded border border-border hover:bg-muted/30 transition-colors flex-1">
                    <input
                      type="checkbox"
                      v-model="statisticsFilters.breakthroughMACD.exclude"
                      @change="handleBreakthroughExcludeChange('MACD')"
                      class="checkbox mr-0.5"
                    />
                    <span class="text-xs">不含</span>
                  </label>
                </div>
                <!-- RSI -->
                <div class="flex items-center gap-1">
                  <span class="text-xs w-10 flex-shrink-0">RSI:</span>
                  <label class="flex items-center cursor-pointer px-1 py-0.5 rounded border border-border hover:bg-muted/30 transition-colors flex-1">
                    <input
                      type="checkbox"
                      v-model="statisticsFilters.breakthroughRSI.include"
                      @change="handleBreakthroughSignalChange"
                      class="checkbox mr-0.5"
                    />
                    <span class="text-xs">含</span>
                  </label>
                  <label class="flex items-center cursor-pointer px-1 py-0.5 rounded border border-border hover:bg-muted/30 transition-colors flex-1">
                    <input
                      type="checkbox"
                      v-model="statisticsFilters.breakthroughRSI.exclude"
                      @change="handleBreakthroughExcludeChange('RSI')"
                      class="checkbox mr-0.5"
                    />
                    <span class="text-xs">不含</span>
                  </label>
                </div>
                <!-- KDJ -->
                <div class="flex items-center gap-1">
                  <span class="text-xs w-10 flex-shrink-0">KDJ:</span>
                  <label class="flex items-center cursor-pointer px-1 py-0.5 rounded border border-border hover:bg-muted/30 transition-colors flex-1">
                    <input
                      type="checkbox"
                      v-model="statisticsFilters.breakthroughKDJ.include"
                      @change="handleBreakthroughSignalChange"
                      class="checkbox mr-0.5"
                    />
                    <span class="text-xs">含</span>
                  </label>
                  <label class="flex items-center cursor-pointer px-1 py-0.5 rounded border border-border hover:bg-muted/30 transition-colors flex-1">
                    <input
                      type="checkbox"
                      v-model="statisticsFilters.breakthroughKDJ.exclude"
                      @change="handleBreakthroughExcludeChange('KDJ')"
                      class="checkbox mr-0.5"
                    />
                    <span class="text-xs">不含</span>
                  </label>
                </div>
                <!-- 布林带 -->
                <div class="flex items-center gap-1">
                  <span class="text-xs w-10 flex-shrink-0">布林:</span>
                  <label class="flex items-center cursor-pointer px-1 py-0.5 rounded border border-border hover:bg-muted/30 transition-colors flex-1">
                    <input
                      type="checkbox"
                      v-model="statisticsFilters.breakthroughBollinger.include"
                      @change="handleBreakthroughSignalChange"
                      class="checkbox mr-0.5"
                    />
                    <span class="text-xs">含</span>
                  </label>
                  <label class="flex items-center cursor-pointer px-1 py-0.5 rounded border border-border hover:bg-muted/30 transition-colors flex-1">
                    <input
                      type="checkbox"
                      v-model="statisticsFilters.breakthroughBollinger.exclude"
                      @change="handleBreakthroughExcludeChange('Bollinger')"
                      class="checkbox mr-0.5"
                    />
                    <span class="text-xs">不含</span>
                  </label>
                </div>
                <!-- 无突破前兆 -->
                <div class="col-span-2">
                  <label class="flex items-center cursor-pointer px-1 py-0.5 rounded border border-border hover:bg-muted/30 transition-colors w-fit">
                    <input
                      type="checkbox"
                      v-model="statisticsFilters.breakthroughNone"
                      @change="handleBreakthroughNoneChange"
                      class="checkbox mr-1"
                    />
                    <span class="text-xs">无突破前兆</span>
                  </label>
                </div>
              </div>
            </div>
  
            <!-- 确认突破 -->
            <div>
              <label class="block text-xs font-medium mb-1">确认突破</label>
              <select
                v-model="statisticsFilters.breakthroughConfirmation"
                class="input w-full text-xs py-1 h-7"
              >
                <option :value="null">不筛选</option>
                <option :value="true">是（已确认突破）</option>
                <option :value="false">否（未确认突破）</option>
              </select>
            </div>

            <!-- ========== 第三组：质量指标（Range Slider） ========== -->
            <!-- 箱体质量 -->
            <div>
              <label class="block text-xs font-medium mb-1">箱体质量</label>
              <div v-if="allStockAttributes.maxBoxQuality > allStockAttributes.minBoxQuality && allStockAttributes.maxBoxQuality > 0" class="space-y-1.5">
                <Slider
                  v-model="boxQualityRangeArray"
                  :min="allStockAttributes.minBoxQuality"
                  :max="allStockAttributes.maxBoxQuality"
                  :step="Math.max(0.01, (allStockAttributes.maxBoxQuality - allStockAttributes.minBoxQuality) / 100)"
                />
                <div class="flex justify-between items-center text-xs">
                  <span class="text-muted-foreground">{{ allStockAttributes.minBoxQuality.toFixed(2) }}</span>
                  <span class="font-medium text-foreground">
                    {{ boxQualityRangeArray[0].toFixed(2) }} - {{ boxQualityRangeArray[1].toFixed(2) }}
                  </span>
                  <span class="text-muted-foreground">{{ allStockAttributes.maxBoxQuality.toFixed(2) }}</span>
                </div>
              </div>
              <p v-else class="text-xs text-muted-foreground">暂无数据</p>
            </div>

            <!-- 价格区间 -->
            <div>
              <label class="block text-xs font-medium mb-1">价格区间</label>
              <div v-if="allStockAttributes.maxBoxRange > allStockAttributes.minBoxRange && allStockAttributes.maxBoxRange > 0" class="space-y-1.5">
                <Slider
                  v-model="boxRangeArray"
                  :min="allStockAttributes.minBoxRange"
                  :max="allStockAttributes.maxBoxRange"
                  :step="Math.max(0.01, (allStockAttributes.maxBoxRange - allStockAttributes.minBoxRange) / 100)"
                />
                <div class="flex justify-between items-center text-xs">
                  <span class="text-muted-foreground">{{ allStockAttributes.minBoxRange.toFixed(2) }}</span>
                  <span class="font-medium text-foreground">
                    {{ boxRangeArray[0].toFixed(2) }} - {{ boxRangeArray[1].toFixed(2) }}
                  </span>
                  <span class="text-muted-foreground">{{ allStockAttributes.maxBoxRange.toFixed(2) }}</span>
                </div>
              </div>
              <p v-else class="text-xs text-muted-foreground">暂无数据</p>
            </div>

            <!-- 均线收敛 -->
            <div>
              <label class="block text-xs font-medium mb-1">均线收敛</label>
              <div v-if="allStockAttributes.maxMaDiff > allStockAttributes.minMaDiff && allStockAttributes.maxMaDiff > 0" class="space-y-1.5">
                <Slider
                  v-model="maDiffRangeArray"
                  :min="allStockAttributes.minMaDiff"
                  :max="allStockAttributes.maxMaDiff"
                  :step="Math.max(0.01, (allStockAttributes.maxMaDiff - allStockAttributes.minMaDiff) / 100)"
                />
                <div class="flex justify-between items-center text-xs">
                  <span class="text-muted-foreground">{{ allStockAttributes.minMaDiff.toFixed(2) }}</span>
                  <span class="font-medium text-foreground">
                    {{ maDiffRangeArray[0].toFixed(2) }} - {{ maDiffRangeArray[1].toFixed(2) }}
                  </span>
                  <span class="text-muted-foreground">{{ allStockAttributes.maxMaDiff.toFixed(2) }}</span>
                </div>
              </div>
              <p v-else class="text-xs text-muted-foreground">暂无数据</p>
            </div>

            <!-- 波动率 -->
            <div>
              <label class="block text-xs font-medium mb-1">波动率</label>
              <div v-if="allStockAttributes.maxVolatility > allStockAttributes.minVolatility && allStockAttributes.maxVolatility > 0" class="space-y-1.5">
                <Slider
                  v-model="volatilityRangeArray"
                  :min="allStockAttributes.minVolatility"
                  :max="allStockAttributes.maxVolatility"
                  :step="Math.max(0.01, (allStockAttributes.maxVolatility - allStockAttributes.minVolatility) / 100)"
                />
                <div class="flex justify-between items-center text-xs">
                  <span class="text-muted-foreground">{{ allStockAttributes.minVolatility.toFixed(2) }}</span>
                  <span class="font-medium text-foreground">
                    {{ volatilityRangeArray[0].toFixed(2) }} - {{ volatilityRangeArray[1].toFixed(2) }}
                  </span>
                  <span class="text-muted-foreground">{{ allStockAttributes.maxVolatility.toFixed(2) }}</span>
                </div>
              </div>
              <p v-else class="text-xs text-muted-foreground">暂无数据</p>
            </div>

            <!-- 成交量变化 -->
            <div>
              <label class="block text-xs font-medium mb-1">成交量变化</label>
              <div v-if="allStockAttributes.maxVolumeChange > allStockAttributes.minVolumeChange && allStockAttributes.maxVolumeChange > 0" class="space-y-1.5">
                <Slider
                  v-model="volumeChangeRangeArray"
                  :min="allStockAttributes.minVolumeChange"
                  :max="allStockAttributes.maxVolumeChange"
                  :step="Math.max(0.01, (allStockAttributes.maxVolumeChange - allStockAttributes.minVolumeChange) / 100)"
                />
                <div class="flex justify-between items-center text-xs">
                  <span class="text-muted-foreground">{{ allStockAttributes.minVolumeChange.toFixed(2) }}</span>
                  <span class="font-medium text-foreground">
                    {{ volumeChangeRangeArray[0].toFixed(2) }} - {{ volumeChangeRangeArray[1].toFixed(2) }}
                  </span>
                  <span class="text-muted-foreground">{{ allStockAttributes.maxVolumeChange.toFixed(2) }}</span>
                </div>
              </div>
              <p v-else class="text-xs text-muted-foreground">暂无数据</p>
            </div>

            <!-- 成交量稳定性 -->
            <div>
              <label class="block text-xs font-medium mb-1">成交量稳定性</label>
              <div v-if="allStockAttributes.maxVolumeStability > allStockAttributes.minVolumeStability && allStockAttributes.maxVolumeStability > 0" class="space-y-1.5">
                <Slider
                  v-model="volumeStabilityRangeArray"
                  :min="allStockAttributes.minVolumeStability"
                  :max="allStockAttributes.maxVolumeStability"
                  :step="Math.max(0.01, (allStockAttributes.maxVolumeStability - allStockAttributes.minVolumeStability) / 100)"
                />
                <div class="flex justify-between items-center text-xs">
                  <span class="text-muted-foreground">{{ allStockAttributes.minVolumeStability.toFixed(2) }}</span>
                  <span class="font-medium text-foreground">
                    {{ volumeStabilityRangeArray[0].toFixed(2) }} - {{ volumeStabilityRangeArray[1].toFixed(2) }}
                  </span>
                  <span class="text-muted-foreground">{{ allStockAttributes.maxVolumeStability.toFixed(2) }}</span>
                </div>
              </div>
              <p v-else class="text-xs text-muted-foreground">暂无数据</p>
            </div>

            <!-- 换手率 -->
            <div>
              <label class="block text-xs font-medium mb-1">换手率 (%)</label>
              <div v-if="allStockAttributes.maxTurnoverRate > allStockAttributes.minTurnoverRate && allStockAttributes.maxTurnoverRate > 0" class="space-y-1.5">
                <Slider
                  v-model="turnoverRateRangeArray"
                  :min="allStockAttributes.minTurnoverRate"
                  :max="allStockAttributes.maxTurnoverRate"
                  :step="Math.max(0.01, (allStockAttributes.maxTurnoverRate - allStockAttributes.minTurnoverRate) / 100)"
                />
                <div class="flex justify-between items-center text-xs">
                  <span class="text-muted-foreground">{{ allStockAttributes.minTurnoverRate.toFixed(2) }}%</span>
                  <span class="font-medium text-foreground">
                    {{ turnoverRateRangeArray[0].toFixed(2) }}% - {{ turnoverRateRangeArray[1].toFixed(2) }}%
                  </span>
                  <span class="text-muted-foreground">{{ allStockAttributes.maxTurnoverRate.toFixed(2) }}%</span>
                </div>
              </div>
              <p v-else class="text-xs text-muted-foreground">暂无数据</p>
            </div>

            <!-- 相对强度 -->
            <div>
              <label class="block text-xs font-medium mb-1">相对强度 (%)</label>
              <div v-if="allStockAttributes.maxOutperformIndex !== undefined && allStockAttributes.minOutperformIndex !== undefined && allStockAttributes.maxOutperformIndex > allStockAttributes.minOutperformIndex" class="space-y-1.5">
                <Slider
                  v-model="outperformIndexRangeArray"
                  :min="allStockAttributes.minOutperformIndex"
                  :max="allStockAttributes.maxOutperformIndex"
                  :step="Math.max(0.1, (allStockAttributes.maxOutperformIndex - allStockAttributes.minOutperformIndex) / 100)"
                />
                <div class="flex justify-between items-center text-xs">
                  <span class="text-muted-foreground">{{ allStockAttributes.minOutperformIndex.toFixed(2) }}%</span>
                  <span class="font-medium text-foreground">
                    {{ outperformIndexRangeArray[0].toFixed(2) }}% - {{ outperformIndexRangeArray[1].toFixed(2) }}%
                  </span>
                  <span class="text-muted-foreground">{{ allStockAttributes.maxOutperformIndex.toFixed(2) }}%</span>
                </div>
              </div>
              <p v-else class="text-xs text-muted-foreground">暂无数据</p>
            </div>

            <!-- 布林极限 (%B) -->
            <div>
              <label class="block text-xs font-medium mb-1">布林极限 (%B)</label>
              <div v-if="allStockAttributes.maxPercentB > allStockAttributes.minPercentB && allStockAttributes.maxPercentB > 0" class="space-y-1.5">
                <Slider
                  v-model="percentBRangeArray"
                  :min="allStockAttributes.minPercentB"
                  :max="allStockAttributes.maxPercentB"
                  :step="Math.max(0.01, (allStockAttributes.maxPercentB - allStockAttributes.minPercentB) / 100)"
                />
                <div class="flex justify-between items-center text-xs">
                  <span class="text-muted-foreground">{{ allStockAttributes.minPercentB.toFixed(2) }}</span>
                  <span class="font-medium text-foreground">
                    {{ percentBRangeArray[0].toFixed(2) }} - {{ percentBRangeArray[1].toFixed(2) }}
                  </span>
                  <span class="text-muted-foreground">{{ allStockAttributes.maxPercentB.toFixed(2) }}</span>
                </div>
              </div>
              <p v-else class="text-xs text-muted-foreground">暂无数据</p>
            </div>

            <!-- ========== 第四组：位置和下跌（百分比 Range Slider） ========== -->
            <!-- 低位判断百分比 -->
            <div>
              <label class="block text-xs font-medium mb-1">低位百分比</label>
              <div v-if="allStockAttributes.maxLowPositionPercent > allStockAttributes.minLowPositionPercent && allStockAttributes.maxLowPositionPercent > 0" class="space-y-1.5">
                <Slider
                  v-model="lowPositionPercentRangeArray"
                  :min="allStockAttributes.minLowPositionPercent"
                  :max="allStockAttributes.maxLowPositionPercent"
                  :step="Math.max(0.01, (allStockAttributes.maxLowPositionPercent - allStockAttributes.minLowPositionPercent) / 100)"
                />
                <div class="flex justify-between items-center text-xs">
                  <span class="text-muted-foreground">{{ allStockAttributes.minLowPositionPercent.toFixed(2) }}%</span>
                  <span class="font-medium text-foreground">
                    {{ lowPositionPercentRangeArray[0].toFixed(2) }}% - {{ lowPositionPercentRangeArray[1].toFixed(2) }}%
                  </span>
                  <span class="text-muted-foreground">{{ allStockAttributes.maxLowPositionPercent.toFixed(2) }}%</span>
                </div>
              </div>
              <p v-else class="text-xs text-muted-foreground">暂无数据</p>
            </div>

            <!-- 快速下跌百分比 -->
            <div>
              <label class="block text-xs font-medium mb-1">快速下跌百分比</label>
              <div v-if="allStockAttributes.maxRapidDeclinePercent > allStockAttributes.minRapidDeclinePercent && allStockAttributes.maxRapidDeclinePercent > 0" class="space-y-1.5">
                <Slider
                  v-model="rapidDeclinePercentRangeArray"
                  :min="allStockAttributes.minRapidDeclinePercent"
                  :max="allStockAttributes.maxRapidDeclinePercent"
                  :step="Math.max(0.01, (allStockAttributes.maxRapidDeclinePercent - allStockAttributes.minRapidDeclinePercent) / 100)"
                />
                <div class="flex justify-between items-center text-xs">
                  <span class="text-muted-foreground">{{ allStockAttributes.minRapidDeclinePercent.toFixed(2) }}%</span>
                  <span class="font-medium text-foreground">
                    {{ rapidDeclinePercentRangeArray[0].toFixed(2) }}% - {{ rapidDeclinePercentRangeArray[1].toFixed(2) }}%
                  </span>
                  <span class="text-muted-foreground">{{ allStockAttributes.maxRapidDeclinePercent.toFixed(2) }}%</span>
                </div>
              </div>
              <p v-else class="text-xs text-muted-foreground">暂无数据</p>
            </div>

            <!-- ========== 第五组：周期统计（Range Slider） ========== -->
            <!-- 周期内购买的股票数量 -->
            <div>
              <label class="block text-xs font-medium mb-1">周期内股票数量</label>
              <div v-if="allStockAttributes.maxStockCount > allStockAttributes.minStockCount && allStockAttributes.maxStockCount > 0 && stockCountRangeArray && stockCountRangeArray.length === 2" class="space-y-1.5">
                <Slider
                  v-model="stockCountRangeArray"
                  :min="allStockAttributes.minStockCount"
                  :max="allStockAttributes.maxStockCount"
                  :step="1"
                />
                <div class="flex justify-between items-center text-xs">
                  <span class="text-muted-foreground">{{ allStockAttributes.minStockCount }}</span>
                  <span class="font-medium text-foreground">
                    {{ Math.round(stockCountRangeArray[0]) }} - {{ Math.round(stockCountRangeArray[1]) }}
                  </span>
                  <span class="text-muted-foreground">{{ allStockAttributes.maxStockCount }}</span>
                </div>
              </div>
              <p v-else class="text-xs text-muted-foreground">暂无数据</p>
            </div>
          </div>
        </div>
  
        <!-- 统计结果 -->
        <div class="flex-1 flex flex-col overflow-hidden p-2 sm:p-3 min-h-0">
          <h3 class="text-sm font-semibold mb-2 flex items-center flex-shrink-0">
            <i class="fas fa-calculator mr-1 text-primary"></i>
            统计结果
          </h3>
          <div v-if="dataLoading" class="text-center py-8 flex-shrink-0">
            <i class="fas fa-spinner fa-spin text-3xl mb-3 text-primary"></i>
            <p class="text-muted-foreground text-sm">数据加载中...</p>
            <p class="text-xs text-muted-foreground mt-1">正在获取回测历史记录详情</p>
          </div>
          <div v-else-if="statisticsLoading" class="text-center py-4 flex-shrink-0">
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
                  <div class="text-xs text-muted-foreground mb-0.5 whitespace-nowrap">盈利/亏损股票数</div>
                  <div class="text-base sm:text-lg font-bold">
                    <span class="text-red-600 dark:text-red-400">{{ statisticsResult.profitableRecords }}</span>
                    <span class="text-muted-foreground mx-1">/</span>
                    <span class="text-blue-600 dark:text-blue-400">{{ statisticsResult.lossRecords }}</span>
                  </div>
                </div>
                <div class="p-1.5 sm:p-2 bg-muted/30 rounded-md">
                  <div class="text-xs text-muted-foreground mb-0.5 whitespace-nowrap">整体胜率</div>
                  <div class="text-base sm:text-lg font-bold" :class="statisticsResult.winRate >= 50 ? 'text-red-600 dark:text-red-400' : 'text-blue-600 dark:text-blue-400'">
                    {{ formatPercent(statisticsResult.winRate) }}%
                  </div>
                </div>
              </div>
              <div class="grid grid-cols-3 gap-1.5">
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
                <div class="p-1.5 sm:p-2 bg-muted/30 rounded-md">
                  <div class="text-xs text-muted-foreground mb-0.5 whitespace-nowrap">总投入资金</div>
                  <div class="text-base sm:text-lg font-bold truncate">¥{{ formatNumber(statisticsResult.totalInvestment) }}</div>
                </div>
              </div>
              <div class="grid grid-cols-3 gap-1.5">
                <div v-if="statisticsResult.maxDrawdown !== null && statisticsResult.maxDrawdown !== undefined" class="p-1.5 sm:p-2 bg-muted/30 rounded-md">
                  <div class="text-xs text-muted-foreground mb-0.5 whitespace-nowrap">最大回撤</div>
                  <div class="text-base sm:text-lg font-bold text-blue-600 dark:text-blue-400">
                    {{ formatPercent(statisticsResult.maxDrawdown) }}%
                  </div>
                  <div v-if="statisticsResult.maxDrawdownDateRange" class="text-xs text-muted-foreground mt-0.5">
                    {{ statisticsResult.maxDrawdownDateRange.start }} ~ {{ statisticsResult.maxDrawdownDateRange.end }}
                  </div>
                </div>
                <div v-if="statisticsResult.sharpeRatio !== null && statisticsResult.sharpeRatio !== undefined" class="p-1.5 sm:p-2 bg-muted/30 rounded-md">
                  <div class="text-xs text-muted-foreground mb-0.5 whitespace-nowrap">夏普比</div>
                  <div class="text-base sm:text-lg font-bold" :class="statisticsResult.sharpeRatio >= 1 ? 'text-red-600 dark:text-red-400' : 'text-blue-600 dark:text-blue-400'">
                    {{ statisticsResult.sharpeRatio.toFixed(2) }}
                  </div>
                </div>
                <div v-if="statisticsResult.totalRepeatCount !== undefined && statisticsResult.totalRepeatCount !== null" class="p-1.5 sm:p-2 bg-muted/30 rounded-md">
                  <div class="text-xs text-muted-foreground mb-0.5 whitespace-nowrap">重复数总额</div>
                  <div class="text-base sm:text-lg font-bold text-blue-600 dark:text-blue-400">
                    {{ statisticsResult.totalRepeatCount }}
                  </div>
                </div>
              </div>
            </div>
  
            <!-- 周期统计 -->
            <div v-if="statisticsResult.periodStats && statisticsResult.periodStats.length > 0" class="mt-2 flex-shrink-0">
              <h4 class="text-xs sm:text-sm font-semibold mb-2 flex items-center">
                <i class="fas fa-calendar-alt mr-1 text-primary"></i>
                周期统计
              </h4>
              <div class="space-y-2">
                <div 
                  v-for="(periodStat, index) in statisticsResult.periodStats" 
                  :key="index"
                  class="border border-border rounded-md overflow-hidden"
                >
                  <!-- 周期统计头部 -->
                  <div class="bg-muted/50 p-2 sm:p-3 border-b border-border">
                    <div class="flex items-center justify-between">
                      <div class="flex-1 grid grid-cols-2 sm:grid-cols-7 gap-2 sm:gap-4">
                        <div>
                          <div class="text-xs text-muted-foreground mb-0.5">周期</div>
                          <div class="text-sm font-medium">{{ periodStat.periodLabel }}</div>
                        </div>
                        <div>
                          <div class="text-xs text-muted-foreground mb-0.5">股票数</div>
                          <div class="text-sm font-medium">{{ periodStat.stockCount }}</div>
                        </div>
                        <div>
                          <div class="text-xs text-muted-foreground mb-0.5">重复数</div>
                          <div class="text-sm font-medium text-blue-600 dark:text-blue-400">
                            {{ index === 0 ? '-' : periodStat.repeatCount || 0 }}
                          </div>
                        </div>
                        <div>
                          <div class="text-xs text-muted-foreground mb-0.5">投入资金</div>
                          <div class="text-sm font-medium">¥{{ formatNumber(periodStat.investment || 0) }}</div>
                        </div>
                        <div>
                          <div class="text-xs text-muted-foreground mb-0.5">额外投入</div>
                          <div class="text-sm font-medium text-orange-600 dark:text-orange-400">
                            ¥{{ formatNumber(periodStat.additionalInvestment || 0) }}
                          </div>
                        </div>
                        <div>
                          <div class="text-xs text-muted-foreground mb-0.5">收益</div>
                          <div class="text-sm font-medium" :class="periodStat.totalProfit >= 0 ? 'text-red-600 dark:text-red-400' : 'text-blue-600 dark:text-blue-400'">
                            {{ periodStat.totalProfit >= 0 ? '+' : '' }}¥{{ formatNumber(periodStat.totalProfit) }}
                          </div>
                        </div>
                        <div>
                          <div class="text-xs text-muted-foreground mb-0.5">收益率</div>
                          <div class="text-sm font-medium" :class="periodStat.returnRate >= 0 ? 'text-red-600 dark:text-red-400' : 'text-blue-600 dark:text-blue-400'">
                            {{ periodStat.returnRate >= 0 ? '+' : '' }}{{ formatPercent(periodStat.returnRate) }}%
                          </div>
                        </div>
                      </div>
                      <button
                        @click="togglePeriodExpanded(index)"
                        class="ml-2 px-2 py-1 rounded-md bg-secondary text-secondary-foreground hover:bg-secondary/80 transition-colors text-xs"
                      >
                        <i :class="[expandedPeriods.has(index) ? 'fas fa-chevron-up' : 'fas fa-chevron-down']"></i>
                      </button>
                    </div>
                  </div>
                  <!-- 股票详情（展开时显示） -->
                  <div v-show="expandedPeriods.has(index)" class="overflow-x-auto -mx-2 sm:mx-0">
                    <table class="w-full text-xs sm:text-sm">
                      <thead>
                        <tr class="border-b border-border bg-muted/30">
                          <th class="text-left p-2 sm:p-3 font-medium sticky left-0 bg-muted/30 z-10">股票代码</th>
                          <th class="text-left p-2 sm:p-3 font-medium sticky left-[100px] sm:left-[120px] bg-muted/30 z-10">股票名称</th>
                          <th class="text-left p-2 sm:p-3 font-medium">收益率</th>
                          <th class="text-left p-2 sm:p-3 font-medium">操作</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr 
                          v-for="(stock, stockIndex) in periodStat.stocks" 
                          :key="stockIndex"
                          class="border-b border-border/50 hover:bg-muted/30 transition-colors"
                        >
                          <td class="p-2 sm:p-3 font-mono sticky left-0 bg-background z-10 text-xs sm:text-sm">{{ stock.code }}</td>
                          <td class="p-2 sm:p-3 sticky left-[100px] sm:left-[120px] bg-background z-10 text-xs sm:text-sm">{{ stock.name }}</td>
                          <td class="p-2 sm:p-3 text-xs sm:text-sm">
                            <span v-if="stock.returnRate !== null && stock.returnRate !== undefined" 
                                  :class="[
                                    'px-1.5 sm:px-2 py-0.5 sm:py-1 rounded text-xs font-medium',
                                    stock.returnRate >= 0 
                                      ? 'bg-red-100 text-red-800' 
                                      : 'bg-green-100 text-green-800'
                                  ]">
                              {{ stock.returnRate >= 0 ? '+' : '' }}{{ stock.returnRate.toFixed(2) }}%
                            </span>
                            <span v-else class="text-muted-foreground text-xs sm:text-sm">-</span>
                          </td>
                          <td class="p-2 sm:p-3 text-xs sm:text-sm">
                            <button
                              @click.stop="goToStockCheck(stock, periodStat)"
                              class="px-2 py-1 text-xs rounded-md bg-primary text-primary-foreground hover:bg-primary/80 transition-colors flex items-center gap-1"
                              title="单股查询"
                            >
                              <i class="fas fa-search"></i>
                              <span class="hidden sm:inline">查询</span>
                            </button>
                          </td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div v-else-if="!allStocksDataLoaded" class="text-center py-8 flex-shrink-0">
            <i class="fas fa-info-circle text-2xl mb-2 text-muted-foreground"></i>
            <p class="text-muted-foreground text-sm">请先加载数据</p>
          </div>
        </div>
  
        <!-- 对话框底部 -->
        <div class="p-4 sm:p-6 border-t border-border flex justify-end gap-2">
          <button
            v-if="allStocksDataLoaded"
            @click="calculateStatistics"
            class="px-4 py-2 rounded-md bg-primary text-primary-foreground hover:bg-primary/80 transition-colors text-sm"
            :disabled="statisticsLoading || dataLoading"
          >
            <i v-if="statisticsLoading" class="fas fa-spinner fa-spin mr-1"></i>
            <i v-else class="fas fa-filter mr-1"></i>
            {{ statisticsLoading ? '筛选中...' : '筛选' }}
          </button>
        </div>
      </div>
    </div>
  </template>
  
<script setup>
import { ref, watch, computed } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { calculateTotalReturnRate } from '../utils/returnRateCalculator.js'
import {
  extractBoxRange,
  extractMaDiff,
  extractVolatility,
  extractLowPositionPercent,
  extractRapidDeclinePercent,
  extractPercentB
} from '../utils/selectionReasonsParser.js'
import { getStockBoard } from '../utils/stockBoardUtils.js'
import Slider from './ui/slider.vue'
  
const router = useRouter()
  
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
    boxQualityRange: { min: null, max: null }, // 箱体质量范围
    industries: [], // 选中的行业列表
    boards: ['创业板', '科创板', '主板'], // 选中的板块列表，默认选中所有板块
    boxRange: { min: null, max: null }, // 价格区间范围（min/max为null表示不限制）
    maDiffRange: { min: null, max: null }, // 均线收敛范围（min/max为null表示不限制）
    volatilityRange: { min: null, max: null }, // 波动率范围（min/max为null表示不限制）
    volumeChangeRange: { min: null, max: null }, // 成交量变化范围（min/max为null表示不限制）
    volumeStabilityRange: { min: null, max: null }, // 成交量稳定性范围（min/max为null表示不限制）
    lowPositionPercentRange: { min: null, max: null }, // 低位判断百分比范围（从高点下跌的百分比）
    rapidDeclinePercentRange: { min: null, max: null }, // 快速下跌百分比范围
    stockCountRange: { min: null, max: null }, // 周期内购买的股票数量范围
    turnoverRateRange: { min: null, max: null }, // 换手率范围（min/max为null表示不限制）
    outperformIndexRange: { min: null, max: null }, // 相对强度范围（min/max为null表示不限制）
    percentBRange: { min: null, max: null } // 布林极限 (%B) 范围（min/max为null表示不限制）
  })
  
  // 所有股票的属性集合（用于筛选条件选项）
  const allStockAttributes = ref({
    platformPeriods: new Set(), // 所有出现的平台期
    industries: new Set(), // 所有行业
    minBoxQuality: 1, // 最小箱体质量
    maxBoxQuality: 0, // 最大箱体质量
    minBoxRange: 0, // 最小价格区间
    maxBoxRange: 0, // 最大价格区间
    minMaDiff: 0, // 最小均线收敛
    maxMaDiff: 0, // 最大均线收敛
    minVolatility: 0, // 最小波动率
    maxVolatility: 0, // 最大波动率
    minVolumeChange: 0, // 最小成交量变化
    maxVolumeChange: 0, // 最大成交量变化
    minVolumeStability: 0, // 最小成交量稳定性
    maxVolumeStability: 0, // 最大成交量稳定性
    minLowPositionPercent: 0, // 最小低位判断百分比
    maxLowPositionPercent: 0, // 最大低位判断百分比
    minRapidDeclinePercent: 0, // 最小快速下跌百分比
    maxRapidDeclinePercent: 0, // 最大快速下跌百分比
    minStockCount: 0, // 最小股票数量
    maxStockCount: 0, // 最大股票数量
    minTurnoverRate: 0, // 最小换手率
    maxTurnoverRate: 0, // 最大换手率
    minOutperformIndex: undefined, // 最小相对强度
    maxOutperformIndex: undefined, // 最大相对强度
    minPercentB: 0, // 最小布林极限 (%B)
    maxPercentB: 1 // 最大布林极限 (%B)
  })

  // 价格区间数组（用于 shadcn-vue Slider 组件）
  const boxRangeArray = computed({
    get: () => {
      const min = statisticsFilters.value.boxRange.min ?? allStockAttributes.value.minBoxRange
      const max = statisticsFilters.value.boxRange.max ?? allStockAttributes.value.maxBoxRange
      return [min, max]
    },
    set: (value) => {
      if (Array.isArray(value) && value.length === 2) {
        statisticsFilters.value.boxRange = {
          min: value[0],
          max: value[1]
        }
      }
    }
  })

  // 均线收敛数组（用于 shadcn-vue Slider 组件）
  const maDiffRangeArray = computed({
    get: () => {
      const min = statisticsFilters.value.maDiffRange.min ?? allStockAttributes.value.minMaDiff
      const max = statisticsFilters.value.maDiffRange.max ?? allStockAttributes.value.maxMaDiff
      return [min, max]
    },
    set: (value) => {
      if (Array.isArray(value) && value.length === 2) {
        statisticsFilters.value.maDiffRange = {
          min: value[0],
          max: value[1]
        }
      }
    }
  })

  // 波动率数组（用于 shadcn-vue Slider 组件）
  const volatilityRangeArray = computed({
    get: () => {
      const min = statisticsFilters.value.volatilityRange.min ?? allStockAttributes.value.minVolatility
      const max = statisticsFilters.value.volatilityRange.max ?? allStockAttributes.value.maxVolatility
      return [min, max]
    },
    set: (value) => {
      if (Array.isArray(value) && value.length === 2) {
        statisticsFilters.value.volatilityRange = {
          min: value[0],
          max: value[1]
        }
      }
    }
  })

  // 成交量变化数组（用于 shadcn-vue Slider 组件）
  const volumeChangeRangeArray = computed({
    get: () => {
      const min = statisticsFilters.value.volumeChangeRange.min ?? allStockAttributes.value.minVolumeChange
      const max = statisticsFilters.value.volumeChangeRange.max ?? allStockAttributes.value.maxVolumeChange
      return [min, max]
    },
    set: (value) => {
      if (Array.isArray(value) && value.length === 2) {
        statisticsFilters.value.volumeChangeRange = {
          min: value[0],
          max: value[1]
        }
      }
    }
  })

  // 成交量稳定性数组（用于 shadcn-vue Slider 组件）
  const volumeStabilityRangeArray = computed({
    get: () => {
      const min = statisticsFilters.value.volumeStabilityRange.min ?? allStockAttributes.value.minVolumeStability
      const max = statisticsFilters.value.volumeStabilityRange.max ?? allStockAttributes.value.maxVolumeStability
      return [min, max]
    },
    set: (value) => {
      if (Array.isArray(value) && value.length === 2) {
        statisticsFilters.value.volumeStabilityRange = {
          min: value[0],
          max: value[1]
        }
      }
    }
  })

  // 低位判断百分比数组（用于 shadcn-vue Slider 组件）
  const lowPositionPercentRangeArray = computed({
    get: () => {
      const min = statisticsFilters.value.lowPositionPercentRange.min ?? allStockAttributes.value.minLowPositionPercent
      const max = statisticsFilters.value.lowPositionPercentRange.max ?? allStockAttributes.value.maxLowPositionPercent
      return [min, max]
    },
    set: (value) => {
      if (Array.isArray(value) && value.length === 2) {
        statisticsFilters.value.lowPositionPercentRange = {
          min: value[0],
          max: value[1]
        }
      }
    }
  })

  // 快速下跌百分比数组（用于 shadcn-vue Slider 组件）
  const rapidDeclinePercentRangeArray = computed({
    get: () => {
      const min = statisticsFilters.value.rapidDeclinePercentRange.min ?? allStockAttributes.value.minRapidDeclinePercent
      const max = statisticsFilters.value.rapidDeclinePercentRange.max ?? allStockAttributes.value.maxRapidDeclinePercent
      return [min, max]
    },
    set: (value) => {
      if (Array.isArray(value) && value.length === 2) {
        statisticsFilters.value.rapidDeclinePercentRange = {
          min: value[0],
          max: value[1]
        }
      }
    }
  })

  // 股票数量数组（用于 shadcn-vue Slider 组件）
  const stockCountRangeArray = computed({
    get: () => {
      const min = statisticsFilters.value.stockCountRange.min ?? allStockAttributes.value.minStockCount ?? 0
      const max = statisticsFilters.value.stockCountRange.max ?? allStockAttributes.value.maxStockCount ?? 0
      // 确保返回有效的数组
      if (min === null || max === null || isNaN(min) || isNaN(max) || min < 0 || max < 0) {
        return [0, 0]
      }
      return [min, max]
    },
    set: (value) => {
      if (Array.isArray(value) && value.length === 2) {
        statisticsFilters.value.stockCountRange = {
          min: value[0],
          max: value[1]
        }
      }
    }
  })

  // 换手率数组（用于 shadcn-vue Slider 组件）
  const turnoverRateRangeArray = computed({
    get: () => {
      const min = statisticsFilters.value.turnoverRateRange.min ?? allStockAttributes.value.minTurnoverRate
      const max = statisticsFilters.value.turnoverRateRange.max ?? allStockAttributes.value.maxTurnoverRate
      return [min, max]
    },
    set: (value) => {
      if (Array.isArray(value) && value.length === 2) {
        statisticsFilters.value.turnoverRateRange = {
          min: value[0],
          max: value[1]
        }
      }
    }
  })

  // 相对强度数组（用于 shadcn-vue Slider 组件）
  const outperformIndexRangeArray = computed({
    get: () => {
      const min = statisticsFilters.value.outperformIndexRange.min ?? allStockAttributes.value.minOutperformIndex
      const max = statisticsFilters.value.outperformIndexRange.max ?? allStockAttributes.value.maxOutperformIndex
      // 如果没有数据，返回默认值（但不会显示，因为 UI 会显示"暂无数据"）
      return [min ?? 0, max ?? 0]
    },
    set: (value) => {
      if (Array.isArray(value) && value.length === 2) {
        statisticsFilters.value.outperformIndexRange = {
          min: value[0],
          max: value[1]
        }
      }
    }
  })

  // 布林极限 (%B) 数组（用于 shadcn-vue Slider 组件）
  const percentBRangeArray = computed({
    get: () => {
      const min = statisticsFilters.value.percentBRange.min ?? allStockAttributes.value.minPercentB
      const max = statisticsFilters.value.percentBRange.max ?? allStockAttributes.value.maxPercentB
      return [min, max]
    },
    set: (value) => {
      if (Array.isArray(value) && value.length === 2) {
        statisticsFilters.value.percentBRange = {
          min: value[0],
          max: value[1]
        }
      }
    }
  })

  // 箱体质量数组（用于 shadcn-vue Slider 组件）
  const boxQualityRangeArray = computed({
    get: () => {
      const min = statisticsFilters.value.boxQualityRange.min ?? allStockAttributes.value.minBoxQuality
      const max = statisticsFilters.value.boxQualityRange.max ?? allStockAttributes.value.maxBoxQuality
      return [min, max]
    },
    set: (value) => {
      if (Array.isArray(value) && value.length === 2) {
        statisticsFilters.value.boxQualityRange = {
          min: value[0],
          max: value[1]
        }
      }
    }
  })
  
  // 完整数据缓存（不筛选的完整数据）
  const allStocksData = ref(null) // 存储所有股票的完整数据
  const allStocksDataLoaded = ref(false) // 是否已加载完整数据
  const dataLoading = ref(false) // 数据加载状态
  const expandedPeriods = ref(new Set()) // 展开的周期索引集合
  
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
  function formatPercent(num, decimals = 2) {
    if (num === null || num === undefined) return '0.00'
    return Number(num).toFixed(decimals)
  }


  // 解析函数已移至公共工具文件 src/utils/selectionReasonsParser.js

  // 判断是否是交易日（排除周末，不包括节假日）
  function isTradingDay(dateStr) {
    try {
      const date = new Date(dateStr)
      const weekday = date.getDay() // 0=周日, 1=周一, ..., 6=周六
      return weekday >= 1 && weekday <= 5 // 周一到周五是交易日
    } catch (e) {
      return false
    }
  }

  // 计算两个日期之间的交易日数量
  function countTradingDays(startDateStr, endDateStr) {
    try {
      const startDate = new Date(startDateStr)
      const endDate = new Date(endDateStr)
      
      if (startDate > endDate) {
        return 0
      }
      
      let tradingDays = 0
      const currentDate = new Date(startDate)
      
      // 遍历从开始日期到结束日期的每一天
      while (currentDate <= endDate) {
        if (isTradingDay(currentDate.toISOString().split('T')[0])) {
          tradingDays++
        }
        currentDate.setDate(currentDate.getDate() + 1)
      }
      
      return Math.max(1, tradingDays) // 至少返回1，避免除零错误
    } catch (e) {
      // 如果计算失败，返回日历天数作为后备
      const startDate = new Date(startDateStr)
      const endDate = new Date(endDateStr)
      const daysDiff = Math.max(1, Math.ceil((endDate - startDate) / (1000 * 60 * 60 * 24)))
      return daysDiff
    }
  }
  
  // 切换周期展开状态
  function togglePeriodExpanded(index) {
    if (expandedPeriods.value.has(index)) {
      expandedPeriods.value.delete(index)
    } else {
      expandedPeriods.value.add(index)
    }
  }
  
  // 跳转到单股检查页面
  function goToStockCheck(stock, periodStat) {
    const query = {
      code: stock.code
    }
    
    // 从周期统计中获取回测日期（从第一个记录中获取）
    if (periodStat && periodStat.records && periodStat.records.length > 0) {
      const firstRecord = periodStat.records[0]
      if (firstRecord && firstRecord.scanDate) {
        query.date = firstRecord.scanDate
      } else if (firstRecord && firstRecord.record && firstRecord.record.config && firstRecord.record.config.backtest_date) {
        query.date = firstRecord.record.config.backtest_date
      }
    }
    
    router.push({
      path: '/platform/check',
      query: query
    })
  }
  
  // 判断是否是批量统计（有周期概率）
  function isBatchStatistics(records) {
    // 检查是否有周期概率字段，或者检查配置中是否有批量统计相关的字段
    for (const record of records) {
      const config = record.config || {}
      // 如果有周期概率相关的配置，认为是批量统计
      if (config.period_probabilities || config.batch_statistics) {
        return true
      }
    }
    return false
  }
  
  // 按回测统计日划分周期
  function groupByWeek(records) {
    const statDateGroups = {}
    records.forEach(record => {
      // 获取回测统计日期（stat_date）
      const statDate = record.record?.config?.stat_date
      if (!statDate) {
        // 如果没有统计日期，使用回测日期作为后备
        const scanDate = record.scanDate || record.record?.config?.backtest_date
        if (!scanDate) return
        
        const date = new Date(scanDate)
        const dateKey = date.toISOString().split('T')[0]
        const dateLabel = `${date.getFullYear()}年${date.getMonth() + 1}月${date.getDate()}日`
        
        if (!statDateGroups[dateKey]) {
          statDateGroups[dateKey] = {
            label: dateLabel,
            records: []
          }
        }
        statDateGroups[dateKey].records.push(record)
        return
      }
      
      // 使用统计日期作为周期标识
      const date = new Date(statDate)
      const dateKey = date.toISOString().split('T')[0]
      const dateLabel = `${date.getFullYear()}年${date.getMonth() + 1}月${date.getDate()}日`
      
      if (!statDateGroups[dateKey]) {
        statDateGroups[dateKey] = {
          label: dateLabel,
          records: []
        }
      }
      statDateGroups[dateKey].records.push(record)
    })
    
    return Object.keys(statDateGroups).sort().map(dateKey => ({
      periodLabel: statDateGroups[dateKey].label,
      records: statDateGroups[dateKey].records
    }))
  }
  
  // 按周期分组（如果有周期概率，使用周期概率；否则按星期分组）
  function groupByPeriod(records) {
    // 获取原始记录列表用于判断是否是批量统计
    const originalRecords = records.map(r => r.record).filter(r => r)
    if (isBatchStatistics(originalRecords)) {
      // 批量统计：按周期概率分组
      const periodGroups = {}
      records.forEach(record => {
        const config = record.record?.config || {}
        const period = config.period || config.period_probability || '未知周期'
        if (!periodGroups[period]) {
          periodGroups[period] = []
        }
        periodGroups[period].push(record)
      })
      
      return Object.keys(periodGroups).sort().map(period => ({
        periodLabel: `周期 ${period}`,
        records: periodGroups[period]
      }))
    } else {
      // 非批量统计：按星期分组
      return groupByWeek(records)
    }
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
              outperform_index: stockDetails?.outperform_index !== undefined ? stockDetails.outperform_index : (stock.outperform_index !== undefined ? stock.outperform_index : null),
              stock_return: stockDetails?.stock_return !== undefined ? stockDetails.stock_return : (stock.stock_return !== undefined ? stock.stock_return : null),
              market_return: stockDetails?.market_return !== undefined ? stockDetails.market_return : (stock.market_return !== undefined ? stock.market_return : null),
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
              outperform_index: stockDetails?.outperform_index !== undefined ? stockDetails.outperform_index : null,
              stock_return: stockDetails?.stock_return !== undefined ? stockDetails.stock_return : null,
              market_return: stockDetails?.market_return !== undefined ? stockDetails.market_return : null,
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
      const boxRanges = []
      const maDiffs = []
      const volatilities = []
      const volumeChanges = []
      const volumeStabilities = []
      const turnoverRates = []
      const outperformIndices = []
      const lowPositionPercents = []
      const rapidDeclinePercents = []
      const percentBs = []

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

        // 收集价格区间、均线收敛、波动率、低位百分比、快速下跌百分比（从 selection_reasons 中解析）
        if (stock.selection_reasons) {
          const boxRange = extractBoxRange(stock.selection_reasons)
          if (boxRange !== null) {
            boxRanges.push(boxRange)
          }
          const maDiff = extractMaDiff(stock.selection_reasons)
          if (maDiff !== null) {
            maDiffs.push(maDiff)
          }
          const volatility = extractVolatility(stock.selection_reasons)
          if (volatility !== null) {
            volatilities.push(volatility)
          }
          const lowPositionPercent = extractLowPositionPercent(stock.selection_reasons)
          if (lowPositionPercent !== null) {
            lowPositionPercents.push(lowPositionPercent)
          }
          const rapidDeclinePercent = extractRapidDeclinePercent(stock.selection_reasons)
          if (rapidDeclinePercent !== null) {
            rapidDeclinePercents.push(rapidDeclinePercent)
          }
        }

        // 收集成交量变化和成交量稳定性（从 volume_analysis 中提取）
        if (stock.volume_analysis && typeof stock.volume_analysis === 'object') {
          // 使用 Object.entries 来获取窗口期信息
          Object.entries(stock.volume_analysis).forEach(([window, windowAnalysis]) => {
            if (windowAnalysis && typeof windowAnalysis === 'object') {
              // 从 consolidation_details 中提取（新格式）
              if (windowAnalysis.consolidation_details && typeof windowAnalysis.consolidation_details === 'object') {
                const volumeChangeRatio = windowAnalysis.consolidation_details.volume_change_ratio
                const volumeStability = windowAnalysis.consolidation_details.volume_stability
                
                // 打印日志（显示窗口期信息）
                const stockInfo = `${stock.code || 'N/A'} ${stock.name || 'N/A'}`
                const windowInfo = `[${window}天]`
                if (volumeChangeRatio !== null && volumeChangeRatio !== undefined && typeof volumeChangeRatio === 'number') {
                  if (volumeChangeRatio > 0.5) {
                    console.log(`%c[成交量变化] ${stockInfo} ${windowInfo}: ${volumeChangeRatio.toFixed(4)}`, 'color: red; font-weight: bold')
                  } else {
                    console.log(`[成交量变化] ${stockInfo} ${windowInfo}: ${volumeChangeRatio.toFixed(4)}`)
                  }
                }
                if (volumeStability !== null && volumeStability !== undefined && typeof volumeStability === 'number') {
                  if (volumeStability > 0.5) {
                    console.log(`%c[成交量稳定性] ${stockInfo} ${windowInfo}: ${volumeStability.toFixed(4)}`, 'color: red; font-weight: bold')
                  } else {
                    console.log(`[成交量稳定性] ${stockInfo} ${windowInfo}: ${volumeStability.toFixed(4)}`)
                  }
                }
                
                // 检查 volume_change_ratio：必须是正数、有限值，且合理范围（0.01 到 100）
                if (volumeChangeRatio !== null && volumeChangeRatio !== undefined && typeof volumeChangeRatio === 'number' && !isNaN(volumeChangeRatio) && isFinite(volumeChangeRatio) && volumeChangeRatio > 0 && volumeChangeRatio <= 100) {
                  volumeChanges.push(volumeChangeRatio)
                }
                // 检查 volume_stability：必须是非负数、有限值，且合理范围（0 到 10）
                if (volumeStability !== null && volumeStability !== undefined && typeof volumeStability === 'number' && !isNaN(volumeStability) && isFinite(volumeStability) && volumeStability >= 0 && volumeStability <= 10) {
                  volumeStabilities.push(volumeStability)
                }
              }
            }
          })
        }
        // 从 details 中提取（兼容旧数据格式）
        // details[window].volume_analysis 可能直接就是 consolidation_details 的内容
        // 注意：如果 volume_analysis 中已有数据，则不再从 details 中提取，避免重复
        if ((!stock.volume_analysis || Object.keys(stock.volume_analysis).length === 0) && stock.details && typeof stock.details === 'object') {
          Object.entries(stock.details).forEach(([window, windowDetail]) => {
            if (windowDetail && typeof windowDetail === 'object') {
              // 方式1：details[window].volume_analysis 直接包含 volume_change_ratio 和 volume_stability
              if (windowDetail.volume_analysis && typeof windowDetail.volume_analysis === 'object') {
                const volumeChangeRatio = windowDetail.volume_analysis.volume_change_ratio
                const volumeStability = windowDetail.volume_analysis.volume_stability
                
                // 打印日志（旧格式，显示窗口期信息）
                const stockInfo = `${stock.code || 'N/A'} ${stock.name || 'N/A'}`
                const windowInfo = `[${window}天]`
                if (volumeChangeRatio !== null && volumeChangeRatio !== undefined && typeof volumeChangeRatio === 'number') {
                  if (volumeChangeRatio > 0.5) {
                    console.log(`%c[成交量变化-旧格式] ${stockInfo} ${windowInfo}: ${volumeChangeRatio.toFixed(4)}`, 'color: red; font-weight: bold')
                  } else {
                    console.log(`[成交量变化-旧格式] ${stockInfo} ${windowInfo}: ${volumeChangeRatio.toFixed(4)}`)
                  }
                }
                if (volumeStability !== null && volumeStability !== undefined && typeof volumeStability === 'number') {
                  if (volumeStability > 0.5) {
                    console.log(`%c[成交量稳定性-旧格式] ${stockInfo} ${windowInfo}: ${volumeStability.toFixed(4)}`, 'color: red; font-weight: bold')
                  } else {
                    console.log(`[成交量稳定性-旧格式] ${stockInfo} ${windowInfo}: ${volumeStability.toFixed(4)}`)
                  }
                }
                
                // 检查 volume_change_ratio：必须是正数、有限值，且合理范围（0.01 到 100）
                if (volumeChangeRatio !== null && volumeChangeRatio !== undefined && typeof volumeChangeRatio === 'number' && !isNaN(volumeChangeRatio) && isFinite(volumeChangeRatio) && volumeChangeRatio > 0 && volumeChangeRatio <= 100) {
                  volumeChanges.push(volumeChangeRatio)
                }
                // 检查 volume_stability：必须是非负数、有限值，且合理范围（0 到 10）
                if (volumeStability !== null && volumeStability !== undefined && typeof volumeStability === 'number' && !isNaN(volumeStability) && isFinite(volumeStability) && volumeStability >= 0 && volumeStability <= 10) {
                  volumeStabilities.push(volumeStability)
                }
              }
            }
          })
        }
        
        // 收集换手率数据
        // 从 turnover_analysis 中提取（如果后端返回了）
        if (stock.turnover_analysis && typeof stock.turnover_analysis === 'object') {
          Object.values(stock.turnover_analysis).forEach(windowAnalysis => {
            if (windowAnalysis && typeof windowAnalysis === 'object') {
              const avgTurnoverRate = windowAnalysis.avg_turnover_rate
              if (avgTurnoverRate !== null && avgTurnoverRate !== undefined && typeof avgTurnoverRate === 'number' && !isNaN(avgTurnoverRate) && isFinite(avgTurnoverRate) && avgTurnoverRate >= 0) {
                turnoverRates.push(avgTurnoverRate)
              }
            }
          })
        }
        
        // 如果没有，从kline_data中计算
        // 注意：需要排除最近5天，与后端逻辑保持一致（避免突破期的放量干扰平台期判断）
        if ((!stock.turnover_analysis || Object.keys(stock.turnover_analysis).length === 0) && stock.kline_data && Array.isArray(stock.kline_data) && stock.kline_data.length > 0) {
          // 获取所有窗口期的换手率
          const windows = Array.from(platformPeriodsSet)
          const excludeRecentDays = 5 // 排除最近5天，与后端逻辑一致
          
          windows.forEach(window => {
            const windowDays = parseInt(window)
            if (!isNaN(windowDays) && windowDays > 0) {
              // 确保有足够的数据
              if (stock.kline_data.length < windowDays) {
                return
              }
              
              // 获取平台期数据（排除最近5天）
              let platformData
              if (excludeRecentDays > 0 && stock.kline_data.length > windowDays) {
                // 排除最近5天：从倒数第windowDays天到倒数第excludeRecentDays天
                platformData = stock.kline_data.slice(-windowDays, -excludeRecentDays)
              } else {
                // 如果数据不足，使用全部数据
                platformData = stock.kline_data.slice(-windowDays)
              }
              
              const windowTurnoverRates = platformData
                .map(item => item.turn)
                .filter(turn => turn !== null && turn !== undefined && !isNaN(turn) && turn >= 0 && turn <= 100)
              
              if (windowTurnoverRates.length > 0) {
                const avgTurnoverRate = windowTurnoverRates.reduce((sum, rate) => sum + rate, 0) / windowTurnoverRates.length
                turnoverRates.push(avgTurnoverRate)
              }
            }
          })
        }
        
        // 收集相对强度数据
        if (stock.outperform_index !== null && stock.outperform_index !== undefined && typeof stock.outperform_index === 'number' && !isNaN(stock.outperform_index) && isFinite(stock.outperform_index)) {
          outperformIndices.push(stock.outperform_index)
        }
        
        // 收集布林极限 (%B) 数据
        const percentB = extractPercentB(stock)
        if (percentB !== null && typeof percentB === 'number' && !isNaN(percentB) && isFinite(percentB)) {
          percentBs.push(percentB)
        }
      })

      // 更新属性集合
      allStockAttributes.value.platformPeriods = platformPeriodsSet
      allStockAttributes.value.industries = industriesSet
      if (boxQualities.length > 0) {
        allStockAttributes.value.minBoxQuality = Math.min(...boxQualities)
        allStockAttributes.value.maxBoxQuality = Math.max(...boxQualities)
        // 如果 boxQualityRange 未设置，默认设置为最小值和最大值（默认启用，不筛选）
        if (statisticsFilters.value.boxQualityRange.min === null || statisticsFilters.value.boxQualityRange.max === null) {
          statisticsFilters.value.boxQualityRange = {
            min: allStockAttributes.value.minBoxQuality,
            max: allStockAttributes.value.maxBoxQuality
          }
        }
      }
      if (boxRanges.length > 0) {
        allStockAttributes.value.minBoxRange = Math.min(...boxRanges)
        allStockAttributes.value.maxBoxRange = Math.max(...boxRanges)
        // 如果 boxRange 未设置，默认设置为最小值和最大值（默认启用，不筛选）
        if (statisticsFilters.value.boxRange.min === null || statisticsFilters.value.boxRange.max === null) {
          statisticsFilters.value.boxRange = {
            min: allStockAttributes.value.minBoxRange,
            max: allStockAttributes.value.maxBoxRange
          }
        }
      }
      if (maDiffs.length > 0) {
        allStockAttributes.value.minMaDiff = Math.min(...maDiffs)
        allStockAttributes.value.maxMaDiff = Math.max(...maDiffs)
        // 如果 maDiffRange 未设置，默认设置为最小值和最大值（默认启用，不筛选）
        if (statisticsFilters.value.maDiffRange.min === null || statisticsFilters.value.maDiffRange.max === null) {
          statisticsFilters.value.maDiffRange = {
            min: allStockAttributes.value.minMaDiff,
            max: allStockAttributes.value.maxMaDiff
          }
        }
      }
      if (volatilities.length > 0) {
        allStockAttributes.value.minVolatility = Math.min(...volatilities)
        allStockAttributes.value.maxVolatility = Math.max(...volatilities)
        // 如果 volatilityRange 未设置，默认设置为最小值和最大值（默认启用，不筛选）
        if (statisticsFilters.value.volatilityRange.min === null || statisticsFilters.value.volatilityRange.max === null) {
          statisticsFilters.value.volatilityRange = {
            min: allStockAttributes.value.minVolatility,
            max: allStockAttributes.value.maxVolatility
          }
        }
      }
      if (volumeChanges.length > 0) {
        // 过滤掉异常值：volume_change_ratio 通常在 0.01 到 100 之间
        const validVolumeChanges = volumeChanges.filter(v => v > 0 && v <= 100)
        if (validVolumeChanges.length > 0) {
          allStockAttributes.value.minVolumeChange = Math.min(...validVolumeChanges)
          allStockAttributes.value.maxVolumeChange = Math.max(...validVolumeChanges)
          // 打印汇总信息
          console.log(`%c[成交量变化汇总] 总数: ${validVolumeChanges.length}, 最小值: ${allStockAttributes.value.minVolumeChange.toFixed(4)}, 最大值: ${allStockAttributes.value.maxVolumeChange.toFixed(4)}`, 'color: blue; font-weight: bold')
          // 如果 volumeChangeRange 未设置，默认设置为最小值和最大值（默认启用，不筛选）
          if (statisticsFilters.value.volumeChangeRange.min === null || statisticsFilters.value.volumeChangeRange.max === null) {
            statisticsFilters.value.volumeChangeRange = {
              min: allStockAttributes.value.minVolumeChange,
              max: allStockAttributes.value.maxVolumeChange
            }
          }
        } else {
          // 如果过滤后没有有效数据，设置为默认值
          allStockAttributes.value.minVolumeChange = 0
          allStockAttributes.value.maxVolumeChange = 1
          if (statisticsFilters.value.volumeChangeRange.min === null || statisticsFilters.value.volumeChangeRange.max === null) {
            statisticsFilters.value.volumeChangeRange = {
              min: 0,
              max: 1
            }
          }
        }
      } else {
        // 如果没有数据，设置为默认值，避免筛选逻辑出错
        allStockAttributes.value.minVolumeChange = 0
        allStockAttributes.value.maxVolumeChange = 1
        if (statisticsFilters.value.volumeChangeRange.min === null || statisticsFilters.value.volumeChangeRange.max === null) {
          statisticsFilters.value.volumeChangeRange = {
            min: 0,
            max: 1
          }
        }
      }
      if (volumeStabilities.length > 0) {
        // 过滤掉异常值：volume_stability 通常在 0 到 10 之间（变异系数）
        const validVolumeStabilities = volumeStabilities.filter(v => v >= 0 && v <= 10)
        if (validVolumeStabilities.length > 0) {
          allStockAttributes.value.minVolumeStability = Math.min(...validVolumeStabilities)
          allStockAttributes.value.maxVolumeStability = Math.max(...validVolumeStabilities)
          // 打印汇总信息
          console.log(`%c[成交量稳定性汇总] 总数: ${validVolumeStabilities.length}, 最小值: ${allStockAttributes.value.minVolumeStability.toFixed(4)}, 最大值: ${allStockAttributes.value.maxVolumeStability.toFixed(4)}`, 'color: blue; font-weight: bold')
          // 如果 volumeStabilityRange 未设置，默认设置为最小值和最大值（默认启用，不筛选）
          if (statisticsFilters.value.volumeStabilityRange.min === null || statisticsFilters.value.volumeStabilityRange.max === null) {
            statisticsFilters.value.volumeStabilityRange = {
              min: allStockAttributes.value.minVolumeStability,
              max: allStockAttributes.value.maxVolumeStability
            }
          }
        } else {
          // 如果过滤后没有有效数据，设置为默认值
          allStockAttributes.value.minVolumeStability = 0
          allStockAttributes.value.maxVolumeStability = 1
          if (statisticsFilters.value.volumeStabilityRange.min === null || statisticsFilters.value.volumeStabilityRange.max === null) {
            statisticsFilters.value.volumeStabilityRange = {
              min: 0,
              max: 1
            }
          }
        }
      } else {
        // 如果没有数据，设置为默认值，避免筛选逻辑出错
        allStockAttributes.value.minVolumeStability = 0
        allStockAttributes.value.maxVolumeStability = 1
        if (statisticsFilters.value.volumeStabilityRange.min === null || statisticsFilters.value.volumeStabilityRange.max === null) {
          statisticsFilters.value.volumeStabilityRange = {
            min: 0,
            max: 1
          }
        }
      }
      if (turnoverRates.length > 0) {
        // 过滤掉异常值：换手率通常在 0 到 100 之间
        const validTurnoverRates = turnoverRates.filter(v => v >= 0 && v <= 100)
        if (validTurnoverRates.length > 0) {
          allStockAttributes.value.minTurnoverRate = Math.min(...validTurnoverRates)
          allStockAttributes.value.maxTurnoverRate = Math.max(...validTurnoverRates)
          // 如果 turnoverRateRange 未设置，默认设置为最小值和最大值（默认启用，不筛选）
          if (statisticsFilters.value.turnoverRateRange.min === null || statisticsFilters.value.turnoverRateRange.max === null) {
            statisticsFilters.value.turnoverRateRange = {
              min: allStockAttributes.value.minTurnoverRate,
              max: allStockAttributes.value.maxTurnoverRate
            }
          }
        } else {
          // 如果过滤后没有有效数据，设置为默认值
          allStockAttributes.value.minTurnoverRate = 0
          allStockAttributes.value.maxTurnoverRate = 10
          if (statisticsFilters.value.turnoverRateRange.min === null || statisticsFilters.value.turnoverRateRange.max === null) {
            statisticsFilters.value.turnoverRateRange = {
              min: 0,
              max: 10
            }
          }
        }
      } else {
        // 如果没有数据，设置为默认值，避免筛选逻辑出错
        allStockAttributes.value.minTurnoverRate = 0
        allStockAttributes.value.maxTurnoverRate = 10
        if (statisticsFilters.value.turnoverRateRange.min === null || statisticsFilters.value.turnoverRateRange.max === null) {
          statisticsFilters.value.turnoverRateRange = {
            min: 0,
            max: 10
          }
        }
      }
      if (outperformIndices.length > 0) {
        allStockAttributes.value.minOutperformIndex = Math.min(...outperformIndices)
        allStockAttributes.value.maxOutperformIndex = Math.max(...outperformIndices)
        // 如果 outperformIndexRange 未设置，默认设置为最小值和最大值（默认启用，不筛选）
        if (statisticsFilters.value.outperformIndexRange.min === null || statisticsFilters.value.outperformIndexRange.max === null) {
          statisticsFilters.value.outperformIndexRange = {
            min: allStockAttributes.value.minOutperformIndex,
            max: allStockAttributes.value.maxOutperformIndex
          }
        }
      } else {
        // 如果没有数据，不设置默认值，保持为 undefined
        allStockAttributes.value.minOutperformIndex = undefined
        allStockAttributes.value.maxOutperformIndex = undefined
        // 如果没有数据，清空筛选范围
        statisticsFilters.value.outperformIndexRange = {
          min: null,
          max: null
        }
      }
      if (lowPositionPercents.length > 0) {
        allStockAttributes.value.minLowPositionPercent = Math.min(...lowPositionPercents)
        allStockAttributes.value.maxLowPositionPercent = Math.max(...lowPositionPercents)
        // 如果 lowPositionPercentRange 未设置，默认设置为最小值和最大值（默认启用，不筛选）
        if (statisticsFilters.value.lowPositionPercentRange.min === null || statisticsFilters.value.lowPositionPercentRange.max === null) {
          statisticsFilters.value.lowPositionPercentRange = {
            min: allStockAttributes.value.minLowPositionPercent,
            max: allStockAttributes.value.maxLowPositionPercent
          }
        }
      }
      if (rapidDeclinePercents.length > 0) {
        allStockAttributes.value.minRapidDeclinePercent = Math.min(...rapidDeclinePercents)
        allStockAttributes.value.maxRapidDeclinePercent = Math.max(...rapidDeclinePercents)
        // 如果 rapidDeclinePercentRange 未设置，默认设置为最小值和最大值（默认启用，不筛选）
        if (statisticsFilters.value.rapidDeclinePercentRange.min === null || statisticsFilters.value.rapidDeclinePercentRange.max === null) {
          statisticsFilters.value.rapidDeclinePercentRange = {
            min: allStockAttributes.value.minRapidDeclinePercent,
            max: allStockAttributes.value.maxRapidDeclinePercent
          }
        }
      }
      if (percentBs.length > 0) {
        allStockAttributes.value.minPercentB = Math.min(...percentBs)
        allStockAttributes.value.maxPercentB = Math.max(...percentBs)
        // 如果 percentBRange 未设置，默认设置为最小值和最大值（默认启用，不筛选）
        if (statisticsFilters.value.percentBRange.min === null || statisticsFilters.value.percentBRange.max === null) {
          statisticsFilters.value.percentBRange = {
            min: allStockAttributes.value.minPercentB,
            max: allStockAttributes.value.maxPercentB
          }
        }
      } else {
        // 如果没有数据，设置为默认值（0-1）
        allStockAttributes.value.minPercentB = 0
        allStockAttributes.value.maxPercentB = 1
        if (statisticsFilters.value.percentBRange.min === null || statisticsFilters.value.percentBRange.max === null) {
          statisticsFilters.value.percentBRange = {
            min: 0,
            max: 1
          }
        }
      }
      
      return {
        allStocks,
        selectedRecords
      }
  }
  
  // 检查是否有筛选条件被应用
  function hasFiltersApplied() {
    const filters = statisticsFilters.value
    const maxBoxRange = allStockAttributes.value.maxBoxRange
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
      (filters.boxQualityRange.min !== null && filters.boxQualityRange.max !== null && 
       (filters.boxQualityRange.min > allStockAttributes.value.minBoxQuality || 
        filters.boxQualityRange.max < allStockAttributes.value.maxBoxQuality)) ||
      filters.industries.length > 0 ||
      filters.boards.length > 0 ||
      (filters.boxRange.min !== null && filters.boxRange.max !== null && 
       (filters.boxRange.min > allStockAttributes.value.minBoxRange || 
        filters.boxRange.max < allStockAttributes.value.maxBoxRange)) ||
      (filters.maDiffRange.min !== null && filters.maDiffRange.max !== null && 
       (filters.maDiffRange.min > allStockAttributes.value.minMaDiff || 
        filters.maDiffRange.max < allStockAttributes.value.maxMaDiff)) ||
      (filters.volatilityRange.min !== null && filters.volatilityRange.max !== null && 
       (filters.volatilityRange.min > allStockAttributes.value.minVolatility || 
        filters.volatilityRange.max < allStockAttributes.value.maxVolatility)) ||
      (filters.volumeChangeRange.min !== null && filters.volumeChangeRange.max !== null && 
       (filters.volumeChangeRange.min > allStockAttributes.value.minVolumeChange || 
        filters.volumeChangeRange.max < allStockAttributes.value.maxVolumeChange)) ||
      (filters.volumeStabilityRange.min !== null && filters.volumeStabilityRange.max !== null && 
       (filters.volumeStabilityRange.min > allStockAttributes.value.minVolumeStability || 
        filters.volumeStabilityRange.max < allStockAttributes.value.maxVolumeStability)) ||
      (filters.lowPositionPercentRange.min !== null && filters.lowPositionPercentRange.max !== null && 
       (filters.lowPositionPercentRange.min > allStockAttributes.value.minLowPositionPercent || 
        filters.lowPositionPercentRange.max < allStockAttributes.value.maxLowPositionPercent)) ||
      (filters.rapidDeclinePercentRange.min !== null && filters.rapidDeclinePercentRange.max !== null && 
       (filters.rapidDeclinePercentRange.min > allStockAttributes.value.minRapidDeclinePercent || 
        filters.rapidDeclinePercentRange.max < allStockAttributes.value.maxRapidDeclinePercent)) ||
      (filters.stockCountRange.min !== null && filters.stockCountRange.max !== null && 
       (filters.stockCountRange.min > allStockAttributes.value.minStockCount || 
        filters.stockCountRange.max < allStockAttributes.value.maxStockCount)) ||
      (filters.turnoverRateRange.min !== null && filters.turnoverRateRange.max !== null && 
       (filters.turnoverRateRange.min > allStockAttributes.value.minTurnoverRate || 
        filters.turnoverRateRange.max < allStockAttributes.value.maxTurnoverRate)) ||
      (filters.outperformIndexRange.min !== null && filters.outperformIndexRange.max !== null && 
       allStockAttributes.value.minOutperformIndex !== undefined && allStockAttributes.value.maxOutperformIndex !== undefined &&
       (filters.outperformIndexRange.min > allStockAttributes.value.minOutperformIndex || 
        filters.outperformIndexRange.max < allStockAttributes.value.maxOutperformIndex)) ||
      (filters.percentBRange.min !== null && filters.percentBRange.max !== null && 
       (filters.percentBRange.min > allStockAttributes.value.minPercentB || 
        filters.percentBRange.max < allStockAttributes.value.maxPercentB)) ||
      (filters.boxQualityRange.min !== null && filters.boxQualityRange.max !== null && 
       (filters.boxQualityRange.min > allStockAttributes.value.minBoxQuality || 
        filters.boxQualityRange.max < allStockAttributes.value.maxBoxQuality))
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
      boxQualityRange: { min: null, max: null },
      industries: [],
      boxRange: { min: null, max: null },
      maDiffRange: { min: null, max: null },
      volatilityRange: { min: null, max: null },
      volumeChangeRange: { min: null, max: null },
      volumeStabilityRange: { min: null, max: null },
      lowPositionPercentRange: { min: null, max: null },
      rapidDeclinePercentRange: { min: null, max: null },
      stockCountRange: { min: null, max: null }
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

        // 板块筛选
        if (statisticsFilters.value.boards.length > 0) {
          const stockBoard = getStockBoard(stock.code)
          if (!stockBoard) {
            // 无法识别板块，排除股票
            return false
          }
          if (!statisticsFilters.value.boards.includes(stockBoard)) {
            return false
          }
        }

        // 箱体质量筛选
        const boxQualityRangeFilter = statisticsFilters.value.boxQualityRange
        if (boxQualityRangeFilter.min !== null && boxQualityRangeFilter.max !== null) {
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
          
          // 如果股票没有箱体质量数据，排除该股票（因为用户明确选择了筛选条件）
          if (!hasBoxQualityData) {
            return false
          }
          
          // 检查是否在范围内（只有当范围不是默认的全范围时才筛选）
          const minBoxQuality = allStockAttributes.value.minBoxQuality
          const maxBoxQuality = allStockAttributes.value.maxBoxQuality
          if (boxQualityRangeFilter.min > minBoxQuality || boxQualityRangeFilter.max < maxBoxQuality) {
            if (stockBoxQuality < boxQualityRangeFilter.min || stockBoxQuality > boxQualityRangeFilter.max) {
              return false
            }
          }
        }

        // 价格区间筛选
        const boxRangeFilter = statisticsFilters.value.boxRange
        if (boxRangeFilter.min !== null && boxRangeFilter.max !== null) {
          const stockBoxRange = extractBoxRange(stock.selection_reasons)
          if (stockBoxRange === null) {
            // 没有数据，排除股票（因为用户明确选择了筛选条件）
            return false
          } else {
            // 检查是否在范围内（只有当范围不是默认的全范围时才筛选）
            const minBoxRange = allStockAttributes.value.minBoxRange
            const maxBoxRange = allStockAttributes.value.maxBoxRange
            // 只有当用户设置的范围比全范围更窄时才进行筛选
            if (boxRangeFilter.min > minBoxRange || boxRangeFilter.max < maxBoxRange) {
              if (stockBoxRange < boxRangeFilter.min || stockBoxRange > boxRangeFilter.max) {
                return false
              }
            }
            // 如果用户设置的范围等于全范围，不进行筛选（所有股票都通过）
          }
        }

        // 均线收敛筛选
        const maDiffRangeFilter = statisticsFilters.value.maDiffRange
        if (maDiffRangeFilter.min !== null && maDiffRangeFilter.max !== null) {
          const stockMaDiff = extractMaDiff(stock.selection_reasons)
          if (stockMaDiff === null) {
            // 没有数据，排除股票（因为用户明确选择了筛选条件）
            return false
          } else {
            // 检查是否在范围内（只有当范围不是默认的全范围时才筛选）
            const minMaDiff = allStockAttributes.value.minMaDiff
            const maxMaDiff = allStockAttributes.value.maxMaDiff
            // 只有当用户设置的范围比全范围更窄时才进行筛选
            if (maDiffRangeFilter.min > minMaDiff || maDiffRangeFilter.max < maxMaDiff) {
              if (stockMaDiff < maDiffRangeFilter.min || stockMaDiff > maDiffRangeFilter.max) {
                return false
              }
            }
            // 如果用户设置的范围等于全范围，不进行筛选（所有股票都通过）
          }
        }

        // 波动率筛选
        const volatilityRangeFilter = statisticsFilters.value.volatilityRange
        if (volatilityRangeFilter.min !== null && volatilityRangeFilter.max !== null) {
          const stockVolatility = extractVolatility(stock.selection_reasons)
          if (stockVolatility === null) {
            // 没有数据，排除股票（因为用户明确选择了筛选条件）
            return false
          } else {
            // 检查是否在范围内（只有当范围不是默认的全范围时才筛选）
            const minVolatility = allStockAttributes.value.minVolatility
            const maxVolatility = allStockAttributes.value.maxVolatility
            // 只有当用户设置的范围比全范围更窄时才进行筛选
            if (volatilityRangeFilter.min > minVolatility || volatilityRangeFilter.max < maxVolatility) {
              if (stockVolatility < volatilityRangeFilter.min || stockVolatility > volatilityRangeFilter.max) {
                return false
              }
            }
            // 如果用户设置的范围等于全范围，不进行筛选（所有股票都通过）
          }
        }

        // 成交量变化筛选
        const volumeChangeRangeFilter = statisticsFilters.value.volumeChangeRange
        if (volumeChangeRangeFilter.min !== null && volumeChangeRangeFilter.max !== null) {
          let stockVolumeChange = null
          let hasVolumeChangeData = false
          
          // 从 volume_analysis 中提取（新格式）
          if (stock.volume_analysis && typeof stock.volume_analysis === 'object') {
            Object.values(stock.volume_analysis).forEach(windowAnalysis => {
              if (windowAnalysis && typeof windowAnalysis === 'object') {
                if (windowAnalysis.consolidation_details && typeof windowAnalysis.consolidation_details === 'object') {
                  const volumeChangeRatio = windowAnalysis.consolidation_details.volume_change_ratio
                  if (volumeChangeRatio !== null && volumeChangeRatio !== undefined && typeof volumeChangeRatio === 'number' && !isNaN(volumeChangeRatio) && isFinite(volumeChangeRatio) && volumeChangeRatio > 0 && volumeChangeRatio <= 100) {
                    if (stockVolumeChange === null || volumeChangeRatio < stockVolumeChange) {
                      stockVolumeChange = volumeChangeRatio
                    }
                    hasVolumeChangeData = true
                  }
                }
              }
            })
          }
          // 从 details 中提取（兼容旧数据格式）
          if (!hasVolumeChangeData && stock.details && typeof stock.details === 'object') {
            Object.values(stock.details).forEach(windowDetail => {
              if (windowDetail && typeof windowDetail === 'object') {
                if (windowDetail.volume_analysis && typeof windowDetail.volume_analysis === 'object') {
                  const volumeChangeRatio = windowDetail.volume_analysis.volume_change_ratio
                  if (volumeChangeRatio !== null && volumeChangeRatio !== undefined && typeof volumeChangeRatio === 'number' && !isNaN(volumeChangeRatio) && isFinite(volumeChangeRatio) && volumeChangeRatio > 0 && volumeChangeRatio <= 100) {
                    if (stockVolumeChange === null || volumeChangeRatio < stockVolumeChange) {
                      stockVolumeChange = volumeChangeRatio
                    }
                    hasVolumeChangeData = true
                  }
                }
              }
            })
          }
          
          if (!hasVolumeChangeData) {
            // 没有数据，排除股票（因为用户明确选择了筛选条件）
            return false
          }
          
          // 检查是否在范围内
          const minVolumeChange = allStockAttributes.value.minVolumeChange
          const maxVolumeChange = allStockAttributes.value.maxVolumeChange
          // 只有当用户设置的范围比全范围更窄时才进行筛选
          const isNarrowerThanFullRange = volumeChangeRangeFilter.min > minVolumeChange || volumeChangeRangeFilter.max < maxVolumeChange
          if (isNarrowerThanFullRange) {
            if (stockVolumeChange < volumeChangeRangeFilter.min || stockVolumeChange > volumeChangeRangeFilter.max) {
              return false
            }
          }
        }

        // 成交量稳定性筛选
        const volumeStabilityRangeFilter = statisticsFilters.value.volumeStabilityRange
        if (volumeStabilityRangeFilter.min !== null && volumeStabilityRangeFilter.max !== null) {
          let stockVolumeStability = null
          let hasVolumeStabilityData = false
          
          // 从 volume_analysis 中提取（新格式）
          if (stock.volume_analysis && typeof stock.volume_analysis === 'object') {
            Object.values(stock.volume_analysis).forEach(windowAnalysis => {
              if (windowAnalysis && typeof windowAnalysis === 'object') {
                if (windowAnalysis.consolidation_details && typeof windowAnalysis.consolidation_details === 'object') {
                  const volumeStability = windowAnalysis.consolidation_details.volume_stability
                  if (volumeStability !== null && volumeStability !== undefined && typeof volumeStability === 'number' && !isNaN(volumeStability) && isFinite(volumeStability) && volumeStability >= 0 && volumeStability <= 10) {
                    if (stockVolumeStability === null || volumeStability < stockVolumeStability) {
                      stockVolumeStability = volumeStability
                    }
                    hasVolumeStabilityData = true
                  }
                }
              }
            })
          }
          // 从 details 中提取（兼容旧数据格式）
          if (!hasVolumeStabilityData && stock.details && typeof stock.details === 'object') {
            Object.values(stock.details).forEach(windowDetail => {
              if (windowDetail && typeof windowDetail === 'object') {
                if (windowDetail.volume_analysis && typeof windowDetail.volume_analysis === 'object') {
                  const volumeStability = windowDetail.volume_analysis.volume_stability
                  if (volumeStability !== null && volumeStability !== undefined && typeof volumeStability === 'number' && !isNaN(volumeStability) && isFinite(volumeStability) && volumeStability >= 0 && volumeStability <= 10) {
                    if (stockVolumeStability === null || volumeStability < stockVolumeStability) {
                      stockVolumeStability = volumeStability
                    }
                    hasVolumeStabilityData = true
                  }
                }
              }
            })
          }
          
          if (!hasVolumeStabilityData) {
            // 没有数据，排除股票（因为用户明确选择了筛选条件）
            return false
          }
          
          // 检查是否在范围内
          const minVolumeStability = allStockAttributes.value.minVolumeStability
          const maxVolumeStability = allStockAttributes.value.maxVolumeStability
          // 只有当用户设置的范围比全范围更窄时才进行筛选
          const isNarrowerThanFullRange = volumeStabilityRangeFilter.min > minVolumeStability || volumeStabilityRangeFilter.max < maxVolumeStability
          if (isNarrowerThanFullRange) {
            if (stockVolumeStability < volumeStabilityRangeFilter.min || stockVolumeStability > volumeStabilityRangeFilter.max) {
              return false
            }
          }
        }

        // 换手率筛选
        const turnoverRateRangeFilter = statisticsFilters.value.turnoverRateRange
        if (turnoverRateRangeFilter.min !== null && turnoverRateRangeFilter.max !== null) {
          let stockTurnoverRate = null
          let hasTurnoverRateData = false
          
          // 从 turnover_analysis 中提取（如果后端返回了）
          if (stock.turnover_analysis && typeof stock.turnover_analysis === 'object') {
            Object.values(stock.turnover_analysis).forEach(windowAnalysis => {
              if (windowAnalysis && typeof windowAnalysis === 'object') {
                const avgTurnoverRate = windowAnalysis.avg_turnover_rate
                if (avgTurnoverRate !== null && avgTurnoverRate !== undefined && typeof avgTurnoverRate === 'number' && !isNaN(avgTurnoverRate) && isFinite(avgTurnoverRate) && avgTurnoverRate >= 0) {
                  if (stockTurnoverRate === null || avgTurnoverRate < stockTurnoverRate) {
                    stockTurnoverRate = avgTurnoverRate
                  }
                  hasTurnoverRateData = true
                }
              }
            })
          }
          
          // 如果没有，从kline_data中计算
          // 注意：需要排除最近5天，与后端逻辑保持一致（避免突破期的放量干扰平台期判断）
          if (!hasTurnoverRateData && stock.kline_data && Array.isArray(stock.kline_data) && stock.kline_data.length > 0) {
            // 获取所有窗口期的换手率，取最小值
            const windows = Array.from(allStockAttributes.value.platformPeriods)
            const excludeRecentDays = 5 // 排除最近5天，与后端逻辑一致
            
            windows.forEach(window => {
              const windowDays = parseInt(window)
              if (!isNaN(windowDays) && windowDays > 0) {
                // 确保有足够的数据
                if (stock.kline_data.length < windowDays) {
                  return
                }
                
                // 获取平台期数据（排除最近5天）
                let platformData
                if (excludeRecentDays > 0 && stock.kline_data.length > windowDays) {
                  // 排除最近5天：从倒数第windowDays天到倒数第excludeRecentDays天
                  platformData = stock.kline_data.slice(-windowDays, -excludeRecentDays)
                } else {
                  // 如果数据不足，使用全部数据
                  platformData = stock.kline_data.slice(-windowDays)
                }
                
                const turnoverRates = platformData
                  .map(item => item.turn)
                  .filter(turn => turn !== null && turn !== undefined && !isNaN(turn) && turn >= 0 && turn <= 100)
                
                if (turnoverRates.length > 0) {
                  const avgTurnoverRate = turnoverRates.reduce((sum, rate) => sum + rate, 0) / turnoverRates.length
                  if (stockTurnoverRate === null || avgTurnoverRate < stockTurnoverRate) {
                    stockTurnoverRate = avgTurnoverRate
                  }
                  hasTurnoverRateData = true
                }
              }
            })
          }
          
          if (!hasTurnoverRateData) {
            // 没有数据，排除股票（因为用户明确选择了筛选条件）
            return false
          }
          
          // 检查是否在范围内
          const minTurnoverRate = allStockAttributes.value.minTurnoverRate
          const maxTurnoverRate = allStockAttributes.value.maxTurnoverRate
          // 只有当用户设置的范围比全范围更窄时才进行筛选
          const isNarrowerThanFullRange = turnoverRateRangeFilter.min > minTurnoverRate || turnoverRateRangeFilter.max < maxTurnoverRate
          if (isNarrowerThanFullRange) {
            if (stockTurnoverRate < turnoverRateRangeFilter.min || stockTurnoverRate > turnoverRateRangeFilter.max) {
              return false
            }
          }
        }

        // 低位判断百分比筛选
        const lowPositionPercentRangeFilter = statisticsFilters.value.lowPositionPercentRange
        if (lowPositionPercentRangeFilter.min !== null && lowPositionPercentRangeFilter.max !== null) {
          const stockLowPositionPercent = extractLowPositionPercent(stock.selection_reasons)
          if (stockLowPositionPercent === null) {
            // 没有数据，排除股票（因为用户明确选择了筛选条件）
            return false
          } else {
            // 检查是否在范围内（只有当范围不是默认的全范围时才筛选）
            const minLowPositionPercent = allStockAttributes.value.minLowPositionPercent
            const maxLowPositionPercent = allStockAttributes.value.maxLowPositionPercent
            // 只有当用户设置的范围比全范围更窄时才进行筛选
            if (lowPositionPercentRangeFilter.min > minLowPositionPercent || lowPositionPercentRangeFilter.max < maxLowPositionPercent) {
              if (stockLowPositionPercent < lowPositionPercentRangeFilter.min || stockLowPositionPercent > lowPositionPercentRangeFilter.max) {
                return false
              }
            }
            // 如果用户设置的范围等于全范围，不进行筛选（所有股票都通过）
          }
        }

        // 快速下跌百分比筛选
        const rapidDeclinePercentRangeFilter = statisticsFilters.value.rapidDeclinePercentRange
        if (rapidDeclinePercentRangeFilter.min !== null && rapidDeclinePercentRangeFilter.max !== null) {
          const stockRapidDeclinePercent = extractRapidDeclinePercent(stock.selection_reasons)
          if (stockRapidDeclinePercent === null) {
            // 没有数据，排除股票（因为用户明确选择了筛选条件）
            return false
          } else {
            // 检查是否在范围内（只有当范围不是默认的全范围时才筛选）
            const minRapidDeclinePercent = allStockAttributes.value.minRapidDeclinePercent
            const maxRapidDeclinePercent = allStockAttributes.value.maxRapidDeclinePercent
            // 只有当用户设置的范围比全范围更窄时才进行筛选
            if (rapidDeclinePercentRangeFilter.min > minRapidDeclinePercent || rapidDeclinePercentRangeFilter.max < maxRapidDeclinePercent) {
              if (stockRapidDeclinePercent < rapidDeclinePercentRangeFilter.min || stockRapidDeclinePercent > rapidDeclinePercentRangeFilter.max) {
                return false
              }
            }
            // 如果用户设置的范围等于全范围，不进行筛选（所有股票都通过）
          }
        }

        // 相对强度筛选
        const outperformIndexRangeFilter = statisticsFilters.value.outperformIndexRange
        const minOutperformIndex = allStockAttributes.value.minOutperformIndex
        const maxOutperformIndex = allStockAttributes.value.maxOutperformIndex
        
        // 只有当有数据且设置了筛选范围时才进行筛选
        if (outperformIndexRangeFilter.min !== null && outperformIndexRangeFilter.max !== null 
            && minOutperformIndex !== undefined && maxOutperformIndex !== undefined) {
          const stockOutperformIndex = stock.outperform_index
          
          // 只有当用户设置的范围比全范围更窄时才进行筛选
          const isRangeNarrowed = outperformIndexRangeFilter.min > minOutperformIndex || outperformIndexRangeFilter.max < maxOutperformIndex
          
          if (isRangeNarrowed) {
            // 用户明确缩小了筛选范围，需要进行筛选
            if (stockOutperformIndex === null || stockOutperformIndex === undefined) {
              // 没有相对强度数据，排除股票（因为用户明确选择了筛选条件）
              return false
            } else {
              // 检查是否在范围内
              if (stockOutperformIndex < outperformIndexRangeFilter.min || stockOutperformIndex > outperformIndexRangeFilter.max) {
                return false
              }
            }
          }
          // 如果用户设置的范围等于全范围，不进行筛选（包括没有相对强度数据的股票也通过）
        }

        // 布林极限 (%B) 筛选
        const percentBRangeFilter = statisticsFilters.value.percentBRange
        if (percentBRangeFilter.min !== null && percentBRangeFilter.max !== null) {
          const stockPercentB = extractPercentB(stock)
          if (stockPercentB === null) {
            // 没有数据，排除股票（因为用户明确选择了筛选条件）
            return false
          } else {
            // 检查是否在范围内（只有当范围不是默认的全范围时才筛选）
            const minPercentB = allStockAttributes.value.minPercentB
            const maxPercentB = allStockAttributes.value.maxPercentB
            // 只有当用户设置的范围比全范围更窄时才进行筛选
            if (percentBRangeFilter.min > minPercentB || percentBRangeFilter.max < maxPercentB) {
              if (stockPercentB < percentBRangeFilter.min || stockPercentB > percentBRangeFilter.max) {
                return false
              }
            }
            // 如果用户设置的范围等于全范围，不进行筛选（所有股票都通过）
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
      
      // 对于累计余额策略和固定金额策略，需要跟踪结算余额
      let hasCalculatedInitialInvestment = false
      let firstPeriodInitialCapital = 0
      let previousSettlementBalance = 0  // 上一个周期的结算余额
      let previousActualBuyAmount = 0  // 上一个周期的实际买入金额（用于equal_distribution_fixed策略）

      filteredRecords.forEach(record => {
        const config = record.config || {}
        const result = record.result || {}
        const buyStrategy = config.buy_strategy
        
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
        
        // 计算筛选后股票的实际投入和收益
        filteredStockDetails.forEach(detail => {
          recordProfit += (detail.profit || 0)
          
          // 统计盈利和亏损股票数
          if (detail.profit > 0) {
            profitableStocks++
          } else if (detail.profit < 0) {
            lossStocks++
          }
        })
        
        // 计算本期的实际投入金额（筛选后的股票）
        let actualBuyAmount = 0
        filteredStockDetails.forEach(detail => {
          actualBuyAmount += detail.buyAmount || 0
        })
        
        // 计算本期的结算余额（筛选后的股票）
        const currentSettlementBalance = actualBuyAmount + recordProfit
        
        // 根据策略计算实际新投入
        if (buyStrategy === 'equal_distribution') {
          // 累计余额策略：只有第一个周期算作新投入
          if (!hasCalculatedInitialInvestment) {
            // 第一个周期：使用初始资金作为投入
            // 对于旧记录，如果 initial_capital 不存在，默认使用10万（之前的历史数据都是10万）
            const initialCapital = config.initial_capital !== undefined && config.initial_capital !== null 
              ? config.initial_capital 
              : 100000
            recordInvestment = initialCapital
            firstPeriodInitialCapital = initialCapital
            hasCalculatedInitialInvestment = true
            previousSettlementBalance = currentSettlementBalance
          } else {
            // 后续周期：使用余额，不算新投入（recordInvestment = 0）
            recordInvestment = 0
            previousSettlementBalance = currentSettlementBalance
          }
        } else if (buyStrategy === 'equal_distribution_fixed') {
          // 固定金额策略：每个周期投入固定金额，但需要扣除上期余额
          // 对于旧记录，如果 initial_capital 不存在，默认使用10万（之前的历史数据都是10万）
          const fixedCapital = config.initial_capital !== undefined && config.initial_capital !== null 
            ? config.initial_capital 
            : 100000
          
          if (!hasCalculatedInitialInvestment) {
            // 第一个周期：使用实际买入金额作为投入（因为可能筛选了股票）
            // 如果筛选了股票，actualBuyAmount 可能小于 fixedCapital
            recordInvestment = actualBuyAmount
            firstPeriodInitialCapital = fixedCapital  // 保存固定金额用于收益率计算
            hasCalculatedInitialInvestment = true
            // 更新结算余额（第一个周期处理完后）
            previousSettlementBalance = currentSettlementBalance
            previousActualBuyAmount = actualBuyAmount  // 保存上期的实际买入金额
          } else {
            // 后续周期：新投入 = 实际买入金额 - (上期结算余额 - 上期实际买入金额)
            // 或者更简单：如果本期实际买入金额 > 上期结算余额，说明有新投入
            // 新投入 = max(0, 本期实际买入金额 - 上期结算余额)
            if (actualBuyAmount > previousSettlementBalance) {
              recordInvestment = actualBuyAmount - previousSettlementBalance
            } else {
              // 如果本期实际买入金额 <= 上期结算余额，说明使用的是上期余额，没有新投入
              recordInvestment = 0
            }
            // 更新结算余额（当前周期处理完后）
            previousSettlementBalance = currentSettlementBalance
            previousActualBuyAmount = actualBuyAmount  // 保存上期的实际买入金额
          }
        } else {
          // 其他策略（如fixed_amount）：使用实际买入金额
          recordInvestment = actualBuyAmount
        }

        // 计算本次回测的收益率
        let recordReturnRate = 0
        if (buyStrategy === 'equal_distribution' && recordInvestment === 0) {
          // 累计余额策略的后续周期：使用上期结算余额作为分母
          // 从上一个周期的记录中获取结算余额
          if (recordReturns.length > 0) {
            const lastRecord = recordReturns[recordReturns.length - 1]
            const lastSettlementBalance = lastRecord.settlementBalance || (lastRecord.investment + lastRecord.profit)
            if (lastSettlementBalance > 0) {
              recordReturnRate = (recordProfit / lastSettlementBalance) * 100
            }
          } else {
            // 如果没有上一个周期记录，使用实际买入金额作为分母
            if (actualBuyAmount > 0) {
              recordReturnRate = (recordProfit / actualBuyAmount) * 100
            }
          }
        } else if (recordInvestment > 0) {
          recordReturnRate = (recordProfit / recordInvestment) * 100
        } else if (actualBuyAmount > 0) {
          // 如果没有新投入但有实际买入，使用实际买入金额计算收益率
          recordReturnRate = (recordProfit / actualBuyAmount) * 100
        }
        
        // 保存本次回测的数据（用于后续计算整体收益率）
        recordReturns.push({
          investment: recordInvestment,
          profit: recordProfit,
          returnRate: recordReturnRate,
          actualBuyAmount: actualBuyAmount,  // 保存实际买入金额，用于计算结算余额
          settlementBalance: currentSettlementBalance,  // 保存结算余额
          scanDate: config.backtest_date || ''  // 保存扫描日期，用于最大回撤日期范围
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

              // 从 selection_reasons 中提取价格区间、均线收敛、波动率、低位、快速下跌
              const boxRange = extractBoxRange(filteredStock.selection_reasons)
              const maDiff = extractMaDiff(filteredStock.selection_reasons)
              const volatility = extractVolatility(filteredStock.selection_reasons)
              const lowPositionPercent = extractLowPositionPercent(filteredStock.selection_reasons)
              const rapidDeclinePercent = extractRapidDeclinePercent(filteredStock.selection_reasons)
              
              stocks.push({
                code: filteredStock.code || '',
                name: filteredStock.name || '',
                industry: filteredStock.industry || matchingStock.industry || '',
                platformPeriods: uniquePlatformPeriods,
                breakthroughSignals: breakthroughSignals,
                hasBreakthroughConfirmation: hasBreakthroughConfirmation,
                boxQuality: boxQuality,
                returnRate: returnRate,
                boxRange: boxRange,
                maDiff: maDiff,
                volatility: volatility,
                lowPositionPercent: lowPositionPercent,
                rapidDeclinePercent: rapidDeclinePercent
              })
            }
          }
        })

        recordDetails.push({
          scanDate: config.backtest_date || '',
          stocks: stocks,
          record: record, // 保存原始记录引用，用于周期分组
          investment: recordInvestment, // 保存新投入资金
          actualBuyAmount: actualBuyAmount, // 保存实际买入金额
          settlementBalance: currentSettlementBalance, // 保存结算余额
          buyStrategy: buyStrategy, // 保存策略类型
          fixedCapital: buyStrategy === 'equal_distribution_fixed' 
            ? (config.initial_capital !== undefined && config.initial_capital !== null ? config.initial_capital : 100000)
            : null // 保存固定金额（仅用于equal_distribution_fixed策略）
        })
      })

      // 计算胜率（基于股票数量）
      const totalStocks = profitableStocks + lossStocks
      let winRate = totalStocks > 0 ? (profitableStocks / totalStocks) * 100 : 0

      // 按周期分组统计
      const periodGroups = groupByPeriod(recordDetails)
      let cumulativeAdditionalInvestment = 0  // 累计额外投入（用于equal_distribution_fixed策略）
      let cumulativeProfit = 0  // 累计收益（用于equal_distribution_fixed策略）
      const periodStats = periodGroups.map((group, index) => {
        let periodStockCount = 0
        let periodInvestment = 0
        let periodAdditionalInvestment = 0  // 本周期额外投入的资金
        let periodProfit = 0
        const periodStocks = []
        const periodStockDetails = [] // 存储股票详情，用于排序和筛选
        
        // 获取该周期的第一个记录，用于确定策略类型和固定金额
        let periodBuyStrategy = null
        let periodFixedCapital = null
        let periodSettlementBalance = 0
        
        // 按照原始扫描顺序收集股票详情
        group.records.forEach((recordDetail, recordIndex) => {
          const record = recordDetail.record
          if (!record) return
          
          const config = record.config || {}
          const result = record.result || {}
          
          // 获取策略类型和固定金额（从recordDetail中获取，如果recordDetail中没有则从record中获取）
          if (recordIndex === 0) {
            periodBuyStrategy = recordDetail.buyStrategy || config.buy_strategy
            if (periodBuyStrategy === 'equal_distribution_fixed') {
              periodFixedCapital = recordDetail.fixedCapital !== undefined 
                ? recordDetail.fixedCapital
                : (config.initial_capital !== undefined && config.initial_capital !== null ? config.initial_capital : 100000)
            }
          }
          
          // 获取该记录中筛选后的股票代码列表
          const recordStockCodes = new Set(recordDetail.stocks.map(s => s.code))
          
          // 从stockDetails中获取筛选后股票的收益数据，并创建一个映射以便快速查找
          const stockDetails = result.stockDetails || []
          const stockDetailsMap = new Map()
          stockDetails.forEach(detail => {
            if (recordStockCodes.has(detail.code)) {
              stockDetailsMap.set(detail.code, detail)
            }
          })
          
          // 按照recordDetail.stocks的原始顺序遍历股票（保持原始扫描顺序）
          recordDetail.stocks.forEach(stock => {
            const detail = stockDetailsMap.get(stock.code)
            if (detail) {
              const returnRate = detail.returnRate !== undefined ? detail.returnRate : stock.returnRate
              periodStockDetails.push({
                code: stock.code || '',
                name: stock.name || '',
                returnRate: returnRate,
                buyAmount: detail.buyAmount || 0,
                profit: detail.profit || 0,
                record: record
              })
            }
          })
          
          // 更新周期结算余额（使用最后一个记录的结算余额）
          if (recordDetail.settlementBalance !== undefined) {
            periodSettlementBalance = recordDetail.settlementBalance
          }
        })
        
        // 使用所有股票详情计算周期统计
        periodStockDetails.forEach(detail => {
          periodInvestment += detail.buyAmount
          periodProfit += detail.profit
          periodStockCount++
          
          periodStocks.push({
            code: detail.code,
            name: detail.name,
            returnRate: detail.returnRate
          })
        })
        
        // 计算本周期额外投入的资金
        if (periodBuyStrategy === 'equal_distribution_fixed' && periodFixedCapital !== null) {
          // 固定金额策略：额外投入需要考虑之前所有周期的累计收益
          if (index === 0) {
            // 第一个周期：额外投入就是实际买入金额（因为可能筛选了股票）
            periodAdditionalInvestment = periodInvestment
          } else {
            // 后续周期：累计结算余额 = 累计额外投入 + 累计收益
            // 额外投入 = max(0, 固定金额 - 累计结算余额)
            const cumulativeSettlementBalance = cumulativeAdditionalInvestment + cumulativeProfit
            periodAdditionalInvestment = Math.max(0, periodFixedCapital - cumulativeSettlementBalance)
          }
          // 更新累计额外投入和累计收益
          cumulativeAdditionalInvestment += periodAdditionalInvestment
          cumulativeProfit += periodProfit
        } else if (periodBuyStrategy === 'equal_distribution') {
          // 累计余额策略：只有第一个周期有额外投入
          if (index === 0) {
            periodAdditionalInvestment = periodInvestment
            cumulativeAdditionalInvestment = periodInvestment
            cumulativeProfit = periodProfit
          } else {
            periodAdditionalInvestment = 0
            // 累计余额策略：累计收益继续累加
            cumulativeProfit += periodProfit
          }
        } else {
          // 其他策略：额外投入就是实际买入金额
          periodAdditionalInvestment = periodInvestment
          cumulativeAdditionalInvestment += periodInvestment
          cumulativeProfit += periodProfit
        }
        
        // 计算周期收益率
        let periodReturnRate = 0
        if (periodInvestment > 0) {
          periodReturnRate = (periodProfit / periodInvestment) * 100
        }
        
        return {
          periodLabel: group.periodLabel,
          stockCount: periodStockCount,
          investment: periodInvestment,  // 周期投入资金
          additionalInvestment: periodAdditionalInvestment,  // 本周期额外投入的资金
          totalProfit: periodProfit,
          returnRate: periodReturnRate,
          stocks: periodStocks,
          records: group.records // 保存记录信息，用于获取回测日期
        }
      })
      
      // 计算每个周期与上一个周期的重复股票数量
      periodStats.forEach((periodStat, index) => {
        if (index > 0) {
          // 获取当前周期的股票代码集合
          const currentStockCodes = new Set(periodStat.stocks.map(s => s.code))
          // 获取上一个周期的股票代码集合
          const previousPeriodStat = periodStats[index - 1]
          if (previousPeriodStat && previousPeriodStat.stocks) {
            const previousStockCodes = new Set(previousPeriodStat.stocks.map(s => s.code))
            // 计算交集（重复的股票）
            let repeatCount = 0
            for (const code of currentStockCodes) {
              if (previousStockCodes.has(code)) {
                repeatCount++
              }
            }
            periodStat.repeatCount = repeatCount
          } else {
            periodStat.repeatCount = 0
          }
        } else {
          // 第一个周期没有上一个周期，重复数为0
          periodStat.repeatCount = 0
        }
      })

      // 基于周期统计中的额外投入资金重新计算总投入资金
      // 对于 equal_distribution_fixed 策略，总投入应该是所有周期的额外投入资金之和
      const buyStrategy = filteredRecords.length > 0 ? filteredRecords[0].config?.buy_strategy : null
      if (buyStrategy === 'equal_distribution_fixed' && periodStats.length > 0) {
        // 重新计算总投入：所有周期的额外投入资金之和
        totalInvestment = periodStats.reduce((sum, stat) => sum + (stat.additionalInvestment || 0), 0)
      } else if (buyStrategy === 'equal_distribution' && periodStats.length > 0) {
        // 累计余额策略：总投入就是第一个周期的额外投入
        totalInvestment = periodStats.length > 0 ? (periodStats[0].additionalInvestment || 0) : totalInvestment
      } else if (buyStrategy === 'fixed_amount' && periodStats.length > 0) {
        // fixed_amount 策略：总投入 = 所有周期的实际买入金额之和
        totalInvestment = periodStats.reduce((sum, stat) => sum + (stat.investment || 0), 0)
        // 总收益 = 所有周期的收益之和
        totalProfit = periodStats.reduce((sum, stat) => sum + (stat.totalProfit || 0), 0)
      }
      // 其他策略保持原来的计算方式（基于 recordInvestment 累加）

      // 基于重新计算后的总投入资金和周期统计重新计算整体收益率、最大回撤和夏普比
      let totalReturnRate = 0
      let maxDrawdown = null
      let maxDrawdownDateRange = null
      let sharpeRatio = null

      if (periodStats.length > 0) {
        // 计算整体收益率
        if (buyStrategy === 'fixed_amount') {
          // fixed_amount 策略：简单的根据结算余额和投入总资金计算收益率
          // 总投入已经在上面计算了（所有周期的实际买入金额之和）
          // 总收益已经在上面计算了（所有周期的收益之和）
          // 收益率 = 总收益 / 总投入 * 100
          if (totalInvestment > 0) {
            totalReturnRate = (totalProfit / totalInvestment) * 100
          }
        } else {
          // 其他策略：使用公共函数计算整体收益率
          const returnRateResult = calculateTotalReturnRate(
            periodStats.map(stat => ({
              config: stat.records?.[0]?.record?.config || {},
              result: { summary: { totalInvestment: stat.investment, totalProfit: stat.totalProfit } }
            }))
          )
          totalReturnRate = returnRateResult.totalReturnRate
        }

        // 基于周期统计计算最大回撤
        // 使用累计收益额计算，更直观且不受总投入资金计算方式影响
        if (periodStats.length > 0) {
          let cumulativeProfit = 0 // 累计收益额
          let peakProfit = 0 // 最高点（累计收益额）
          let maxDrawdownValue = 0 // 最大回撤值（收益额的差值）
          let peakDate = '' // 最高点日期
          let drawdownStartDate = '' // 回撤开始日期（峰值日期）
          let drawdownEndDate = '' // 回撤结束日期（最低点日期）
          
          // 获取初始投入资金（用于计算净值）
          let initialCapital = 0
          if (buyStrategy === 'equal_distribution_fixed' && periodStats.length > 0) {
            // 固定金额策略：使用第一个周期的额外投入作为初始资金
            initialCapital = periodStats[0].additionalInvestment || periodStats[0].investment || 0
          } else if (buyStrategy === 'equal_distribution' && periodStats.length > 0) {
            // 累计余额策略：使用第一个周期的额外投入作为初始资金
            initialCapital = periodStats[0].additionalInvestment || periodStats[0].investment || 0
          } else {
            // 其他策略：使用总投入资金
            initialCapital = totalInvestment
          }

          periodStats.forEach((periodStat, index) => {
            // 获取周期日期（与周期统计中的周期字段匹配）
            // 优先使用统计日期（stat_date），如果没有则使用回测日期（backtest_date）
            let periodDate = ''
            if (periodStat.records && periodStat.records.length > 0) {
              const firstRecord = periodStat.records[0].record
              if (firstRecord && firstRecord.config) {
                // 优先使用统计日期，与周期统计的周期字段保持一致
                periodDate = firstRecord.config.stat_date || firstRecord.config.backtest_date || ''
              }
            }

            // 累计收益额
            cumulativeProfit += periodStat.totalProfit

            // 计算净值 = 初始资金 + 累计收益
            const netValue = initialCapital + cumulativeProfit

            // 更新峰值（基于净值）
            if (netValue > peakProfit) {
              peakProfit = netValue
              peakDate = periodDate
            }

            // 计算回撤 = 峰值净值 - 当前净值
            const drawdown = peakProfit - netValue
            
            // 计算回撤百分比 = 回撤 / 峰值净值
            let drawdownPercent = 0
            if (peakProfit > 0) {
              drawdownPercent = (drawdown / peakProfit) * 100
            } else if (peakProfit < 0) {
              // 如果最高点也是负数，使用绝对值
              drawdownPercent = drawdown
            }

            if (drawdownPercent > maxDrawdownValue) {
              maxDrawdownValue = drawdownPercent
              drawdownStartDate = peakDate
              drawdownEndDate = periodDate
            }
          })

          // 最大回撤百分比
          maxDrawdown = maxDrawdownValue

          // 设置日期范围
          if (drawdownStartDate && drawdownEndDate) {
            maxDrawdownDateRange = {
              start: drawdownStartDate,
              end: drawdownEndDate
            }
          }
        }

        // 基于累计收益率计算夏普比（年化）
        // 计算每个周期的累计收益率，然后基于累计收益率的变化来计算夏普比
        if (periodStats.length > 1 && totalInvestment > 0) {
          // 计算累计收益率序列
          let cumulativeReturn = 0
          let cumulativeReturns = [] // 累计收益率序列
          let periodDates = [] // 周期日期序列，用于计算年化因子
          
          periodStats.forEach((periodStat, index) => {
            // 累计收益率 = 累计收益 / 总投入资金
            cumulativeReturn += periodStat.totalProfit
            const cumulativeReturnRate = (cumulativeReturn / totalInvestment) * 100
            cumulativeReturns.push(cumulativeReturnRate)
            
            // 获取周期日期
            let periodDate = ''
            if (periodStat.records && periodStat.records.length > 0) {
              const firstRecord = periodStat.records[0].record
              if (firstRecord && firstRecord.config) {
                periodDate = firstRecord.config.stat_date || firstRecord.config.backtest_date || ''
              }
            }
            if (periodDate) {
              periodDates.push(periodDate)
            }
          })

          if (cumulativeReturns.length > 1) {
            // 计算累计收益率的变化（每个周期的收益率贡献）
            let returnChanges = []
            for (let i = 1; i < cumulativeReturns.length; i++) {
              // 累计收益率的变化 = 当前累计收益率 - 上期累计收益率
              const returnChange = cumulativeReturns[i] - cumulativeReturns[i - 1]
              returnChanges.push(returnChange)
            }

            if (returnChanges.length > 0) {
              // 计算平均收益率变化
              const avgReturnChange = returnChanges.reduce((sum, r) => sum + r, 0) / returnChanges.length

              // 计算样本标准差（除以n-1，而不是n）
              const n = returnChanges.length
              const variance = returnChanges.reduce((sum, r) => sum + Math.pow(r - avgReturnChange, 2), 0) / (n > 1 ? n - 1 : 1)
              const stdDev = Math.sqrt(variance)

              // 周期夏普比 = 平均收益率变化 / 标准差（假设无风险利率为0）
              let periodSharpeRatio = 0
              if (stdDev > 0) {
                periodSharpeRatio = avgReturnChange / stdDev
              }

              // 年化夏普比：需要根据周期之间的时间间隔进行年化
              // 年化因子 = sqrt(252 / 平均周期交易日数)
              if (periodDates.length >= 2 && periodSharpeRatio > 0) {
                // 计算第一个周期和最后一个周期之间的交易日数
                const firstDate = periodDates[0]
                const lastDate = periodDates[periodDates.length - 1]
                const totalTradingDays = countTradingDays(firstDate, lastDate)
                
                if (totalTradingDays > 0 && n > 0) {
                  // 平均周期交易日数 = 总交易日数 / 周期数
                  const avgPeriodTradingDays = totalTradingDays / n
                  
                  // 年化因子：一年约252个交易日
                  const annualizationFactor = Math.sqrt(252 / avgPeriodTradingDays)
                  
                  // 年化夏普比 = 周期夏普比 * 年化因子
                  sharpeRatio = periodSharpeRatio * annualizationFactor
                } else {
                  sharpeRatio = periodSharpeRatio
                }
              } else {
                sharpeRatio = periodSharpeRatio
              }
            }
          }
        }
      }

      // 收集所有周期的股票数量，用于设置筛选范围
      const stockCounts = periodStats.map(stat => stat.stockCount).filter(count => count > 0)
      if (stockCounts.length > 0) {
        allStockAttributes.value.minStockCount = Math.min(...stockCounts)
        allStockAttributes.value.maxStockCount = Math.max(...stockCounts)
        // 如果 stockCountRange 未设置，默认设置为最小值和最大值（默认启用，不筛选）
        if (statisticsFilters.value.stockCountRange.min === null || statisticsFilters.value.stockCountRange.max === null) {
          statisticsFilters.value.stockCountRange = {
            min: allStockAttributes.value.minStockCount,
            max: allStockAttributes.value.maxStockCount
          }
        }
      }

      // 根据股票数量范围筛选周期
      const stockCountRangeFilter = statisticsFilters.value.stockCountRange
      let filteredPeriodStats = periodStats
      if (stockCountRangeFilter.min !== null && stockCountRangeFilter.max !== null) {
        const minStockCount = allStockAttributes.value.minStockCount
        const maxStockCount = allStockAttributes.value.maxStockCount
        // 只有当范围不是默认的全范围时才筛选
        if (stockCountRangeFilter.min > minStockCount || stockCountRangeFilter.max < maxStockCount) {
          filteredPeriodStats = periodStats.filter(stat => {
            return stat.stockCount >= stockCountRangeFilter.min && stat.stockCount <= stockCountRangeFilter.max
          })
          
          // 如果筛选了周期，需要重新计算整体统计数据
          if (filteredPeriodStats.length !== periodStats.length) {
            // 重新计算整体统计（基于筛选后的周期统计）
            let recalculatedTotalInvestment = 0
            let recalculatedTotalProfit = 0
            let recalculatedProfitableStocks = 0
            let recalculatedLossStocks = 0
            const recalculatedRecordReturns = []
            
            // 获取策略类型（从第一个周期统计中获取）
            let recalculatedBuyStrategy = buyStrategy
            if (filteredPeriodStats.length > 0 && filteredPeriodStats[0].records && filteredPeriodStats[0].records.length > 0) {
              const firstRecord = filteredPeriodStats[0].records[0].record
              if (firstRecord && firstRecord.config) {
                recalculatedBuyStrategy = firstRecord.config.buy_strategy || buyStrategy
              }
            }
            
            // 基于筛选后的周期统计重新计算额外投入资金
            let recalculatedCumulativeAdditionalInvestment = 0
            let recalculatedCumulativeProfit = 0
            
            // 从筛选后的周期统计中重新计算整体统计
            filteredPeriodStats.forEach((periodStat, periodIndex) => {
              // 从原始记录中获取该周期的投资金额
              let periodInvestment = 0
              let periodBuyStrategy = null
              let periodFixedCapital = null
              
              periodStat.records.forEach((recordDetail, recordIndex) => {
                const record = recordDetail.record
                if (!record) return
                
                const config = record.config || {}
                const result = record.result || {}
                
                // 获取策略类型和固定金额
                if (recordIndex === 0) {
                  periodBuyStrategy = recordDetail.buyStrategy || config.buy_strategy
                  if (periodBuyStrategy === 'equal_distribution_fixed') {
                    periodFixedCapital = recordDetail.fixedCapital !== undefined 
                      ? recordDetail.fixedCapital
                      : (config.initial_capital !== undefined && config.initial_capital !== null ? config.initial_capital : 100000)
                  }
                }
                
                const stockDetails = result.stockDetails || []
                
                // 获取该周期筛选后的股票代码
                const periodStockCodes = new Set(periodStat.stocks.map(s => s.code))
                
                stockDetails.forEach(detail => {
                  if (periodStockCodes.has(detail.code)) {
                    periodInvestment += detail.buyAmount || 0
                  }
                })
              })
              
              // 计算本周期额外投入资金
              let periodAdditionalInvestment = 0
              if (periodBuyStrategy === 'equal_distribution_fixed' && periodFixedCapital !== null) {
                if (periodIndex === 0) {
                  periodAdditionalInvestment = periodInvestment
                } else {
                  const cumulativeSettlementBalance = recalculatedCumulativeAdditionalInvestment + recalculatedCumulativeProfit
                  periodAdditionalInvestment = Math.max(0, periodFixedCapital - cumulativeSettlementBalance)
                }
                recalculatedCumulativeAdditionalInvestment += periodAdditionalInvestment
                recalculatedCumulativeProfit += periodStat.totalProfit
              } else if (periodBuyStrategy === 'equal_distribution') {
                if (periodIndex === 0) {
                  periodAdditionalInvestment = periodInvestment
                  recalculatedCumulativeAdditionalInvestment = periodInvestment
                  recalculatedCumulativeProfit = periodStat.totalProfit
                } else {
                  periodAdditionalInvestment = 0
                  recalculatedCumulativeProfit += periodStat.totalProfit
                }
              } else {
                periodAdditionalInvestment = periodInvestment
                recalculatedCumulativeAdditionalInvestment += periodInvestment
                recalculatedCumulativeProfit += periodStat.totalProfit
              }
              
              // 基于额外投入资金累加总投入
              if (periodBuyStrategy === 'equal_distribution_fixed' || periodBuyStrategy === 'equal_distribution') {
                recalculatedTotalInvestment += periodAdditionalInvestment
              } else if (periodBuyStrategy === 'fixed_amount') {
                // fixed_amount 策略：累加实际买入金额
                recalculatedTotalInvestment += periodInvestment
              } else {
                recalculatedTotalInvestment += periodInvestment
              }
              
              recalculatedTotalProfit += periodStat.totalProfit
              
              // 统计盈利和亏损股票数
              periodStat.stocks.forEach(stock => {
                if (stock.returnRate !== null && stock.returnRate !== undefined) {
                  if (stock.returnRate > 0) {
                    recalculatedProfitableStocks++
                  } else if (stock.returnRate < 0) {
                    recalculatedLossStocks++
                  }
                }
              })
              
              // 保存周期数据用于重新计算
              // 获取该周期的扫描日期（使用第一个记录的日期）
              let periodScanDate = ''
              if (periodStat.records && periodStat.records.length > 0) {
                const firstRecord = periodStat.records[0].record
                if (firstRecord && firstRecord.config) {
                  periodScanDate = firstRecord.config.backtest_date || ''
                }
              }
              
              if (periodInvestment > 0) {
                recalculatedRecordReturns.push({
                  investment: periodInvestment,
                  profit: periodStat.totalProfit,
                  returnRate: periodStat.returnRate,
                  scanDate: periodScanDate  // 添加扫描日期
                })
              }
            })
            
            // 重新计算筛选后的周期统计中每个周期与上一个周期的重复股票数量
            filteredPeriodStats.forEach((periodStat, index) => {
              if (index > 0) {
                // 获取当前周期的股票代码集合
                const currentStockCodes = new Set(periodStat.stocks.map(s => s.code))
                // 获取上一个周期的股票代码集合
                const previousPeriodStat = filteredPeriodStats[index - 1]
                if (previousPeriodStat && previousPeriodStat.stocks) {
                  const previousStockCodes = new Set(previousPeriodStat.stocks.map(s => s.code))
                  // 计算交集（重复的股票）
                  let repeatCount = 0
                  for (const code of currentStockCodes) {
                    if (previousStockCodes.has(code)) {
                      repeatCount++
                    }
                  }
                  periodStat.repeatCount = repeatCount
                } else {
                  periodStat.repeatCount = 0
                }
              } else {
                // 第一个周期没有上一个周期，重复数为0
                periodStat.repeatCount = 0
              }
            })
            
            // 基于筛选后的周期统计重新计算整体收益率、最大回撤和夏普比
            let recalculatedTotalReturnRate = 0
            let recalculatedMaxDrawdown = null
            let recalculatedMaxDrawdownDateRange = null
            let recalculatedSharpeRatio = null

            // 计算整体收益率
            if (recalculatedBuyStrategy === 'fixed_amount') {
              // fixed_amount 策略：简单的根据结算余额和投入总资金计算收益率
              // 总投入和总收益已经在上面计算了
              if (recalculatedTotalInvestment > 0) {
                recalculatedTotalReturnRate = (recalculatedTotalProfit / recalculatedTotalInvestment) * 100
              }
            } else {
              // 其他策略：使用公共函数计算整体收益率
              const recalculatedReturnRateResult = calculateTotalReturnRate(
                filteredPeriodStats.map(stat => ({
                  config: stat.records?.[0]?.record?.config || {},
                  result: { summary: { totalInvestment: stat.investment, totalProfit: stat.totalProfit } }
                }))
              )
              recalculatedTotalReturnRate = recalculatedReturnRateResult.totalReturnRate
            }

            // 基于筛选后的周期统计计算最大回撤
            // 使用累计收益额计算，更直观且不受总投入资金计算方式影响
            if (filteredPeriodStats.length > 0) {
              let recalculatedCumulativeProfit = 0 // 累计收益额
              let peakProfit = 0 // 最高点（累计收益额）
              let maxDrawdownValue = 0 // 最大回撤值（收益额的差值）
              let peakDate = '' // 最高点日期
              let drawdownStartDate = '' // 回撤开始日期（峰值日期）
              let drawdownEndDate = '' // 回撤结束日期（最低点日期）
              
              // 获取初始投入资金（用于计算净值）
              let recalculatedInitialCapital = 0
              if (recalculatedBuyStrategy === 'equal_distribution_fixed' && filteredPeriodStats.length > 0) {
                // 固定金额策略：使用第一个周期的额外投入作为初始资金
                recalculatedInitialCapital = filteredPeriodStats[0].additionalInvestment || filteredPeriodStats[0].investment || 0
              } else if (recalculatedBuyStrategy === 'equal_distribution' && filteredPeriodStats.length > 0) {
                // 累计余额策略：使用第一个周期的额外投入作为初始资金
                recalculatedInitialCapital = filteredPeriodStats[0].additionalInvestment || filteredPeriodStats[0].investment || 0
              } else {
                // 其他策略：使用总投入资金
                recalculatedInitialCapital = recalculatedTotalInvestment
              }

              filteredPeriodStats.forEach((periodStat, index) => {
                // 获取周期日期（与周期统计中的周期字段匹配）
                // 优先使用统计日期（stat_date），如果没有则使用回测日期（backtest_date）
                let periodDate = ''
                if (periodStat.records && periodStat.records.length > 0) {
                  const firstRecord = periodStat.records[0].record
                  if (firstRecord && firstRecord.config) {
                    // 优先使用统计日期，与周期统计的周期字段保持一致
                    periodDate = firstRecord.config.stat_date || firstRecord.config.backtest_date || ''
                  }
                }

                // 累计收益额
                recalculatedCumulativeProfit += periodStat.totalProfit

                // 计算净值 = 初始资金 + 累计收益
                const netValue = recalculatedInitialCapital + recalculatedCumulativeProfit

                // 更新峰值（基于净值）
                if (netValue > peakProfit) {
                  peakProfit = netValue
                  peakDate = periodDate
                }

                // 计算回撤 = 峰值净值 - 当前净值
                const drawdown = peakProfit - netValue
                
                // 计算回撤百分比 = 回撤 / 峰值净值
                let drawdownPercent = 0
                if (peakProfit > 0) {
                  drawdownPercent = (drawdown / peakProfit) * 100
                } else if (peakProfit < 0) {
                  // 如果最高点也是负数，使用绝对值
                  drawdownPercent = drawdown
                }

                if (drawdownPercent > maxDrawdownValue) {
                  maxDrawdownValue = drawdownPercent
                  drawdownStartDate = peakDate
                  drawdownEndDate = periodDate
                }
              })

              // 最大回撤百分比
              recalculatedMaxDrawdown = maxDrawdownValue

              // 设置日期范围
              if (drawdownStartDate && drawdownEndDate) {
                recalculatedMaxDrawdownDateRange = {
                  start: drawdownStartDate,
                  end: drawdownEndDate
                }
              }
            }

            // 基于累计收益率计算夏普比（筛选后的周期，年化）
            if (filteredPeriodStats.length > 1 && recalculatedTotalInvestment > 0) {
              // 计算累计收益率序列
              let cumulativeReturn = 0
              let cumulativeReturns = [] // 累计收益率序列
              let periodDates = [] // 周期日期序列，用于计算年化因子
              
              filteredPeriodStats.forEach((periodStat, index) => {
                // 累计收益率 = 累计收益 / 总投入资金
                cumulativeReturn += periodStat.totalProfit
                const cumulativeReturnRate = (cumulativeReturn / recalculatedTotalInvestment) * 100
                cumulativeReturns.push(cumulativeReturnRate)
                
                // 获取周期日期
                let periodDate = ''
                if (periodStat.records && periodStat.records.length > 0) {
                  const firstRecord = periodStat.records[0].record
                  if (firstRecord && firstRecord.config) {
                    periodDate = firstRecord.config.stat_date || firstRecord.config.backtest_date || ''
                  }
                }
                if (periodDate) {
                  periodDates.push(periodDate)
                }
              })

              if (cumulativeReturns.length > 1) {
                // 计算累计收益率的变化（每个周期的收益率贡献）
                let returnChanges = []
                for (let i = 1; i < cumulativeReturns.length; i++) {
                  // 累计收益率的变化 = 当前累计收益率 - 上期累计收益率
                  const returnChange = cumulativeReturns[i] - cumulativeReturns[i - 1]
                  returnChanges.push(returnChange)
                }

                if (returnChanges.length > 0) {
                  // 计算平均收益率变化
                  const avgReturnChange = returnChanges.reduce((sum, r) => sum + r, 0) / returnChanges.length
                  // 计算样本标准差（除以n-1，而不是n）
                  const n = returnChanges.length
                  const variance = returnChanges.reduce((sum, r) => sum + Math.pow(r - avgReturnChange, 2), 0) / (n > 1 ? n - 1 : 1)
                  const stdDev = Math.sqrt(variance)

                  // 周期夏普比 = 平均收益率变化 / 标准差（假设无风险利率为0）
                  let periodSharpeRatio = 0
                  if (stdDev > 0) {
                    periodSharpeRatio = avgReturnChange / stdDev
                  }

                  // 年化夏普比：需要根据周期之间的时间间隔进行年化
                  if (periodDates.length >= 2 && periodSharpeRatio > 0) {
                    // 计算第一个周期和最后一个周期之间的交易日数
                    const firstDate = periodDates[0]
                    const lastDate = periodDates[periodDates.length - 1]
                    const totalTradingDays = countTradingDays(firstDate, lastDate)
                    
                    if (totalTradingDays > 0 && n > 0) {
                      // 平均周期交易日数 = 总交易日数 / 周期数
                      const avgPeriodTradingDays = totalTradingDays / n
                      
                      // 年化因子：一年约252个交易日
                      const annualizationFactor = Math.sqrt(252 / avgPeriodTradingDays)
                      
                      // 年化夏普比 = 周期夏普比 * 年化因子
                      recalculatedSharpeRatio = periodSharpeRatio * annualizationFactor
                    } else {
                      recalculatedSharpeRatio = periodSharpeRatio
                    }
                  } else {
                    recalculatedSharpeRatio = periodSharpeRatio
                  }
                }
              }
            }
            
            // 重新计算胜率
            const recalculatedTotalStocks = recalculatedProfitableStocks + recalculatedLossStocks
            const recalculatedWinRate = recalculatedTotalStocks > 0 ? (recalculatedProfitableStocks / recalculatedTotalStocks) * 100 : 0
            
            // 更新整体统计数据
            totalInvestment = recalculatedTotalInvestment
            totalProfit = recalculatedTotalProfit
            totalReturnRate = recalculatedTotalReturnRate
            maxDrawdown = recalculatedMaxDrawdown
            maxDrawdownDateRange = recalculatedMaxDrawdownDateRange
            sharpeRatio = recalculatedSharpeRatio
            profitableStocks = recalculatedProfitableStocks
            lossStocks = recalculatedLossStocks
            winRate = recalculatedWinRate
          }
        }
      }

      // 计算所有周期的重复数总和
      const totalRepeatCount = filteredPeriodStats.reduce((sum, stat, index) => {
        if (index > 0 && stat.repeatCount !== undefined) {
          return sum + stat.repeatCount
        }
        return sum
      }, 0)
      
      statisticsResult.value = {
        totalRecords,
        profitableRecords: profitableStocks,  // 使用盈利股票数
        lossRecords: lossStocks,  // 使用亏损股票数
        winRate,
        totalInvestment,
        totalProfit,
        totalReturnRate,
        maxDrawdown,  // 最大回撤
        maxDrawdownDateRange,  // 最大回撤日期范围
        sharpeRatio,  // 夏普比
        totalRepeatCount,  // 所有周期的重复数总和
        periodStats: filteredPeriodStats,  // 使用筛选后的周期统计
        filteredRecords: recordDetails
      }
      
      // 重置展开状态
      expandedPeriods.value.clear()
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

<style scoped>
/* Range Slider 样式 */
.range-slider {
  -webkit-appearance: none;
  appearance: none;
  height: 8px;
  border-radius: 4px;
  outline: none;
  background: hsl(var(--muted));
  background-image: linear-gradient(
    to right,
    hsl(var(--primary)) 0%,
    hsl(var(--primary)) var(--slider-progress, 0%),
    hsl(var(--muted)) var(--slider-progress, 0%),
    hsl(var(--muted)) 100%
  );
  transition: background 0.2s ease;
}

.range-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: hsl(var(--primary));
  cursor: pointer;
  border: 3px solid hsl(var(--background));
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2), 0 0 0 2px hsl(var(--primary) / 0.1);
  transition: all 0.2s ease;
  position: relative;
  z-index: 1;
}

.range-slider::-webkit-slider-thumb:hover {
  transform: scale(1.1);
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.3);
}

.range-slider::-moz-range-thumb {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: hsl(var(--primary));
  cursor: pointer;
  border: 3px solid hsl(var(--background));
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2), 0 0 0 2px hsl(var(--primary) / 0.1);
  transition: all 0.2s ease;
  position: relative;
  z-index: 1;
}

.range-slider::-moz-range-thumb:hover {
  transform: scale(1.1);
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.3);
}

.range-slider:focus {
  outline: none;
}

.range-slider:focus::-webkit-slider-thumb {
  box-shadow: 0 0 0 3px hsl(var(--primary) / 0.2);
}

.range-slider:focus::-moz-range-thumb {
  box-shadow: 0 0 0 3px hsl(var(--primary) / 0.2);
}
</style>