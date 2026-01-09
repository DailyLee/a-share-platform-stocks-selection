<template>
  <div class="min-h-screen bg-background text-foreground">
    <!-- 参数帮助管理器 -->
    <ParameterHelpManager ref="parameterHelpManager" />

    <!-- 顶部导航栏 -->
    <header class="bg-card border-b border-border p-4 flex justify-between items-center sticky top-0 z-30">
      <div class="flex items-center">
        <img src="/gundam-logo.svg" alt="Gundam Logo" class="w-8 h-8 mr-2" />
        <h1 class="text-xl font-semibold hidden sm:block">股票平台期扫描工具</h1>
        <h1 class="text-xl font-semibold sm:hidden">平台期扫描</h1>
      </div>

      <div class="flex items-center space-x-2 sm:space-x-3">
        <!-- 平台期检查入口 -->
        <router-link to="/platform/check" class="flex items-center justify-center px-2 sm:px-3 py-1.5 sm:py-2 rounded-md bg-gundam-yellow text-white hover:bg-gundam-yellow/80 transition-colors">
          <i class="fas fa-search mr-1 sm:mr-2"></i>
          <span class="hidden sm:inline">单股检查</span>
        </router-link>

        <!-- 案例管理入口 -->
        <button @click="showCaseManager = true"
          class="flex items-center justify-center px-2 sm:px-3 py-1.5 sm:py-2 rounded-md bg-gundam-blue text-white hover:bg-gundam-blue/80 transition-colors">
          <i class="fas fa-book mr-1 sm:mr-2"></i>
          <span class="hidden sm:inline">案例管理</span>
        </button>

        <!-- 缓存管理入口 -->
        <router-link to="/platform/cache" class="flex items-center justify-center px-2 sm:px-3 py-1.5 sm:py-2 rounded-md bg-green-600 text-white hover:bg-green-600/80 transition-colors">
          <i class="fas fa-database mr-1 sm:mr-2"></i>
          <span class="hidden sm:inline">缓存管理</span>
        </router-link>

        <!-- 扫描历史入口 -->
        <button @click="showScanHistoryDialog = true; loadScanHistory()"
          class="flex items-center justify-center px-2 sm:px-3 py-1.5 sm:py-2 rounded-md bg-purple-600 text-white hover:bg-purple-600/80 transition-colors">
          <i class="fas fa-history mr-1 sm:mr-2"></i>
          <span class="hidden sm:inline">扫描历史</span>
        </button>

        <!-- 批量扫描入口 -->
        <router-link to="/platform/batch-scan" class="flex items-center justify-center px-2 sm:px-3 py-1.5 sm:py-2 rounded-md bg-orange-600 text-white hover:bg-orange-600/80 transition-colors">
          <i class="fas fa-tasks mr-1 sm:mr-2"></i>
          <span class="hidden sm:inline">批量扫描</span>
        </router-link>

        <!-- 主题切换 -->
        <ThemeToggle />
      </div>
    </header>

    <!-- 完整K线图弹窗 -->
    <FullKlineChart v-model:visible="showFullChart"
      :title="selectedStock ? `${selectedStock.name} (${selectedStock.code})` : '股票详情'"
      :klineData="selectedStock ? selectedStock.kline_data : []"
      :markLines="selectedStock ? selectedStock.markLines : []"
      :supportLevels="selectedStock ? selectedStock.supportLevels : []"
      :resistanceLevels="selectedStock ? selectedStock.resistanceLevels : []" :isDarkMode="isDarkMode" />

    <!-- 案例管理弹窗 -->
    <div v-if="showCaseManager"
      class="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center overflow-auto">
      <div class="bg-background rounded-lg shadow-xl w-full max-w-6xl h-[90vh] flex flex-col">
        <div class="flex-1 overflow-auto">
          <CaseManager @close="showCaseManager = false" />
        </div>
      </div>
    </div>

    <!-- 扫描历史对话框 -->
    <transition name="fade">
      <div v-if="showScanHistoryDialog" class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" @click.self="showScanHistoryDialog = false">
        <div class="bg-card border border-border rounded-lg shadow-lg max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
          <!-- 对话框头部 -->
          <div class="p-4 sm:p-6 border-b border-border">
            <div class="flex justify-between items-center mb-4">
              <h2 class="text-lg font-semibold flex items-center">
                <i class="fas fa-history mr-2 text-primary"></i>
                扫描历史记录
              </h2>
              <button
                @click="showScanHistoryDialog = false"
                class="text-muted-foreground hover:text-foreground transition-colors"
              >
                <i class="fas fa-times text-xl"></i>
              </button>
            </div>
            <!-- 筛选器 -->
            <DateRangeFilter
              :data="scanHistory"
              date-field="scanDate"
              :loading="scanHistoryLoading"
              @query="handleScanHistoryQuery"
            />
          </div>

          <!-- 对话框内容 -->
          <div class="flex-1 overflow-y-auto p-4 sm:p-6">
            <div v-if="scanHistoryLoading" class="text-center py-8">
              <i class="fas fa-spinner fa-spin text-2xl mb-4 text-primary"></i>
              <p class="text-muted-foreground">加载中...</p>
            </div>
            <div v-else-if="scanHistory.length === 0" class="text-center py-8 text-muted-foreground">
              <i class="fas fa-inbox text-4xl mb-4"></i>
              <p>暂无扫描历史记录</p>
            </div>
            <div v-else class="space-y-6">
              <!-- 按日期分组显示 -->
              <div v-for="(records, scanDate) in filteredScanHistoryGroupedByDate" :key="scanDate" class="space-y-3">
                <div class="sticky top-0 bg-card/95 backdrop-blur-sm border-b border-border pb-2 mb-3">
                  <h3 class="text-md font-semibold text-primary flex items-center">
                    <i class="fas fa-calendar-alt mr-2"></i>
                    扫描日期: {{ scanDate }}
                    <span class="ml-2 text-sm text-muted-foreground">({{ records.length }} 条记录)</span>
                  </h3>
                </div>
                <div
                  v-for="(record, index) in records"
                  :key="record.id"
                  class="card p-4 hover:bg-muted/30 transition-colors"
                >
                  <div class="flex justify-between items-start mb-2">
                    <div class="flex-1 cursor-pointer" @click="viewScanHistoryRecord(record)">
                      <h3 class="font-semibold text-sm mb-1">
                        扫描 #{{ records.length - index }}
                      </h3>
                      <p class="text-xs text-muted-foreground mt-1">
                        {{ formatDateTime(record.createdAt) }}
                      </p>
                    </div>
                    <div class="flex items-center gap-2">
                      <button
                        @click.stop="loadScanHistoryToPage(record)"
                        class="px-3 py-1.5 text-xs rounded-md bg-green-600 text-white hover:bg-green-600/80 transition-colors flex items-center"
                        title="加载到扫描工具"
                      >
                        <i class="fas fa-upload mr-1"></i>
                        加载结果
                      </button>
                      <button
                        @click.stop="goToBacktestFromScanHistory(record)"
                        class="px-3 py-1.5 text-xs rounded-md bg-primary text-primary-foreground hover:bg-primary/80 transition-colors flex items-center"
                        title="数据回测"
                      >
                        <i class="fas fa-chart-line mr-1"></i>
                        数据回测
                      </button>
                      <button
                        @click.stop="showDeleteScanHistoryConfirm(record.id)"
                        class="px-2 py-1 text-xs rounded-md bg-destructive/10 text-destructive hover:bg-destructive/20 transition-colors"
                        title="删除"
                      >
                        <i class="fas fa-trash"></i>
                      </button>
                    </div>
                  </div>
                  <div class="grid grid-cols-2 gap-2 text-xs cursor-pointer" @click="viewScanHistoryRecord(record)">
                    <div>
                      <span class="text-muted-foreground">股票数量:</span>
                      <span class="ml-1 font-medium">{{ record.stockCount }}</span>
                    </div>
                    <div>
                      <span class="text-muted-foreground">窗口期:</span>
                      <span class="ml-1 font-medium">{{ record.scanConfig?.windows?.join(', ') || 'N/A' }}</span>
                    </div>
                    <div v-if="record.totalScanned !== null && record.totalScanned !== undefined && record.successCount !== null && record.successCount !== undefined">
                      <span class="text-muted-foreground">扫描统计:</span>
                      <span class="ml-1 font-medium">{{ record.successCount }}/{{ record.totalScanned }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 对话框底部 -->
          <div class="p-4 sm:p-6 border-t border-border flex justify-between items-center">
            <button
              v-if="scanHistory.length > 0"
              @click="showClearScanHistoryConfirm"
              class="px-4 py-2 rounded-md bg-destructive/10 text-destructive hover:bg-destructive/20 transition-colors text-sm"
            >
              <i class="fas fa-trash mr-2"></i>
              清空历史
            </button>
            <div class="flex-1"></div>
            <button
              @click="showScanHistoryDialog = false"
              class="px-4 py-2 rounded-md bg-primary text-primary-foreground hover:bg-primary/80 transition-colors text-sm"
            >
              关闭
            </button>
          </div>
        </div>
      </div>
    </transition>

    <!-- 扫描历史详情对话框 -->
    <transition name="fade">
      <div v-if="selectedScanHistoryRecord" class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
        <div class="bg-card border border-border rounded-lg shadow-lg max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col" @click.stop>
          <!-- 对话框头部 -->
          <div class="p-4 sm:p-6 border-b border-border flex justify-between items-center">
            <h2 class="text-lg font-semibold flex items-center">
              <i class="fas fa-info-circle mr-2 text-primary"></i>
              扫描历史详情
            </h2>
            <button
              @click="selectedScanHistoryRecord = null"
              class="text-muted-foreground hover:text-foreground transition-colors"
            >
              <i class="fas fa-times text-xl"></i>
            </button>
          </div>

          <!-- 对话框内容 -->
          <div class="flex-1 overflow-y-auto p-4 sm:p-6">
            <div v-if="selectedScanHistoryRecord" class="space-y-4">
              <div class="grid grid-cols-2 gap-4">
                <div>
                  <span class="text-sm text-muted-foreground">扫描日期:</span>
                  <p class="font-medium">{{ selectedScanHistoryRecord.scanDate }}</p>
                </div>
                <div>
                  <span class="text-sm text-muted-foreground">创建时间:</span>
                  <p class="font-medium">{{ formatDateTime(selectedScanHistoryRecord.createdAt) }}</p>
                </div>
                <div>
                  <span class="text-sm text-muted-foreground">股票数量:</span>
                  <p class="font-medium">{{ selectedScanHistoryRecord.stockCount }}</p>
                </div>
                <div>
                  <span class="text-sm text-muted-foreground">窗口期:</span>
                  <p class="font-medium">{{ selectedScanHistoryRecord.scanConfig?.windows?.join(', ') || 'N/A' }}</p>
                </div>
              </div>

              <!-- 扫描配置详情（可折叠） -->
              <div class="border border-border rounded-lg overflow-hidden">
                <button
                  @click="showScanConfigDetails = !showScanConfigDetails"
                  class="w-full px-4 py-3 flex items-center justify-between hover:bg-muted/30 transition-colors"
                >
                  <span class="font-semibold flex items-center">
                    <i class="fas fa-cog mr-2 text-primary"></i>
                    扫描参数配置
                  </span>
                  <i 
                    :class="['fas transition-transform', showScanConfigDetails ? 'fa-chevron-up' : 'fa-chevron-down']"
                  ></i>
                </button>
                <div v-show="showScanConfigDetails" class="px-4 py-4 bg-muted/10 border-t border-border">
                  <div v-if="selectedScanHistoryRecord.scanConfig" class="space-y-4">
                    <!-- 窗口期设置 -->
                    <div>
                      <h4 class="text-sm font-semibold mb-2 text-primary">窗口期设置</h4>
                      <div class="grid grid-cols-2 gap-2 text-sm">
                        <div>
                          <span class="text-muted-foreground">窗口期:</span>
                          <span class="ml-2">{{ selectedScanHistoryRecord.scanConfig.windows?.join(', ') || 'N/A' }}</span>
                        </div>
                        <div v-if="selectedScanHistoryRecord.scanConfig.use_window_weights">
                          <span class="text-muted-foreground">窗口权重:</span>
                          <span class="ml-2">{{ JSON.stringify(selectedScanHistoryRecord.scanConfig.window_weights || {}) }}</span>
                        </div>
                      </div>
                    </div>

                    <!-- 价格模式阈值 -->
                    <div>
                      <h4 class="text-sm font-semibold mb-2 text-primary">价格模式阈值</h4>
                      <div class="grid grid-cols-2 gap-2 text-sm">
                        <div>
                          <span class="text-muted-foreground">箱体阈值:</span>
                          <span class="ml-2">{{ selectedScanHistoryRecord.scanConfig.box_threshold ?? 'N/A' }}</span>
                        </div>
                        <div>
                          <span class="text-muted-foreground">MA差异阈值:</span>
                          <span class="ml-2">{{ selectedScanHistoryRecord.scanConfig.ma_diff_threshold ?? 'N/A' }}</span>
                        </div>
                        <div>
                          <span class="text-muted-foreground">波动率阈值:</span>
                          <span class="ml-2">{{ selectedScanHistoryRecord.scanConfig.volatility_threshold ?? 'N/A' }}</span>
                        </div>
                        <div v-if="selectedScanHistoryRecord.scanConfig.box_quality_threshold !== undefined">
                          <span class="text-muted-foreground">箱体质量阈值:</span>
                          <span class="ml-2">{{ selectedScanHistoryRecord.scanConfig.box_quality_threshold }}</span>
                        </div>
                      </div>
                    </div>

                    <!-- 成交量分析设置 -->
                    <div v-if="selectedScanHistoryRecord.scanConfig.use_volume_analysis">
                      <h4 class="text-sm font-semibold mb-2 text-primary">成交量分析设置</h4>
                      <div class="grid grid-cols-2 gap-2 text-sm">
                        <div>
                          <span class="text-muted-foreground">成交量变化阈值:</span>
                          <span class="ml-2">{{ selectedScanHistoryRecord.scanConfig.volume_change_threshold ?? 'N/A' }}</span>
                        </div>
                        <div>
                          <span class="text-muted-foreground">成交量稳定性阈值:</span>
                          <span class="ml-2">{{ selectedScanHistoryRecord.scanConfig.volume_stability_threshold ?? 'N/A' }}</span>
                        </div>
                        <div>
                          <span class="text-muted-foreground">成交量增长阈值:</span>
                          <span class="ml-2">{{ selectedScanHistoryRecord.scanConfig.volume_increase_threshold ?? 'N/A' }}</span>
                        </div>
                      </div>
                    </div>

                    <!-- 技术指标设置 -->
                    <div>
                      <h4 class="text-sm font-semibold mb-2 text-primary">技术指标设置</h4>
                      <div class="grid grid-cols-2 gap-2 text-sm">
                        <div>
                          <span class="text-muted-foreground">使用突破预测:</span>
                          <span class="ml-2">{{ selectedScanHistoryRecord.scanConfig.use_breakthrough_prediction ? '是' : '否' }}</span>
                        </div>
                        <div v-if="selectedScanHistoryRecord.scanConfig.use_breakthrough_confirmation">
                          <span class="text-muted-foreground">突破确认天数:</span>
                          <span class="ml-2">{{ selectedScanHistoryRecord.scanConfig.breakthrough_confirmation_days ?? 'N/A' }}</span>
                        </div>
                        <div>
                          <span class="text-muted-foreground">使用箱体检测:</span>
                          <span class="ml-2">{{ selectedScanHistoryRecord.scanConfig.use_box_detection ? '是' : '否' }}</span>
                        </div>
                      </div>
                    </div>

                    <!-- 位置分析设置 -->
                    <div v-if="selectedScanHistoryRecord.scanConfig.use_low_position">
                      <h4 class="text-sm font-semibold mb-2 text-primary">位置分析设置</h4>
                      <div class="grid grid-cols-2 gap-2 text-sm">
                        <div>
                          <span class="text-muted-foreground">高点回看天数:</span>
                          <span class="ml-2">{{ selectedScanHistoryRecord.scanConfig.high_point_lookback_days ?? 'N/A' }}</span>
                        </div>
                        <div>
                          <span class="text-muted-foreground">下跌周期天数:</span>
                          <span class="ml-2">{{ selectedScanHistoryRecord.scanConfig.decline_period_days ?? 'N/A' }}</span>
                        </div>
                        <div>
                          <span class="text-muted-foreground">下跌阈值:</span>
                          <span class="ml-2">{{ selectedScanHistoryRecord.scanConfig.decline_threshold ?? 'N/A' }}</span>
                        </div>
                      </div>
                    </div>

                    <!-- 快速下跌检测设置 -->
                    <div v-if="selectedScanHistoryRecord.scanConfig.use_rapid_decline_detection">
                      <h4 class="text-sm font-semibold mb-2 text-primary">快速下跌检测设置</h4>
                      <div class="grid grid-cols-2 gap-2 text-sm">
                        <div>
                          <span class="text-muted-foreground">快速下跌天数:</span>
                          <span class="ml-2">{{ selectedScanHistoryRecord.scanConfig.rapid_decline_days ?? 'N/A' }}</span>
                        </div>
                        <div>
                          <span class="text-muted-foreground">快速下跌阈值:</span>
                          <span class="ml-2">{{ selectedScanHistoryRecord.scanConfig.rapid_decline_threshold ?? 'N/A' }}</span>
                        </div>
                      </div>
                    </div>

                    <!-- 基本面分析设置 -->
                    <div v-if="selectedScanHistoryRecord.scanConfig.use_fundamental_filter">
                      <h4 class="text-sm font-semibold mb-2 text-primary">基本面分析设置</h4>
                      <div class="grid grid-cols-2 gap-2 text-sm">
                        <div>
                          <span class="text-muted-foreground">营收增长百分位:</span>
                          <span class="ml-2">{{ selectedScanHistoryRecord.scanConfig.revenue_growth_percentile ?? 'N/A' }}</span>
                        </div>
                        <div>
                          <span class="text-muted-foreground">净利润增长百分位:</span>
                          <span class="ml-2">{{ selectedScanHistoryRecord.scanConfig.profit_growth_percentile ?? 'N/A' }}</span>
                        </div>
                        <div>
                          <span class="text-muted-foreground">ROE百分位:</span>
                          <span class="ml-2">{{ selectedScanHistoryRecord.scanConfig.roe_percentile ?? 'N/A' }}</span>
                        </div>
                        <div>
                          <span class="text-muted-foreground">资产负债率百分位:</span>
                          <span class="ml-2">{{ selectedScanHistoryRecord.scanConfig.liability_percentile ?? 'N/A' }}</span>
                        </div>
                        <div>
                          <span class="text-muted-foreground">PE百分位:</span>
                          <span class="ml-2">{{ selectedScanHistoryRecord.scanConfig.pe_percentile ?? 'N/A' }}</span>
                        </div>
                        <div>
                          <span class="text-muted-foreground">PB百分位:</span>
                          <span class="ml-2">{{ selectedScanHistoryRecord.scanConfig.pb_percentile ?? 'N/A' }}</span>
                        </div>
                        <div>
                          <span class="text-muted-foreground">检查年数:</span>
                          <span class="ml-2">{{ selectedScanHistoryRecord.scanConfig.fundamental_years_to_check ?? 'N/A' }}</span>
                        </div>
                      </div>
                    </div>

                    <!-- 系统设置 -->
                    <div>
                      <h4 class="text-sm font-semibold mb-2 text-primary">系统设置</h4>
                      <div class="grid grid-cols-2 gap-2 text-sm">
                        <div>
                          <span class="text-muted-foreground">最大并发数:</span>
                          <span class="ml-2">{{ selectedScanHistoryRecord.scanConfig.max_workers ?? 'N/A' }}</span>
                        </div>
                        <div>
                          <span class="text-muted-foreground">重试次数:</span>
                          <span class="ml-2">{{ selectedScanHistoryRecord.scanConfig.retry_attempts ?? 'N/A' }}</span>
                        </div>
                        <div>
                          <span class="text-muted-foreground">重试延迟(秒):</span>
                          <span class="ml-2">{{ selectedScanHistoryRecord.scanConfig.retry_delay ?? 'N/A' }}</span>
                        </div>
                        <div v-if="selectedScanHistoryRecord.scanConfig.expected_count !== undefined">
                          <span class="text-muted-foreground">预期数量:</span>
                          <span class="ml-2">{{ selectedScanHistoryRecord.scanConfig.expected_count }}</span>
                        </div>
                        <div v-if="selectedScanHistoryRecord.scanConfig.use_local_database_first !== undefined">
                          <span class="text-muted-foreground">优先使用本地数据库:</span>
                          <span class="ml-2">{{ selectedScanHistoryRecord.scanConfig.use_local_database_first ? '是' : '否' }}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                  <div v-else class="text-sm text-muted-foreground">
                    暂无配置信息
                  </div>
                </div>
              </div>

              <div v-if="selectedScanHistoryRecord.scannedStocks && selectedScanHistoryRecord.scannedStocks.length > 0">
                <h3 class="text-md font-semibold mb-3">扫描结果股票列表 ({{ selectedScanHistoryRecord.scannedStocks.length }} 只)</h3>
                <div class="space-y-3 max-h-[60vh] overflow-y-auto">
                  <div
                    v-for="stock in selectedScanHistoryRecord.scannedStocks"
                    :key="stock.code"
                    class="border border-border rounded-lg p-3 hover:bg-muted/30 transition-colors"
                  >
                    <div class="flex justify-between items-start mb-2">
                      <div class="flex-1">
                        <div class="font-medium">{{ stock.name }}</div>
                        <div class="text-sm text-muted-foreground">{{ stock.code }}</div>
                        <div v-if="stock.industry" class="text-xs text-muted-foreground mt-1">
                          {{ stock.industry }}
                        </div>
                      </div>
                      <button
                        @click.stop="goToStockCheck(stock)"
                        class="px-2 py-1 text-xs rounded-md bg-primary/10 text-primary hover:bg-primary/20 transition-colors ml-2"
                        title="单股查询"
                      >
                        <i class="fas fa-search"></i>
                      </button>
                    </div>

                    <!-- 选择理由（可折叠） -->
                    <div v-if="stock.selection_reasons && Object.keys(stock.selection_reasons).length > 0" class="mt-2">
                      <div
                        @click="expandedReasons[stock.code] = !expandedReasons[stock.code]"
                        class="flex items-center justify-between cursor-pointer text-xs text-muted-foreground hover:text-foreground transition-colors"
                      >
                        <span class="font-medium">选择理由</span>
                        <i :class="[
                          'fas transition-transform duration-300',
                          expandedReasons[stock.code] ? 'fa-chevron-up' : 'fa-chevron-down'
                        ]"></i>
                      </div>
                      <div :class="[
                        'overflow-hidden transition-all duration-300 mt-1',
                        expandedReasons[stock.code] ? 'h-auto opacity-100' : 'h-0 opacity-0'
                      ]">
                        <div v-if="Object.keys(stock.selection_reasons || {}).length > 0"
                          class="p-2 bg-muted/10 rounded">
                          <div v-for="(reason, window) in stock.selection_reasons" :key="window"
                            class="mb-1 text-xs text-muted-foreground">
                            <span class="font-medium text-primary">{{ window }}天:</span>
                            <span v-html="formatSelectionReason(reason)"></span>

                            <!-- 成交量分析结果（每个窗口期） -->
                            <div v-if="stock.volume_analysis && stock.volume_analysis[window]"
                              class="mt-2 border-t border-border pt-1">
                              <div class="text-xs font-medium text-primary">成交量分析:</div>
                              <div v-if="stock.volume_analysis[window].has_consolidation_volume"
                                class="text-xs text-muted-foreground flex items-center">
                                <i class="fas fa-check-circle text-green-500 mr-1"></i>
                                成交量萎缩
                              </div>
                              <div v-if="stock.volume_analysis[window].has_breakthrough"
                                class="text-xs text-muted-foreground flex items-center">
                                <i class="fas fa-arrow-circle-up text-primary mr-1"></i>
                                成交量突破 ({{
                                  stock.volume_analysis[window].breakthrough_details?.volume_increase_ratio?.toFixed(2) || 'N/A' }}倍)
                              </div>
                              <!-- 成交量变化和稳定性数值 -->
                              <div v-if="stock.volume_analysis[window].consolidation_details" class="mt-1 space-y-0.5">
                                <div v-if="stock.volume_analysis[window].consolidation_details.volume_change_ratio !== null && stock.volume_analysis[window].consolidation_details.volume_change_ratio !== undefined"
                                  class="text-xs text-muted-foreground">
                                  <span class="font-medium">成交量变化:</span> 
                                  {{ stock.volume_analysis[window].consolidation_details.volume_change_ratio.toFixed(4) }}
                                </div>
                                <div v-if="stock.volume_analysis[window].consolidation_details.volume_stability !== null && stock.volume_analysis[window].consolidation_details.volume_stability !== undefined"
                                  class="text-xs text-muted-foreground">
                                  <span class="font-medium">成交量稳定性:</span> 
                                  {{ stock.volume_analysis[window].consolidation_details.volume_stability.toFixed(4) }}
                                </div>
                              </div>
                            </div>

                            <!-- 换手率分析结果（每个窗口期） -->
                            <div v-if="getTurnoverRateForWindow(stock, window) !== null" class="mt-2 border-t border-border pt-1">
                              <div class="text-xs font-medium text-primary">换手率分析:</div>
                              <div class="text-xs text-muted-foreground flex items-center">
                                <i class="fas fa-exchange-alt text-blue-500 mr-1"></i>
                                <span class="font-medium">平均换手率:</span> 
                                {{ getTurnoverRateForWindow(stock, window).toFixed(2) }}%
                              </div>
                            </div>

                             <!-- 相对强度/涨跌幅 -->
                            <div v-if="stock.outperform_index !== null && stock.outperform_index !== undefined" class="mb-3 pb-3 border-b border-border">
                              <div class="text-xs font-medium text-primary mb-1.5">相对强度/涨跌幅:</div>
                              <div class="space-y-1">
                                <!-- 相对强度 -->
                                <div class="flex items-center">
                                  <span class="text-xs text-muted-foreground mr-2 w-16">相对强度:</span>
                                  <span
                                    :class="[
                                      'px-2 py-0.5 rounded text-xs font-medium',
                                      stock.outperform_index >= 0 ? 'bg-green-500/20 text-green-600 dark:text-green-400' : 'bg-red-500/20 text-red-600 dark:text-red-400'
                                    ]">
                                    {{ stock.outperform_index >= 0 ? '+' : '' }}{{ stock.outperform_index.toFixed(2) }}%
                                  </span>
                                </div>
                                <!-- 股票涨跌幅 -->
                                <div v-if="stock.stock_return !== null && stock.stock_return !== undefined" class="flex items-center">
                                  <span class="text-xs text-muted-foreground mr-2 w-16">股票涨跌:</span>
                                  <span
                                    :class="[
                                      'px-2 py-0.5 rounded text-xs font-medium',
                                      stock.stock_return >= 0 ? 'bg-blue-500/20 text-blue-600 dark:text-blue-400' : 'bg-orange-500/20 text-orange-600 dark:text-orange-400'
                                    ]">
                                    {{ stock.stock_return >= 0 ? '+' : '' }}{{ stock.stock_return.toFixed(2) }}%
                                  </span>
                                </div>
                                <!-- 大盘涨跌幅 -->
                                <div v-if="stock.market_return !== null && stock.market_return !== undefined" class="flex items-center">
                                  <span class="text-xs text-muted-foreground mr-2 w-16">大盘涨跌:</span>
                                  <span
                                    :class="[
                                      'px-2 py-0.5 rounded text-xs font-medium',
                                      stock.market_return >= 0 ? 'bg-purple-500/20 text-purple-600 dark:text-purple-400' : 'bg-pink-500/20 text-pink-600 dark:text-pink-400'
                                    ]">
                                    {{ stock.market_return >= 0 ? '+' : '' }}{{ stock.market_return.toFixed(2) }}%
                                  </span>
                                </div>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 对话框底部 -->
          <div class="p-4 sm:p-6 border-t border-border flex justify-between items-center">
            <button
              v-if="selectedScanHistoryRecord && selectedScanHistoryRecord.scannedStocks && selectedScanHistoryRecord.scannedStocks.length > 0"
              @click="goToBacktestFromScanHistory(selectedScanHistoryRecord)"
              class="px-4 py-2 rounded-md bg-primary text-primary-foreground hover:bg-primary/80 transition-colors text-sm flex items-center"
            >
              <i class="fas fa-chart-line mr-2"></i>
              数据回测
            </button>
            <div class="flex-1"></div>
            <button
              @click="selectedScanHistoryRecord = null"
              class="px-4 py-2 rounded-md bg-muted text-muted-foreground hover:bg-muted/80 transition-colors text-sm"
            >
              关闭
            </button>
          </div>
        </div>
      </div>
    </transition>

    <!-- 主内容区 -->
    <main class="p-4 sm:p-6 md:p-8">
      <div class="max-w-6xl mx-auto">

        <!-- 参数配置卡片 -->
        <div class="card p-4 sm:p-6 mb-6">
          <h2 class="text-lg font-semibold mb-4 flex items-center">
            <i class="fas fa-sliders-h mr-2 text-primary"></i>
            扫描参数配置
          </h2>
          <ScanConfigForm
            v-model="config"
            :show-scan-date="true"
            ref="scanConfigFormRef"
          />
          <div class="flex items-center justify-center mt-6">
            <button @click="fetchPlatformStocks" :disabled="loading" class="btn btn-primary py-2 px-6" type="button">
              <i class="fas fa-search mr-2" v-if="!loading"></i>
              <i class="fas fa-spinner fa-spin mr-2" v-if="loading"></i>
              {{ loading ? '扫描中...' : '开始扫描' }}
            </button>
          </div>
        </div>

        <!-- 任务进度组件 -->
        <transition name="fade">
          <TaskProgress v-if="taskStatus && taskStatus !== 'completed'" :status="taskStatus" :progress="taskProgress"
            :message="taskMessage" :error="taskError" @retry="fetchPlatformStocks" />
        </transition>

        <!-- 错误提示 -->
        <transition name="fade">
          <div v-if="error && !taskStatus"
            class="bg-destructive/10 border border-destructive text-destructive px-4 py-3 rounded-md my-5" role="alert">
            <div class="flex items-center">
              <i class="fas fa-exclamation-circle mr-2"></i>
              <strong class="font-bold">发生错误:</strong>
              <span class="ml-2"> {{ error }}</span>
            </div>
          </div>
        </transition>

        <!-- 扫描结果 -->
        <transition name="slide-up">
          <div v-if="(!loading || taskStatus === 'completed') && platformStocks.length > 0"
            class="card overflow-hidden">
            <div class="p-4 border-b border-border flex justify-between items-center">
              <h2 class="text-lg font-semibold flex items-center">
                <i class="fas fa-list-ul mr-2 text-primary"></i>
                扫描结果
              </h2>
              <div class="flex space-x-2">
                <button 
                  @click="goToBacktest" 
                  :disabled="!selectedStocks || selectedStocks.length === 0"
                  class="btn btn-primary text-xs py-1 px-2"
                  :class="!selectedStocks || selectedStocks.length === 0 ? 'opacity-50 cursor-not-allowed' : ''"
                >
                  <i class="fas fa-chart-line mr-1"></i> 数据回测
                </button>
                <button @click="exportToCSV" class="btn btn-secondary text-xs py-1 px-2">
                  <i class="fas fa-download mr-1"></i> 导出
                </button>
                <button 
                  @click="showFilterPanel = !showFilterPanel" 
                  class="btn btn-secondary text-xs py-1 px-2"
                  :class="showFilterPanel ? 'bg-primary text-primary-foreground' : ''"
                >
                  <i class="fas fa-filter mr-1"></i> 筛选
                  <span v-if="selectedPlatformPeriods.length > 0 && selectedPlatformPeriods.length < availablePlatformPeriods.length" 
                    class="ml-1 px-1 bg-primary/20 rounded text-xs">
                    {{ selectedPlatformPeriods.length }}
                  </span>
                </button>
              </div>
            </div>
            
            <!-- 筛选面板 -->
            <div v-if="showFilterPanel" class="p-4 border-b border-border bg-muted/20">
              <div class="mb-3">
                <h3 class="text-sm font-semibold mb-2 flex items-center">
                  <i class="fas fa-filter mr-1 text-primary"></i>
                  平台期筛选
                </h3>
                <div class="flex flex-wrap gap-2">
                  <label 
                    v-for="period in availablePlatformPeriods" 
                    :key="period"
                    class="flex items-center cursor-pointer px-2 py-1 rounded border border-border hover:bg-muted/50 transition-colors"
                    :class="selectedPlatformPeriods.includes(period) ? 'bg-primary/20 border-primary' : ''"
                  >
                    <input
                      type="checkbox"
                      :value="period"
                      v-model="selectedPlatformPeriods"
                      class="checkbox mr-1.5"
                    />
                    <span class="text-xs">{{ period }}天</span>
                  </label>
                  <button
                    @click="selectAllPlatformPeriods"
                    class="px-2 py-1 text-xs rounded border border-border hover:bg-muted/50 transition-colors"
                  >
                    全选
                  </button>
                  <button
                    @click="clearPlatformPeriodFilter"
                    class="px-2 py-1 text-xs rounded border border-border hover:bg-muted/50 transition-colors"
                  >
                    清空
                  </button>
                </div>
                <p class="text-xs text-muted-foreground mt-2">
                  已选择 {{ selectedPlatformPeriods.length }} / {{ availablePlatformPeriods.length }} 个平台期
                </p>
              </div>
              
              <!-- 板块筛选 -->
              <div class="mb-3">
                <h3 class="text-sm font-semibold mb-2 flex items-center">
                  <i class="fas fa-building mr-1 text-primary"></i>
                  板块筛选
                </h3>
                <div class="flex flex-wrap gap-2">
                  <label 
                    class="flex items-center cursor-pointer px-2 py-1 rounded border border-border hover:bg-muted/50 transition-colors"
                    :class="selectedBoards.includes('创业板') ? 'bg-primary/20 border-primary' : ''"
                  >
                    <input
                      type="checkbox"
                      value="创业板"
                      v-model="selectedBoards"
                      class="checkbox mr-1.5"
                    />
                    <span class="text-xs">创业板</span>
                  </label>
                  <label 
                    class="flex items-center cursor-pointer px-2 py-1 rounded border border-border hover:bg-muted/50 transition-colors"
                    :class="selectedBoards.includes('科创板') ? 'bg-primary/20 border-primary' : ''"
                  >
                    <input
                      type="checkbox"
                      value="科创板"
                      v-model="selectedBoards"
                      class="checkbox mr-1.5"
                    />
                    <span class="text-xs">科创板</span>
                  </label>
                  <label 
                    class="flex items-center cursor-pointer px-2 py-1 rounded border border-border hover:bg-muted/50 transition-colors"
                    :class="selectedBoards.includes('主板') ? 'bg-primary/20 border-primary' : ''"
                  >
                    <input
                      type="checkbox"
                      value="主板"
                      v-model="selectedBoards"
                      class="checkbox mr-1.5"
                    />
                    <span class="text-xs">主板</span>
                  </label>
                  <button
                    @click="selectedBoards = ['创业板', '科创板', '主板']"
                    class="px-2 py-1 text-xs rounded border border-border hover:bg-muted/50 transition-colors"
                  >
                    全选
                  </button>
                  <button
                    @click="selectedBoards = []"
                    class="px-2 py-1 text-xs rounded border border-border hover:bg-muted/50 transition-colors"
                  >
                    清空
                  </button>
                </div>
                <p class="text-xs text-muted-foreground mt-2">
                  已选择 {{ selectedBoards.length }} / 3 个板块
                </p>
              </div>
            </div>
            
            <!-- 桌面端表格视图 -->
            <div class="hidden md:block overflow-x-auto">
              <table class="w-full">
                <thead class="bg-muted/50">
                  <tr>
                    <th scope="col"
                      class="px-2 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider w-[60px]">
                      <div class="flex items-center space-x-1">
                        <input
                          type="checkbox"
                          :checked="isAllSelected"
                          @change="toggleSelectAll"
                          class="checkbox"
                        />
                        <span class="text-xs text-muted-foreground whitespace-nowrap">
                          ({{ selectedStocks ? selectedStocks.length : 0 }} / {{ filteredStocks.length }})
                        </span>
                      </div>
                    </th>
                    <th scope="col"
                      class="px-2 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider w-[80px]">
                      <div class="flex items-center">
                        <i class="fas fa-hashtag mr-1"></i> 代码
                      </div>
                    </th>
                    <th scope="col"
                      class="px-2 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider w-[100px]">
                      <div class="flex items-center">
                        <i class="fas fa-font mr-1"></i> 名称
                      </div>
                    </th>
                    <th scope="col"
                      class="px-2 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider w-[60px]">
                      <div class="flex items-center">
                        <i class="fas fa-tag mr-1"></i> 行业
                      </div>
                    </th>
                    <th scope="col"
                      class="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider w-[500px] min-w-[400px]">
                      <div class="flex items-center">
                        <i class="fas fa-check-circle mr-1"></i> 选择理由
                      </div>
                    </th>
                    <th scope="col"
                      class="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider w-[500px] min-w-[400px]">
                      <div class="flex items-center">
                        <i class="fas fa-chart-line mr-1"></i> 近期K线
                      </div>
                    </th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-border">
                  <tr v-for="stock in paginatedStocks" :key="stock.code">
                    <td class="px-2 py-3 whitespace-nowrap w-[60px]">
                      <input
                        type="checkbox"
                        :checked="isStockSelected(stock.code)"
                        @change="toggleStockSelection(stock)"
                        class="checkbox"
                      />
                    </td>
                    <td class="px-2 py-3 whitespace-nowrap text-sm font-medium w-[80px]">{{ stock.code }}</td>
                    <td class="px-2 py-3 whitespace-nowrap text-sm w-[100px]">{{ stock.name }}</td>
                    <td class="px-2 py-3 whitespace-nowrap text-sm w-[60px]">
                      <span class="px-1 py-0.5 rounded-full text-xs bg-primary/20 text-primary">
                        {{ stock.industry || '未知行业' }}
                      </span>
                    </td>
                    <td class="px-4 py-3 text-sm">
                      <!-- 选择理由标题栏（可点击） -->
                      <div @click="toggleReasonExpand(stock.code)"
                        class="flex items-center justify-between cursor-pointer p-1.5 rounded hover:bg-muted/50 transition-colors">
                        <div class="flex items-center">
                          <i class="fas fa-info-circle text-primary mr-1.5"></i>
                          <span class="font-medium">选择理由</span>
                          <span v-if="Object.keys(stock.selection_reasons || {}).length > 0"
                            class="ml-1.5 text-xs px-1.5 py-0.5 rounded-full bg-primary/10 text-primary">
                            {{ Object.keys(stock.selection_reasons || {}).length }}
                          </span>
                        </div>
                        <i :class="[
                          'fas transition-transform duration-300',
                          expandedReasons[stock.code] ? 'fa-chevron-up' : 'fa-chevron-down'
                        ]"></i>
                      </div>

                      <!-- 选择理由详情（可折叠） -->
                      <div :id="`reason-${stock.code.replace(/\./g, '_').replace(/[^\w-]/g, '')}`" :class="[
                        'overflow-hidden transition-all duration-300 mt-1',
                        expandedReasons[stock.code] === undefined || expandedReasons[stock.code] ? 'h-auto opacity-100' : 'h-0 opacity-0'
                      ]">
                        <div v-if="Object.keys(stock.selection_reasons || {}).length > 0"
                          class="p-2 bg-muted/10 rounded">
                          <div v-for="(reason, window) in stock.selection_reasons" :key="window"
                            class="mb-1 text-xs text-muted-foreground">
                            <span class="font-medium text-primary">{{ window }}天:</span>
                            <span v-html="formatSelectionReason(reason)"></span>

                            <!-- 成交量分析结果（每个窗口期） -->
                            <div v-if="stock.volume_analysis && stock.volume_analysis[window]"
                              class="mt-2 border-t border-border pt-1">
                              <div class="text-xs font-medium text-primary mb-1">成交量分析:</div>
                              <div v-if="stock.volume_analysis[window].has_consolidation_volume"
                                class="text-xs text-muted-foreground flex items-center">
                                <i class="fas fa-check-circle text-green-500 mr-1"></i>
                                成交量萎缩
                              </div>
                              <div v-if="stock.volume_analysis[window].has_breakthrough"
                                class="text-xs text-muted-foreground flex items-center">
                                <i class="fas fa-arrow-circle-up text-primary mr-1"></i>
                                成交量突破 ({{
                                  stock.volume_analysis[window].breakthrough_details?.volume_increase_ratio?.toFixed(2) || 'N/A' }}倍)
                              </div>
                              <!-- 成交量变化和稳定性数值 -->
                              <div v-if="stock.volume_analysis[window].consolidation_details" class="mt-1 space-y-0.5">
                                <div v-if="stock.volume_analysis[window].consolidation_details.volume_change_ratio !== null && stock.volume_analysis[window].consolidation_details.volume_change_ratio !== undefined"
                                  class="text-xs text-muted-foreground">
                                  <span class="font-medium">成交量变化:</span> 
                                  {{ stock.volume_analysis[window].consolidation_details.volume_change_ratio.toFixed(4) }}
                                </div>
                                <div v-if="stock.volume_analysis[window].consolidation_details.volume_stability !== null && stock.volume_analysis[window].consolidation_details.volume_stability !== undefined"
                                  class="text-xs text-muted-foreground">
                                  <span class="font-medium">成交量稳定性:</span> 
                                  {{ stock.volume_analysis[window].consolidation_details.volume_stability.toFixed(4) }}
                                </div>
                              </div>
                            </div>

                            <!-- 换手率分析结果（每个窗口期） -->
                            <div v-if="getTurnoverRateForWindow(stock, window) !== null" class="mt-2 border-t border-border pt-1">
                              <div class="text-xs font-medium text-primary mb-1">换手率分析:</div>
                              <div class="text-xs text-muted-foreground flex items-center">
                                <i class="fas fa-exchange-alt text-blue-500 mr-1"></i>
                                <span class="font-medium">平均换手率:</span> 
                                {{ getTurnoverRateForWindow(stock, window).toFixed(2) }}%
                              </div>
                            </div>
                          </div>

                          <!-- 突破前兆识别结果 -->
                          <div
                            v-if="stock.breakthrough_prediction && stock.breakthrough_prediction.has_breakthrough_signal"
                            class="mt-2 border-t border-border pt-1">
                            <div class="text-xs font-medium text-primary mb-1">突破前兆:</div>
                            <div class="text-xs text-muted-foreground">
                              <span class="flex items-center">
                                <i class="fas fa-bolt text-amber-500 mr-1"></i>
                                {{ getActiveBreakthroughSignals(stock.breakthrough_prediction.signals).length }}个技术指标显示突破信号
                              </span>
                              <div class="mt-1 flex flex-wrap gap-1">
                                <span v-for="indicator in getActiveBreakthroughSignals(stock.breakthrough_prediction.signals)"
                                  :key="indicator" 
                                  class="px-1.5 py-0.5 rounded text-xs bg-amber-500/20 text-amber-700 dark:text-amber-400">
                                  {{ indicator }}
                                  <i class="fas fa-check-circle text-xs ml-0.5"></i>
                                </span>
                              </div>
                            </div>
                          </div>

                          <!-- 窗口权重得分 -->
                          <!-- <div v-if="stock.weighted_score !== undefined" class="mt-2 border-t border-border pt-1">
                            <div class="text-xs font-medium text-primary">加权得分:</div>
                            <div class="text-xs text-muted-foreground flex items-center">
                              <i class="fas fa-star text-yellow-500 mr-1"></i>
                              <div class="flex items-center">
                                <span class="font-medium">{{ stock.weighted_score.toFixed(2) }}</span>
                                <div class="ml-2 w-24 bg-muted rounded-full h-1.5 overflow-hidden">
                                  <div class="bg-yellow-500 h-full rounded-full"
                                    :style="{ width: `${Math.min(100, stock.weighted_score * 100)}%` }"></div>
                                </div>
                              </div>
                            </div>
                            <div v-if="stock.weight_details && stock.weight_details.window_scores" class="mt-1">
                              <div class="text-xs text-muted-foreground flex flex-wrap gap-1 mt-1">
                                <span v-for="(score, window) in stock.weight_details.window_scores" :key="window"
                                  class="px-1.5 py-0.5 rounded text-xs bg-muted/50">
                                  {{ window }}天: {{ score.toFixed(2) }}
                                </span>
                              </div>
                            </div>
                          </div> -->
                          <!-- 相对强度/涨跌幅 -->
                          <div v-if="stock.outperform_index !== null && stock.outperform_index !== undefined" class=" mt-2 border-t border-border pt-1">
                          <div class="text-xs font-medium text-primary mb-1" >相对强度/涨跌幅:</div>
                          <div class="space-y-1">
                            <!-- 相对强度 -->
                            <div class="flex items-center">
                              <span class="text-xs text-muted-foreground mr-2 w-16">相对强度:</span>
                              <span
                                :class="[
                                  'px-2 py-0.5 rounded text-xs font-medium',
                                  stock.outperform_index >= 0 ? 'bg-green-500/20 text-green-600 dark:text-green-400' : 'bg-red-500/20 text-red-600 dark:text-red-400'
                                ]">
                                {{ stock.outperform_index >= 0 ? '+' : '' }}{{ stock.outperform_index.toFixed(2) }}%
                              </span>
                            </div>
                            <!-- 股票涨跌幅 -->
                            <div v-if="stock.stock_return !== null && stock.stock_return !== undefined" class="flex items-center">
                              <span class="text-xs text-muted-foreground mr-2 w-16">股票涨跌:</span>
                              <span
                                :class="[
                                  'px-2 py-0.5 rounded text-xs font-medium',
                                  stock.stock_return >= 0 ? 'bg-blue-500/20 text-blue-600 dark:text-blue-400' : 'bg-orange-500/20 text-orange-600 dark:text-orange-400'
                                ]">
                                {{ stock.stock_return >= 0 ? '+' : '' }}{{ stock.stock_return.toFixed(2) }}%
                              </span>
                            </div>
                            <!-- 大盘涨跌幅 -->
                            <div v-if="stock.market_return !== null && stock.market_return !== undefined" class="flex items-center">
                              <span class="text-xs text-muted-foreground mr-2 w-16">大盘涨跌:</span>
                              <span
                                :class="[
                                  'px-2 py-0.5 rounded text-xs font-medium',
                                  stock.market_return >= 0 ? 'bg-purple-500/20 text-purple-600 dark:text-purple-400' : 'bg-pink-500/20 text-pink-600 dark:text-pink-400'
                                ]">
                                {{ stock.market_return >= 0 ? '+' : '' }}{{ stock.market_return.toFixed(2) }}%
                              </span>
                            </div>
                          </div>
                          </div>
                        </div>
                        <div v-else class="text-xs text-muted-foreground italic p-2">
                          无选择理由
                        </div>
                      </div>
                    </td>
                    <td class="px-4 py-3 align-top">
                      <!-- 缩略图K线图容器 -->
                      <div class="relative group w-full">
                        <!-- K线图 -->
                        <KlineChart :klineData="stock.kline_data" height="220px" width="100%"
                          :title="`${stock.name} (${stock.code})`" :isDarkMode="isDarkMode"
                          :markLines="generateMarkLines(stock)" :supportLevels="getSupportLevels(stock)"
                          :resistanceLevels="getResistanceLevels(stock)" class="rounded-md overflow-hidden w-full" />

                        <!-- 操作按钮组 -->
                        <div
                          class="absolute top-3 right-3 flex space-x-2 opacity-0 group-hover:opacity-100 transition-all duration-300 z-10">
                          <!-- 放大按钮 -->
                          <button @click="openFullChart(stock)"
                            class="bg-gundam-blue/30 hover:bg-gundam-blue text-white rounded-md p-1.5 shadow-md backdrop-blur-sm transform hover:scale-110 transition-all"
                            title="查看完整K线图">
                            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
                              stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
                              class="w-3.5 h-3.5">
                              <polyline points="15 3 21 3 21 9"></polyline>
                              <polyline points="9 21 3 21 3 15"></polyline>
                              <line x1="21" y1="3" x2="14" y2="10"></line>
                              <line x1="3" y1="21" x2="10" y2="14"></line>
                            </svg>
                          </button>

                          <!-- 导出到案例按钮 -->
                          <button @click="exportToCase(stock)"
                            class="bg-gundam-yellow/30 hover:bg-gundam-yellow text-white rounded-md p-1.5 shadow-md backdrop-blur-sm transform hover:scale-110 transition-all"
                            title="导出到案例库">
                            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
                              stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
                              class="w-3.5 h-3.5">
                              <path d="M12 2v8"></path>
                              <path d="m16 6-4 4-4-4"></path>
                              <path d="M8 10H4a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-8a2 2 0 0 0-2-2h-4">
                              </path>
                            </svg>
                          </button>

                          <!-- 单股检查按钮 -->
                          <button @click="goToStockCheck(stock)"
                            class="bg-green-500/30 hover:bg-green-500 text-white rounded-md p-1.5 shadow-md backdrop-blur-sm transform hover:scale-110 transition-all"
                            title="单股检查">
                            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
                              stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
                              class="w-3.5 h-3.5">
                              <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"></path>
                              <polyline points="10 17 15 12 10 7"></polyline>
                              <line x1="15" y1="12" x2="3" y2="12"></line>
                            </svg>
                          </button>

                        </div>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>

              <!-- 分页控制器 -->
              <div class="flex items-center justify-between px-4 py-3 border-t border-border">
                <div class="flex items-center">
                  <span class="text-sm text-muted-foreground">
                    每页显示
                  </span>
                  <select v-model="pageSize" class="mx-2 p-1 bg-background border border-border rounded text-sm"
                    @change="changePageSize(pageSize)">
                    <option value="5">5</option>
                    <option value="10">10</option>
                    <option value="20">20</option>
                  </select>
                  <span class="text-sm text-muted-foreground">
                    条数据，共 {{ filteredStocks.length }} 条
                  </span>
                </div>
                <div class="flex items-center space-x-2">
                  <button class="btn btn-secondary text-xs py-1 px-2" @click="prevPage" :disabled="currentPage <= 1">
                    <i class="fas fa-chevron-left mr-1"></i> 上一页
                  </button>
                  <div class="flex items-center">
                    <span class="mx-2 text-sm text-muted-foreground">
                      第 {{ currentPage }} 页 / 共 {{ totalPages }} 页
                    </span>
                  </div>
                  <button class="btn btn-secondary text-xs py-1 px-2" @click="nextPage"
                    :disabled="currentPage >= totalPages">
                    下一页 <i class="fas fa-chevron-right ml-1"></i>
                  </button>
                </div>
              </div>
            </div>

            <!-- 移动端卡片视图 -->
            <div class="md:hidden">
              <!-- 移动端全选/反选按钮 -->
              <div class="p-3 border-b border-border bg-muted/30 flex items-center justify-between">
                <div class="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    :checked="isAllSelected"
                    @change="toggleSelectAll"
                    class="checkbox"
                  />
                </div>
                <span class="text-xs text-muted-foreground whitespace-nowrap">
                  {{ selectedStocks ? selectedStocks.length : 0 }} / {{ filteredStocks.length }} 只
                </span>
              </div>
              
              <div v-for="stock in paginatedStocks" :key="stock.code"
                class="mb-4 border border-border rounded-lg overflow-hidden bg-card">
                <!-- 股票基本信息 -->
                <div class="p-3 border-b border-border bg-muted/20">
                  <div class="flex justify-between items-center">
                    <div class="flex items-center space-x-2 flex-1">
                      <input
                        type="checkbox"
                        :checked="isStockSelected(stock.code)"
                        @change="toggleStockSelection(stock)"
                        class="checkbox"
                      />
                      <div>
                        <div class="font-medium">{{ stock.name }} <span class="text-muted-foreground">{{ stock.code
                            }}</span></div>
                        <div class="mt-1">
                          <span class="px-2 py-0.5 rounded-full text-xs bg-primary/20 text-primary">
                            {{ stock.industry || '未知行业' }}
                          </span>
                        </div>
                      </div>
                    </div>
                    <div class="flex space-x-2">
                      <button @click="openFullChart(stock)"
                        class="bg-gundam-blue/20 hover:bg-gundam-blue/30 text-gundam-blue rounded-md p-1.5 transition-colors"
                        title="查看完整K线图">
                        <i class="fas fa-expand-alt text-sm"></i>
                      </button>
                      <button @click="exportToCase(stock)"
                        class="bg-gundam-yellow/20 hover:bg-gundam-yellow/30 text-gundam-yellow rounded-md p-1.5 transition-colors"
                        title="导出到案例库">
                        <i class="fas fa-download text-sm"></i>
                      </button>
                      <button @click="goToStockCheck(stock)"
                        class="bg-green-500/20 hover:bg-green-500/30 text-green-600 dark:text-green-400 rounded-md p-1.5 transition-colors"
                        title="单股检查">
                        <i class="fas fa-search text-sm"></i>
                      </button>
                    </div>
                  </div>
                </div>

                <!-- K线图 -->
                <div class="relative">
                  <KlineChart :klineData="stock.kline_data" height="180px" width="100%"
                    :title="`${stock.name} (${stock.code})`" :isDarkMode="isDarkMode"
                    :markLines="generateMarkLines(stock)" :supportLevels="getSupportLevels(stock)"
                    :resistanceLevels="getResistanceLevels(stock)" class="rounded-md overflow-hidden w-full" />
                </div>

                <!-- 选择理由 -->
                <div class="p-3 border-t border-border">
                  <!-- 选择理由标题栏（可点击） -->
                  <div @click="toggleReasonExpand(stock.code)"
                    class="flex items-center justify-between cursor-pointer p-1.5 rounded hover:bg-muted/50 transition-colors">
                    <div class="flex items-center">
                      <i class="fas fa-info-circle text-primary mr-1.5"></i>
                      <span class="font-medium">选择理由</span>
                      <span v-if="Object.keys(stock.selection_reasons || {}).length > 0"
                        class="ml-1.5 text-xs px-1.5 py-0.5 rounded-full bg-primary/10 text-primary">
                        {{ Object.keys(stock.selection_reasons || {}).length }}
                      </span>
                    </div>
                    <i :class="[
                      'fas transition-transform duration-300',
                      expandedReasons[stock.code] ? 'fa-chevron-up' : 'fa-chevron-down'
                    ]"></i>
                  </div>

                  <!-- 选择理由详情（可折叠） -->
                  <div :id="`reason-mobile-${stock.code.replace(/\./g, '_').replace(/[^\w-]/g, '')}`" :class="[
                    'overflow-hidden transition-all duration-300 mt-1',
                    expandedReasons[stock.code] === undefined || expandedReasons[stock.code] ? 'h-auto opacity-100' : 'h-0 opacity-0'
                  ]">
                    <div v-if="Object.keys(stock.selection_reasons || {}).length > 0" class="p-2 bg-muted/10 rounded">
                      <div v-for="(reason, window) in stock.selection_reasons" :key="window"
                        class="mb-1 text-xs text-muted-foreground">
                        <span class="font-medium text-primary">{{ window }}天:</span>
                        <span v-html="formatSelectionReason(reason)"></span>

                        <!-- 成交量分析结果（每个窗口期） -->
                        <div v-if="stock.volume_analysis && stock.volume_analysis[window]"
                          class="mt-2 border-t border-border pt-1">
                          <div class="text-xs font-medium text-primary mb-1">成交量分析:</div>
                          <div v-if="stock.volume_analysis[window].has_consolidation_volume"
                            class="text-xs text-muted-foreground flex items-center">
                            <i class="fas fa-check-circle text-green-500 mr-1"></i>
                            成交量萎缩
                          </div>
                          <div v-if="stock.volume_analysis[window].has_breakthrough"
                            class="text-xs text-muted-foreground flex items-center">
                            <i class="fas fa-arrow-circle-up text-primary mr-1"></i>
                            成交量突破 ({{
                              stock.volume_analysis[window].breakthrough_details?.volume_increase_ratio?.toFixed(2) || 'N/A' }}倍)
                          </div>
                          <!-- 成交量变化和稳定性数值 -->
                          <div v-if="stock.volume_analysis[window].consolidation_details" class="mt-1 space-y-0.5">
                            <div v-if="stock.volume_analysis[window].consolidation_details.volume_change_ratio !== null && stock.volume_analysis[window].consolidation_details.volume_change_ratio !== undefined"
                              class="text-xs text-muted-foreground">
                              <span class="font-medium">成交量变化:</span> 
                              {{ stock.volume_analysis[window].consolidation_details.volume_change_ratio.toFixed(4) }}
                              <span class="text-muted-foreground/70">(阈值: {{ stock.volume_analysis[window].consolidation_details.volume_change_threshold ?? 'N/A' }})</span>
                            </div>
                            <div v-if="stock.volume_analysis[window].consolidation_details.volume_stability !== null && stock.volume_analysis[window].consolidation_details.volume_stability !== undefined"
                              class="text-xs text-muted-foreground">
                              <span class="font-medium">成交量稳定性:</span> 
                              {{ stock.volume_analysis[window].consolidation_details.volume_stability.toFixed(4) }}
                              <span class="text-muted-foreground/70">(阈值: {{ stock.volume_analysis[window].consolidation_details.volume_stability_threshold ?? 'N/A' }})</span>
                            </div>
                          </div>
                        </div>

                        <!-- 换手率分析结果（每个窗口期） -->
                        <div v-if="getTurnoverRateForWindow(stock, window) !== null" class="mt-2 border-t border-border pt-1">
                          <div class="text-xs font-medium text-primary">换手率分析:</div>
                          <div class="text-xs text-muted-foreground flex items-center">
                            <i class="fas fa-exchange-alt text-blue-500 mr-1"></i>
                            <span class="font-medium">平均换手率:</span> 
                            {{ getTurnoverRateForWindow(stock, window).toFixed(2) }}%
                          </div>
                        </div>
                      </div>

                      <!-- 突破前兆识别结果 -->
                      <div
                        v-if="stock.breakthrough_prediction && stock.breakthrough_prediction.has_breakthrough_signal"
                        class="mt-2 border-t border-border pt-1">
                        <div class="text-xs font-medium text-primary mb-1">突破前兆:</div>
                        <div class="text-xs text-muted-foreground">
                          <span class="flex items-center">
                            <i class="fas fa-bolt text-amber-500 mr-1"></i>
                            {{ getActiveBreakthroughSignals(stock.breakthrough_prediction.signals).length }}个技术指标显示突破信号
                          </span>
                          <div class="mt-1 flex flex-wrap gap-1">
                            <span v-for="indicator in getActiveBreakthroughSignals(stock.breakthrough_prediction.signals)"
                              :key="indicator" 
                              class="px-1.5 py-0.5 rounded text-xs bg-amber-500/20 text-amber-700 dark:text-amber-400">
                              {{ indicator }}
                              <i class="fas fa-check-circle text-xs ml-0.5"></i>
                            </span>
                          </div>
                        </div>
                      </div>

                      <!-- 窗口权重得分 -->
                      <!-- <div v-if="stock.weighted_score !== undefined" class="mt-2 border-t border-border pt-1">
                        <div class="text-xs font-medium text-primary">加权得分:</div>
                        <div class="text-xs text-muted-foreground flex items-center">
                          <i class="fas fa-star text-yellow-500 mr-1"></i>
                          <div class="flex items-center">
                            <span class="font-medium">{{ stock.weighted_score.toFixed(2) }}</span>
                            <div class="ml-2 w-24 bg-muted rounded-full h-1.5 overflow-hidden">
                              <div class="bg-yellow-500 h-full rounded-full"
                                :style="{ width: `${Math.min(100, stock.weighted_score * 100)}%` }"></div>
                            </div>
                          </div>
                        </div>
                      </div> -->
                       <!-- 相对强度/涨跌幅 -->
                       <div v-if="stock.outperform_index !== null && stock.outperform_index !== undefined" class="mt-2 border-t border-border pt-1">
                        <div class="text-xs font-medium text-primary mb-1">相对强度/涨跌幅:</div>
                        <div class="space-y-1">
                          <!-- 相对强度 -->
                          <div class="flex items-center">
                            <span class="text-xs text-muted-foreground mr-2 w-16">相对强度:</span>
                            <span
                              :class="[
                                'px-2 py-0.5 rounded text-xs font-medium',
                                stock.outperform_index >= 0 ? 'bg-green-500/20 text-green-600 dark:text-green-400' : 'bg-red-500/20 text-red-600 dark:text-red-400'
                              ]">
                              {{ stock.outperform_index >= 0 ? '+' : '' }}{{ stock.outperform_index.toFixed(2) }}%
                            </span>
                          </div>
                          <!-- 股票涨跌幅 -->
                          <div v-if="stock.stock_return !== null && stock.stock_return !== undefined" class="flex items-center">
                            <span class="text-xs text-muted-foreground mr-2 w-16">股票涨跌:</span>
                            <span
                              :class="[
                                'px-2 py-0.5 rounded text-xs font-medium',
                                stock.stock_return >= 0 ? 'bg-blue-500/20 text-blue-600 dark:text-blue-400' : 'bg-orange-500/20 text-orange-600 dark:text-orange-400'
                              ]">
                              {{ stock.stock_return >= 0 ? '+' : '' }}{{ stock.stock_return.toFixed(2) }}%
                            </span>
                          </div>
                          <!-- 大盘涨跌幅 -->
                          <div v-if="stock.market_return !== null && stock.market_return !== undefined" class="flex items-center">
                            <span class="text-xs text-muted-foreground mr-2 w-16">大盘涨跌:</span>
                            <span
                              :class="[
                                'px-2 py-0.5 rounded text-xs font-medium',
                                stock.market_return >= 0 ? 'bg-purple-500/20 text-purple-600 dark:text-purple-400' : 'bg-pink-500/20 text-pink-600 dark:text-pink-400'
                              ]">
                              {{ stock.market_return >= 0 ? '+' : '' }}{{ stock.market_return.toFixed(2) }}%
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                    <div v-else class="text-xs text-muted-foreground italic p-2">
                      无选择理由
                    </div>
                  </div>
                </div>
              </div>

              <!-- 移动端数据回测按钮 -->
              <div class="px-2 mb-3">
                <button 
                  @click="goToBacktest" 
                  :disabled="!selectedStocks || selectedStocks.length === 0"
                  class="btn btn-primary w-full text-sm py-2"
                  :class="!selectedStocks || selectedStocks.length === 0 ? 'opacity-50 cursor-not-allowed' : ''"
                >
                  <i class="fas fa-chart-line mr-2"></i> 
                  数据回测
                  <span v-if="selectedStocks && selectedStocks.length > 0" class="ml-2 px-2 py-0.5 rounded-full text-xs bg-white/20">
                    {{ selectedStocks.length }} 只
                  </span>
                </button>
              </div>

              <!-- 移动端分页控制器 -->
              <div class="flex flex-col space-y-3 my-4 px-2">
                <div class="flex items-center justify-between">
                  <span class="text-sm text-muted-foreground">
                    每页 {{ pageSize }} 条，共 {{ filteredStocks.length }} 条
                  </span>
                  <div class="flex items-center space-x-1">
                    <button class="btn btn-secondary text-xs py-1 px-2" @click="prevPage" :disabled="currentPage <= 1">
                      <i class="fas fa-chevron-left"></i>
                    </button>
                    <span class="mx-2 text-sm text-muted-foreground">
                      {{ currentPage }}/{{ totalPages }}
                    </span>
                    <button class="btn btn-secondary text-xs py-1 px-2" @click="nextPage"
                      :disabled="currentPage >= totalPages">
                      <i class="fas fa-chevron-right"></i>
                    </button>
                  </div>
                </div>
                <div class="flex justify-center space-x-2">
                  <select v-model="pageSize" class="p-1 bg-background border border-border rounded text-sm"
                    @change="changePageSize(pageSize)">
                    <option value="5">5条/页</option>
                    <option value="10">10条/页</option>
                    <option value="20">20条/页</option>
                  </select>
                </div>
              </div>
            </div>
          </div>
        </transition>

        <!-- 无结果提示 -->
        <transition name="fade">
          <div v-if="!loading && taskStatus === 'completed' && platformStocks.length === 0 && !error && hasSearched"
            class="card p-8 text-center my-5 text-muted-foreground">
            <i class="fas fa-search text-4xl mb-3 opacity-50"></i>
            <p>未找到符合当前条件的股票。</p>
            <p class="text-sm mt-2">尝试调整扫描参数后重新搜索。</p>
          </div>
        </transition>
      </div>
    </main>

    <!-- 确认对话框 -->
    <ConfirmDialog
      v-model:show="confirmDialog.show"
      :title="confirmDialog.title"
      :message="confirmDialog.message"
      :type="confirmDialog.type"
      confirm-text="确认"
      cancel-text="取消"
      @confirm="confirmDialog.onConfirm && confirmDialog.onConfirm()"
    />
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, inject, provide, nextTick } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';
import KlineChart from './components/KlineChart.vue'; // 缩略图K线图组件
import FullKlineChart from './components/FullKlineChart.vue'; // 完整K线图组件
import TaskProgress from './components/TaskProgress.vue'; // 任务进度组件
import { ParameterHelpManager, ParameterLabel } from './components/parameter-help'; // 参数帮助组件
import CaseManager from './components/case-management/CaseManager.vue'; // 案例管理组件
import ThemeToggle from './components/ThemeToggle.vue'; // 主题切换组件
import ConfirmDialog from './components/ConfirmDialog.vue'; // 确认对话框组件
import DateRangeFilter from './components/DateRangeFilter.vue'; // 日期筛选组件
import ScanConfigForm from './components/ScanConfigForm.vue'; // 扫描配置表单组件
import { getStockBoard } from './utils/stockBoardUtils.js'; // 板块工具函数
import { getDefaultScanConfig } from './config/scanConfig.js'; // 默认扫描配置
import { gsap } from 'gsap';

const router = useRouter();

// 计算最大日期（今天）
const maxDate = computed(() => {
  const today = new Date()
  return today.toISOString().split('T')[0]
})

const platformStocks = ref([]);
const loading = ref(false);
const error = ref(null);
const hasSearched = ref(false); // Track if a search has been performed
const isDarkMode = ref(false); // 暗色模式状态
const expandedReasons = ref({}); // 跟踪每个股票的选择理由是否展开
const selectedStocks = ref([]); // 选中的股票列表（用于回测）
const scanConfigFormRef = ref(null); // 扫描配置表单引用
const config = ref(getDefaultScanConfig()); // 扫描配置，使用默认配置初始化

// 筛选相关状态
const showFilterPanel = ref(false); // 筛选面板显示状态
const selectedPlatformPeriods = ref([]); // 选中的平台期列表
const availablePlatformPeriods = ref([]); // 可用的平台期列表（从结果中统计）
const selectedBoards = ref(['创业板', '科创板', '主板']); // 选中的板块列表（默认选中所有板块）
const minOutperformIndex = ref(null); // 最小相对强度值
const maxOutperformIndex = ref(null); // 最大相对强度值

// 筛选后的股票列表
const filteredStocks = computed(() => {
  let filtered = platformStocks.value
  
  // 应用板块筛选
  if (selectedBoards.value.length > 0 && selectedBoards.value.length < 3) {
    filtered = filtered.filter(stock => {
      const stockBoard = getStockBoard(stock.code)
      return stockBoard && selectedBoards.value.includes(stockBoard)
    }).map(stock => {
      // 确保筛选后的对象保留所有原始字段
      return {
        ...stock,
        volume_analysis: stock.volume_analysis || null,
        breakthrough_prediction: stock.breakthrough_prediction || null,
        turnover_analysis: stock.turnover_analysis || null,
        box_analysis: stock.box_analysis || null,
        details: stock.details || {},
        selection_reasons: stock.selection_reasons || {},
        platform_windows: stock.platform_windows || [],
        kline_data: stock.kline_data || [],
        markLines: stock.markLines || stock.mark_lines || []
      }
    })
  }
  
  // 应用平台期筛选
  if (selectedPlatformPeriods.value.length > 0 && selectedPlatformPeriods.value.length < availablePlatformPeriods.value.length) {
    filtered = filtered.filter(stock => {
      // 获取股票的所有平台期
      const stockPeriods = []
      
      // 从 selection_reasons 中获取平台期
      if (stock.selection_reasons && typeof stock.selection_reasons === 'object') {
        Object.keys(stock.selection_reasons).forEach(key => {
          const period = parseInt(key)
          if (!isNaN(period)) {
            stockPeriods.push(period)
          }
        })
      }
      
      // 从 platform_windows 中获取平台期
      if (stock.platform_windows && Array.isArray(stock.platform_windows)) {
        stock.platform_windows.forEach(period => {
          if (!stockPeriods.includes(period)) {
            stockPeriods.push(period)
          }
        })
      }
      
      // 检查股票是否有任何一个选中的平台期（使用 OR 逻辑）
      return selectedPlatformPeriods.value.some(period => stockPeriods.includes(period))
    }).map(stock => {
      // 确保筛选后的对象保留所有原始字段
      return {
        ...stock,
        volume_analysis: stock.volume_analysis || null,
        breakthrough_prediction: stock.breakthrough_prediction || null,
        turnover_analysis: stock.turnover_analysis || null,
        box_analysis: stock.box_analysis || null,
        details: stock.details || {},
        selection_reasons: stock.selection_reasons || {},
        platform_windows: stock.platform_windows || [],
        kline_data: stock.kline_data || [],
        markLines: stock.markLines || stock.mark_lines || []
      }
    })
  }
  
  // 应用相对强度筛选
  if (minOutperformIndex.value !== null || maxOutperformIndex.value !== null) {
    filtered = filtered.filter(stock => {
      const outperformIndex = stock.outperform_index
      if (outperformIndex === null || outperformIndex === undefined) {
        return false // 如果没有相对强度数据，排除
      }
      if (minOutperformIndex.value !== null && outperformIndex < minOutperformIndex.value) {
        return false
      }
      if (maxOutperformIndex.value !== null && outperformIndex > maxOutperformIndex.value) {
        return false
      }
      return true
    }).map(stock => {
      // 确保筛选后的对象保留所有原始字段
      return {
        ...stock,
        volume_analysis: stock.volume_analysis || null,
        breakthrough_prediction: stock.breakthrough_prediction || null,
        turnover_analysis: stock.turnover_analysis || null,
        box_analysis: stock.box_analysis || null,
        details: stock.details || {},
        selection_reasons: stock.selection_reasons || {},
        platform_windows: stock.platform_windows || [],
        kline_data: stock.kline_data || [],
        markLines: stock.markLines || stock.mark_lines || []
      }
    })
  }
  
  return filtered
})

// 分页相关状态
const currentPage = ref(1);
const pageSize = ref(10);
const totalPages = computed(() => Math.ceil(filteredStocks.value.length / pageSize.value));
const paginatedStocks = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value;
  const end = start + pageSize.value;
  return filteredStocks.value.slice(start, end);
});

// 统计可用平台期（从结果中提取）
function updateAvailablePlatformPeriods() {
  const periodsSet = new Set()
  
  platformStocks.value.forEach(stock => {
    // 从 selection_reasons 中获取平台期
    if (stock.selection_reasons && typeof stock.selection_reasons === 'object') {
      Object.keys(stock.selection_reasons).forEach(key => {
        const period = parseInt(key)
        if (!isNaN(period)) {
          periodsSet.add(period)
        }
      })
    }
    
    // 从 platform_windows 中获取平台期
    if (stock.platform_windows && Array.isArray(stock.platform_windows)) {
      stock.platform_windows.forEach(period => {
        if (!isNaN(period)) {
          periodsSet.add(period)
        }
      })
    }
  })
  
  // 排序并更新可用平台期列表
  availablePlatformPeriods.value = Array.from(periodsSet).sort((a, b) => a - b)
  
  // 如果可用平台期列表为空，清空选中的平台期
  if (availablePlatformPeriods.value.length === 0) {
    selectedPlatformPeriods.value = []
    return
  }
  
  // 如果当前没有选中任何平台期，或者选中的平台期数量不等于可用平台期数量，或者有选中的平台期不在新的列表中，则默认全选
  if (selectedPlatformPeriods.value.length === 0 || 
      selectedPlatformPeriods.value.length !== availablePlatformPeriods.value.length ||
      !selectedPlatformPeriods.value.every(p => availablePlatformPeriods.value.includes(p))) {
    selectedPlatformPeriods.value = [...availablePlatformPeriods.value]
  }
}

// 全选平台期
function selectAllPlatformPeriods() {
  selectedPlatformPeriods.value = [...availablePlatformPeriods.value]
}

// 清空平台期筛选
function clearPlatformPeriodFilter() {
  selectedPlatformPeriods.value = []
}

// 监听筛选变化，重置分页
watch(selectedPlatformPeriods, () => {
  currentPage.value = 1
  expandedReasons.value = {}
}, { deep: true })

// 分页控制函数
function goToPage (page) {
  if (page >= 1 && page <= totalPages.value) {
    currentPage.value = page;
    // 重置选择理由展开状态
    expandedReasons.value = {};
  }
}

function nextPage () {
  if (currentPage.value < totalPages.value) {
    goToPage(currentPage.value + 1);
  }
}

function prevPage () {
  if (currentPage.value > 1) {
    goToPage(currentPage.value - 1);
  }
}

function changePageSize (size) {
  pageSize.value = size;
  // 调整当前页，确保不超出总页数
  if (currentPage.value > totalPages.value) {
    currentPage.value = totalPages.value || 1;
  }
}


// 任务状态相关
const currentTaskId = ref(null);
const taskStatus = ref(null); // 'pending', 'running', 'completed', 'failed'
const taskProgress = ref(0);
const taskMessage = ref('');
const taskError = ref(null);
const pollingInterval = ref(null);

// K线图弹窗相关状态
const showFullChart = ref(false);
const showCaseManager = ref(false);
const selectedStock = ref(null);

// 扫描历史相关
const showScanHistoryDialog = ref(false);
const scanHistory = ref([]);
const scanHistoryLoading = ref(false);
const selectedScanHistoryRecord = ref(null);
const scanHistoryGroupedByDate = ref({});
const selectedScanYear = ref('');
const selectedScanQuarter = ref('');
const selectedScanMonth = ref('');
const showScanConfigDetails = ref(false); // 控制配置详情展开/折叠

// 确认对话框相关
const confirmDialog = ref({
  show: false,
  title: '确认操作',
  message: '',
  type: 'default',
  onConfirm: null,
  pendingAction: null // 存储待执行的删除操作参数
});

// 参数帮助相关
const parameterHelp = inject('parameterHelp', {
  openTutorial: (id) => {
    console.log('打开教程:', id);
  },
  closeTutorial: () => {
    console.log('关闭教程');
  },
  getTooltip: (id) => {
    console.log('获取提示:', id);
    return null;
  }
});

// 初始化时检查系统偏好
onMounted(() => {
  // 检查本地存储中的主题设置
  const savedTheme = localStorage.getItem('theme');
  if (savedTheme === 'dark' || (!savedTheme && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
    isDarkMode.value = true;
    document.documentElement.classList.add('dark');
  }

  // 添加页面加载动画
  gsap.from('.card', {
    y: 20,
    opacity: 0,
    duration: 0.6,
    stagger: 0.1,
    ease: 'power2.out'
  });

  // 初始化所有选择理由为收起状态
  expandedReasons.value = {};
});

// 切换暗色模式
function toggleDarkMode () {
  isDarkMode.value = !isDarkMode.value;
  if (isDarkMode.value) {
    document.documentElement.classList.add('dark');
    localStorage.setItem('theme', 'dark');
  } else {
    document.documentElement.classList.remove('dark');
    localStorage.setItem('theme', 'light');
  }
}

// 提供 isDarkMode 变量和 toggleDarkMode 函数，以便子组件可以注入它们
provide('isDarkMode', isDarkMode);
provide('toggleDarkMode', toggleDarkMode);

// 生成标记线数据
function generateMarkLines (stock) {
  // 打印完整的股票数据，用于调试
  console.log('生成标记线数据，股票数据:', stock);

  // 首先检查后端是否直接提供了标记线数据（支持两种可能的字段名）
  if (stock.mark_lines && stock.mark_lines.length > 0) {
    console.log('使用后端提供的标记线数据 (mark_lines):', stock.mark_lines);
    return stock.mark_lines;
  }

  if (stock.markLines && stock.markLines.length > 0) {
    console.log('使用后端提供的标记线数据 (markLines):', stock.markLines);
    return stock.markLines;
  }

  const markLines = [];
  console.log('后端未提供标记线数据，尝试从分析数据生成');

  // 如果有低位分析，添加高点标记
  if (stock.position_analysis && stock.position_analysis.details) {
    const details = stock.position_analysis.details;
    console.log('低位分析详情:', details);
    if (details.high_date) {
      markLines.push({
        date: details.high_date,
        text: '高点',
        color: '#ec0000' // 红色
      });
    }
  }

  // 如果有快速下跌分析，添加快速下跌开始和结束标记
  if (stock.decline_details) {
    const details = stock.decline_details;
    console.log('快速下跌详情:', details);
    if (details.rapid_decline_start_date) {
      markLines.push({
        date: details.rapid_decline_start_date,
        text: '开始下跌',
        color: '#ec0000' // 红色
      });
    }
    if (details.rapid_decline_end_date) {
      markLines.push({
        date: details.rapid_decline_end_date,
        text: '平台期开始',
        color: '#3b82f6' // 蓝色
      });
    }
  }

  // 如果有突破分析，添加突破标记
  if (stock.breakthrough_analysis && stock.breakthrough_analysis.has_breakthrough_signal) {
    const details = stock.breakthrough_analysis;
    console.log('突破分析详情:', details);
    if (details.breakthrough_date) {
      markLines.push({
        date: details.breakthrough_date,
        text: '突破',
        color: '#10b981' // 绿色
      });
    }
  }

  // 检查是否有decline_analysis字段（可能是后端返回的字段名不同）
  if (stock.decline_analysis) {
    const details = stock.decline_analysis;
    console.log('下跌分析详情 (decline_analysis):', details);
    if (details.high_date) {
      markLines.push({
        date: details.high_date,
        text: '高点',
        color: '#ec0000' // 红色
      });
    }
    if (details.rapid_decline_start_date) {
      markLines.push({
        date: details.rapid_decline_start_date,
        text: '开始下跌',
        color: '#ec0000' // 红色
      });
    }
    if (details.rapid_decline_end_date) {
      markLines.push({
        date: details.rapid_decline_end_date,
        text: '平台期开始',
        color: '#3b82f6' // 蓝色
      });
    }
  }

  // 检查是否有position_details字段（可能是后端返回的字段名不同）
  if (stock.position_details) {
    const details = stock.position_details;
    console.log('位置分析详情 (position_details):', details);
    if (details.high_date) {
      markLines.push({
        date: details.high_date,
        text: '高点',
        color: '#ec0000' // 红色
      });
    }
  }

  // 检查是否有decline_details字段（可能是后端返回的字段名不同）
  if (stock.decline_details) {
    const details = stock.decline_details;
    console.log('下跌分析详情 (decline_details):', details);
    if (details.high_date) {
      markLines.push({
        date: details.high_date,
        text: '高点',
        color: '#ec0000' // 红色
      });
    }
    if (details.rapid_decline_start_date) {
      markLines.push({
        date: details.rapid_decline_start_date,
        text: '开始下跌',
        color: '#ec0000' // 红色
      });
    }
    if (details.rapid_decline_end_date) {
      markLines.push({
        date: details.rapid_decline_end_date,
        text: '平台期开始',
        color: '#3b82f6' // 蓝色
      });
    }
  }

  console.log('生成的标记线数据:', markLines);
  return markLines;
}

// 获取支撑位数据
function getSupportLevels (stock) {
  if (!stock) return [];

  // 首先检查后端是否直接提供了箱体分析结果
  if (stock.box_analysis) {
    console.log('使用后端提供的箱体分析结果获取支撑位');
    return stock.box_analysis.support_levels || [];
  }

  if (!stock.details) return [];

  // 遍历所有窗口，查找箱体分析结果
  for (const window in stock.details) {
    if (stock.details[window].box_analysis) {
      console.log(`从窗口 ${window} 获取支撑位`);
      return stock.details[window].box_analysis.support_levels || [];
    }
  }

  return [];
}

// 获取阻力位数据
function getResistanceLevels (stock) {
  if (!stock) return [];

  // 首先检查后端是否直接提供了箱体分析结果
  if (stock.box_analysis) {
    console.log('使用后端提供的箱体分析结果获取阻力位');
    return stock.box_analysis.resistance_levels || [];
  }

  if (!stock.details) return [];

  // 遍历所有窗口，查找箱体分析结果
  for (const window in stock.details) {
    if (stock.details[window].box_analysis) {
      console.log(`从窗口 ${window} 获取阻力位`);
      return stock.details[window].box_analysis.resistance_levels || [];
    }
  }

  return [];
}

// 打开完整K线图
function openFullChart (stock) {
  console.log('打开K线图:', stock.code, stock.name);
  console.log('K线数据长度:', stock.kline_data?.length);
  console.log('当前主题模式:', isDarkMode.value ? '暗色' : '亮色');

  // 生成标记线数据
  const markLines = generateMarkLines(stock);
  console.log('标记线数据:', markLines);

  // 获取支撑位和阻力位
  const supportLevels = getSupportLevels(stock);
  const resistanceLevels = getResistanceLevels(stock);
  console.log('支撑位:', supportLevels);
  console.log('阻力位:', resistanceLevels);

  // 设置选中的股票和标记线数据
  selectedStock.value = {
    ...stock,
    markLines: markLines,
    supportLevels: supportLevels,
    resistanceLevels: resistanceLevels
  };
  showFullChart.value = true;
}

// 获取有信号的突破前兆指标列表
function getActiveBreakthroughSignals(signals) {
  if (!signals || typeof signals !== 'object') {
    return []
  }
  
  const activeSignals = []
  
  // 检查每个指标是否有信号
  Object.entries(signals).forEach(([indicator, hasSignal]) => {
    // 支持多种格式：布尔值、数字1/0、字符串'true'/'false'
    let isActive = false
    if (hasSignal === true || hasSignal === 1) {
      isActive = true
    } else if (typeof hasSignal === 'string') {
      isActive = hasSignal.toLowerCase() === 'true'
    } else if (typeof hasSignal === 'boolean') {
      isActive = hasSignal === true
    }
    
    if (isActive) {
      activeSignals.push(indicator)
    }
  })
  
  return activeSignals
}

// 获取指定窗口期的换手率
function getTurnoverRateForWindow(stock, window) {
  if (!stock || !window) return null
  
  // 首先检查后端是否返回了换手率分析数据
  if (stock.turnover_analysis && stock.turnover_analysis[window]) {
    const analysis = stock.turnover_analysis[window]
    if (analysis.avg_turnover_rate !== null && analysis.avg_turnover_rate !== undefined) {
      return analysis.avg_turnover_rate
    }
  }
  
  // 如果没有，从kline_data中计算平台期的平均换手率
  // 注意：需要排除最近5天，与后端逻辑保持一致（避免突破期的放量干扰平台期判断）
  if (stock.kline_data && Array.isArray(stock.kline_data) && stock.kline_data.length > 0) {
    const windowDays = parseInt(window)
    const excludeRecentDays = 5 // 排除最近5天，与后端逻辑一致
    
    // 确保有足够的数据
    if (stock.kline_data.length < windowDays) {
      return null
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
    
    // 计算平均换手率
    const turnoverRates = platformData
      .map(item => item.turn)
      .filter(turn => turn !== null && turn !== undefined && !isNaN(turn) && turn >= 0 && turn <= 100)
    
    if (turnoverRates.length > 0) {
      const avgTurnoverRate = turnoverRates.reduce((sum, rate) => sum + rate, 0) / turnoverRates.length
      return avgTurnoverRate
    }
  }
  
  return null
}

// 格式化选择理由，将相对强度/涨跌幅信息显示在最后
function formatSelectionReason(reason) {
  if (!reason) return '';
  
  // 匹配相对强度/涨跌幅信息（格式：, 相对强度X.XX%/股票涨跌幅X.XX%/大盘涨跌幅X.XX%）
  // 匹配模式：以逗号开头，后跟相对强度信息（可能包含股票涨跌幅和大盘涨跌幅，直到字符串末尾或下一个逗号）
  // 使用非贪婪匹配，匹配到字符串末尾或下一个逗号之前
  const rsPattern = /(,\s*相对强度[\d.-]+%(\/股票涨跌幅[\d.-]+%)?(\/大盘涨跌幅[\d.-]+%)?)/;
  const match = reason.match(rsPattern);
  
  if (match) {
    // 移除原始字符串中的相对强度/涨跌幅信息
    const mainReason = reason.replace(rsPattern, '').trim();
    // 提取相对强度/涨跌幅信息（去掉开头的逗号和空格）
    const rsInfo = match[1].replace(/^,\s*/, '');
    
    // 返回格式化后的HTML，相对强度/涨跌幅信息用特殊样式显示在最后
    // 使用转义HTML来防止XSS攻击
    const escapedMainReason = mainReason.replace(/</g, '&lt;').replace(/>/g, '&gt;');
    const escapedRsInfo = rsInfo.replace(/</g, '&lt;').replace(/>/g, '&gt;');
    return `${escapedMainReason}<span class="text-primary font-medium ml-1">${escapedRsInfo}</span>`;
  }
  
  // 如果没有匹配到，直接返回（转义HTML）
  return reason.replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

// 切换选择理由的展开/收起状态
function toggleReasonExpand (stockCode) {
  // 如果该股票的展开状态尚未初始化，则初始化为true（展开）
  // 否则切换当前状态
  expandedReasons.value[stockCode] = expandedReasons.value[stockCode] === undefined ?
    true : !expandedReasons.value[stockCode];

  // 创建安全的选择器ID（替换点号和其他特殊字符）
  const safeStockCode = stockCode.replace(/\./g, '_').replace(/[^\w-]/g, '');

  // 使用GSAP添加动画效果
  nextTick(() => {
    // 同时处理桌面端和移动端的元素
    const desktopElement = document.querySelector(`#reason-${safeStockCode}`);
    const mobileElement = document.querySelector(`#reason-mobile-${safeStockCode}`);

    const elements = [desktopElement, mobileElement].filter(el => el); // 过滤掉不存在的元素

    if (elements.length > 0) {
      if (expandedReasons.value[stockCode]) {
        // 展开动画
        elements.forEach(element => {
          gsap.fromTo(element,
            { height: 0, opacity: 0 },
            {
              height: 'auto',
              opacity: 1,
              duration: 0.3,
              ease: 'power2.out',
              onComplete: () => {
                // 确保展开后高度为auto
                element.style.height = 'auto';
              }
            }
          );
        });
      } else {
        // 收起动画
        elements.forEach(element => {
          // 先获取当前高度
          const height = element.offsetHeight;

          // 设置为具体高度，以便动画
          element.style.height = `${height}px`;

          // 强制回流
          element.offsetHeight;

          // 执行收起动画
          gsap.to(element, {
            height: 0,
            opacity: 0,
            duration: 0.3,
            ease: 'power2.in'
          });
        });
      }
    }
  });
}

// 导出股票到案例库
// 股票选择相关方法
function isStockSelected(code) {
  return selectedStocks.value && selectedStocks.value.some(s => s.code === code);
}

function toggleStockSelection(stock) {
  if (!selectedStocks.value) {
    selectedStocks.value = [];
  }
  const index = selectedStocks.value.findIndex(s => s.code === stock.code);
  if (index >= 0) {
    selectedStocks.value.splice(index, 1);
  } else {
    selectedStocks.value.push(stock);
  }
}

const isAllSelected = computed(() => {
  return paginatedStocks.value.length > 0 && 
         paginatedStocks.value.every(stock => isStockSelected(stock.code));
});

function toggleSelectAll() {
  if (!selectedStocks.value) {
    selectedStocks.value = [];
  }
  if (isAllSelected.value) {
    // 取消选择当前页的所有股票
    paginatedStocks.value.forEach(stock => {
      const index = selectedStocks.value.findIndex(s => s.code === stock.code);
      if (index >= 0) {
        selectedStocks.value.splice(index, 1);
      }
    });
  } else {
    // 选择当前页的所有股票
    paginatedStocks.value.forEach(stock => {
      if (!isStockSelected(stock.code)) {
        selectedStocks.value.push(stock);
      }
    });
  }
}

// 跳转到单股检查页面
function goToStockCheck(stock) {
  const query = {
    code: stock.code
  }
  
  // 如果从扫描历史详情页面调用，传递扫描日期
  if (selectedScanHistoryRecord.value && selectedScanHistoryRecord.value.scanDate) {
    query.date = selectedScanHistoryRecord.value.scanDate
  }
  
  router.push({
    path: '/platform/check',
    query: query
  });
}

// 跳转到回测页面
function goToBacktest() {
  if (!selectedStocks.value || selectedStocks.value.length === 0) {
    error.value = '请至少选择一只股票进行回测';
    return;
  }
  // 获取当前扫描配置（使用辅助函数构建）
  const currentScanConfig = buildScanPayload(config.value, {
    includeScanDate: true,
    windows: parsedWindows.value,
    scanDate: config.value.scan_date || maxDate.value
  })
  
  console.log('准备跳转到回测页面，当前扫描配置:', currentScanConfig);
  
  // 保存选中的股票和扫描配置到sessionStorage
  try {
    sessionStorage.setItem('selectedStocks', JSON.stringify(selectedStocks.value));
    sessionStorage.setItem('scanConfig', JSON.stringify(currentScanConfig));
    console.log('已保存选中的股票和扫描配置到 sessionStorage');
    
    // 跳转到回测页面
    router.push('/platform/backtest');
  } catch (e) {
    console.error('保存数据到 sessionStorage 失败:', e);
    error.value = '保存数据失败，请重试';
  }
}

async function exportToCase (stock) {
  try {
    // 显示加载状态
    const loadingToast = showToast('正在导出到案例库...', 'loading');

    // 生成标记线数据
    const markLines = generateMarkLines(stock);
    console.log('导出到案例库: 标记线数据:', markLines);

    // 获取支撑位和阻力位
    const supportLevels = getSupportLevels(stock);
    const resistanceLevels = getResistanceLevels(stock);
    console.log('导出到案例库: 支撑位:', supportLevels);
    console.log('导出到案例库: 阻力位:', resistanceLevels);

    // 准备请求数据
    const exportData = {
      stockData: {
        code: stock.code,
        name: stock.name,
        industry: stock.industry || '未知行业'
      },
      analysisResult: {
        is_platform: true,
        platform_windows: Object.keys(stock.selection_reasons || {}).map(w => parseInt(w)),
        selection_reasons: stock.selection_reasons || {},
        parameters: {
          windows: parsedWindows.value,
          box_threshold: config.value.box_threshold,
          ma_diff_threshold: config.value.ma_diff_threshold,
          volatility_threshold: config.value.volatility_threshold,
          use_volume_analysis: config.value.use_volume_analysis,
          volume_change_threshold: config.value.volume_change_threshold,
          volume_stability_threshold: config.value.volume_stability_threshold,
          volume_increase_threshold: config.value.volume_increase_threshold,
          max_turnover_rate: config.value.max_turnover_rate,
          allow_turnover_spikes: config.value.allow_turnover_spikes,
          use_breakthrough_prediction: config.value.use_breakthrough_prediction,
          use_window_weights: config.value.use_window_weights,
          use_low_position: config.value.use_low_position,
          high_point_lookback_days: config.value.high_point_lookback_days,
          decline_period_days: config.value.decline_period_days,
          decline_threshold: config.value.decline_threshold,

          // 快速下跌判断参数
          use_rapid_decline_detection: config.value.use_rapid_decline_detection,
          rapid_decline_days: config.value.rapid_decline_days,
          rapid_decline_threshold: config.value.rapid_decline_threshold,

          // 箱体检测参数
          use_box_detection: config.value.use_box_detection,
          box_quality_threshold: config.value.box_quality_threshold
        },
        // 添加标记线数据
        mark_lines: markLines
      },
      klineData: stock.kline_data || []
    };

    // 如果有成交量分析，添加到结果中
    if (stock.volume_analysis) {
      exportData.analysisResult.volume_analysis = stock.volume_analysis;
    }

    // 如果有突破预测，添加到结果中
    if (stock.breakthrough_prediction) {
      exportData.analysisResult.breakthrough_prediction = stock.breakthrough_prediction;
    }

    // 如果有低位分析，添加到结果中
    if (stock.position_analysis) {
      exportData.analysisResult.position_analysis = stock.position_analysis;
    }

    // 如果有快速下跌分析，添加到结果中
    if (stock.decline_details) {
      exportData.analysisResult.decline_details = stock.decline_details;
      exportData.analysisResult.is_rapid_decline = stock.is_rapid_decline || false;
      exportData.analysisResult.has_decline_pattern = stock.has_decline_pattern || false;
    }

    // 如果有箱体分析，添加到结果中
    if (stock.box_analysis) {
      exportData.analysisResult.box_analysis = stock.box_analysis;

      // 确保箱体分析中包含支撑位和阻力位
      if (supportLevels && supportLevels.length > 0) {
        exportData.analysisResult.box_analysis.support_levels = supportLevels;
      }
      if (resistanceLevels && resistanceLevels.length > 0) {
        exportData.analysisResult.box_analysis.resistance_levels = resistanceLevels;
      }
    } else if (supportLevels.length > 0 || resistanceLevels.length > 0) {
      // 如果没有箱体分析但有支撑位或阻力位，创建箱体分析对象
      exportData.analysisResult.box_analysis = {
        is_box_pattern: true,
        box_quality: 0.8,
        support_levels: supportLevels,
        resistance_levels: resistanceLevels
      };
    }

    // 发送请求到后端
    const response = await axios.post('/platform/api/cases/export', exportData);

    // 关闭加载提示
    closeToast(loadingToast);

    // 显示成功提示
    if (response.data && response.data.success) {
      showToast(`${stock.name} 已成功导出到案例库`, 'success');
    } else {
      throw new Error(response.data.message || '导出失败');
    }
  } catch (error) {
    console.error('导出到案例库失败:', error);
    showToast(`导出失败: ${error.message || '未知错误'}`, 'error');
  }
}

// 导出扫描结果到CSV文件
function exportToCSV () {
  if (filteredStocks.value.length === 0) {
    showToast('没有可导出的数据', 'error');
    return;
  }

  try {
    // CSV 表头
    const headers = ['代码', '名称', '行业', '选择理由'];
    
    // 构建CSV行数据（使用筛选后的股票）
    const rows = filteredStocks.value.map(stock => {
      // 格式化选择理由
      let reasons = '';
      if (stock.selection_reasons) {
        reasons = Object.entries(stock.selection_reasons)
          .map(([key, value]) => `${key}: ${value}`)
          .join('; ');
      }
      
      return [
        stock.code || '',
        stock.name || '',
        stock.industry || '未知行业',
        reasons
      ];
    });

    // 添加BOM以支持中文Excel打开
    const BOM = '\uFEFF';
    
    // 构建CSV内容
    const csvContent = BOM + [
      headers.join(','),
      ...rows.map(row => row.map(cell => {
        // 处理包含逗号、引号或换行的单元格
        const cellStr = String(cell);
        if (cellStr.includes(',') || cellStr.includes('"') || cellStr.includes('\n')) {
          return `"${cellStr.replace(/"/g, '""')}"`;
        }
        return cellStr;
      }).join(','))
    ].join('\n');

    // 创建下载链接
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    
    // 生成文件名（包含日期）
    const date = new Date();
    const dateStr = `${date.getFullYear()}${String(date.getMonth() + 1).padStart(2, '0')}${String(date.getDate()).padStart(2, '0')}`;
    const filename = `平台股扫描结果_${dateStr}.csv`;
    
    link.setAttribute('href', url);
    link.setAttribute('download', filename);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);

    showToast(`已导出 ${filteredStocks.value.length} 条数据`, 'success');
  } catch (error) {
    console.error('导出CSV失败:', error);
    showToast(`导出失败: ${error.message || '未知错误'}`, 'error');
  }
}

// 显示提示消息
function showToast (message, type = 'info') {
  const toast = document.createElement('div');
  toast.className = `fixed top-4 right-4 p-4 rounded-md shadow-md z-50 transition-all duration-300 transform translate-y-0 opacity-100 ${type === 'success' ? 'bg-gundam-blue' :
    type === 'error' ? 'bg-gundam-red' :
      type === 'loading' ? 'bg-gundam-yellow' : 'bg-gray-700'
    } text-white`;

  // 添加图标
  let icon = '';
  if (type === 'success') {
    icon = '<i class="fas fa-check-circle mr-2"></i>';
  } else if (type === 'error') {
    icon = '<i class="fas fa-exclamation-circle mr-2"></i>';
  } else if (type === 'loading') {
    icon = '<i class="fas fa-spinner fa-spin mr-2"></i>';
  } else {
    icon = '<i class="fas fa-info-circle mr-2"></i>';
  }

  toast.innerHTML = `<div class="flex items-center">${icon}${message}</div>`;
  document.body.appendChild(toast);

  // 如果不是加载中状态，3秒后自动关闭
  if (type !== 'loading') {
    setTimeout(() => {
      closeToast(toast);
    }, 3000);
  }

  return toast;
}

// 关闭提示消息
function closeToast (toast) {
  if (!toast) return;

  toast.classList.replace('translate-y-0', '-translate-y-4');
  toast.classList.replace('opacity-100', 'opacity-0');

  setTimeout(() => {
    if (toast.parentNode) {
      toast.parentNode.removeChild(toast);
    }
  }, 300);
}

// Computed property to parse windows input string into an array of numbers
const parsedWindows = computed(() => {
  // 优先从 ScanConfigForm 组件获取 parsedWindows
  if (scanConfigFormRef.value && scanConfigFormRef.value.parsedWindows) {
    return scanConfigFormRef.value.parsedWindows;
  }
  
  // 如果没有组件引用，则从 config 中解析
  // 添加安全检查，确保 windowsInput 存在且有效
  const windowsInput = config.value?.windowsInput || '30,60,90';
  const windows = windowsInput
    .split(',')
    .map(w => parseInt(w.trim(), 10))
    .filter(w => !isNaN(w) && w > 0);

  // 如果解析结果为空，返回默认值
  if (windows.length === 0) {
    return [30, 60, 90];
  }

  return windows;
});

// 构建扫描配置 payload 的辅助函数
// 从 config 中提取所有扫描相关参数，排除不需要的字段
function buildScanPayload(config, options = {}) {
  const {
    includeScanDate = true, // 是否包含 scan_date
    windows = null, // 自定义 windows（如果提供则使用，否则从 config 解析）
    scanDate = null // 自定义 scan_date（如果提供则使用，否则从 config 获取）
  } = options

  // 需要排除的字段（这些字段不应该发送到后端）
  const excludeFields = ['windowsInput'] // windowsInput 需要转换为 windows 数组

  // 从 config 中提取所有字段，排除不需要的
  const payload = {}
  Object.keys(config).forEach(key => {
    if (!excludeFields.includes(key)) {
      const value = config[key]
      // 处理 null/undefined 值
      if (value !== null && value !== undefined) {
        payload[key] = value
      }
    }
  })

  // 设置 windows（优先使用传入的，否则从 config 解析）
  if (windows) {
    payload.windows = windows
  } else if (config.windowsInput) {
    const parsed = config.windowsInput
      .split(',')
      .map(w => parseInt(w.trim(), 10))
      .filter(w => !isNaN(w) && w > 0)
    payload.windows = parsed.length > 0 ? parsed : [30, 60, 90]
  }

  // 设置 scan_date（如果包含）
  if (includeScanDate) {
    payload.scan_date = scanDate || config.scan_date || maxDate.value
  }

  // 处理特殊字段的默认值
  if (payload.expected_count === undefined || payload.expected_count === null) {
    payload.expected_count = 10
  }

  // 处理 outperform_index_threshold（null 值需要明确传递）
  if (payload.outperform_index_threshold === null || payload.outperform_index_threshold === undefined) {
    payload.outperform_index_threshold = null
  }

  // 处理 use_scan_cache 默认值
  if (payload.use_scan_cache === undefined) {
    payload.use_scan_cache = false
  }

  // 处理 max_stock_count（null 或 0 表示不限制）
  if (payload.max_stock_count && payload.max_stock_count > 0) {
    payload.max_stock_count = payload.max_stock_count
  } else {
    payload.max_stock_count = null
  }

  // 处理 use_local_database_first 默认值
  if (payload.use_local_database_first === undefined) {
    payload.use_local_database_first = true
  }

  // 处理 window_weights（确保是对象）
  if (payload.window_weights && typeof payload.window_weights === 'object') {
    payload.window_weights = payload.window_weights
  } else {
    payload.window_weights = {}
  }

  return payload
}

// 清理轮询定时器
onUnmounted(() => {
  if (pollingInterval.value) {
    clearInterval(pollingInterval.value);
  }
});

// 开始轮询任务状态
function startPolling (taskId) {
  // 清除之前的轮询
  if (pollingInterval.value) {
    clearInterval(pollingInterval.value);
  }

  // 设置新的轮询
  pollingInterval.value = setInterval(async () => {
    try {
      const response = await axios.get(`/platform/api/scan/status/${taskId}`);
      const taskData = response.data;

      // 更新任务状态
      taskStatus.value = taskData.status;
      taskProgress.value = taskData.progress;
      taskMessage.value = taskData.message;

      // 如果任务完成或失败，停止轮询
      if (taskData.status === 'completed') {
        clearInterval(pollingInterval.value);
        loading.value = false;

        // 处理结果
        if (taskData.result && Array.isArray(taskData.result)) {
          // 处理每个股票数据，确保所有字段都被正确保留
          const processedResults = taskData.result.map(stock => {
            // 创建处理后的股票对象，确保所有字段都被正确保留
            const processedStock = {
              ...stock, // 先保留所有原始字段
              // 如果后端返回了mark_lines字段，将其重命名为markLines
              markLines: stock.mark_lines || stock.markLines || [],
              // 确保这些字段存在（即使后端没有返回，也设置为null或空对象）
              volume_analysis: stock.volume_analysis || null,
              breakthrough_prediction: stock.breakthrough_prediction || null,
              turnover_analysis: stock.turnover_analysis || null,
              box_analysis: stock.box_analysis || null,
              details: stock.details || {},
              selection_reasons: stock.selection_reasons || {},
              platform_windows: stock.platform_windows || [],
              kline_data: stock.kline_data || [],
              outperform_index: stock.outperform_index !== undefined ? stock.outperform_index : null,
              stock_return: stock.stock_return !== undefined ? stock.stock_return : null,
              market_return: stock.market_return !== undefined ? stock.market_return : null
            };
            
            // 如果后端返回了mark_lines字段，确保markLines也被设置
            if (stock.mark_lines && !processedStock.markLines) {
              processedStock.markLines = stock.mark_lines;
            }
            
            console.log(`处理股票 ${processedStock.code} 的数据:`, {
              hasVolumeAnalysis: !!processedStock.volume_analysis,
              hasBreakthroughPrediction: !!processedStock.breakthrough_prediction,
              hasTurnoverAnalysis: !!processedStock.turnover_analysis
            });
            
            return processedStock;
          });

          platformStocks.value = processedResults;
          console.log('处理后的平台股票数据:', platformStocks.value);

          // 统计可用平台期并设置默认全选
          updateAvailablePlatformPeriods();

          // 重置分页状态
          currentPage.value = 1;
          
          // 默认全选所有扫描结果
          selectedStocks.value = [...processedResults];
          console.log('✓ 扫描完成，默认全选所有股票:', selectedStocks.value.length, '只');
        } else {
          console.error("Task completed but no valid result:", taskData);
          error.value = "任务完成但未返回有效数据。";
        }
      } else if (taskData.status === 'failed') {
        clearInterval(pollingInterval.value);
        loading.value = false;
        taskError.value = taskData.error;
      }
    } catch (e) {
      console.error("Error polling task status:", e);
      // 如果轮询出错，不要立即停止，可能是临时网络问题
    }
  }, 2000); // 每2秒轮询一次
}

async function fetchPlatformStocks () {
  if (loading.value) return; // Prevent multiple clicks

  loading.value = true;
  error.value = null;
  taskError.value = null;
  platformStocks.value = []; // Clear previous results
  availablePlatformPeriods.value = []; // 清空可用平台期
  selectedPlatformPeriods.value = []; // 清空选中的平台期
  expandedReasons.value = {}; // 重置所有选择理由为收起状态
  hasSearched.value = true; // Mark that a search was initiated
  currentPage.value = 1; // 重置到第一页

  // Reset task status
  taskStatus.value = 'pending';
  taskProgress.value = 0;
  taskMessage.value = '准备开始扫描...';

  // Basic validation
  if (!parsedWindows.value.length) {
    error.value = "请输入有效的窗口期天数 (正整数，用逗号分隔)";
    loading.value = false;
    taskStatus.value = null;
    return;
  }
  if (config.value.box_threshold <= 0 || config.value.box_threshold >= 1) {
    error.value = "振幅阈值应在 0 和 1 之间 (例如 0.3 代表 30%)";
    loading.value = false;
    taskStatus.value = null;
    return;
  }
  // Add similar validation for other thresholds if needed

  try {
    // 使用辅助函数构建 payload
    const payload = buildScanPayload(config.value, {
      includeScanDate: true,
      windows: parsedWindows.value,
      scanDate: config.value.scan_date || maxDate.value
    })

    console.log("发送POST请求到 /platform/api/scan/start...");
    const resp = await axios.post('/platform/api/scan/start', payload);
    console.log("POST请求完成，获取任务ID:", resp.data);

    if (resp.data && resp.data.task_id) {
      currentTaskId.value = resp.data.task_id;
      taskMessage.value = resp.data.message || '任务已开始，正在处理...';
      taskStatus.value = 'running';

      // 开始轮询任务状态
      startPolling(currentTaskId.value);
    } else {
      throw new Error("服务器未返回有效的任务ID");
    }
  } catch (e) {
    console.error("Error starting scan:", e);
    error.value = `请求失败: ${e.message || '未知错误'}`;
    if (e.response) {
      console.error("Response error:", e.response.data);
      error.value = `服务器错误: ${e.response.data.detail || e.response.statusText}`;
    }
    loading.value = false;
    taskStatus.value = null;
  }
}

// 兼容旧版API的直接请求方法（用于测试）
async function fetchPlatformStocksLegacy () {
  if (loading.value) return;

  loading.value = true;
  error.value = null;
  platformStocks.value = [];
  availablePlatformPeriods.value = []; // 清空可用平台期
  selectedPlatformPeriods.value = []; // 清空选中的平台期
  hasSearched.value = true;
  currentPage.value = 1; // 重置到第一页
  expandedReasons.value = {}; // 重置所有选择理由为收起状态

  // Basic validation
  if (!parsedWindows.value.length) {
    error.value = "请输入有效的窗口期天数";
    loading.value = false;
    return;
  }

  try {
    // 使用辅助函数构建 payload
    const payload = buildScanPayload(config.value, {
      includeScanDate: true,
      windows: parsedWindows.value,
      scanDate: config.value.scan_date || maxDate.value
    })

    console.log("使用旧版API直接请求...");
    const resp = await axios.post('/platform/api/scan', payload, {
      timeout: 300000
    });

    if (Array.isArray(resp.data)) {
      // 处理每个股票数据，确保所有字段都被正确保留
      const processedResults = resp.data.map(stock => {
        // 创建处理后的股票对象，确保所有字段都被正确保留
        const processedStock = {
          ...stock, // 先保留所有原始字段
          // 如果后端返回了mark_lines字段，将其重命名为markLines
          markLines: stock.mark_lines || stock.markLines || [],
          // 确保这些字段存在（即使后端没有返回，也设置为null或空对象）
          volume_analysis: stock.volume_analysis || null,
          breakthrough_prediction: stock.breakthrough_prediction || null,
          turnover_analysis: stock.turnover_analysis || null,
          box_analysis: stock.box_analysis || null,
          details: stock.details || {},
          selection_reasons: stock.selection_reasons || {},
          platform_windows: stock.platform_windows || [],
          kline_data: stock.kline_data || []
        };
        
        // 如果后端返回了mark_lines字段，确保markLines也被设置
        if (stock.mark_lines && !processedStock.markLines) {
          processedStock.markLines = stock.mark_lines;
        }
        
        console.log(`处理股票 ${processedStock.code} 的数据:`, {
          hasVolumeAnalysis: !!processedStock.volume_analysis,
          hasBreakthroughPrediction: !!processedStock.breakthrough_prediction,
          hasTurnoverAnalysis: !!processedStock.turnover_analysis
        });
        
        return processedStock;
      });

      platformStocks.value = processedResults;
      console.log('处理后的平台股票数据:', platformStocks.value);
      
      // 统计可用平台期并设置默认全选
      updateAvailablePlatformPeriods();
      
      // 默认全选所有扫描结果
      selectedStocks.value = [...processedResults];
      console.log('✓ 扫描完成，默认全选所有股票:', selectedStocks.value.length, '只');
      
      // 保存扫描配置到 localStorage，供回测使用（使用辅助函数构建）
      const currentScanConfig = buildScanPayload(config.value, {
        includeScanDate: true,
        windows: parsedWindows.value,
        scanDate: config.value.scan_date || maxDate.value
      })
      
      try {
        localStorage.setItem('scanConfig', JSON.stringify(currentScanConfig));
        console.log('扫描配置已保存到 localStorage');
      } catch (e) {
        console.error('保存扫描配置失败:', e);
      }
    } else {
      error.value = "API返回的数据格式不正确";
    }
  } catch (e) {
    console.error("Error with legacy API:", e);
    error.value = `请求失败: ${e.message || '未知错误'}`;
  } finally {
    loading.value = false;
  }
}

// 格式化日期时间
function formatDateTime(isoString) {
  if (!isoString) return ''
  const date = new Date(isoString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 处理日期筛选组件的查询事件
async function handleScanHistoryQuery(queryParams) {
  scanHistoryLoading.value = true
  try {
    // 如果没有选择年度，查询所有数据（用户选择了"全部年度"）
    if (!queryParams.year) {
      const url = '/platform/api/scan/history?use_current_quarter=false'
      const response = await axios.get(url)
      if (response.data.success) {
        scanHistory.value = response.data.data || []
        groupScanHistoryByDate()
      } else {
        error.value = '加载扫描历史失败'
      }
      return
    }
    
    // 使用组件计算的日期范围
    const { startDate, endDate, useCurrentQuarter } = queryParams
    
    // 构建查询URL
    let url = '/platform/api/scan/history'
    const params = []
    
    if (useCurrentQuarter) {
      // 使用当前季度（默认）
      params.push('use_current_quarter=true')
    } else {
      // 使用指定的日期范围
      params.push(`start_date=${startDate}`)
      params.push(`end_date=${endDate}`)
      params.push('use_current_quarter=false')
    }
    
    if (params.length > 0) {
      url += '?' + params.join('&')
    }
    
    const response = await axios.get(url)
    if (response.data.success) {
      scanHistory.value = response.data.data || []
      // 按扫描日期分组
      groupScanHistoryByDate()
    } else {
      error.value = '加载扫描历史失败'
    }
  } catch (e) {
    console.error('加载扫描历史失败:', e)
    error.value = '加载扫描历史失败: ' + (e.response?.data?.detail || e.message)
    scanHistory.value = []
  } finally {
    scanHistoryLoading.value = false
  }
}

// 获取当前季度信息
function getCurrentQuarter() {
  const now = new Date()
  const year = now.getFullYear()
  const month = now.getMonth() + 1 // 0-11 -> 1-12
  
  const quarter = Math.ceil(month / 3)
  
  return {
    year: year.toString(),
    quarter: `Q${quarter}`,
    quarterNum: quarter
  }
}

// 加载扫描历史记录列表（初始化时调用，使用默认筛选条件）
async function loadScanHistory() {
  // 默认使用当前季度查询
  const currentQuarter = getCurrentQuarter()
  await handleScanHistoryQuery({
    year: currentQuarter.year,
    quarter: currentQuarter.quarter,
    month: '',
    useCurrentQuarter: true
  })
}

// 按扫描日期分组扫描历史
function groupScanHistoryByDate() {
  const grouped = {}
  scanHistory.value.forEach(record => {
    const scanDate = record.scanDate || '未知日期'
    if (!grouped[scanDate]) {
      grouped[scanDate] = []
    }
    grouped[scanDate].push(record)
  })
  // 按日期倒序排序
  const sortedDates = Object.keys(grouped).sort((a, b) => {
    if (a === '未知日期') return 1
    if (b === '未知日期') return -1
    return b.localeCompare(a)
  })
  const sortedGrouped = {}
  sortedDates.forEach(date => {
    sortedGrouped[date] = grouped[date]
  })
  scanHistoryGroupedByDate.value = sortedGrouped
}

// 获取可用的年度列表
const availableScanYears = computed(() => {
  const years = new Set()
  scanHistory.value.forEach(record => {
    const scanDate = record.scanDate || ''
    if (scanDate && scanDate !== '未知日期') {
      const year = scanDate.substring(0, 4)
      if (year && /^\d{4}$/.test(year)) {
        years.add(year)
      }
    }
  })
  return Array.from(years).sort((a, b) => b.localeCompare(a))
})

// 获取可用的季度列表（基于选中的年度）
const availableScanQuarters = computed(() => {
  if (!selectedScanYear.value) {
    return []
  }
  const quarters = new Set()
  scanHistory.value.forEach(record => {
    const scanDate = record.scanDate || ''
    if (scanDate && scanDate !== '未知日期' && scanDate.startsWith(selectedScanYear.value)) {
      const month = parseInt(scanDate.substring(5, 7))
      if (month >= 1 && month <= 12) {
        const quarter = Math.ceil(month / 3)
        quarters.add(`Q${quarter}`)
      }
    }
  })
  return Array.from(quarters).sort()
})

// 获取可用的月度列表（基于选中的年度和季度）
const availableScanMonths = computed(() => {
  if (!selectedScanYear.value) {
    return []
  }
  const months = new Set()
  let targetMonths = []
  
  // 如果选择了季度，只显示该季度的月份
  if (selectedScanQuarter.value) {
    const quarterNum = parseInt(selectedScanQuarter.value.substring(1))
    if (quarterNum === 1) targetMonths = [1, 2, 3]
    else if (quarterNum === 2) targetMonths = [4, 5, 6]
    else if (quarterNum === 3) targetMonths = [7, 8, 9]
    else if (quarterNum === 4) targetMonths = [10, 11, 12]
  } else {
    // 如果没有选择季度，显示该年度所有月份
    targetMonths = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
  }
  
  scanHistory.value.forEach(record => {
    const scanDate = record.scanDate || ''
    if (scanDate && scanDate !== '未知日期' && scanDate.startsWith(selectedScanYear.value)) {
      const month = parseInt(scanDate.substring(5, 7))
      if (month >= 1 && month <= 12 && targetMonths.includes(month)) {
        months.add(month)
      }
    }
  })
  return Array.from(months).sort((a, b) => a - b)
})

// 按年度、季度、月度筛选后的分组历史记录（现在数据已在服务端过滤，直接返回分组结果）
const filteredScanHistoryGroupedByDate = computed(() => {
  return scanHistoryGroupedByDate.value
})

// 查看扫描历史记录详情
async function viewScanHistoryRecord(record) {
  try {
    showScanConfigDetails.value = false // 重置折叠状态
    const response = await axios.get(`/platform/api/scan/history/${record.id}`)
    if (response.data.success) {
      selectedScanHistoryRecord.value = response.data.data
    } else {
      error.value = '加载扫描历史详情失败'
    }
  } catch (e) {
    console.error('加载扫描历史详情失败:', e)
    error.value = '加载扫描历史详情失败: ' + (e.response?.data?.detail || e.message)
  }
}

// 删除扫描历史记录
function showDeleteScanHistoryConfirm(cacheKey) {
  confirmDialog.value = {
    show: true,
    title: '确认删除',
    message: '确定要删除这条扫描历史记录吗？此操作不可恢复。',
    type: 'danger',
    onConfirm: () => executeDeleteScanHistory(cacheKey),
    pendingAction: cacheKey
  }
}

async function executeDeleteScanHistory(cacheKey) {
  try {
    const response = await axios.delete(`/platform/api/scan/history/${cacheKey}`)
    if (response.data.success) {
      // 从列表中移除
      scanHistory.value = scanHistory.value.filter(r => r.id !== cacheKey)
      // 重新分组
      groupScanHistoryByDate()
      // 如果正在查看这条记录，关闭详情对话框
      if (selectedScanHistoryRecord.value && selectedScanHistoryRecord.value.id === cacheKey) {
        selectedScanHistoryRecord.value = null
      }
    } else {
      error.value = '删除扫描历史记录失败'
    }
  } catch (e) {
    console.error('删除扫描历史记录失败:', e)
    error.value = '删除扫描历史记录失败: ' + (e.response?.data?.detail || e.message)
  }
}

// 清空所有扫描历史
function showClearScanHistoryConfirm() {
  confirmDialog.value = {
    show: true,
    title: '确认清空',
    message: '确定要清空所有扫描历史记录吗？此操作不可恢复。',
    type: 'danger',
    onConfirm: executeClearScanHistory,
    pendingAction: null
  }
}

async function executeClearScanHistory() {
  try {
    const response = await axios.delete('/platform/api/scan/history')
    if (response.data.success) {
      scanHistory.value = []
      scanHistoryGroupedByDate.value = {}
      selectedScanHistoryRecord.value = null
    } else {
      error.value = '清空扫描历史记录失败'
    }
  } catch (e) {
    console.error('清空扫描历史记录失败:', e)
    error.value = '清空扫描历史记录失败: ' + (e.response?.data?.detail || e.message)
  }
}

// 加载扫描历史记录到扫描工具页面
async function loadScanHistoryToPage(record) {
  try {
    // 如果记录中没有完整的股票数据，需要先获取详情
    let scanRecord = record
    if (!record.scannedStocks || record.scannedStocks.length === 0) {
      const response = await axios.get(`/platform/api/scan/history/${record.id}`)
      if (response.data.success) {
        scanRecord = response.data.data
      } else {
        error.value = '加载扫描历史详情失败'
        return
      }
    }

    // 检查是否有股票数据
    if (!scanRecord.scannedStocks || scanRecord.scannedStocks.length === 0) {
      error.value = '该扫描记录中没有股票数据'
      return
    }

    // 处理股票数据，转换为扫描工具页面需要的格式
    const processedStocks = scanRecord.scannedStocks.map(stock => {
      const processedStock = {
        code: stock.code || '',
        name: stock.name || '',
        industry: stock.industry || '未知行业',
        selection_reasons: stock.selection_reasons || {},
        platform_windows: stock.platform_windows || [],
        kline_data: stock.kline_data || [],
        markLines: stock.mark_lines || stock.markLines || [],
        supportLevels: stock.supportLevels || [],
        resistanceLevels: stock.resistanceLevels || [],
        breakthrough_prediction: stock.breakthrough_prediction || null,
        volume_analysis: stock.volume_analysis || null,
        box_analysis: stock.box_analysis || null,
        details: stock.details || {},
        outperform_index: stock.outperform_index !== undefined ? stock.outperform_index : null,
        stock_return: stock.stock_return !== undefined ? stock.stock_return : null,
        market_return: stock.market_return !== undefined ? stock.market_return : null
      }
      
      // 如果后端返回了mark_lines字段，将其重命名为markLines
      if (stock.mark_lines && !processedStock.markLines) {
        processedStock.markLines = stock.mark_lines
      }
      
      return processedStock
    })

    // 更新平台股票数据
    platformStocks.value = processedStocks
    console.log('已加载扫描历史记录到扫描工具页面，股票数量:', processedStocks.length)

    // 设置状态，确保结果区域可见
    loading.value = false
    hasSearched.value = true
    error.value = null

    // 统计可用平台期并设置默认全选
    updateAvailablePlatformPeriods()

    // 重置分页状态
    currentPage.value = 1
    expandedReasons.value = {}

    // 默认全选所有扫描结果
    selectedStocks.value = [...processedStocks]
    console.log('✓ 已加载扫描历史，默认全选所有股票:', selectedStocks.value.length, '只')

    // 关闭扫描历史对话框
    showScanHistoryDialog.value = false
    selectedScanHistoryRecord.value = null

    // 显示成功提示
    showToast(`已加载 ${processedStocks.length} 只股票到扫描工具`, 'success')

    // 滚动到结果区域
    nextTick(() => {
      const resultsSection = document.querySelector('.card.overflow-hidden')
      if (resultsSection) {
        resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' })
      }
    })
  } catch (e) {
    console.error('加载扫描历史到扫描工具页面失败:', e)
    error.value = '加载扫描历史数据失败: ' + (e.response?.data?.detail || e.message)
    showToast('加载失败: ' + (e.response?.data?.detail || e.message), 'error')
  }
}

// 从扫描历史跳转到回测页面
async function goToBacktestFromScanHistory(record) {
  try {
    // 如果记录中没有完整的股票数据，需要先获取详情
    let scanRecord = record
    if (!record.scannedStocks || record.scannedStocks.length === 0) {
      const response = await axios.get(`/platform/api/scan/history/${record.id}`)
      if (response.data.success) {
        scanRecord = response.data.data
      } else {
        error.value = '加载扫描历史详情失败'
        return
      }
    }

    // 检查是否有股票数据
    if (!scanRecord.scannedStocks || scanRecord.scannedStocks.length === 0) {
      error.value = '该扫描记录中没有股票数据，无法进行回测'
      return
    }

    // 准备股票数据（确保格式正确）
    const stocksForBacktest = scanRecord.scannedStocks.map(stock => ({
      code: stock.code,
      name: stock.name,
      industry: stock.industry || '未知行业',
      selection_reasons: stock.selection_reasons || {}
    }))

    // 准备扫描配置
    const scanConfig = scanRecord.scanConfig || {}
    
    console.log('准备从扫描历史跳转到回测页面')
    console.log('股票数量:', stocksForBacktest.length)
    console.log('扫描配置:', scanConfig)
    
    // 保存选中的股票和扫描配置到sessionStorage
    try {
      sessionStorage.setItem('selectedStocks', JSON.stringify(stocksForBacktest))
      sessionStorage.setItem('scanConfig', JSON.stringify(scanConfig))
      console.log('已保存选中的股票和扫描配置到 sessionStorage')
      
      // 关闭扫描历史对话框
      showScanHistoryDialog.value = false
      selectedScanHistoryRecord.value = null
      
      // 跳转到回测页面
      router.push('/platform/backtest')
    } catch (e) {
      console.error('保存数据到 sessionStorage 失败:', e)
      error.value = '保存数据失败，请重试'
    }
  } catch (e) {
    console.error('从扫描历史跳转到回测页面失败:', e)
    error.value = '加载扫描历史数据失败: ' + (e.response?.data?.detail || e.message)
  }
}

</script>

<style>
/* Add any global styles if needed, or rely on Tailwind */
body {
  background-color: #f7fafc;
  /* Light gray background */
}

/* 防止图表在鼠标悬停时变模糊 */
.chart-container {
  isolation: isolate;
  /* 创建新的层叠上下文 */
  transform: translateZ(0);
  /* 启用硬件加速 */
  backface-visibility: hidden;
  /* 防止 3D 变换时的模糊 */
  will-change: transform;
  /* 告诉浏览器该元素会变化，优化渲染 */
  position: relative;
  /* 创建新的层叠上下文 */
  z-index: 1;
  /* 确保在正确的层级 */
}

/* 确保表格行不会影响图表渲染 */
tbody tr {
  transition: none;
  /* 移除所有过渡效果 */
}

/* 表格行悬停效果，但不影响子元素 */
tbody tr:hover>td:not(:last-child) {
  background-color: rgba(0, 0, 0, 0.05);
}
</style>