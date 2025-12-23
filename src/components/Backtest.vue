<template>
  <div class="min-h-screen bg-background text-foreground">
    <!-- 顶部导航栏 -->
    <header class="bg-card border-b border-border p-4 flex justify-between items-center sticky top-0 z-30">
      <div class="flex items-center">
        <img src="/gundam-logo.svg" alt="Gundam Logo" class="w-8 h-8 mr-2" />
        <h1 class="text-xl font-semibold">数据回测</h1>
      </div>

      <div class="flex items-center space-x-2 sm:space-x-3">
        <!-- 回测历史按钮 -->
        <button
          @click="showHistoryDialog = true; loadBacktestHistory()"
          class="flex items-center justify-center px-2 sm:px-3 py-1.5 sm:py-2 rounded-md bg-primary text-primary-foreground hover:bg-primary/80 transition-colors"
        >
          <i class="fas fa-history mr-1 sm:mr-2"></i>
          <span class="hidden sm:inline">回测历史</span>
        </button>

        <!-- 返回按钮 -->
        <button 
          @click="goBack" 
          class="flex items-center justify-center px-2 sm:px-3 py-1.5 sm:py-2 rounded-md bg-gundam-blue text-white hover:bg-gundam-blue/80 transition-colors"
        >
          <i class="fas fa-arrow-left mr-1 sm:mr-2"></i>
          <span class="hidden sm:inline">返回</span>
        </button>

        <!-- 主题切换 -->
        <ThemeToggle />
      </div>
    </header>

    <!-- 主内容区 -->
    <main class="p-4 sm:p-6 md:p-8">
      <div class="max-w-6xl mx-auto">
        <!-- 回测参数配置卡片 -->
        <div class="card p-4 sm:p-6 mb-6">
          <h2 class="text-lg font-semibold mb-4 flex items-center">
            <i class="fas fa-sliders-h mr-2 text-primary"></i>
            回测参数配置
          </h2>

          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
            <!-- 回测日 -->
            <div>
              <label class="block text-sm font-medium mb-2">
                <i class="fas fa-calendar-alt mr-1 text-primary"></i>
                回测日（截止日）
              </label>
              <input
                v-model="backtestConfig.backtestDate"
                type="date"
                class="input w-full"
                :max="maxDate"
              />
              <p class="text-xs text-muted-foreground mt-1">
                以这一天为买入日，买入选中的股票
              </p>
            </div>

            <!-- 统计日 -->
            <div>
              <label class="block text-sm font-medium mb-2">
                <i class="fas fa-calendar-check mr-1 text-primary"></i>
                统计日
              </label>
              <input
                v-model="backtestConfig.statDate"
                type="date"
                class="input w-full"
                :max="maxDate"
              />
              <p class="text-xs text-muted-foreground mt-1">
                以这一天的数据计算收益
              </p>
            </div>
          </div>

          <!-- 买入卖出策略 -->
          <BuySellStrategy
            v-model="backtestConfig"
            unique-id="backtest"
            :show-help-text="true"
            stop-loss-placeholder="-3"
            take-profit-placeholder="10"
          />

          <!-- 回测股票预览 -->
          <div v-if="selectedStocks.length > 0" class="mb-6">
            <div class="flex items-center justify-between mb-3">
              <h3 class="text-sm font-medium flex items-center">
                <i class="fas fa-list mr-2 text-primary"></i>
                回测股票预览（已选 {{ selectedStockCodes.size }} / 共 {{ selectedStocks.length }} 只）
              </h3>
              <div class="flex items-center space-x-2">
                <button
                  @click="toggleSelectAll"
                  class="text-xs px-2 py-1 rounded-md bg-primary/10 text-primary hover:bg-primary/20 transition-colors"
                >
                  {{ isAllSelected ? '反选' : '全选' }}
                </button>
              </div>
            </div>
            <div class="bg-muted/30 p-4 rounded-md max-h-60 overflow-y-auto">
              <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2">
                <div 
                  v-for="stock in selectedStocks" 
                  :key="stock.code" 
                  class="flex items-center justify-between text-sm p-1.5 rounded transition-colors group"
                >
                  <div 
                    class="flex items-center space-x-2 flex-1 cursor-pointer hover:bg-muted/50 rounded p-1"
                    @click="toggleStock(stock.code)"
                  >
                    <input
                      type="checkbox"
                      :checked="selectedStockCodes.has(stock.code)"
                      @click.stop="toggleStock(stock.code)"
                      class="checkbox w-4 h-4 cursor-pointer"
                    />
                    <span class="font-medium">{{ stock.code }}</span>
                    <span class="text-muted-foreground">{{ stock.name }}</span>
                  </div>
                  <button
                    @click.stop="goToStockCheck(stock)"
                    class="ml-2 px-2 py-1 text-xs rounded-md bg-primary/10 text-primary hover:bg-primary/20 transition-colors opacity-0 group-hover:opacity-100"
                    title="单股查询"
                  >
                    <i class="fas fa-search"></i>
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- 提示信息 -->
          <div class="mb-6 p-4" :class="selectedStocks.length > 0 ? 'bg-green-500/10 border border-green-500/20' : 'bg-amber-500/10 border border-amber-500/20'">
            <div class="flex items-start">
              <i :class="[
                selectedStocks.length > 0 ? 'fas fa-check-circle text-green-500' : 'fas fa-info-circle text-amber-500',
                'mr-2 mt-0.5'
              ]"></i>
              <div class="flex-1">
                <p class="text-sm" :class="selectedStocks.length > 0 ? 'text-green-700 dark:text-green-400' : 'text-amber-700 dark:text-amber-400'">
                  <strong v-if="selectedStocks.length > 0">已加载回测股票：</strong>
                  <strong v-else>提示：</strong>
                  <span v-if="selectedStocks.length > 0">已从扫描工具页面选择 {{ selectedStocks.length }} 只股票，当前选中 {{ selectedStockCodes.size }} 只，可以开始回测。</span>
                  <span v-else>请先在扫描工具页面选择股票，然后点击"数据回测"按钮进入此页面。</span>
                </p>
              </div>
            </div>
          </div>

          <!-- 一键回测按钮 -->
          <div class="flex flex-col items-center space-y-4">
            <button
              @click="runBacktest"
              :disabled="loading || !canRunBacktest"
              class="btn btn-primary px-8 py-3 text-lg"
            >
              <i class="fas fa-play mr-2" v-if="!loading"></i>
              <i class="fas fa-spinner fa-spin mr-2" v-if="loading"></i>
              {{ loading ? '回测中...' : '一键回测' }}
            </button>
            
            <!-- 进度显示 -->
            <div v-if="loading" class="w-full max-w-md">
              <div class="mb-2 flex justify-between items-center text-sm">
                <span class="text-muted-foreground">{{ progressMessage || '正在初始化...' }}</span>
                <span class="font-medium">{{ progress }}%</span>
              </div>
              <div class="w-full bg-muted rounded-full h-2.5">
                <div 
                  class="bg-primary h-2.5 rounded-full transition-all duration-300"
                  :style="{ width: progress + '%' }"
                ></div>
              </div>
            </div>
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

        <!-- 回测结果 -->
        <transition name="slide-up">
          <div v-if="backtestResult" class="space-y-6">
            <!-- 回测摘要 -->
            <div class="card p-4 sm:p-6">
              <h2 class="text-lg font-semibold mb-4 flex items-center">
                <i class="fas fa-chart-bar mr-2 text-primary"></i>
                回测摘要
              </h2>
              <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div class="p-4 bg-muted/30 rounded-md">
                  <div class="text-sm text-muted-foreground mb-1">总买入股票数</div>
                  <div class="text-2xl font-bold">{{ backtestResult.summary.totalStocks }}</div>
                </div>
                <div class="p-4 bg-muted/30 rounded-md">
                  <div class="text-sm text-muted-foreground mb-1">总投入资金</div>
                  <div class="text-2xl font-bold">¥{{ formatNumber(backtestResult.summary.totalInvestment) }}</div>
                </div>
                <div class="p-4 bg-muted/30 rounded-md">
                  <div class="text-sm text-muted-foreground mb-1">总收益</div>
                  <div class="text-2xl font-bold" :class="backtestResult.summary.totalProfit >= 0 ? 'text-red-600 dark:text-red-400' : 'text-blue-600 dark:text-blue-400'">
                    {{ backtestResult.summary.totalProfit >= 0 ? '+' : '' }}¥{{ formatNumber(backtestResult.summary.totalProfit) }}
                  </div>
                </div>
                <div class="p-4 bg-muted/30 rounded-md">
                  <div class="text-sm text-muted-foreground mb-1">总收益率</div>
                  <div class="text-2xl font-bold" :class="backtestResult.summary.totalReturnRate >= 0 ? 'text-red-600 dark:text-red-400' : 'text-blue-600 dark:text-blue-400'">
                    {{ backtestResult.summary.totalReturnRate >= 0 ? '+' : '' }}{{ formatPercent(backtestResult.summary.totalReturnRate) }}%
                  </div>
                </div>
                <div class="p-4 bg-muted/30 rounded-md" v-if="backtestResult.summary.marketReturnRate !== null && backtestResult.summary.marketReturnRate !== undefined">
                  <div class="text-sm text-muted-foreground mb-1">大盘收益率（上证指数）</div>
                  <div class="text-2xl font-bold" :class="backtestResult.summary.marketReturnRate >= 0 ? 'text-red-600 dark:text-red-400' : 'text-blue-600 dark:text-blue-400'">
                    {{ backtestResult.summary.marketReturnRate >= 0 ? '+' : '' }}{{ formatPercent(backtestResult.summary.marketReturnRate) }}%
                  </div>
                </div>
                <div class="p-4 bg-muted/30 rounded-md" v-if="backtestResult.summary.marketReturnRate !== null && backtestResult.summary.marketReturnRate !== undefined">
                  <div class="text-sm text-muted-foreground mb-1">相对大盘超额收益</div>
                  <div class="text-2xl font-bold" :class="(backtestResult.summary.totalReturnRate - backtestResult.summary.marketReturnRate) >= 0 ? 'text-red-600 dark:text-red-400' : 'text-blue-600 dark:text-blue-400'">
                    {{ (backtestResult.summary.totalReturnRate - backtestResult.summary.marketReturnRate) >= 0 ? '+' : '' }}{{ formatPercent(backtestResult.summary.totalReturnRate - backtestResult.summary.marketReturnRate) }}%
                  </div>
                </div>
                <div class="p-4 bg-muted/30 rounded-md">
                  <div class="text-sm text-muted-foreground mb-1">盈利股票数</div>
                  <div class="text-2xl font-bold text-red-600 dark:text-red-400">{{ backtestResult.summary.profitableStocks }}</div>
                </div>
                <div class="p-4 bg-muted/30 rounded-md">
                  <div class="text-sm text-muted-foreground mb-1">亏损股票数</div>
                  <div class="text-2xl font-bold text-blue-600 dark:text-blue-400">{{ backtestResult.summary.lossStocks }}</div>
                </div>
              </div>
            </div>

            <!-- 买入记录 -->
            <div class="card p-4 sm:p-6">
              <h2 class="text-lg font-semibold mb-4 flex items-center">
                <i class="fas fa-shopping-cart mr-2 text-primary"></i>
                买入记录
              </h2>
              <div class="overflow-x-auto">
                <table class="w-full text-sm">
                  <thead>
                    <tr class="border-b border-border">
                      <th class="text-left p-2">股票代码</th>
                      <th class="text-left p-2">股票名称</th>
                      <th class="text-right p-2">买入日期</th>
                      <th class="text-right p-2">买入价格</th>
                      <th class="text-right p-2">买入数量</th>
                      <th class="text-right p-2">买入金额</th>
                      <th class="text-left p-2">筛选理由</th>
                    </tr>
                  </thead>
                  <tbody>
                    <template v-for="record in backtestResult.buyRecords" :key="record.code">
                      <tr class="border-b border-border/50 hover:bg-muted/30">
                        <td class="p-2">{{ record.code }}</td>
                        <td class="p-2">{{ record.name }}</td>
                        <td class="p-2 text-right">{{ record.buyDate }}</td>
                        <td class="p-2 text-right">¥{{ formatNumber(record.buyPrice, 2) }}</td>
                        <td class="p-2 text-right">{{ record.quantity }}</td>
                        <td class="p-2 text-right">¥{{ formatNumber(record.buyAmount) }}</td>
                        <td class="p-2">
                          <!-- 筛选理由标题栏（可点击） -->
                          <div v-if="record.selection_reasons && Object.keys(record.selection_reasons).length > 0"
                            @click="toggleReasonExpand(record.code)"
                            class="flex items-center justify-between cursor-pointer p-1.5 rounded hover:bg-muted/50 transition-colors">
                            <div class="flex items-center">
                              <i class="fas fa-info-circle text-primary mr-1.5"></i>
                              <span class="font-medium text-xs">查看理由</span>
                              <span class="ml-1.5 text-xs px-1.5 py-0.5 rounded-full bg-primary/10 text-primary">
                                {{ Object.keys(record.selection_reasons).length }}
                              </span>
                            </div>
                            <i :class="[
                              'fas transition-transform duration-300 text-xs',
                              expandedReasons[record.code] ? 'fa-chevron-up' : 'fa-chevron-down'
                            ]"></i>
                          </div>
                          <span v-else class="text-xs text-muted-foreground">无</span>
                        </td>
                      </tr>
                      <!-- 筛选理由详情行（可折叠） -->
                      <tr v-if="record.selection_reasons && Object.keys(record.selection_reasons).length > 0"
                        :key="`reason-${record.code}`"
                        class="border-b border-border/50">
                        <td colspan="7" class="p-2">
                          <div :class="[
                            'overflow-hidden transition-all duration-300',
                            expandedReasons[record.code] ? 'max-h-96 opacity-100' : 'max-h-0 opacity-0'
                          ]">
                            <div class="p-3 bg-muted/10 rounded">
                              <div v-for="(reason, window) in record.selection_reasons" :key="window"
                                class="mb-2 text-xs text-muted-foreground">
                                <span class="font-medium text-primary">{{ window }}天:</span>
                                {{ reason }}
                              </div>
                            </div>
                          </div>
                        </td>
                      </tr>
                    </template>
                  </tbody>
                </table>
              </div>
            </div>

            <!-- 卖出记录 -->
            <div class="card p-4 sm:p-6">
              <h2 class="text-lg font-semibold mb-4 flex items-center">
                <i class="fas fa-sign-out-alt mr-2 text-primary"></i>
                卖出记录
              </h2>
              <div class="overflow-x-auto">
                <table class="w-full text-sm">
                  <thead>
                    <tr class="border-b border-border">
                      <th class="text-left p-2">股票代码</th>
                      <th class="text-left p-2">股票名称</th>
                      <th class="text-right p-2">买入日期</th>
                      <th class="text-right p-2">卖出日期</th>
                      <th class="text-right p-2">买入价格</th>
                      <th class="text-right p-2">卖出价格</th>
                      <th class="text-right p-2">收益率</th>
                      <th class="text-right p-2">盈亏金额</th>
                      <th class="text-right p-2">卖出原因</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="record in backtestResult.sellRecords" :key="`${record.code}-${record.buyDate}`" class="border-b border-border/50 hover:bg-muted/30">
                      <td class="p-2">{{ record.code }}</td>
                      <td class="p-2">{{ record.name }}</td>
                      <td class="p-2 text-right">{{ record.buyDate }}</td>
                      <td class="p-2 text-right">{{ record.sellDate }}</td>
                      <td class="p-2 text-right">¥{{ formatNumber(record.buyPrice, 2) }}</td>
                      <td class="p-2 text-right">¥{{ formatNumber(record.sellPrice, 2) }}</td>
                      <td class="p-2 text-right" :class="record.returnRate >= 0 ? 'text-red-600 dark:text-red-400' : 'text-blue-600 dark:text-blue-400'">
                        {{ record.returnRate >= 0 ? '+' : '' }}{{ formatPercent(record.returnRate) }}%
                      </td>
                      <td class="p-2 text-right" :class="record.profit >= 0 ? 'text-red-600 dark:text-red-400' : 'text-blue-600 dark:text-blue-400'">
                        {{ record.profit >= 0 ? '+' : '' }}¥{{ formatNumber(record.profit) }}
                      </td>
                      <td class="p-2 text-right">
                        <span class="px-2 py-0.5 rounded-full text-xs" :class="getSellReasonClass(record.sellReason)">
                          {{ record.sellReason }}
                        </span>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

          </div>
        </transition>
      </div>
    </main>

    <!-- 回测历史对话框 -->
    <transition name="fade">
      <div v-if="showHistoryDialog" class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" @click.self="showHistoryDialog = false">
        <div class="bg-card border border-border rounded-lg shadow-lg max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
          <!-- 对话框头部 -->
          <div class="p-4 sm:p-6 border-b border-border">
            <div class="flex justify-between items-center mb-4">
              <h2 class="text-lg font-semibold flex items-center">
                <i class="fas fa-history mr-2 text-primary"></i>
                回测历史记录
              </h2>
              <button
                @click="showHistoryDialog = false"
                class="text-muted-foreground hover:text-foreground transition-colors"
              >
                <i class="fas fa-times text-xl"></i>
              </button>
            </div>
            <!-- 筛选器 -->
            <div class="flex flex-wrap items-center gap-3">
              <!-- 年度筛选 -->
              <div class="flex items-center space-x-2">
                <label class="text-sm text-muted-foreground whitespace-nowrap">
                  <i class="fas fa-filter mr-1"></i>
                  年度：
                </label>
                <select
                  v-model="selectedBacktestYear"
                  @change="selectedBacktestQuarter = ''; selectedBacktestMonth = ''"
                  class="input text-sm px-3 py-1.5 min-w-[120px]"
                >
                  <option value="">全部年度</option>
                  <option v-for="year in availableBacktestYears" :key="year" :value="year">
                    {{ year }}年
                  </option>
                </select>
              </div>
              <!-- 季度筛选 -->
              <div class="flex items-center space-x-2" v-if="selectedBacktestYear">
                <label class="text-sm text-muted-foreground whitespace-nowrap">
                  季度：
                </label>
                <select
                  v-model="selectedBacktestQuarter"
                  @change="selectedBacktestMonth = ''"
                  class="input text-sm px-3 py-1.5 min-w-[120px]"
                >
                  <option value="">全部季度</option>
                  <option v-for="quarter in availableBacktestQuarters" :key="quarter" :value="quarter">
                    {{ quarter }}
                  </option>
                </select>
              </div>
              <!-- 月度筛选 -->
              <div class="flex items-center space-x-2" v-if="selectedBacktestYear">
                <label class="text-sm text-muted-foreground whitespace-nowrap">
                  月度：
                </label>
                <select
                  v-model="selectedBacktestMonth"
                  class="input text-sm px-3 py-1.5 min-w-[120px]"
                >
                  <option value="">全部月度</option>
                  <option v-for="month in availableBacktestMonths" :key="month" :value="month">
                    {{ month }}月
                  </option>
                </select>
              </div>
            </div>
          </div>

          <!-- 历史记录列表 -->
          <div class="flex-1 overflow-y-auto p-4 sm:p-6">
            <div v-if="backtestHistoryLoading" class="text-center py-8">
              <i class="fas fa-spinner fa-spin text-2xl mb-4 text-primary"></i>
              <p class="text-muted-foreground">加载中...</p>
            </div>
            <div v-else-if="backtestHistory.length === 0" class="text-center py-8 text-muted-foreground">
              <i class="fas fa-inbox text-4xl mb-4"></i>
              <p>暂无回测历史记录</p>
            </div>
            <div v-else class="space-y-6">
              <!-- 按日期分组显示 -->
              <div v-for="(records, scanDate) in filteredBacktestHistoryGroupedByDate" :key="scanDate" class="space-y-3">
                <div class="sticky top-0 bg-card/95 backdrop-blur-sm border-b border-border pb-2 mb-3 flex justify-between items-center">
                  <h3 class="text-md font-semibold text-primary flex items-center">
                    <i class="fas fa-calendar-alt mr-2"></i>
                    扫描日期: {{ scanDate }}
                    <span class="ml-2 text-sm text-muted-foreground">({{ records.length }} 条记录)</span>
                  </h3>
                  <button
                    @click.stop="showDeleteDateConfirm(scanDate)"
                    class="px-3 py-1.5 rounded-md bg-destructive/10 text-destructive hover:bg-destructive/20 transition-colors text-xs"
                    title="删除此日期的所有回测记录"
                  >
                    <i class="fas fa-trash mr-1"></i>
                    删除
                  </button>
                </div>
                <div
                  v-for="(record, index) in records"
                  :key="record.id"
                  class="card p-3 hover:bg-muted/30 transition-colors relative"
                >
                  <!-- 删除按钮 -->
                  <button
                    @click.stop="showDeleteHistoryConfirm(record.id)"
                    class="absolute top-2 right-2 p-1.5 rounded-md bg-destructive/10 text-destructive hover:bg-destructive/20 transition-colors z-10"
                    title="删除记录"
                  >
                    <i class="fas fa-trash text-xs"></i>
                  </button>

                  <!-- 可点击区域 -->
                  <div class="cursor-pointer" @click="viewHistoryRecord(record)">
                    <!-- 顶部：标题和主要收益信息 -->
                    <div class="flex justify-between items-start mb-2 pr-8">
                      <div class="flex-1 min-w-0">
                        <div class="flex items-center gap-2 mb-1">
                          <h3 class="font-semibold text-sm">
                            回测 #{{ records.length - index }}
                          </h3>
                          <span class="text-xs text-muted-foreground">
                            {{ formatDateTime(record.createdAt) }}
                          </span>
                        </div>
                        <div class="flex items-center gap-3 text-xs">
                          <span class="text-muted-foreground">回测日: {{ record.backtestDate }}</span>
                          <span class="text-muted-foreground">统计日: {{ record.statDate }}</span>
                        </div>
                      </div>
                      <div class="text-right ml-3 flex-shrink-0">
                        <div class="text-lg font-bold leading-tight" :class="record.summary.totalReturnRate >= 0 ? 'text-red-600 dark:text-red-400' : 'text-blue-600 dark:text-blue-400'">
                          {{ record.summary.totalReturnRate >= 0 ? '+' : '' }}{{ formatPercent(record.summary.totalReturnRate) }}%
                        </div>
                        <div class="text-xs text-muted-foreground leading-tight">
                          {{ record.summary.totalReturnRate >= 0 ? '+' : '' }}¥{{ formatNumber(record.summary.totalProfit) }}
                        </div>
                      </div>
                    </div>
                  </div>

                  <!-- 中间：详细信息网格 -->
                  <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-x-3 gap-y-1.5 text-xs border-t border-border/50 pt-2 mt-2 cursor-pointer" @click="viewHistoryRecord(record)">
                    <div>
                      <span class="text-muted-foreground">股票数:</span>
                      <span class="ml-1 font-medium">{{ record.summary.totalStocks }}</span>
                    </div>
                    <div>
                      <span class="text-muted-foreground">投入:</span>
                      <span class="ml-1 font-medium">¥{{ formatNumber(record.summary.totalInvestment) }}</span>
                    </div>
                    <!-- 大盘信息 -->
                    <div v-if="record.summary.marketReturnRate !== null && record.summary.marketReturnRate !== undefined">
                      <span class="text-muted-foreground">大盘:</span>
                      <span class="ml-1 font-medium" :class="record.summary.marketReturnRate >= 0 ? 'text-red-600 dark:text-red-400' : 'text-blue-600 dark:text-blue-400'">
                        {{ record.summary.marketReturnRate >= 0 ? '+' : '' }}{{ formatPercent(record.summary.marketReturnRate) }}%
                      </span>
                    </div>
                    <div v-if="record.summary.marketReturnRate !== null && record.summary.marketReturnRate !== undefined">
                      <span class="text-muted-foreground">超额:</span>
                      <span class="ml-1 font-medium" :class="(record.summary.totalReturnRate - record.summary.marketReturnRate) >= 0 ? 'text-green-600 dark:text-green-400' : 'text-orange-600 dark:text-orange-400'">
                        {{ (record.summary.totalReturnRate - record.summary.marketReturnRate) >= 0 ? '+' : '' }}{{ formatPercent(record.summary.totalReturnRate - record.summary.marketReturnRate) }}%
                      </span>
                    </div>
                    <!-- 止损止盈 -->
                    <div class="flex items-center gap-1 flex-wrap">
                      <span v-if="record.useStopLoss" class="px-1.5 py-0.5 rounded text-xs bg-blue-500/20 text-blue-700 dark:text-blue-400 whitespace-nowrap">
                        止损{{ record.stopLossPercent }}%
                      </span>
                      <span v-if="record.useTakeProfit" class="px-1.5 py-0.5 rounded text-xs bg-red-500/20 text-red-700 dark:text-red-400 whitespace-nowrap">
                        止盈{{ record.takeProfitPercent }}%
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 对话框底部 -->
          <div class="p-4 sm:p-6 border-t border-border flex justify-between items-center">
            <div class="flex space-x-2">
              <!-- <button
                @click="showBatchBacktestDialog = true"
                :disabled="selectedStocks.length === 0"
                class="px-4 py-2 rounded-md bg-green-600 text-white hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm"
              >
                <i class="fas fa-layer-group mr-2"></i>
                批量回测
              </button> -->
              <button
                v-if="backtestHistory.length > 0"
                @click="generateBacktestChart"
                class="px-4 py-2 rounded-md bg-primary text-primary-foreground hover:bg-primary/80 transition-colors text-sm"
              >
                <i class="fas fa-chart-line mr-2"></i>
                生成折线图
              </button>
              <button
                v-if="backtestHistory.length > 0"
                @click="showStatisticsDialog = true"
                class="px-4 py-2 rounded-md bg-blue-600 text-white hover:bg-blue-700 transition-colors text-sm"
              >
                <i class="fas fa-chart-bar mr-2"></i>
                数据统计
              </button>
            </div>
            <div class="flex space-x-2">
              <button
                v-if="backtestHistory.length > 0"
                @click="showClearBacktestHistoryConfirm"
                class="px-4 py-2 rounded-md bg-destructive/10 text-destructive hover:bg-destructive/20 transition-colors text-sm"
              >
                <i class="fas fa-trash mr-2"></i>
                清空历史
              </button>
              <button
                @click="showHistoryDialog = false"
                class="px-4 py-2 rounded-md bg-muted text-muted-foreground hover:bg-muted/80 transition-colors text-sm"
              >
                关闭
              </button>
            </div>
          </div>
        </div>
      </div>
    </transition>

    <!-- 历史记录详情对话框 -->
    <transition name="fade">
      <div v-if="selectedHistoryRecord" class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
        <div class="bg-card border border-border rounded-lg shadow-lg max-w-6xl w-full max-h-[90vh] overflow-hidden flex flex-col" @click.stop>
          <!-- 详情对话框头部 -->
          <div class="p-4 sm:p-6 border-b border-border flex justify-between items-center">
            <h2 class="text-lg font-semibold flex items-center">
              <i class="fas fa-chart-line mr-2 text-primary"></i>
              回测详情 - {{ formatDateTime(selectedHistoryRecord.createdAt) }}
            </h2>
            <button
              @click="selectedHistoryRecord = null"
              class="text-muted-foreground hover:text-foreground transition-colors"
            >
              <i class="fas fa-times text-xl"></i>
            </button>
          </div>

          <!-- 详情内容 -->
          <div class="flex-1 overflow-y-auto p-4 sm:p-6">
            <div class="space-y-6">
              <!-- 回测摘要 -->
              <div class="card p-4">
                <h3 class="text-md font-semibold mb-4">回测摘要</h3>
                <div class="grid grid-cols-2 sm:grid-cols-3 gap-4">
                  <div class="p-3 bg-muted/30 rounded-md">
                    <div class="text-sm text-muted-foreground mb-1">总买入股票数</div>
                    <div class="text-xl font-bold">{{ selectedHistoryRecord.result.summary.totalStocks }}</div>
                  </div>
                  <div class="p-3 bg-muted/30 rounded-md">
                    <div class="text-sm text-muted-foreground mb-1">总投入资金</div>
                    <div class="text-xl font-bold">¥{{ formatNumber(selectedHistoryRecord.result.summary.totalInvestment) }}</div>
                  </div>
                  <div class="p-3 bg-muted/30 rounded-md">
                    <div class="text-sm text-muted-foreground mb-1">总收益</div>
                    <div class="text-xl font-bold" :class="selectedHistoryRecord.result.summary.totalProfit >= 0 ? 'text-red-600 dark:text-red-400' : 'text-blue-600 dark:text-blue-400'">
                      {{ selectedHistoryRecord.result.summary.totalProfit >= 0 ? '+' : '' }}¥{{ formatNumber(selectedHistoryRecord.result.summary.totalProfit) }}
                    </div>
                  </div>
                  <div class="p-3 bg-muted/30 rounded-md">
                    <div class="text-sm text-muted-foreground mb-1">总收益率</div>
                    <div class="text-xl font-bold" :class="selectedHistoryRecord.result.summary.totalReturnRate >= 0 ? 'text-red-600 dark:text-red-400' : 'text-blue-600 dark:text-blue-400'">
                      {{ selectedHistoryRecord.result.summary.totalReturnRate >= 0 ? '+' : '' }}{{ formatPercent(selectedHistoryRecord.result.summary.totalReturnRate) }}%
                    </div>
                  </div>
                  <div class="p-3 bg-muted/30 rounded-md" v-if="selectedHistoryRecord.result.summary.marketReturnRate !== null && selectedHistoryRecord.result.summary.marketReturnRate !== undefined">
                    <div class="text-sm text-muted-foreground mb-1">大盘收益率（上证指数）</div>
                    <div class="text-xl font-bold" :class="selectedHistoryRecord.result.summary.marketReturnRate >= 0 ? 'text-red-600 dark:text-red-400' : 'text-blue-600 dark:text-blue-400'">
                      {{ selectedHistoryRecord.result.summary.marketReturnRate >= 0 ? '+' : '' }}{{ formatPercent(selectedHistoryRecord.result.summary.marketReturnRate) }}%
                    </div>
                  </div>
                  <div class="p-3 bg-muted/30 rounded-md" v-if="selectedHistoryRecord.result.summary.marketReturnRate !== null && selectedHistoryRecord.result.summary.marketReturnRate !== undefined">
                    <div class="text-sm text-muted-foreground mb-1">相对大盘超额收益</div>
                    <div class="text-xl font-bold" :class="(selectedHistoryRecord.result.summary.totalReturnRate - selectedHistoryRecord.result.summary.marketReturnRate) >= 0 ? 'text-red-600 dark:text-red-400' : 'text-blue-600 dark:text-blue-400'">
                      {{ (selectedHistoryRecord.result.summary.totalReturnRate - selectedHistoryRecord.result.summary.marketReturnRate) >= 0 ? '+' : '' }}{{ formatPercent(selectedHistoryRecord.result.summary.totalReturnRate - selectedHistoryRecord.result.summary.marketReturnRate) }}%
                    </div>
                  </div>
                  <div class="p-3 bg-muted/30 rounded-md">
                    <div class="text-sm text-muted-foreground mb-1">盈利股票数</div>
                    <div class="text-xl font-bold text-red-600 dark:text-red-400">{{ selectedHistoryRecord.result.summary.profitableStocks }}</div>
                  </div>
                  <div class="p-3 bg-muted/30 rounded-md">
                    <div class="text-sm text-muted-foreground mb-1">亏损股票数</div>
                    <div class="text-xl font-bold text-blue-600 dark:text-blue-400">{{ selectedHistoryRecord.result.summary.lossStocks }}</div>
                  </div>
                </div>
              </div>

              <!-- 回测配置 -->
              <div class="card p-4">
                <h3 class="text-md font-semibold mb-4">回测配置</h3>
                <div class="grid grid-cols-2 sm:grid-cols-3 gap-4 text-sm">
                  <div>
                    <span class="text-muted-foreground">回测日：</span>
                    <span>{{ selectedHistoryRecord.config.backtest_date }}</span>
                  </div>
                  <div>
                    <span class="text-muted-foreground">统计日：</span>
                    <span>{{ selectedHistoryRecord.config.stat_date }}</span>
                  </div>
                  <div>
                    <span class="text-muted-foreground">买入策略：</span>
                    <span>
                      {{ 
                        selectedHistoryRecord.config.buy_strategy === 'fixed_amount' 
                          ? '固定金额' 
                          : selectedHistoryRecord.config.buy_strategy === 'equal_distribution' 
                            ? '平均分配（累计余额）' 
                            : selectedHistoryRecord.config.buy_strategy === 'equal_distribution_fixed'
                              ? '平均分配（固定金额）'
                              : selectedHistoryRecord.config.buy_strategy 
                      }}
                    </span>
                    <span v-if="(selectedHistoryRecord.config.buy_strategy === 'equal_distribution' || selectedHistoryRecord.config.buy_strategy === 'equal_distribution_fixed') && selectedHistoryRecord.config.initial_capital" class="ml-2 text-muted-foreground">
                      (初始资金: ¥{{ formatNumber(selectedHistoryRecord.config.initial_capital) }})
                    </span>
                  </div>
                  <div v-if="selectedHistoryRecord.config.use_stop_loss">
                    <span class="text-muted-foreground">止损：</span>
                    <span>{{ selectedHistoryRecord.config.stop_loss_percent }}%</span>
                  </div>
                  <div v-if="selectedHistoryRecord.config.use_take_profit">
                    <span class="text-muted-foreground">止盈：</span>
                    <span>{{ selectedHistoryRecord.config.take_profit_percent }}%</span>
                  </div>
                </div>
              </div>

              <!-- 操作按钮 -->
              <div class="flex justify-end space-x-2">
                <button
                  @click="loadHistoryRecordToCurrent(selectedHistoryRecord)"
                  class="px-4 py-2 rounded-md bg-primary text-primary-foreground hover:bg-primary/80 transition-colors text-sm"
                >
                  <i class="fas fa-upload mr-2"></i>
                  加载到当前回测
                </button>
                <button
                  @click="selectedHistoryRecord = null"
                  class="px-4 py-2 rounded-md bg-muted text-muted-foreground hover:bg-muted/80 transition-colors text-sm"
                >
                  关闭
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </transition>

    <!-- 回测折线图对话框 -->
    <transition name="fade">
      <div v-if="showChartDialog" class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" @click.self="showChartDialog = false">
        <div class="bg-card border border-border rounded-lg shadow-lg max-w-6xl w-full max-h-[90vh] overflow-hidden flex flex-col">
          <!-- 图表对话框头部 -->
          <div class="p-4 sm:p-6 border-b border-border flex justify-between items-center">
            <h2 class="text-lg font-semibold flex items-center">
              <i class="fas fa-chart-line mr-2 text-primary"></i>
              回测数据折线图
            </h2>
            <div class="flex items-center space-x-4">
              <!-- 图表类型切换 -->
              <div v-if="chartData && chartData.dates && chartData.dates.length > 0" class="flex items-center space-x-2 bg-muted/30 rounded-md p-1">
                <button
                  @click="chartType = 'rate'"
                  :class="[
                    'px-3 py-1.5 rounded text-sm font-medium transition-colors',
                    chartType === 'rate' 
                      ? 'bg-primary text-primary-foreground' 
                      : 'text-muted-foreground hover:text-foreground'
                  ]"
                >
                  <i class="fas fa-percentage mr-1"></i>
                  收益率
                </button>
                <button
                  @click="chartType = 'profit'"
                  :class="[
                    'px-3 py-1.5 rounded text-sm font-medium transition-colors',
                    chartType === 'profit' 
                      ? 'bg-primary text-primary-foreground' 
                      : 'text-muted-foreground hover:text-foreground'
                  ]"
                >
                  <i class="fas fa-yen-sign mr-1"></i>
                  收益金额
                </button>
              </div>
              <button
                @click="showChartDialog = false"
                class="text-muted-foreground hover:text-foreground transition-colors"
              >
                <i class="fas fa-times text-xl"></i>
              </button>
            </div>
          </div>

          <!-- 图表内容 -->
          <div class="flex-1 overflow-y-auto p-4 sm:p-6">
            <div v-if="chartLoading" class="text-center py-8">
              <i class="fas fa-spinner fa-spin text-2xl mb-4 text-primary"></i>
              <p class="text-muted-foreground">正在生成图表...</p>
            </div>
            <div v-else-if="chartError" class="text-center py-8">
              <i class="fas fa-exclamation-circle text-2xl mb-4 text-destructive"></i>
              <p class="text-destructive">{{ chartError }}</p>
            </div>
            <div v-else-if="chartData && chartData.dates && chartData.dates.length > 0" class="space-y-4">
              <!-- 图表说明 -->
              <div class="bg-muted/30 p-3 rounded-md text-sm text-muted-foreground">
                <p><i class="fas fa-info-circle mr-2"></i>相同止损止盈条件的回测数据已自动合并，按时间顺序展示。大盘数据（上证指数）用于对比参考。</p>
              </div>
              <!-- 数据窗口信息 -->
              <div v-if="chartData.dates && chartData.dates.length > maxChartItemsPerPage" class="flex items-center justify-between text-sm text-muted-foreground bg-muted/20 p-2 rounded-md">
                <span>
                  显示第 {{ chartWindowStart + 1 }} - {{ Math.min(chartWindowStart + maxChartItemsPerPage, chartData.dates.length) }} 条，共 {{ chartData.dates.length }} 条数据
                </span>
              </div>
              <!-- 图表容器 -->
              <div ref="chartRef" class="w-full h-[500px] min-h-[500px]"></div>
              <!-- 数据窗口导航 -->
              <div v-if="chartData && chartData.dates && chartData.dates.length > 0" class="flex items-center justify-center space-x-2 pt-2">
                <button
                  @click="goToPreviousPage"
                  :disabled="getCurrentPage() === 1"
                  :class="[
                    'px-2 py-1 rounded text-xs',
                    getCurrentPage() === 1
                      ? 'text-muted-foreground cursor-not-allowed opacity-50'
                      : 'text-foreground hover:bg-muted/50'
                  ]"
                  title="上一页"
                >
                  <i class="fas fa-chevron-left"></i>
                </button>
                <span class="text-xs text-muted-foreground px-2">
                  {{ getCurrentPage() }} / {{ getTotalPages() }}
                </span>
                <button
                  @click="goToNextPage"
                  :disabled="getCurrentPage() >= getTotalPages()"
                  :class="[
                    'px-2 py-1 rounded text-xs',
                    getCurrentPage() >= getTotalPages()
                      ? 'text-muted-foreground cursor-not-allowed opacity-50'
                      : 'text-foreground hover:bg-muted/50'
                  ]"
                  title="下一页"
                >
                  <i class="fas fa-chevron-right"></i>
                </button>
              </div>
            </div>
            <div v-else class="text-center py-8 text-muted-foreground">
              <i class="fas fa-chart-line text-4xl mb-4"></i>
              <p>暂无数据可显示</p>
            </div>
          </div>

          <!-- 图表对话框底部 -->
          <div class="p-4 sm:p-6 border-t border-border flex justify-end">
            <button
              @click="showChartDialog = false"
              class="px-4 py-2 rounded-md bg-primary text-primary-foreground hover:bg-primary/80 transition-colors text-sm"
            >
              关闭
            </button>
          </div>
        </div>
      </div>
    </transition>

    <!-- 数据统计对话框 -->
    <BacktestStatistics
      v-if="showStatisticsDialog"
      :history-records="backtestHistory"
      @close="showStatisticsDialog = false"
    />

    <!-- 批量回测对话框 -->
    <transition name="fade">
      <div v-if="showBatchBacktestDialog" class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" @click.self="showBatchBacktestDialog = false">
        <div class="bg-card border border-border rounded-lg shadow-lg max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
          <!-- 对话框头部 -->
          <div class="p-4 sm:p-6 border-b border-border flex justify-between items-center">
            <h2 class="text-lg font-semibold flex items-center">
              <i class="fas fa-layer-group mr-2 text-primary"></i>
              批量回测
            </h2>
            <button
              @click="showBatchBacktestDialog = false"
              class="text-muted-foreground hover:text-foreground transition-colors"
            >
              <i class="fas fa-times text-xl"></i>
            </button>
          </div>

          <!-- 对话框内容 -->
          <div class="flex-1 overflow-y-auto p-4 sm:p-6">
            <div class="space-y-6">
              <!-- 回测参数 -->
              <div class="space-y-4">
                <h3 class="text-md font-semibold">回测参数</h3>
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label class="block text-sm font-medium mb-2">
                      <i class="fas fa-calendar-alt mr-1 text-primary"></i>
                      回测日（截止日）
                    </label>
                    <input
                      v-model="batchBacktestConfig.backtestDate"
                      type="date"
                      class="input w-full"
                      :max="maxDate"
                    />
                  </div>
                  <div>
                    <label class="block text-sm font-medium mb-2">
                      <i class="fas fa-calendar-check mr-1 text-primary"></i>
                      统计日
                    </label>
                    <input
                      v-model="batchBacktestConfig.statDate"
                      type="date"
                      class="input w-full"
                      :max="maxDate"
                    />
                  </div>
                </div>
              </div>

              <!-- 止盈止损组合列表 -->
              <div class="space-y-4">
                <div class="flex justify-between items-center">
                  <h3 class="text-md font-semibold">止盈止损组合</h3>
                  <button
                    @click="addProfitLossCombination"
                    class="px-3 py-1.5 rounded-md bg-primary text-primary-foreground hover:bg-primary/80 transition-colors text-sm"
                  >
                    <i class="fas fa-plus mr-1"></i>
                    添加组合
                  </button>
                </div>
                
                <div v-if="batchBacktestConfig.profitLossCombinations.length === 0" class="text-center py-8 text-muted-foreground">
                  <i class="fas fa-inbox text-4xl mb-4"></i>
                  <p>请至少添加一个止盈止损组合</p>
                </div>
                
                <div v-else class="space-y-3">
                  <div
                    v-for="(combination, index) in batchBacktestConfig.profitLossCombinations"
                    :key="index"
                    class="card p-4 border border-border"
                  >
                    <div class="flex justify-between items-start mb-3">
                      <h4 class="font-medium">组合 #{{ index + 1 }}</h4>
                      <button
                        @click="removeProfitLossCombination(index)"
                        class="text-destructive hover:text-destructive/80 transition-colors"
                      >
                        <i class="fas fa-trash"></i>
                      </button>
                    </div>
                    
                    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <!-- 止损设置 -->
                      <div class="space-y-2">
                        <div class="flex items-center space-x-2">
                          <input
                            type="checkbox"
                            :id="`stopLoss-${index}`"
                            v-model="combination.useStopLoss"
                            class="checkbox"
                          />
                          <label :for="`stopLoss-${index}`" class="text-sm">
                            止损
                          </label>
                        </div>
                        <div v-if="combination.useStopLoss" class="ml-6 flex items-center space-x-2">
                          <label :for="`stopLossPercent-${index}`" class="text-sm text-muted-foreground whitespace-nowrap">百分比：</label>
                          <input
                            :id="`stopLossPercent-${index}`"
                            v-model.number="combination.stopLossPercent"
                            type="number"
                            step="0.1"
                            min="-100"
                            max="0"
                            class="input w-24"
                            placeholder="-3"
                          />
                          <span class="text-sm text-muted-foreground">%</span>
                        </div>
                      </div>
                      
                      <!-- 止盈设置 -->
                      <div class="space-y-2">
                        <div class="flex items-center space-x-2">
                          <input
                            type="checkbox"
                            :id="`takeProfit-${index}`"
                            v-model="combination.useTakeProfit"
                            class="checkbox"
                          />
                          <label :for="`takeProfit-${index}`" class="text-sm">
                            止盈
                          </label>
                        </div>
                        <div v-if="combination.useTakeProfit" class="ml-6 flex items-center space-x-2">
                          <label :for="`takeProfitPercent-${index}`" class="text-sm text-muted-foreground whitespace-nowrap">百分比：</label>
                          <input
                            :id="`takeProfitPercent-${index}`"
                            v-model.number="combination.takeProfitPercent"
                            type="number"
                            step="0.1"
                            min="0"
                            max="1000"
                            class="input w-24"
                            placeholder="10"
                          />
                          <span class="text-sm text-muted-foreground">%</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- 提示信息 -->
              <div class="bg-blue-500/10 border border-blue-500/20 p-4 rounded-md">
                <div class="flex items-start">
                  <i class="fas fa-info-circle text-blue-500 mr-2 mt-0.5"></i>
                  <div class="flex-1 text-sm text-blue-700 dark:text-blue-400">
                    <p><strong>提示：</strong></p>
                    <ul class="list-disc list-inside mt-2 space-y-1">
                      <li>批量回测将依次执行每个止盈止损组合的回测</li>
                      <li>如果某个组合的回测数据已存在，将自动跳过</li>
                      <li>回测完成后会自动保存到历史记录</li>
                    </ul>
                  </div>
                </div>
              </div>

              <!-- 批量回测结果 -->
              <div v-if="batchBacktestResult" class="space-y-3">
                <h3 class="text-md font-semibold">批量回测结果</h3>
                <div class="grid grid-cols-2 sm:grid-cols-4 gap-4">
                  <div class="p-3 bg-muted/30 rounded-md text-center">
                    <div class="text-sm text-muted-foreground mb-1">总计</div>
                    <div class="text-xl font-bold">{{ batchBacktestResult.total }}</div>
                  </div>
                  <div class="p-3 bg-green-500/10 rounded-md text-center">
                    <div class="text-sm text-muted-foreground mb-1">已完成</div>
                    <div class="text-xl font-bold text-green-600 dark:text-green-400">{{ batchBacktestResult.completed }}</div>
                  </div>
                  <div class="p-3 bg-yellow-500/10 rounded-md text-center">
                    <div class="text-sm text-muted-foreground mb-1">已跳过</div>
                    <div class="text-xl font-bold text-yellow-600 dark:text-yellow-400">{{ batchBacktestResult.skipped }}</div>
                  </div>
                  <div class="p-3 bg-red-500/10 rounded-md text-center">
                    <div class="text-sm text-muted-foreground mb-1">失败</div>
                    <div class="text-xl font-bold text-red-600 dark:text-red-400">{{ batchBacktestResult.failed }}</div>
                  </div>
                </div>
                
                <!-- 详细结果列表 -->
                <div class="max-h-60 overflow-y-auto space-y-2 mt-4">
                  <div
                    v-for="(result, index) in batchBacktestResult.results"
                    :key="index"
                    class="p-3 rounded-md text-sm"
                    :class="{
                      'bg-green-500/10': result.status === 'completed',
                      'bg-yellow-500/10': result.status === 'skipped',
                      'bg-red-500/10': result.status === 'failed'
                    }"
                  >
                    <div class="flex justify-between items-center">
                      <span class="font-medium">组合 #{{ result.index }}</span>
                      <span
                        class="px-2 py-0.5 rounded-full text-xs"
                        :class="{
                          'bg-green-500/20 text-green-700 dark:text-green-400': result.status === 'completed',
                          'bg-yellow-500/20 text-yellow-700 dark:text-yellow-400': result.status === 'skipped',
                          'bg-red-500/20 text-red-700 dark:text-red-400': result.status === 'failed'
                        }"
                      >
                        {{ result.status === 'completed' ? '已完成' : result.status === 'skipped' ? '已跳过' : '失败' }}
                      </span>
                    </div>
                    <p class="text-muted-foreground mt-1">{{ result.message }}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 对话框底部 -->
          <div class="p-4 sm:p-6 border-t border-border flex justify-between items-center">
            <button
              @click="showBatchBacktestDialog = false"
              class="px-4 py-2 rounded-md bg-muted text-muted-foreground hover:bg-muted/80 transition-colors text-sm"
            >
              关闭
            </button>
            <div class="flex space-x-2">
              <button
                @click="runBatchBacktest"
                :disabled="batchBacktestLoading || !canRunBatchBacktest"
                class="px-4 py-2 rounded-md bg-primary text-primary-foreground hover:bg-primary/80 transition-colors text-sm disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <i class="fas fa-play mr-2" v-if="!batchBacktestLoading"></i>
                <i class="fas fa-spinner fa-spin mr-2" v-if="batchBacktestLoading"></i>
                {{ batchBacktestLoading ? '批量回测中...' : '开始批量回测' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </transition>

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
import { ref, computed, onMounted, onBeforeUnmount, onActivated, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import * as echarts from 'echarts/core'
import { LineChart } from 'echarts/charts'
import { TitleComponent, TooltipComponent, LegendComponent, GridComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import ThemeToggle from './ThemeToggle.vue'
import ConfirmDialog from './ConfirmDialog.vue'
import BacktestStatistics from './BacktestStatistics.vue'
import BuySellStrategy from './BuySellStrategy.vue'

// 注册 ECharts 组件
echarts.use([
  LineChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  CanvasRenderer
])

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const error = ref(null)
const backtestResult = ref(null)
const progress = ref(0)
const progressMessage = ref('')

// 回测配置
const backtestConfig = ref({
  backtestDate: '', // 回测日，默认一周前
  statDate: '', // 统计日，默认今天
  buyStrategy: 'fixed_amount', // 买入策略
  initialCapital: 100000, // 初始资金（用于平均分配策略）
  useStopLoss: true, // 使用止损
  useTakeProfit: true, // 使用止盈
  stopLossPercent: -2, // 止损百分比
  takeProfitPercent: 18 // 止盈百分比
})

// 选中的股票列表（从扫描工具页面获取）
const selectedStocks = ref([])
// 用于回测的选中股票代码集合（默认全选）
const selectedStockCodes = ref(new Set())
// 扫描配置（从扫描工具页面获取，用于设置默认回测日）
const scanConfig = ref(null)

// 回测历史相关
const showHistoryDialog = ref(false)
const backtestHistory = ref([])
const backtestHistoryLoading = ref(false)
const selectedBacktestYear = ref('')
const selectedBacktestQuarter = ref('')
const selectedBacktestMonth = ref('')

// 批量回测相关
const showBatchBacktestDialog = ref(false)
const batchBacktestLoading = ref(false)
const batchBacktestConfig = ref({
  backtestDate: '',
  statDate: '',
  profitLossCombinations: []
})
const batchBacktestResult = ref(null)

// 确认对话框相关
const confirmDialog = ref({
  show: false,
  title: '确认操作',
  message: '',
  type: 'default',
  onConfirm: null,
  pendingAction: null
})
const selectedHistoryRecord = ref(null)
const backtestHistoryGroupedByDate = ref({})

// 筛选理由展开状态
const expandedReasons = ref({})

// 图表相关
const showChartDialog = ref(false)
const chartLoading = ref(false)
const chartError = ref(null)
const chartRef = ref(null)
const chartData = ref([])
const chartType = ref('rate') // 'rate' 收益率 或 'profit' 收益金额
const chartWindowStart = ref(0) // 当前窗口起始索引
const maxChartItemsPerPage = 12 // 每页最多显示的数据条数
let chartInstance = null
let chartResizeHandler = null

// 数据统计相关
const showStatisticsDialog = ref(false)
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

// 计算最大日期（今天）
const maxDate = computed(() => {
  const today = new Date()
  return today.toISOString().split('T')[0]
})

// 获取实际选中的股票列表（用于回测）
const stocksForBacktest = computed(() => {
  return selectedStocks.value.filter(stock => selectedStockCodes.value.has(stock.code))
})

// 是否全选
const isAllSelected = computed(() => {
  return selectedStocks.value.length > 0 && 
         selectedStockCodes.value.size === selectedStocks.value.length
})

// 检查是否可以运行回测
const canRunBacktest = computed(() => {
  return stocksForBacktest.value.length > 0 &&
         backtestConfig.value.backtestDate && 
         backtestConfig.value.statDate &&
         (backtestConfig.value.useStopLoss || backtestConfig.value.useTakeProfit)
})

// 检查是否可以运行批量回测
const canRunBatchBacktest = computed(() => {
  return selectedStocks.value.length > 0 &&
         batchBacktestConfig.value.backtestDate && 
         batchBacktestConfig.value.statDate &&
         batchBacktestConfig.value.profitLossCombinations.length > 0 &&
         batchBacktestConfig.value.profitLossCombinations.every(combo => 
           combo.useStopLoss || combo.useTakeProfit
         )
})

// 计算给定日期后的第一个周五
function getNextFriday(dateString) {
  const date = new Date(dateString)
  const dayOfWeek = date.getDay() // 0 = 周日, 1 = 周一, ..., 5 = 周五, 6 = 周六
  
  // 计算到下一个周五需要加的天数
  // 如果今天是周五(5)，则加7天（下一个周五）
  // 如果今天是周六(6)，则加6天
  // 如果今天是周日(0)，则加5天
  // 如果今天是周一(1)，则加4天
  // 如果今天是周二(2)，则加3天
  // 如果今天是周三(3)，则加2天
  // 如果今天是周四(4)，则加1天
  let daysToAdd
  if (dayOfWeek === 5) {
    // 如果是周五，使用下一个周五
    daysToAdd = 7
  } else if (dayOfWeek === 6) {
    // 如果是周六
    daysToAdd = 6
  } else if (dayOfWeek === 0) {
    // 如果是周日
    daysToAdd = 5
  } else {
    // 周一(1)到周四(4)：到本周五的天数
    daysToAdd = 5 - dayOfWeek
  }
  
  const nextFriday = new Date(date)
  nextFriday.setDate(date.getDate() + daysToAdd)
  return nextFriday.toISOString().split('T')[0]
}

// 初始化日期
function initDates() {
  const today = new Date()
  
  // 如果扫描配置中有扫描日期，使用扫描日期作为默认回测日
  if (scanConfig.value && scanConfig.value.scan_date) {
    backtestConfig.value.backtestDate = scanConfig.value.scan_date
  } else {
    // 否则使用一周前
    const oneWeekAgo = new Date(today)
    oneWeekAgo.setDate(today.getDate() - 7)
    backtestConfig.value.backtestDate = oneWeekAgo.toISOString().split('T')[0]
  }
  
  // 统计日默认设置为回测日的未来第一个周五
  backtestConfig.value.statDate = getNextFriday(backtestConfig.value.backtestDate)
  
  // 初始化批量回测配置
  batchBacktestConfig.value.backtestDate = backtestConfig.value.backtestDate
  batchBacktestConfig.value.statDate = backtestConfig.value.statDate
}

// 切换单只股票的选择状态
function toggleStock(code) {
  if (selectedStockCodes.value.has(code)) {
    selectedStockCodes.value.delete(code)
  } else {
    selectedStockCodes.value.add(code)
  }
}

// 全选/反选所有股票
function toggleSelectAll() {
  if (isAllSelected.value) {
    // 反选：清空所有选择
    selectedStockCodes.value.clear()
  } else {
    // 全选：选择所有股票
    selectedStocks.value.forEach(stock => {
      selectedStockCodes.value.add(stock.code)
    })
  }
}

// 跳转到单股检查页面
function goToStockCheck(stock) {
  const query = {
    code: stock.code,
    from: 'backtest'
  }
  
  // 如果有回测日期，添加到查询参数中
  if (backtestConfig.value.backtestDate) {
    query.date = backtestConfig.value.backtestDate
  }
  
  router.push({
    path: '/platform/check',
    query: query
  })
}

// 从 sessionStorage 加载选中的股票和扫描配置
function loadSelectedStocksAndConfig() {
  try {
    console.log('开始加载选中的股票和扫描配置...')
    
    // 清除之前的回测结果，避免显示旧数据
    backtestResult.value = null
    
    // 从 sessionStorage 获取选中的股票
    const savedStocks = sessionStorage.getItem('selectedStocks')
    if (savedStocks) {
      try {
        selectedStocks.value = JSON.parse(savedStocks)
        console.log('✓ 从 sessionStorage 加载选中的股票成功:', selectedStocks.value.length, '只')
        
        // 默认全选所有股票
        selectedStockCodes.value.clear()
        selectedStocks.value.forEach(stock => {
          selectedStockCodes.value.add(stock.code)
        })
        console.log('✓ 默认全选所有股票:', selectedStockCodes.value.size, '只')
      } catch (e) {
        console.error('✗ 解析 sessionStorage 中的选中股票失败:', e)
      }
    } else {
      console.log('✗ sessionStorage 中没有找到 selectedStocks')
    }
    
    // 从 sessionStorage 获取扫描配置（用于设置默认回测日）
    const savedConfig = sessionStorage.getItem('scanConfig')
    if (savedConfig) {
      try {
        scanConfig.value = JSON.parse(savedConfig)
        console.log('✓ 从 sessionStorage 加载扫描配置成功:', scanConfig.value)
      } catch (e) {
        console.error('✗ 解析 sessionStorage 中的扫描配置失败:', e)
      }
    } else {
      console.log('✗ sessionStorage 中没有找到 scanConfig')
    }
    
    return selectedStocks.value.length > 0
  } catch (e) {
    console.error('✗ 加载数据时发生异常:', e)
    error.value = '加载数据失败: ' + e.message
    return false
  }
}

// 运行回测
async function runBacktest() {
  if (!canRunBacktest.value) {
    error.value = '请完善回测参数配置'
    return
  }

  // 检查是否有选中的股票
  if (stocksForBacktest.value.length === 0) {
    error.value = '请至少选择一只股票进行回测'
    return
  }

  loading.value = true
  error.value = null
  backtestResult.value = null
  progress.value = 0
  progressMessage.value = '正在初始化...'

  try {
    // 使用流式API获取进度更新
    const response = await fetch('/platform/api/backtest/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        backtest_date: backtestConfig.value.backtestDate,
        stat_date: backtestConfig.value.statDate,
        buy_strategy: backtestConfig.value.buyStrategy,
        initial_capital: backtestConfig.value.initialCapital,
        use_stop_loss: backtestConfig.value.useStopLoss,
        use_take_profit: backtestConfig.value.useTakeProfit,
        stop_loss_percent: backtestConfig.value.stopLossPercent,
        take_profit_percent: backtestConfig.value.takeProfitPercent,
        selected_stocks: stocksForBacktest.value
      })
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      
      if (done) {
        break
      }

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || '' // 保留最后一个不完整的行

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6))
            
            if (data.type === 'progress') {
              progress.value = data.progress
              progressMessage.value = data.message
            } else if (data.type === 'result') {
              backtestResult.value = data.data
              progress.value = 100
              progressMessage.value = '回测完成！'
            } else if (data.type === 'error') {
              throw new Error(data.message)
            }
          } catch (e) {
            console.error('解析进度数据失败:', e, line)
          }
        }
      }
    }
  } catch (e) {
    console.error('回测失败:', e)
    if (e.message) {
      error.value = e.message
    } else {
      error.value = '网络错误，请稍后重试'
    }
  } finally {
    loading.value = false
    // 延迟清除进度信息，让用户看到完成状态
    setTimeout(() => {
      if (progress.value === 100) {
        progress.value = 0
        progressMessage.value = ''
      }
    }, 2000)
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

// 获取卖出原因样式
function getSellReasonClass(reason) {
  if (reason === '止损') {
    return 'bg-blue-500/20 text-blue-700 dark:text-blue-400'
  } else if (reason === '止盈') {
    return 'bg-red-500/20 text-red-700 dark:text-red-400'
  } else if (reason === '统计日卖出') {
    return 'bg-gray-500/20 text-gray-700 dark:text-gray-400'
  }
  return 'bg-gray-500/20 text-gray-700 dark:text-gray-400'
}

// 切换筛选理由展开/折叠
function toggleReasonExpand(code) {
  expandedReasons.value[code] = !expandedReasons.value[code]
}

// 加载回测历史记录列表
async function loadBacktestHistory() {
  backtestHistoryLoading.value = true
  try {
    const response = await axios.get('/platform/api/backtest/history')
    if (response.data.success) {
      backtestHistory.value = response.data.data || []
      // 清除回测记录缓存（因为历史记录已更新）
      clearBacktestRecordsCache()
      // 按扫描日期分组
      groupBacktestHistoryByDate()
    } else {
      error.value = '加载回测历史失败'
    }
  } catch (e) {
    console.error('加载回测历史失败:', e)
    error.value = '加载回测历史失败: ' + (e.response?.data?.detail || e.message)
    backtestHistory.value = []
  } finally {
    backtestHistoryLoading.value = false
  }
}

// 按扫描日期分组回测历史
function groupBacktestHistoryByDate() {
  const grouped = {}
  backtestHistory.value.forEach(record => {
    // 使用回测日作为扫描日期（因为回测日通常是扫描日期）
    const scanDate = record.backtestDate || '未知日期'
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
  backtestHistoryGroupedByDate.value = sortedGrouped
}

// 获取可用的年度列表
const availableBacktestYears = computed(() => {
  const years = new Set()
  backtestHistory.value.forEach(record => {
    const scanDate = record.backtestDate || ''
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
const availableBacktestQuarters = computed(() => {
  if (!selectedBacktestYear.value) {
    return []
  }
  const quarters = new Set()
  backtestHistory.value.forEach(record => {
    const scanDate = record.backtestDate || ''
    if (scanDate && scanDate !== '未知日期' && scanDate.startsWith(selectedBacktestYear.value)) {
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
const availableBacktestMonths = computed(() => {
  if (!selectedBacktestYear.value) {
    return []
  }
  const months = new Set()
  let targetMonths = []
  
  // 如果选择了季度，只显示该季度的月份
  if (selectedBacktestQuarter.value) {
    const quarterNum = parseInt(selectedBacktestQuarter.value.substring(1))
    if (quarterNum === 1) targetMonths = [1, 2, 3]
    else if (quarterNum === 2) targetMonths = [4, 5, 6]
    else if (quarterNum === 3) targetMonths = [7, 8, 9]
    else if (quarterNum === 4) targetMonths = [10, 11, 12]
  } else {
    // 如果没有选择季度，显示该年度所有月份
    targetMonths = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
  }
  
  backtestHistory.value.forEach(record => {
    const scanDate = record.backtestDate || ''
    if (scanDate && scanDate !== '未知日期' && scanDate.startsWith(selectedBacktestYear.value)) {
      const month = parseInt(scanDate.substring(5, 7))
      if (month >= 1 && month <= 12 && targetMonths.includes(month)) {
        months.add(month)
      }
    }
  })
  return Array.from(months).sort((a, b) => a - b)
})

// 按年度、季度、月度筛选后的分组历史记录
const filteredBacktestHistoryGroupedByDate = computed(() => {
  const filtered = {}
  Object.keys(backtestHistoryGroupedByDate.value).forEach(date => {
    if (date === '未知日期') {
      return
    }
    
    // 年度筛选
    if (selectedBacktestYear.value && !date.startsWith(selectedBacktestYear.value)) {
      return
    }
    
    // 季度筛选
    if (selectedBacktestQuarter.value) {
      const month = parseInt(date.substring(5, 7))
      if (month >= 1 && month <= 12) {
        const quarter = Math.ceil(month / 3)
        const selectedQuarter = parseInt(selectedBacktestQuarter.value.substring(1))
        if (quarter !== selectedQuarter) {
          return
        }
      }
    }
    
    // 月度筛选
    if (selectedBacktestMonth.value) {
      const month = parseInt(date.substring(5, 7))
      if (month !== parseInt(selectedBacktestMonth.value)) {
        return
      }
    }
    
    filtered[date] = backtestHistoryGroupedByDate.value[date]
  })
  return filtered
})

// 按年度、季度、月度筛选后的历史记录列表（用于生成折线图）
const filteredBacktestHistory = computed(() => {
  return backtestHistory.value.filter(record => {
    const scanDate = record.backtestDate || ''
    if (!scanDate || scanDate === '未知日期') {
      return false
    }
    
    // 年度筛选
    if (selectedBacktestYear.value && !scanDate.startsWith(selectedBacktestYear.value)) {
      return false
    }
    
    // 季度筛选
    if (selectedBacktestQuarter.value) {
      const month = parseInt(scanDate.substring(5, 7))
      if (month >= 1 && month <= 12) {
        const quarter = Math.ceil(month / 3)
        const selectedQuarter = parseInt(selectedBacktestQuarter.value.substring(1))
        if (quarter !== selectedQuarter) {
          return false
        }
      } else {
        return false
      }
    }
    
    // 月度筛选
    if (selectedBacktestMonth.value) {
      const month = parseInt(scanDate.substring(5, 7))
      if (month !== parseInt(selectedBacktestMonth.value)) {
        return false
      }
    }
    
    return true
  })
})

// 查看历史记录详情
async function viewHistoryRecord(record) {
  try {
    const response = await axios.get(`/platform/api/backtest/history/${record.id}`)
    if (response.data.success) {
      selectedHistoryRecord.value = response.data.data
    } else {
      error.value = '加载回测历史详情失败'
    }
  } catch (e) {
    console.error('加载回测历史详情失败:', e)
    error.value = '加载回测历史详情失败: ' + (e.response?.data?.detail || e.message)
  }
}

// 删除历史记录
function showDeleteHistoryConfirm(historyId) {
  confirmDialog.value = {
    show: true,
    title: '确认删除',
    message: '确定要删除这条回测历史记录吗？此操作不可恢复。',
    type: 'danger',
    onConfirm: () => executeDeleteHistory(historyId),
    pendingAction: historyId
  }
}

async function executeDeleteHistory(historyId) {
  try {
    const response = await axios.delete(`/platform/api/backtest/history/${historyId}`)
    if (response.data.success) {
      // 从列表中移除
      backtestHistory.value = backtestHistory.value.filter(r => r.id !== historyId)
      // 重新分组
      groupBacktestHistoryByDate()
      // 如果正在查看这条记录，关闭详情对话框
      if (selectedHistoryRecord.value && selectedHistoryRecord.value.id === historyId) {
        selectedHistoryRecord.value = null
      }
    } else {
      error.value = '删除回测历史记录失败'
    }
  } catch (e) {
    console.error('删除回测历史记录失败:', e)
    error.value = '删除回测历史记录失败: ' + (e.response?.data?.detail || e.message)
  }
}

// 清空所有回测历史
function showClearBacktestHistoryConfirm() {
  confirmDialog.value = {
    show: true,
    title: '确认清空',
    message: '确定要清空所有回测历史记录吗？此操作不可恢复。',
    type: 'danger',
    onConfirm: executeClearBacktestHistory,
    pendingAction: null
  }
}

async function executeClearBacktestHistory() {
  try {
    const response = await axios.delete('/platform/api/backtest/history')
    if (response.data.success) {
      backtestHistory.value = []
      backtestHistoryGroupedByDate.value = {}
      selectedHistoryRecord.value = null
    } else {
      error.value = '清空回测历史记录失败'
    }
  } catch (e) {
    console.error('清空回测历史记录失败:', e)
    error.value = '清空回测历史记录失败: ' + (e.response?.data?.detail || e.message)
  }
}

// 删除指定日期的所有回测记录
function showDeleteDateConfirm(backtestDate) {
  const records = backtestHistoryGroupedByDate.value[backtestDate] || []
  confirmDialog.value = {
    show: true,
    title: '确认删除',
    message: `确定要删除扫描日期 "${backtestDate}" 的所有回测记录吗？共 ${records.length} 条记录，此操作不可恢复。`,
    type: 'danger',
    onConfirm: () => executeDeleteBacktestHistoryByDate(backtestDate),
    pendingAction: backtestDate
  }
}

async function executeDeleteBacktestHistoryByDate(backtestDate) {
  try {
    const response = await axios.delete(`/platform/api/backtest/history/date/${backtestDate}`)
    if (response.data.success) {
      // 从列表中移除该日期的所有记录
      backtestHistory.value = backtestHistory.value.filter(r => r.backtestDate !== backtestDate)
      // 重新分组
      groupBacktestHistoryByDate()
      // 如果正在查看该日期的记录，关闭详情对话框
      if (selectedHistoryRecord.value && selectedHistoryRecord.value.config.backtest_date === backtestDate) {
        selectedHistoryRecord.value = null
      }
    } else {
      error.value = '删除回测历史记录失败'
    }
  } catch (e) {
    console.error('删除回测历史记录失败:', e)
    error.value = '删除回测历史记录失败: ' + (e.response?.data?.detail || e.message)
  }
}

// 加载历史记录到当前回测
async function loadHistoryRecordToCurrent(record) {
  if (record && record.config) {
    // 加载回测配置
    backtestConfig.value.backtestDate = record.config.backtest_date
    backtestConfig.value.statDate = record.config.stat_date
    backtestConfig.value.buyStrategy = record.config.buy_strategy || 'fixed_amount'
    backtestConfig.value.initialCapital = record.config.initial_capital || 100000
    backtestConfig.value.useStopLoss = record.config.use_stop_loss || false
    backtestConfig.value.useTakeProfit = record.config.use_take_profit || false
    backtestConfig.value.stopLossPercent = record.config.stop_loss_percent || -3
    backtestConfig.value.takeProfitPercent = record.config.take_profit_percent || 10
    
    // 加载选中的股票
    // 优先从 config.selected_stocks 加载（新格式）
    if (record.config.selected_stocks && Array.isArray(record.config.selected_stocks)) {
      selectedStocks.value = record.config.selected_stocks
      console.log('✓ 从历史记录配置中加载选中的股票成功:', selectedStocks.value.length, '只')
    } 
    // 否则从回测结果中提取（向后兼容旧格式）
    else if (record.result && record.result.buyRecords) {
      selectedStocks.value = record.result.buyRecords.map(record => ({
        code: record.code,
        name: record.name,
        selection_reasons: record.selection_reasons || {}
      }))
      console.log('✓ 从历史记录结果中提取选中的股票成功:', selectedStocks.value.length, '只')
    } else {
      console.warn('历史记录中没有股票信息')
      error.value = '历史记录中没有股票信息，无法加载'
      return
    }
    
    // 默认全选所有股票
    selectedStockCodes.value.clear()
    selectedStocks.value.forEach(stock => {
      selectedStockCodes.value.add(stock.code)
    })
    console.log('✓ 默认全选所有股票:', selectedStockCodes.value.size, '只')
    
    // 加载扫描配置（用于设置默认回测日，向后兼容）
    // 优先级：1. 历史记录中的 scan_config  2. 从扫描历史记录查找  3. sessionStorage
    let scanConfigLoaded = false
    
    // 优先使用历史记录中的 scan_config
    if (record.config.scan_config) {
      scanConfig.value = record.config.scan_config
      scanConfigLoaded = true
      console.log('✓ 从历史记录中加载扫描配置成功')
    } 
    // 如果没有 scan_config，尝试从扫描历史记录中查找对应的扫描配置
    else if (record.config.backtest_date) {
      try {
        // 加载扫描历史记录
        const scanHistory = await loadScanHistoryForStatistics()
        let matchingScanRecord = scanHistory.find(sh => sh.scanDate === record.config.backtest_date)
        
        // 如果列表中没有完整数据，尝试获取详情
        if (matchingScanRecord && (!matchingScanRecord.scannedStocks || matchingScanRecord.scannedStocks.length === 0)) {
          const detail = await getScanHistoryDetail(matchingScanRecord.id)
          if (detail) {
            matchingScanRecord = detail
          }
        }
        
        if (matchingScanRecord && matchingScanRecord.scanConfig) {
          scanConfig.value = matchingScanRecord.scanConfig
          scanConfigLoaded = true
          console.log('✓ 从扫描历史记录中查找并加载扫描配置成功')
        } else {
          console.warn('⚠ 在扫描历史记录中未找到匹配的扫描配置，backtest_date:', record.config.backtest_date)
        }
      } catch (e) {
        console.warn('从扫描历史记录查找扫描配置失败:', e)
      }
    }
    
    // 如果还是没有找到，尝试从 sessionStorage 获取（向后兼容）
    if (!scanConfigLoaded) {
      try {
        const savedScanConfig = sessionStorage.getItem('scanConfig')
        if (savedScanConfig) {
          scanConfig.value = JSON.parse(savedScanConfig)
          scanConfigLoaded = true
          console.log('✓ 从 sessionStorage 加载扫描配置成功')
        }
      } catch (e) {
        console.warn('从 sessionStorage 加载扫描配置失败:', e)
      }
    }
    
    // 保存股票和扫描配置到 sessionStorage
    try {
      sessionStorage.setItem('selectedStocks', JSON.stringify(selectedStocks.value))
      if (scanConfigLoaded && scanConfig.value) {
        sessionStorage.setItem('scanConfig', JSON.stringify(scanConfig.value))
        console.log('✓ 股票和扫描配置已保存到 sessionStorage')
        // 如果加载了扫描配置，重新初始化日期（使用扫描配置中的扫描日期）
        initDates()
      } else {
        console.log('✓ 股票已保存到 sessionStorage（扫描配置未找到）')
      }
    } catch (e) {
      console.error('保存数据到 sessionStorage 失败:', e)
    }
    
    // 加载并显示回测结果数据
    if (record.result) {
      backtestResult.value = record.result
      // 验证summary数据
      if (record.result.summary) {
        console.log('✓ 回测结果数据已加载，summary:', {
          totalStocks: record.result.summary.totalStocks,
          totalInvestment: record.result.summary.totalInvestment,
          totalProfit: record.result.summary.totalProfit,
          totalReturnRate: record.result.summary.totalReturnRate
        })
      } else {
        console.warn('⚠ 回测结果中没有summary数据')
        // 如果没有summary数据，清除回测结果
        backtestResult.value = null
      }
    } else {
      console.warn('历史记录中没有回测结果数据')
      // 如果没有回测结果，确保清除旧数据
      backtestResult.value = null
    }
    
    selectedHistoryRecord.value = null
    showHistoryDialog.value = false
    
    // 滚动到配置区域
    setTimeout(() => {
      const configCard = document.querySelector('.card')
      if (configCard) {
        configCard.scrollIntoView({ behavior: 'smooth', block: 'start' })
      }
    }, 100)
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

// 生成回测折线图
async function generateBacktestChart() {
  // 使用筛选后的历史记录
  const historyToUse = filteredBacktestHistory.value
  
  if (historyToUse.length === 0) {
    error.value = '没有回测历史记录'
    return
  }

  showChartDialog.value = true
  chartLoading.value = true
  chartError.value = null
  chartData.value = []

  try {
    // 需要获取完整的回测历史记录详情（包含大盘收益率）
    const fullRecords = []
    for (const record of historyToUse) {
      try {
        const response = await axios.get(`/platform/api/backtest/history/${record.id}`)
        if (response.data.success) {
          fullRecords.push(response.data.data)
        }
      } catch (e) {
        console.warn(`获取回测记录 ${record.id} 详情失败:`, e)
      }
    }

    if (fullRecords.length === 0) {
      chartError.value = '无法获取回测历史记录详情'
      chartLoading.value = false
      return
    }

    // 按照止损止盈条件分组
    const groupedByCondition = {}
    fullRecords.forEach(record => {
      const conditionKey = getConditionKey(record.config)
      if (!groupedByCondition[conditionKey]) {
        groupedByCondition[conditionKey] = []
      }
      groupedByCondition[conditionKey].push(record)
    })

    // 处理每个分组的数据
    const seriesDataRate = [] // 收益率数据
    const seriesDataProfit = [] // 收益金额数据
    const marketDataRate = [] // 大盘收益率数据
    const marketDataProfit = [] // 大盘收益金额数据（需要计算）
    const dates = new Set()

    // 处理回测数据
    Object.entries(groupedByCondition).forEach(([conditionKey, records]) => {
      // 按回测日排序
      records.sort((a, b) => {
        const dateA = a.config.backtest_date || ''
        const dateB = b.config.backtest_date || ''
        return dateA.localeCompare(dateB)
      })

      // 合并相同时间的数据（按回测日和统计日的时间）
      const mergedDataRate = []
      const mergedDataProfit = []
      records.forEach(record => {
        const backtestDate = record.config.backtest_date
        const statDate = record.config.stat_date
        const timeKey = `${backtestDate}_${statDate}`
        const summary = record.result?.summary || {}
        
        // 处理收益率数据
        const returnRate = summary.totalReturnRate
        if (returnRate !== null && returnRate !== undefined) {
          const existingIndex = mergedDataRate.findIndex(item => item.timeKey === timeKey)
          if (existingIndex < 0) {
            // 相同时间的数据，只取第一条
            mergedDataRate.push({
              timeKey,
              backtestDate,
              statDate,
              totalReturnRate: returnRate,
              count: 1
            })
            if (backtestDate) {
              dates.add(backtestDate)
            }
          }
        }

        // 处理收益金额数据
        const totalProfit = summary.totalProfit
        if (totalProfit !== null && totalProfit !== undefined) {
          const existingIndex = mergedDataProfit.findIndex(item => item.timeKey === timeKey)
          if (existingIndex < 0) {
            // 相同时间的数据，只取第一条
            mergedDataProfit.push({
              timeKey,
              backtestDate,
              statDate,
              totalProfit: totalProfit,
              count: 1
            })
          }
        }
      })

      // 添加到系列数据
      if (mergedDataRate.length > 0) {
        const conditionLabel = getConditionLabel(records[0].config)
        // 同时保存投入金额，用于计算累计收益率
        seriesDataRate.push({
          name: conditionLabel,
          data: mergedDataRate.map(item => {
            // 查找对应的投入金额
            const profitItem = mergedDataProfit.find(p => p.timeKey === item.timeKey)
            const investment = profitItem ? 
              (records.find(r => {
                const key = `${r.config.backtest_date}_${r.config.stat_date}`
                return key === item.timeKey
              })?.result?.summary?.totalInvestment || 0) : 0
            
            return {
              date: item.backtestDate,
              value: item.totalReturnRate,
              investment: investment
            }
          })
        })
      }

      if (mergedDataProfit.length > 0) {
        const conditionLabel = getConditionLabel(records[0].config)
        seriesDataProfit.push({
          name: conditionLabel,
          data: mergedDataProfit.map(item => ({
            date: item.backtestDate,
            value: item.totalProfit
          }))
        })
      }
    })

    // 处理大盘数据
    fullRecords.forEach(record => {
      const backtestDate = record.config.backtest_date
      const summary = record.result?.summary || {}
      const marketReturnRate = summary.marketReturnRate
      const totalInvestment = summary.totalInvestment || 0
      
      // 处理大盘收益率数据
      if (marketReturnRate !== null && marketReturnRate !== undefined) {
        const existingIndex = marketDataRate.findIndex(item => item.date === backtestDate)
        if (existingIndex < 0) {
          // 相同日期的数据，只取第一条
          dates.add(backtestDate)
          marketDataRate.push({
            date: backtestDate,
            value: marketReturnRate,
            investment: totalInvestment
          })

          // 计算大盘收益金额（基于投入金额和收益率）
          const marketProfit = (totalInvestment * marketReturnRate) / 100
          marketDataProfit.push({
            date: backtestDate,
            value: marketProfit
          })
        }
      }
    })

    // 按日期排序
    const sortedDates = Array.from(dates).sort()

    console.log('图表数据准备完成:', {
      datesCount: sortedDates.length,
      seriesRateCount: seriesDataRate.length,
      seriesProfitCount: seriesDataProfit.length,
      marketRateCount: marketDataRate.length,
      marketProfitCount: marketDataProfit.length,
      dates: sortedDates
    })

    // 检查是否有有效数据
    if (sortedDates.length === 0 && seriesDataRate.length === 0 && seriesDataProfit.length === 0) {
      chartError.value = '没有有效的回测数据可显示'
      chartLoading.value = false
      return
    }

    // 预先计算所有窗口的累计数据
    // 从后往前计算窗口起始位置，保证最后一个窗口有12条数据
    const allWindowStarts = []
    const totalLength = sortedDates.length
    
    if (totalLength <= maxChartItemsPerPage) {
      // 数据量小于等于12条，只有一个窗口
      allWindowStarts.push(0)
    } else {
      // 数据量大于12条，从后往前计算
      // 最后一个窗口：从 totalLength - 12 开始，包含12条数据
      let currentStart = totalLength - maxChartItemsPerPage
      allWindowStarts.push(currentStart)
      
      // 向前计算前面的窗口，每次向前移动12条
      while (currentStart > 0) {
        currentStart -= maxChartItemsPerPage
        if (currentStart > 0) {
          // 如果还有空间且大于0，添加窗口（包含12条数据）
          allWindowStarts.push(currentStart)
        } else {
          // 如果 currentStart <= 0，第一个窗口应该从0开始
          // 当 currentStart == 0 时，说明正好对齐（数据量是12的倍数），需要添加窗口0
          // 当 currentStart < 0 时，说明第一个窗口不足12条，也需要从0开始
          allWindowStarts.push(0)
          break
        }
      }
    }
    
    // 排序，确保窗口起始位置从小到大
    allWindowStarts.sort((a, b) => a - b)

    // 预先计算每个窗口的累计数据
    const precomputedCumulativeData = {
      rate: {}, // { seriesIndex: { windowStart: cumulativeData[] } }
      profit: {}, // { seriesIndex: { windowStart: cumulativeData[] } }
      marketRate: {}, // { windowStart: cumulativeData[] }
      marketProfit: {} // { windowStart: cumulativeData[] }
    }

    // 计算每个系列在每个窗口的累计数据
    const calculateCumulativeForWindow = (seriesItem, windowStart, isRateType, nextWindowStart = null) => {
      // 如果有下一个窗口，第一个窗口只包含到下一个窗口之前的数据（避免重叠）
      // 否则，窗口包含12条数据或到数据末尾
      let windowEnd
      if (nextWindowStart !== null && windowStart === 0 && nextWindowStart > 0) {
        // 第一个窗口且不是唯一窗口，只包含到下一个窗口之前的数据
        windowEnd = nextWindowStart
      } else {
        // 其他窗口，包含12条数据或到数据末尾
        windowEnd = Math.min(windowStart + maxChartItemsPerPage, sortedDates.length)
      }
      const windowDates = sortedDates.slice(windowStart, windowEnd)
      
      if (isRateType) {
        // 累计收益率
        let cumulativeProfit = 0
        let cumulativeInvestment = 0
        return windowDates.map(date => {
          const dataPoint = seriesItem.data.find(d => d.date === date)
          if (dataPoint && dataPoint.value !== null && dataPoint.value !== undefined) {
            const investment = dataPoint.investment || 0
            if (investment > 0) {
              cumulativeInvestment += investment
              const profit = (investment * dataPoint.value) / 100
              cumulativeProfit += profit
              return cumulativeInvestment > 0 ? (cumulativeProfit / cumulativeInvestment) * 100 : 0
            }
            return null
          }
          return null
        })
      } else {
        // 累计盈亏金额
        let cumulative = 0
        return windowDates.map(date => {
          const dataPoint = seriesItem.data.find(d => d.date === date)
          if (dataPoint && dataPoint.value !== null && dataPoint.value !== undefined) {
            cumulative += dataPoint.value
            return cumulative
          }
          return null
        })
      }
    }

    // 计算每个系列在每个窗口的累计数据
    seriesDataRate.forEach((item, index) => {
      precomputedCumulativeData.rate[index] = {}
      allWindowStarts.forEach((windowStart, windowIndex) => {
        // 获取下一个窗口的起始位置（用于避免第一个窗口重叠）
        const nextWindowStart = windowIndex < allWindowStarts.length - 1 ? allWindowStarts[windowIndex + 1] : null
        precomputedCumulativeData.rate[index][windowStart] = calculateCumulativeForWindow(item, windowStart, true, nextWindowStart)
      })
    })

    seriesDataProfit.forEach((item, index) => {
      precomputedCumulativeData.profit[index] = {}
      allWindowStarts.forEach((windowStart, windowIndex) => {
        // 获取下一个窗口的起始位置（用于避免第一个窗口重叠）
        const nextWindowStart = windowIndex < allWindowStarts.length - 1 ? allWindowStarts[windowIndex + 1] : null
        precomputedCumulativeData.profit[index][windowStart] = calculateCumulativeForWindow(item, windowStart, false, nextWindowStart)
      })
    })

    // 计算大盘在每个窗口的累计数据
    const sortedMarketRate = marketDataRate.sort((a, b) => a.date.localeCompare(b.date))
    const sortedMarketProfit = marketDataProfit.sort((a, b) => a.date.localeCompare(b.date))
    
    allWindowStarts.forEach((windowStart, windowIndex) => {
      // 获取下一个窗口的起始位置（用于避免第一个窗口重叠）
      const nextWindowStart = windowIndex < allWindowStarts.length - 1 ? allWindowStarts[windowIndex + 1] : null
      // 如果有下一个窗口，第一个窗口只包含到下一个窗口之前的数据（避免重叠）
      let windowEnd
      if (nextWindowStart !== null && windowStart === 0 && nextWindowStart > 0) {
        // 第一个窗口且不是唯一窗口，只包含到下一个窗口之前的数据
        windowEnd = nextWindowStart
      } else {
        // 其他窗口，包含12条数据或到数据末尾
        windowEnd = Math.min(windowStart + maxChartItemsPerPage, sortedDates.length)
      }
      const windowDates = sortedDates.slice(windowStart, windowEnd)
      
      // 大盘收益率累计数据
      let cumulativeProfit = 0
      let cumulativeInvestment = 0
      precomputedCumulativeData.marketRate[windowStart] = windowDates.map(date => {
        const dataPoint = sortedMarketRate.find(d => d.date === date)
        if (dataPoint && dataPoint.value !== null && dataPoint.value !== undefined) {
          const investment = dataPoint.investment || 0
          if (investment > 0) {
            cumulativeInvestment += investment
            const profit = (investment * dataPoint.value) / 100
            cumulativeProfit += profit
            return cumulativeInvestment > 0 ? (cumulativeProfit / cumulativeInvestment) * 100 : 0
          }
          return null
        }
        return null
      })
      
      // 大盘收益金额累计数据
      let cumulative = 0
      precomputedCumulativeData.marketProfit[windowStart] = windowDates.map(date => {
        const dataPoint = sortedMarketProfit.find(d => d.date === date)
        if (dataPoint && dataPoint.value !== null && dataPoint.value !== undefined) {
          cumulative += dataPoint.value
          return cumulative
        }
        return null
      })
    })

    // 准备图表数据
    chartData.value = {
      dates: sortedDates,
      seriesRate: seriesDataRate,
      seriesProfit: seriesDataProfit,
      marketRate: sortedMarketRate,
      marketProfit: sortedMarketProfit,
      precomputedCumulativeData: precomputedCumulativeData, // 预先计算的累计数据
      windowStarts: allWindowStarts // 所有窗口的起始位置数组
    }

    // 设置默认窗口位置为最后一页（最新的一页）
    // 优先保证最新的窗口有12条数据（如果全部数据不足12条，就展示全部数据）
    if (sortedDates.length > maxChartItemsPerPage) {
      // 数据量大于12条，最后一个窗口从倒数第12条开始，包含12条数据
      chartWindowStart.value = sortedDates.length - maxChartItemsPerPage
    } else {
      // 数据量小于等于12条，只有一个窗口，从0开始
      chartWindowStart.value = 0
    }

    // 等待 DOM 更新后渲染图表
    // 需要等待多个 nextTick 确保 DOM 完全渲染
    await nextTick()
    await nextTick()
    
    // 使用 setTimeout 确保 DOM 完全准备好
    setTimeout(() => {
      renderChart()
    }, 100)
  } catch (e) {
    console.error('生成图表失败:', e)
    chartError.value = '生成图表失败: ' + (e.response?.data?.detail || e.message)
  } finally {
    chartLoading.value = false
  }
}

// 获取止损止盈条件键
function getConditionKey(config) {
  const stopLoss = config.use_stop_loss ? config.stop_loss_percent : null
  const takeProfit = config.use_take_profit ? config.take_profit_percent : null
  return `${stopLoss}_${takeProfit}`
}

// 获取止损止盈条件标签
function getConditionLabel(config) {
  const parts = []
  if (config.use_stop_loss) {
    parts.push(`${config.stop_loss_percent}%`)
  }
  if (config.use_take_profit) {
    parts.push(`${config.take_profit_percent}%`)
  }
  if (parts.length === 0) {
    return '-'
  }
  return parts.join('/')
}

// 渲染图表
function renderChart() {
  if (!chartData.value) {
    console.warn('图表数据不存在')
    return
  }

  if (!chartRef.value) {
    console.warn('图表容器不存在，等待 DOM 更新...')
    // 如果容器不存在，延迟重试
    setTimeout(() => {
      if (chartRef.value) {
        renderChart()
      } else {
        console.error('图表容器无法获取')
        chartError.value = '图表容器初始化失败，请重试'
      }
    }, 200)
    return
  }

  if (!chartData.value.dates || chartData.value.dates.length === 0) {
    console.warn('图表日期数据为空:', chartData.value)
    chartError.value = '没有可用的日期数据'
    return
  }

  // 根据图表类型选择数据
  const isRate = chartType.value === 'rate'
  const seriesData = isRate ? chartData.value.seriesRate : chartData.value.seriesProfit
  const marketData = isRate ? chartData.value.marketRate : chartData.value.marketProfit
  
  if (!seriesData || seriesData.length === 0) {
    console.warn('图表系列数据为空:', chartData.value)
    chartError.value = `没有可用的${isRate ? '收益率' : '收益金额'}数据`
    return
  }

  // 计算当前窗口的日期范围
  const allDates = chartData.value.dates || []
  
  // 确保窗口起始位置有效
  if (chartWindowStart.value < 0) {
    chartWindowStart.value = 0
  }
  if (chartWindowStart.value >= allDates.length) {
    // 如果窗口起始位置超出范围，设置为最后一页的起始位置
    if (allDates.length > maxChartItemsPerPage) {
      chartWindowStart.value = allDates.length - maxChartItemsPerPage
    } else {
      chartWindowStart.value = 0
    }
  }
  
  // 计算窗口结束位置
  // 如果当前窗口是第一个窗口（索引0），需要检查下一个窗口的起始位置，避免重叠
  const windowStarts = chartData.value.windowStarts || []
  const currentWindowIndex = windowStarts.indexOf(chartWindowStart.value)
  let windowEnd
  if (currentWindowIndex >= 0 && currentWindowIndex < windowStarts.length - 1 && chartWindowStart.value === 0) {
    // 第一个窗口且不是唯一窗口，只包含到下一个窗口之前的数据（避免重叠）
    const nextWindowStart = windowStarts[currentWindowIndex + 1]
    windowEnd = nextWindowStart
  } else {
    // 其他窗口，包含12条数据或到数据末尾
    windowEnd = Math.min(chartWindowStart.value + maxChartItemsPerPage, allDates.length)
  }
  const visibleDates = allDates.slice(chartWindowStart.value, windowEnd)
  
  if (visibleDates.length === 0) {
    console.warn('当前窗口没有可用的日期数据')
    chartError.value = '当前窗口没有可用的数据'
    return
  }

  // 销毁旧图表实例
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }

  // 创建新图表实例
  chartInstance = echarts.init(chartRef.value, null, {
    width: 'auto',
    height: 500
  })
  const yAxisName = isRate ? '收益率 (%)' : '收益金额 (元)'
  const titleText = isRate ? '回测收益率趋势对比' : '回测收益金额趋势对比'

  // 准备系列数据
  const series = []
  // 自选组合使用红色系，不同条件使用不同深浅的红色
  const redColors = [
    '#d32f2f', '#f44336', '#e57373', '#ef5350', '#e53935',
    '#c62828', '#b71c1c', '#d50000', '#ff1744', '#ff5252'
  ]

  // 添加回测数据系列（自选组合 - 红色）
  if (seriesData && seriesData.length > 0) {
    seriesData.forEach((item, index) => {
      // 将数据映射到当前窗口的日期轴上
      const data = visibleDates.map(date => {
        const dataPoint = item.data.find(d => d.date === date)
        return dataPoint ? dataPoint.value : null
      })

      // 从预先计算的数据中获取当前窗口的累计数据
      let cumulativeData = null
      if (chartData.value.precomputedCumulativeData) {
        const precomputedData = isRate 
          ? chartData.value.precomputedCumulativeData.rate[index]
          : chartData.value.precomputedCumulativeData.profit[index]
        
        if (precomputedData && precomputedData[chartWindowStart.value]) {
          cumulativeData = precomputedData[chartWindowStart.value]
        }
      }
      
      // 如果没有预先计算的数据，则实时计算（向后兼容）
      if (!cumulativeData) {
        if (isRate) {
          // 累计收益率：累计收益金额 / 累计投入金额 * 100
          let cumulativeProfit = 0
          let cumulativeInvestment = 0
          cumulativeData = visibleDates.map((date, idx) => {
            const dataPoint = item.data.find(d => d.date === date)
            if (dataPoint && dataPoint.value !== null && dataPoint.value !== undefined) {
              const investment = dataPoint.investment || 0
              if (investment > 0) {
                cumulativeInvestment += investment
                const profit = (investment * dataPoint.value) / 100
                cumulativeProfit += profit
                return cumulativeInvestment > 0 ? (cumulativeProfit / cumulativeInvestment) * 100 : 0
              }
              return null
            }
            return null
          })
        } else {
          // 累计盈亏金额
          let cumulative = 0
          cumulativeData = data.map(value => {
            if (value !== null && value !== undefined) {
              cumulative += value
              return cumulative
            }
            return null
          })
        }
      }

      // 单期盈亏 - 实线（红色）- 默认隐藏
      series.push({
        name: item.name,
        type: 'line',
        data: data,
        smooth: true,
        symbol: 'circle',
        symbolSize: 8,
        lineStyle: {
          width: 2,
          type: 'solid', // 实线
          opacity: 1
        },
        itemStyle: {
          color: redColors[index % redColors.length],
          borderWidth: 1,
          borderColor: '#fff'
        },
        emphasis: {
          lineStyle: {
            width: 3
          },
          symbolSize: 10
        },
        connectNulls: false,
        show: false // 默认不显示非累计折线
      })

      // 累计数据 - 虚线（红色）
      if (cumulativeData) {
        const baseColor = redColors[index % redColors.length]
        series.push({
          name: `${item.name}（累计）`,
          type: 'line',
          data: cumulativeData,
          smooth: true,
          symbol: 'circle',
          symbolSize: 6,
          lineStyle: {
            width: 2,
            type: [10, 5], // 虚线：10px实线，5px空白
            opacity: 0.9
          },
          itemStyle: {
            color: baseColor
          },
          emphasis: {
            lineStyle: {
              width: 3
            },
            symbolSize: 8
          },
          connectNulls: false,
          z: 1 // 放在后面，避免遮挡
        })
      }
    })
  }

  // 添加大盘数据系列（蓝色）
  if (marketData && marketData.length > 0) {
    const marketDataPoints = visibleDates.map(date => {
      const dataPoint = marketData.find(d => d.date === date)
      return dataPoint ? dataPoint.value : null
    })

    // 从预先计算的数据中获取当前窗口的大盘累计数据
    let marketCumulativeData = null
    if (chartData.value.precomputedCumulativeData) {
      const precomputedMarketData = isRate
        ? chartData.value.precomputedCumulativeData.marketRate
        : chartData.value.precomputedCumulativeData.marketProfit
      
      if (precomputedMarketData && precomputedMarketData[chartWindowStart.value]) {
        marketCumulativeData = precomputedMarketData[chartWindowStart.value]
      }
    }
    
    // 如果没有预先计算的数据，则实时计算（向后兼容）
    if (!marketCumulativeData) {
      if (isRate) {
        // 累计收益率：累计收益金额 / 累计投入金额 * 100
        let cumulativeProfit = 0
        let cumulativeInvestment = 0
        marketCumulativeData = visibleDates.map((date, idx) => {
          const dataPoint = marketData.find(d => d.date === date)
          if (dataPoint && dataPoint.value !== null && dataPoint.value !== undefined) {
            const investment = dataPoint.investment || 0
            if (investment > 0) {
              cumulativeInvestment += investment
              const profit = (investment * dataPoint.value) / 100
              cumulativeProfit += profit
              return cumulativeInvestment > 0 ? (cumulativeProfit / cumulativeInvestment) * 100 : 0
            }
            return null
          }
          return null
        })
      } else {
        // 累计盈亏金额
        let cumulative = 0
        marketCumulativeData = marketDataPoints.map(value => {
          if (value !== null && value !== undefined) {
            cumulative += value
            return cumulative
          }
          return null
        })
      }
    }

    // 大盘单期 - 实线（蓝色）- 默认隐藏
    const marketBlueColor = '#2196F3' // 蓝色
    series.push({
      name: '上证指数',
      type: 'line',
      data: marketDataPoints,
      smooth: true,
      symbol: 'square',
      symbolSize: 8,
      lineStyle: {
        width: 2,
        type: 'solid', // 实线
        opacity: 1
      },
      itemStyle: {
        color: marketBlueColor,
        borderWidth: 1,
        borderColor: '#fff'
      },
      emphasis: {
        lineStyle: {
          width: 3
        },
        symbolSize: 10
      },
      connectNulls: false,
      show: false // 默认不显示非累计折线
    })

    // 大盘累计数据 - 虚线（蓝色）
    if (marketCumulativeData) {
      series.push({
        name: '上证指数累计',
        type: 'line',
        data: marketCumulativeData,
        smooth: true,
        symbol: 'square',
        symbolSize: 6,
        lineStyle: {
          width: 2,
          type: [10, 5], // 虚线：10px实线，5px空白
          opacity: 0.9
        },
        itemStyle: {
          color: marketBlueColor
        },
        emphasis: {
          lineStyle: {
            width: 3
          },
          symbolSize: 8
        },
        connectNulls: false,
        z: 1
      })
    }
  }

  // 配置图表选项
  const option = {
    title: {
      text: titleText,
      left: 'center',
      textStyle: {
        fontSize: 16,
        fontWeight: 'bold'
      }
    },
    tooltip: {
      trigger: 'axis',
      formatter: function(params) {
        let result = `<div style="margin-bottom: 4px;"><strong>${params[0].axisValue}</strong></div>`
        
        // 先显示单期数据
        params.forEach(param => {
          if (param.value !== null && param.value !== undefined && !param.seriesName.includes('累计')) {
            let displayValue
            if (isRate) {
              displayValue = param.value >= 0 ? `+${param.value.toFixed(2)}%` : `${param.value.toFixed(2)}%`
            } else {
              displayValue = param.value >= 0 ? `+¥${formatNumber(param.value)}` : `-¥${formatNumber(Math.abs(param.value))}`
            }
            result += `<div style="margin: 2px 0;">
              <span style="display:inline-block;width:10px;height:10px;background-color:${param.color};border-radius:50%;margin-right:5px;"></span>
              ${param.seriesName}: <strong>${displayValue}</strong>
            </div>`
          }
        })
        
        // 再显示累计数据（如果有，仅对收益金额类型）
        if (!isRate) {
          const hasCumulative = params.some(param => param.seriesName.includes('累计') && param.value !== null && param.value !== undefined)
          if (hasCumulative) {
            result += `<div style="margin-top: 8px; padding-top: 8px; border-top: 1px solid rgba(128,128,128,0.3);"><strong>累计盈亏：</strong></div>`
            params.forEach(param => {
              if (param.value !== null && param.value !== undefined && param.seriesName.includes('累计')) {
                const displayValue = param.value >= 0 ? `+¥${formatNumber(param.value)}` : `-¥${formatNumber(Math.abs(param.value))}`
                result += `<div style="margin: 2px 0;">
                  <span style="display:inline-block;width:10px;height:10px;background-color:${param.color};border-radius:50%;margin-right:5px;"></span>
                  ${param.seriesName}: <strong>${displayValue}</strong>
                </div>`
              }
            })
          }
        }
        
        return result
      }
    },
    legend: {
      data: series.map(s => s.name),
      bottom: 10,
      type: 'scroll',
      selected: (() => {
        // 默认只显示累计折线，隐藏非累计折线
        const selectedMap = {}
        series.forEach(s => {
          // 如果系列名称包含"累计"，则显示；否则隐藏
          selectedMap[s.name] = s.name.includes('累计')
        })
        return selectedMap
      })()
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      top: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: visibleDates,
      axisLabel: {
        rotate: 45,
        interval: 0,
        formatter: function(value) {
          // 只显示月份和日期
          return value.substring(5)
        }
      }
    },
    yAxis: {
      type: 'value',
      name: yAxisName,
      axisLabel: {
        formatter: isRate ? '{value}%' : function(value) {
          if (value >= 10000) {
            return (value / 10000).toFixed(1) + '万'
          }
          return value.toFixed(0)
        }
      }
    },
    series: series
  }

  // 设置图表选项
  chartInstance.setOption(option)

  // 响应式调整
  // 先移除旧的监听器（如果存在）
  if (chartResizeHandler) {
    window.removeEventListener('resize', chartResizeHandler)
  }
  
  chartResizeHandler = () => {
    if (chartInstance) {
      chartInstance.resize()
    }
  }
  window.addEventListener('resize', chartResizeHandler)
}

// 监听图表类型变化，重新渲染图表
watch(chartType, () => {
  if (showChartDialog.value && chartData.value && chartData.value.dates && chartData.value.dates.length > 0) {
    nextTick(() => {
      renderChart()
    })
  }
})

// 计算当前页码
function getCurrentPage() {
  if (!chartData.value || !chartData.value.dates || chartData.value.dates.length === 0) {
    return 1
  }
  
  // 使用窗口起始位置数组来计算页码
  const windowStarts = chartData.value.windowStarts
  if (!windowStarts || windowStarts.length === 0) {
    return 1
  }
  
  // 找到当前窗口起始位置在数组中的索引
  const currentIndex = windowStarts.indexOf(chartWindowStart.value)
  if (currentIndex === -1) {
    // 如果找不到，尝试找到最接近的窗口
    const closestIndex = windowStarts.findIndex(start => start > chartWindowStart.value) - 1
    return closestIndex >= 0 ? closestIndex + 1 : 1
  }
  
  return currentIndex + 1
}

// 计算总页数
function getTotalPages() {
  if (!chartData.value || !chartData.value.dates || chartData.value.dates.length === 0) {
    return 1
  }
  
  // 使用窗口起始位置数组的长度作为总页数
  const windowStarts = chartData.value.windowStarts
  if (windowStarts && windowStarts.length > 0) {
    return windowStarts.length
  }
  
  // 如果没有窗口数组，使用原来的计算方法（向后兼容）
  return Math.ceil(chartData.value.dates.length / maxChartItemsPerPage)
}

// 跳转到下一页
function goToNextPage() {
  if (!chartData.value || !chartData.value.dates || chartData.value.dates.length === 0) {
    return
  }
  
  // 使用窗口起始位置数组来切换
  const windowStarts = chartData.value.windowStarts
  if (!windowStarts || windowStarts.length === 0) {
    return
  }
  
  // 找到当前窗口起始位置在数组中的索引
  const currentIndex = windowStarts.indexOf(chartWindowStart.value)
  if (currentIndex === -1) {
    // 如果找不到，尝试找到最接近的窗口
    const closestIndex = windowStarts.findIndex(start => start > chartWindowStart.value) - 1
    if (closestIndex >= 0 && closestIndex < windowStarts.length - 1) {
      chartWindowStart.value = windowStarts[closestIndex + 1]
    }
    return
  }
  
  // 移动到下一个窗口
  if (currentIndex < windowStarts.length - 1) {
    chartWindowStart.value = windowStarts[currentIndex + 1]
  }
}

// 跳转到上一页
function goToPreviousPage() {
  if (!chartData.value || !chartData.value.dates || chartData.value.dates.length === 0) {
    return
  }
  
  // 使用窗口起始位置数组来切换
  const windowStarts = chartData.value.windowStarts
  if (!windowStarts || windowStarts.length === 0) {
    // 如果没有数组，使用原来的方法（向后兼容）
    chartWindowStart.value = Math.max(0, chartWindowStart.value - maxChartItemsPerPage)
    return
  }
  
  // 找到当前窗口起始位置在数组中的索引
  const currentIndex = windowStarts.indexOf(chartWindowStart.value)
  if (currentIndex === -1) {
    // 如果找不到，尝试找到最接近的窗口
    const closestIndex = windowStarts.findIndex(start => start > chartWindowStart.value) - 1
    if (closestIndex > 0) {
      chartWindowStart.value = windowStarts[closestIndex - 1]
    } else if (closestIndex === 0) {
      chartWindowStart.value = windowStarts[0]
    }
    return
  }
  
  // 移动到上一个窗口
  if (currentIndex > 0) {
    chartWindowStart.value = windowStarts[currentIndex - 1]
  }
}

// 监听窗口变化，重新渲染图表
watch(chartWindowStart, () => {
  if (showChartDialog.value && chartData.value && chartData.value.dates && chartData.value.dates.length > 0) {
    // 确保窗口位置有效
    const allDates = chartData.value.dates
    if (chartWindowStart.value < 0) {
      chartWindowStart.value = 0
    } else if (chartWindowStart.value >= allDates.length) {
      // 如果窗口起始位置超出范围，设置为最后一页的起始位置
      if (allDates.length > maxChartItemsPerPage) {
        chartWindowStart.value = allDates.length - maxChartItemsPerPage
      } else {
        chartWindowStart.value = 0
      }
    }
    nextTick(() => {
      renderChart()
    })
  }
})

// 监听图表对话框关闭，清理图表实例
watch(showChartDialog, (newVal) => {
  if (!newVal) {
    // 对话框关闭时清理
    if (chartInstance) {
      chartInstance.dispose()
      chartInstance = null
    }
    // 移除 resize 监听器
    if (chartResizeHandler) {
      window.removeEventListener('resize', chartResizeHandler)
      chartResizeHandler = null
    }
    // 重置图表类型和窗口位置
    chartType.value = 'rate'
    chartWindowStart.value = 0
  } else {
    // 对话框打开时，窗口位置会在generateBacktestChart中设置为最后一页
    // 如果数据已准备好，等待 DOM 更新后渲染
    if (chartData.value && chartData.value.dates && chartData.value.dates.length > 0 && !chartLoading.value) {
      // 设置窗口位置为最后一页（最新的一页）
      // 优先保证最新的窗口有12条数据（如果全部数据不足12条，就展示全部数据）
      if (chartData.value.dates.length > maxChartItemsPerPage) {
        chartWindowStart.value = chartData.value.dates.length - maxChartItemsPerPage
      } else {
        chartWindowStart.value = 0
      }
      nextTick(() => {
        setTimeout(() => {
          if (chartRef.value && chartData.value) {
            renderChart()
          }
        }, 150)
      })
    }
  }
})

// 添加止盈止损组合
function addProfitLossCombination() {
  batchBacktestConfig.value.profitLossCombinations.push({
    useStopLoss: true,
    useTakeProfit: true,
    stopLossPercent: -2,
    takeProfitPercent: 18
  })
}

// 移除止盈止损组合
function removeProfitLossCombination(index) {
  batchBacktestConfig.value.profitLossCombinations.splice(index, 1)
}

// 运行批量回测
async function runBatchBacktest() {
  if (!canRunBatchBacktest.value) {
    error.value = '请完善批量回测参数配置'
    return
  }

  batchBacktestLoading.value = true
  error.value = null
  batchBacktestResult.value = null

  try {
    const response = await axios.post('/platform/api/backtest/batch', {
      backtest_date: batchBacktestConfig.value.backtestDate,
      stat_date: batchBacktestConfig.value.statDate,
      buy_strategy: backtestConfig.value.buyStrategy,
      initial_capital: backtestConfig.value.initialCapital,
      selected_stocks: selectedStocks.value,
      profit_loss_combinations: batchBacktestConfig.value.profitLossCombinations.map(combo => ({
        use_stop_loss: combo.useStopLoss,
        use_take_profit: combo.useTakeProfit,
        stop_loss_percent: combo.stopLossPercent,
        take_profit_percent: combo.takeProfitPercent
      }))
    })

    if (response.data.success) {
      batchBacktestResult.value = response.data
      // 刷新回测历史记录
      await loadBacktestHistory()
    } else {
      error.value = '批量回测失败: ' + (response.data.detail || '未知错误')
    }
  } catch (e) {
    console.error('批量回测失败:', e)
    error.value = '批量回测失败: ' + (e.response?.data?.detail || e.message)
  } finally {
    batchBacktestLoading.value = false
  }
}

// 监听批量回测对话框打开，初始化配置
watch(showBatchBacktestDialog, (newVal) => {
  if (newVal) {
    // 初始化批量回测配置
    batchBacktestConfig.value.backtestDate = backtestConfig.value.backtestDate || ''
    batchBacktestConfig.value.statDate = backtestConfig.value.statDate || ''
    // 如果没有组合，添加一个默认组合
    if (batchBacktestConfig.value.profitLossCombinations.length === 0) {
      addProfitLossCombination()
    }
    batchBacktestResult.value = null
  }
})

// 获取扫描历史记录（用于查找扫描配置）
let scanHistoryCache = null
let scanHistoryDetailsCache = new Map() // key: record.id, value: record data with scannedStocks

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

// 清除扫描历史记录缓存
function clearScanHistoryCache() {
  scanHistoryCache = null
  scanHistoryDetailsCache.clear()
}

// 缓存回测历史记录详情
let backtestRecordsCache = new Map() // key: record.id, value: record data
let cachedBacktestHistoryIds = null // 缓存的回测历史记录ID列表

// 检查回测历史记录是否发生变化
function hasBacktestHistoryChanged() {
  const currentIds = filteredBacktestHistory.value.map(r => r.id).sort().join(',')
  if (cachedBacktestHistoryIds !== currentIds) {
    cachedBacktestHistoryIds = currentIds
    return true
  }
  return false
}

// 清除缓存（当回测历史记录变化时）
function clearBacktestRecordsCache() {
  backtestRecordsCache.clear()
  cachedBacktestHistoryIds = null
}

// 返回上一页或批量扫描页面
function goBack() {
  // 如果URL中有historyId参数，说明可能是从批量扫描页面打开的，返回到批量扫描页面
  if (route.query.historyId) {
    router.push('/platform/batch-scan')
  } else {
    // 没有historyId参数，返回首页
    router.push('/platform/')
  }
}

// 根据扫描日期查找对应的扫描配置
function findScanConfigByDate(scanDate, scanHistory) {
  if (!scanDate || !scanHistory || scanHistory.length === 0) {
    return null
  }
  // 查找相同扫描日期的记录，返回最新的
  const matchingRecords = scanHistory.filter(record => record.scanDate === scanDate)
  if (matchingRecords.length > 0) {
    // 按创建时间排序，返回最新的
    matchingRecords.sort((a, b) => {
      const timeA = new Date(a.createdAt || 0).getTime()
      const timeB = new Date(b.createdAt || 0).getTime()
      return timeB - timeA
    })
    return matchingRecords[0].scanConfig || null
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

// 计算统计数据
async function calculateStatistics() {
  statisticsLoading.value = true
  statisticsError.value = null
  statisticsResult.value = null

  try {
    // 使用筛选后的历史记录
    const historyToUse = filteredBacktestHistory.value
    
    if (historyToUse.length === 0) {
      statisticsError.value = '没有回测历史记录'
      statisticsLoading.value = false
      return
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
      // 如果缓存中有且历史记录未变化，直接使用缓存
      if (!historyChanged && backtestRecordsCache.has(record.id)) {
        fullRecords.push(backtestRecordsCache.get(record.id))
      } else {
        // 否则从API获取
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
      }
    }

    if (fullRecords.length === 0) {
      statisticsError.value = '无法获取回测历史记录详情'
      statisticsLoading.value = false
      return
    }

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

    // 根据股票属性筛选股票
    console.log('开始筛选股票，总股票数:', allStocks.length)
    console.log('筛选条件:', {
      platformPeriods: statisticsFilters.value.platformPeriods,
      breakthroughMACD: statisticsFilters.value.breakthroughMACD,
      breakthroughRSI: statisticsFilters.value.breakthroughRSI,
      breakthroughKDJ: statisticsFilters.value.breakthroughKDJ,
      breakthroughBollinger: statisticsFilters.value.breakthroughBollinger,
      breakthroughConfirmation: statisticsFilters.value.breakthroughConfirmation,
      industries: statisticsFilters.value.industries,
      boxQualityThreshold: statisticsFilters.value.boxQualityThreshold
    })
    
    // 调试：检查前几只股票的突破前兆和确认突破数据
    if (allStocks.length > 0) {
      console.log('前3只股票的突破前兆和确认突破数据示例:')
      allStocks.slice(0, 3).forEach((stock, idx) => {
        const bp = stock.breakthrough_prediction
        console.log(`股票${idx + 1} (${stock.code}):`, {
          hasBreakthroughPrediction: !!bp,
          signals: bp?.signals,
          signalKeys: bp?.signals ? Object.keys(bp.signals) : [],
          signalValues: bp?.signals ? Object.values(bp.signals) : [],
          RSI: bp?.signals?.RSI,
          '布林带': bp?.signals?.['布林带'],
          hasBreakthroughConfirmation: stock.has_breakthrough_confirmation,
          confirmationType: typeof stock.has_breakthrough_confirmation,
          confirmationValue: stock.has_breakthrough_confirmation
        })
      })
    }
    
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

// 当前正在加载的historyId，用于避免重复请求
let currentLoadingHistoryId = null

// 加载历史记录详情的函数
async function loadHistoryRecordById(historyId) {
  if (!historyId) {
    console.log('loadHistoryRecordById: historyId为空，跳过')
    return
  }
  
  // 如果正在加载相同的historyId，跳过
  if (currentLoadingHistoryId === historyId) {
    console.log('loadHistoryRecordById: 正在加载相同的historyId，跳过重复请求:', historyId)
    return
  }
  
  // 清除之前的回测结果，避免显示旧数据
  backtestResult.value = null
  console.log('✓ 已清除之前的回测结果（准备加载新的历史记录）')
  
  currentLoadingHistoryId = historyId
  
  try {
    console.log('正在加载历史记录详情，historyId:', historyId)
    const response = await axios.get(`/platform/api/backtest/history/${historyId}`)
    console.log('API响应:', response.data)
    if (response.data.success) {
      const record = response.data.data
      // 验证数据一致性：确保 result.summary 存在
      if (record.result && record.result.summary) {
        console.log('✓ 历史记录详情加载成功，summary数据:', record.result.summary)
      } else {
        console.warn('⚠ 历史记录中没有summary数据，record.result:', record.result)
      }
      // 加载历史记录到当前回测配置
      await loadHistoryRecordToCurrent(record)
    } else {
      console.error('API返回失败:', response.data)
      error.value = '加载回测历史详情失败'
    }
  } catch (e) {
    console.error('加载回测历史详情失败:', e)
    error.value = '加载回测历史详情失败: ' + (e.response?.data?.detail || e.message)
  } finally {
    currentLoadingHistoryId = null
  }
}

// 统一的数据加载函数：优先使用历史记录ID，如果没有则从sessionStorage获取
async function loadBacktestData() {
  const historyId = route.query.historyId
  
  console.log('开始加载回测数据，优先级：历史记录ID > sessionStorage')
  console.log('检查historyId参数:', historyId, '当前路由:', route.fullPath)
  
  // 清除之前的回测结果，避免显示旧数据
  backtestResult.value = null
  console.log('✓ 已清除之前的回测结果')
  
  // 优先级1：如果有历史记录ID，从历史记录加载
  if (historyId) {
    console.log('✓ 发现historyId，优先从历史记录加载数据:', historyId)
    try {
      await loadHistoryRecordById(historyId)
      console.log('✓ 从历史记录加载数据完成')
      return true
    } catch (e) {
      console.error('✗ 从历史记录加载数据失败:', e)
      // 如果历史记录加载失败，继续尝试从 sessionStorage 加载
      console.log('⚠ 历史记录加载失败，尝试从 sessionStorage 加载')
    }
  }
  
  // 优先级2：如果没有历史记录ID或加载失败，从sessionStorage加载
  console.log('从 sessionStorage 加载选中的股票和扫描配置')
  const loaded = loadSelectedStocksAndConfig()
  if (loaded) {
    // 初始化日期（会使用扫描配置中的扫描日期作为默认回测日）
    initDates()
    console.log('✓ 从 sessionStorage 加载数据完成')
    return true
  } else {
    console.log('✗ sessionStorage 中没有找到数据')
    return false
  }
}

// 检查并加载历史记录的函数（保留用于watch）
async function checkAndLoadHistory() {
  const historyId = route.query.historyId
  if (historyId) {
    console.log('watch触发：发现historyId，准备加载数据:', historyId)
    await loadHistoryRecordById(historyId)
  }
}

onMounted(async () => {
  // 统一的数据加载入口：优先使用历史记录ID，如果没有则从sessionStorage获取
  await loadBacktestData()
})

// 当组件被激活时（keepAlive组件从缓存中激活时）
onActivated(async () => {
  console.log('Backtest组件被激活，重新加载数据')
  await loadBacktestData()
})

// 监听路由变化，当historyId参数变化时重新加载数据
watch(() => route.query.historyId, async (newHistoryId, oldHistoryId) => {
  console.log('watch触发: historyId参数变化，从', oldHistoryId, '变为', newHistoryId)
  if (newHistoryId) {
    // 如果有新的historyId，优先从历史记录加载
    console.log('watch: 准备从历史记录加载新的historyId:', newHistoryId)
    await loadHistoryRecordById(newHistoryId)
  } else if (oldHistoryId && !newHistoryId) {
    // 如果historyId被移除，回退到从sessionStorage加载
    console.log('watch: historyId被移除，回退到从sessionStorage加载')
    await loadBacktestData()
  }
})

// 监听整个route对象的变化（更可靠）
watch(() => route.fullPath, async (newPath, oldPath) => {
  console.log('watch fullPath触发: 路由路径变化，从', oldPath, '变为', newPath)
  // 如果路径变化且没有historyId，重新加载数据（可能从sessionStorage）
  if (!route.query.historyId && oldPath !== newPath) {
    console.log('watch fullPath: 路径变化且无historyId，重新加载数据')
    await loadBacktestData()
  }
})

onBeforeUnmount(() => {
  // 清理图表实例
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
  // 移除 resize 监听器
  if (chartResizeHandler) {
    window.removeEventListener('resize', chartResizeHandler)
    chartResizeHandler = null
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

