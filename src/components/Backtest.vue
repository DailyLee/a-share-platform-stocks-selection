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

          <!-- 买入策略 -->
          <div class="mb-6">
            <h3 class="text-sm font-medium mb-3 flex items-center">
              <i class="fas fa-shopping-cart mr-2 text-primary"></i>
              买入策略
            </h3>
            <div class="bg-muted/30 p-4 rounded-md">
              <div class="flex items-center space-x-2 mb-2">
                <input
                  type="radio"
                  id="buyStrategy1"
                  v-model="backtestConfig.buyStrategy"
                  value="fixed_amount"
                  class="radio"
                />
                <label for="buyStrategy1" class="text-sm">
                  根据扫描结果，每只当日开盘价买入1万元
                </label>
              </div>
            </div>
          </div>

          <!-- 卖出策略 -->
          <div class="mb-6">
            <h3 class="text-sm font-medium mb-3 flex items-center">
              <i class="fas fa-sign-out-alt mr-2 text-primary"></i>
              卖出策略
            </h3>
            <div class="bg-muted/30 p-4 rounded-md space-y-4">
              <!-- 止损设置 -->
              <div class="space-y-2">
                <div class="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="sellStrategyStopLoss"
                    v-model="backtestConfig.useStopLoss"
                    class="checkbox"
                  />
                  <label for="sellStrategyStopLoss" class="text-sm">
                    止损
                  </label>
                </div>
                <div v-if="backtestConfig.useStopLoss" class="ml-6 flex items-center space-x-2">
                  <label for="stopLossPercent" class="text-sm text-muted-foreground whitespace-nowrap">百分比：</label>
                  <input
                    id="stopLossPercent"
                    v-model.number="backtestConfig.stopLossPercent"
                    type="number"
                    step="0.1"
                    min="-100"
                    max="0"
                    class="input w-24"
                    placeholder="-3"
                  />
                  <span class="text-sm text-muted-foreground">%</span>
                  <p class="text-xs text-muted-foreground ml-2">
                    (负数，例如：-3 表示下跌3%时止损)
                  </p>
                </div>
              </div>
              
              <!-- 止盈设置 -->
              <div class="space-y-2">
                <div class="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="sellStrategyTakeProfit"
                    v-model="backtestConfig.useTakeProfit"
                    class="checkbox"
                  />
                  <label for="sellStrategyTakeProfit" class="text-sm">
                    止盈
                  </label>
                </div>
                <div v-if="backtestConfig.useTakeProfit" class="ml-6 flex items-center space-x-2">
                  <label for="takeProfitPercent" class="text-sm text-muted-foreground whitespace-nowrap">百分比：</label>
                  <input
                    id="takeProfitPercent"
                    v-model.number="backtestConfig.takeProfitPercent"
                    type="number"
                    step="0.1"
                    min="0"
                    max="1000"
                    class="input w-24"
                    placeholder="10"
                  />
                  <span class="text-sm text-muted-foreground">%</span>
                  <p class="text-xs text-muted-foreground ml-2">
                    (正数，例如：10 表示上涨10%时止盈)
                  </p>
                </div>
              </div>
            </div>
          </div>

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
          <div class="p-4 sm:p-6 border-b border-border flex justify-between items-center">
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
              <div v-for="(records, scanDate) in backtestHistoryGroupedByDate" :key="scanDate" class="space-y-3">
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
                  class="card p-4 hover:bg-muted/30 transition-colors cursor-pointer"
                  @click="viewHistoryRecord(record)"
                >
                  <div class="flex justify-between items-start mb-2">
                    <div>
                      <h3 class="font-semibold text-sm sm:text-base">
                        回测 #{{ records.length - index }}
                      </h3>
                      <p class="text-xs text-muted-foreground mt-1">
                        {{ formatDateTime(record.createdAt) }}
                      </p>
                    </div>
                    <div class="text-right">
                      <div class="text-lg font-bold" :class="record.summary.totalReturnRate >= 0 ? 'text-red-600 dark:text-red-400' : 'text-blue-600 dark:text-blue-400'">
                        {{ record.summary.totalReturnRate >= 0 ? '+' : '' }}{{ formatPercent(record.summary.totalReturnRate) }}%
                      </div>
                      <div class="text-xs text-muted-foreground">
                        {{ record.summary.totalReturnRate >= 0 ? '+' : '' }}¥{{ formatNumber(record.summary.totalProfit) }}
                      </div>
                    </div>
                  </div>
                  <div class="grid grid-cols-2 sm:grid-cols-4 gap-2 mt-3 text-xs">
                    <div>
                      <span class="text-muted-foreground">回测日：</span>
                      <span>{{ record.backtestDate }}</span>
                    </div>
                    <div>
                      <span class="text-muted-foreground">统计日：</span>
                      <span>{{ record.statDate }}</span>
                    </div>
                    <div>
                      <span class="text-muted-foreground">股票数：</span>
                      <span>{{ record.summary.totalStocks }}</span>
                    </div>
                    <div>
                      <span class="text-muted-foreground">投入：</span>
                      <span>¥{{ formatNumber(record.summary.totalInvestment) }}</span>
                    </div>
                  </div>
                  <div class="mt-2 flex flex-wrap gap-2">
                    <span v-if="record.useStopLoss" class="px-2 py-0.5 rounded-full text-xs bg-blue-500/20 text-blue-700 dark:text-blue-400">
                      止损: {{ record.stopLossPercent }}%
                    </span>
                    <span v-if="record.useTakeProfit" class="px-2 py-0.5 rounded-full text-xs bg-red-500/20 text-red-700 dark:text-red-400">
                      止盈: {{ record.takeProfitPercent }}%
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 对话框底部 -->
          <div class="p-4 sm:p-6 border-t border-border flex justify-between items-center">
            <button
              v-if="backtestHistory.length > 0"
              @click="generateBacktestChart"
              class="px-4 py-2 rounded-md bg-primary text-primary-foreground hover:bg-primary/80 transition-colors text-sm"
            >
              <i class="fas fa-chart-line mr-2"></i>
              生成折线图
            </button>
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
      <div v-if="selectedHistoryRecord" class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" @click.self="selectedHistoryRecord = null">
        <div class="bg-card border border-border rounded-lg shadow-lg max-w-6xl w-full max-h-[90vh] overflow-hidden flex flex-col">
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
                    <span>{{ selectedHistoryRecord.config.buy_strategy === 'fixed_amount' ? '固定金额' : selectedHistoryRecord.config.buy_strategy }}</span>
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
                  @click="showDeleteHistoryConfirm(selectedHistoryRecord.id)"
                  class="px-4 py-2 rounded-md bg-destructive/10 text-destructive hover:bg-destructive/20 transition-colors text-sm"
                >
                  <i class="fas fa-trash mr-2"></i>
                  删除记录
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
              <!-- 图表容器 -->
              <div ref="chartRef" class="w-full h-[500px] min-h-[500px]"></div>
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
import { ref, computed, onMounted, onBeforeUnmount, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import * as echarts from 'echarts/core'
import { LineChart } from 'echarts/charts'
import { TitleComponent, TooltipComponent, LegendComponent, GridComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import ThemeToggle from './ThemeToggle.vue'
import ConfirmDialog from './ConfirmDialog.vue'

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
let chartInstance = null
let chartResizeHandler = null

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
  router.push({
    path: '/platform/check',
    query: {
      code: stock.code,
      from: 'backtest'
    }
  })
}

// 从 sessionStorage 加载选中的股票和扫描配置
function loadSelectedStocksAndConfig() {
  try {
    console.log('开始加载选中的股票和扫描配置...')
    
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

// 加载历史记录到当前回测
function loadHistoryRecordToCurrent(record) {
  if (record && record.config) {
    // 加载回测配置
    backtestConfig.value.backtestDate = record.config.backtest_date
    backtestConfig.value.statDate = record.config.stat_date
    backtestConfig.value.buyStrategy = record.config.buy_strategy || 'fixed_amount'
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
    // 优先使用 selected_stocks 中的信息，如果没有则尝试从 scan_config 加载
    if (record.config.selected_stocks && record.config.selected_stocks.length > 0) {
      // 新格式：从 selected_stocks 中提取信息，尝试从 sessionStorage 获取扫描配置
      try {
        const savedScanConfig = sessionStorage.getItem('scanConfig')
        if (savedScanConfig) {
          scanConfig.value = JSON.parse(savedScanConfig)
        }
        sessionStorage.setItem('selectedStocks', JSON.stringify(selectedStocks.value))
        console.log('✓ 股票已加载并保存到 sessionStorage')
      } catch (e) {
        console.error('保存数据到 sessionStorage 失败:', e)
      }
    } else if (record.config.scan_config) {
      // 旧格式：向后兼容
      scanConfig.value = record.config.scan_config
      try {
        sessionStorage.setItem('scanConfig', JSON.stringify(record.config.scan_config))
        sessionStorage.setItem('selectedStocks', JSON.stringify(selectedStocks.value))
        console.log('✓ 扫描配置和股票已加载并保存到 sessionStorage（旧格式）')
      } catch (e) {
        console.error('保存数据到 sessionStorage 失败:', e)
      }
    }
    
    // 加载并显示回测结果数据
    if (record.result) {
      backtestResult.value = record.result
      console.log('✓ 回测结果数据已加载')
    } else {
      console.warn('历史记录中没有回测结果数据')
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
  if (backtestHistory.value.length === 0) {
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
    for (const record of backtestHistory.value) {
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
          if (existingIndex >= 0) {
            const existing = mergedDataRate[existingIndex]
            existing.totalReturnRate = (existing.totalReturnRate + returnRate) / 2
            existing.count += 1
          } else {
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
          if (existingIndex >= 0) {
            const existing = mergedDataProfit[existingIndex]
            existing.totalProfit = (existing.totalProfit + totalProfit) / 2
            existing.count += 1
          } else {
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
        dates.add(backtestDate)
        
        const existingIndex = marketDataRate.findIndex(item => item.date === backtestDate)
        if (existingIndex >= 0) {
          marketDataRate[existingIndex].value = (marketDataRate[existingIndex].value + marketReturnRate) / 2
          marketDataRate[existingIndex].investment = (marketDataRate[existingIndex].investment + totalInvestment) / 2
        } else {
          marketDataRate.push({
            date: backtestDate,
            value: marketReturnRate,
            investment: totalInvestment
          })
        }

        // 计算大盘收益金额（基于投入金额和收益率）
        const marketProfit = (totalInvestment * marketReturnRate) / 100
        const existingProfitIndex = marketDataProfit.findIndex(item => item.date === backtestDate)
        if (existingProfitIndex >= 0) {
          marketDataProfit[existingProfitIndex].value = (marketDataProfit[existingProfitIndex].value + marketProfit) / 2
        } else {
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

    // 准备图表数据
    chartData.value = {
      dates: sortedDates,
      seriesRate: seriesDataRate,
      seriesProfit: seriesDataProfit,
      marketRate: marketDataRate.sort((a, b) => a.date.localeCompare(b.date)),
      marketProfit: marketDataProfit.sort((a, b) => a.date.localeCompare(b.date))
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
    parts.push(`止损${config.stop_loss_percent}%`)
  }
  if (config.use_take_profit) {
    parts.push(`止盈${config.take_profit_percent}%`)
  }
  if (parts.length === 0) {
    return '无止损止盈'
  }
  return parts.join(' / ')
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
  // 自选组合使用绿色系，不同条件使用不同深浅的绿色
  const greenColors = [
    '#2ca02c', '#4caf50', '#66bb6a', '#81c784', '#a5d6a7',
    '#388e3c', '#43a047', '#5cb85c', '#7cb342', '#9ccc65'
  ]

  // 添加回测数据系列（自选组合 - 绿色）
  if (seriesData && seriesData.length > 0) {
    seriesData.forEach((item, index) => {
      // 将数据映射到日期轴上
      const data = chartData.value.dates.map(date => {
        const dataPoint = item.data.find(d => d.date === date)
        return dataPoint ? dataPoint.value : null
      })

      // 计算累计数据
      let cumulativeData = null
      if (isRate) {
        // 累计收益率：累计收益金额 / 累计投入金额 * 100
        let cumulativeProfit = 0
        let cumulativeInvestment = 0
        cumulativeData = chartData.value.dates.map((date, idx) => {
          // 找到对应日期的数据点
          const dataPoint = item.data.find(d => d.date === date)
          if (dataPoint && dataPoint.value !== null && dataPoint.value !== undefined) {
            const investment = dataPoint.investment || 0
            if (investment > 0) {
              cumulativeInvestment += investment
              // 计算单期收益金额
              const profit = (investment * dataPoint.value) / 100
              cumulativeProfit += profit
              // 计算累计收益率
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

      // 单期盈亏 - 实线（绿色）
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
          color: greenColors[index % greenColors.length],
          borderWidth: 1,
          borderColor: '#fff'
        },
        emphasis: {
          lineStyle: {
            width: 3
          },
          symbolSize: 10
        },
        connectNulls: false
      })

      // 累计数据 - 虚线（绿色）
      if (cumulativeData) {
        const baseColor = greenColors[index % greenColors.length]
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
    const marketDataPoints = chartData.value.dates.map(date => {
      const dataPoint = marketData.find(d => d.date === date)
      return dataPoint ? dataPoint.value : null
    })

    // 计算大盘累计数据
    let marketCumulativeData = null
    if (isRate) {
      // 累计收益率：累计收益金额 / 累计投入金额 * 100
      let cumulativeProfit = 0
      let cumulativeInvestment = 0
      marketCumulativeData = chartData.value.dates.map((date, idx) => {
        // 找到对应日期的数据点
        const dataPoint = marketData.find(d => d.date === date)
        if (dataPoint && dataPoint.value !== null && dataPoint.value !== undefined) {
          const investment = dataPoint.investment || 0
          if (investment > 0) {
            cumulativeInvestment += investment
            // 计算单期收益金额
            const profit = (investment * dataPoint.value) / 100
            cumulativeProfit += profit
            // 计算累计收益率
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

    // 大盘单期 - 实线（蓝色）
    const marketBlueColor = '#2196F3' // 蓝色
    series.push({
      name: '大盘（上证指数）',
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
      connectNulls: false
    })

    // 大盘累计数据 - 虚线（蓝色）
    if (marketCumulativeData) {
      series.push({
        name: '大盘（上证指数）累计',
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
      type: 'scroll'
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
      data: chartData.value.dates,
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
    // 重置图表类型
    chartType.value = 'rate'
  } else {
    // 对话框打开时，如果数据已准备好，等待 DOM 更新后渲染
    if (chartData.value && chartData.value.dates && chartData.value.dates.length > 0 && !chartLoading.value) {
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

onMounted(() => {
  // 加载选中的股票和扫描配置
  loadSelectedStocksAndConfig()
  // 初始化日期（会使用扫描配置中的扫描日期作为默认回测日）
  initDates()
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

