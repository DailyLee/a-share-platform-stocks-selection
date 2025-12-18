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
            <div v-else class="space-y-4">
              <div
                v-for="(record, index) in backtestHistory"
                :key="record.id"
                class="card p-4 hover:bg-muted/30 transition-colors cursor-pointer"
                @click="viewHistoryRecord(record)"
              >
                <div class="flex justify-between items-start mb-2">
                  <div>
                    <h3 class="font-semibold text-sm sm:text-base">
                      回测 #{{ backtestHistory.length - index }}
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

          <!-- 对话框底部 -->
          <div class="p-4 sm:p-6 border-t border-border flex justify-end space-x-2">
            <button
              v-if="backtestHistory.length > 0"
              @click="clearBacktestHistory"
              class="px-4 py-2 rounded-md bg-destructive/10 text-destructive hover:bg-destructive/20 transition-colors text-sm"
            >
              <i class="fas fa-trash mr-2"></i>
              清空历史
            </button>
            <button
              @click="showHistoryDialog = false"
              class="px-4 py-2 rounded-md bg-primary text-primary-foreground hover:bg-primary/80 transition-colors text-sm"
            >
              关闭
            </button>
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
                  @click="deleteHistoryRecord(selectedHistoryRecord.id)"
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
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import ThemeToggle from './ThemeToggle.vue'

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
  takeProfitPercent: 15 // 止盈百分比
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
const selectedHistoryRecord = ref(null)

// 筛选理由展开状态
const expandedReasons = ref({})

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
  
  backtestConfig.value.statDate = today.toISOString().split('T')[0]
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
async function deleteHistoryRecord(historyId) {
  if (!confirm('确定要删除这条回测历史记录吗？此操作不可恢复。')) {
    return
  }
  
  try {
    const response = await axios.delete(`/platform/api/backtest/history/${historyId}`)
    if (response.data.success) {
      // 从列表中移除
      backtestHistory.value = backtestHistory.value.filter(r => r.id !== historyId)
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
async function clearBacktestHistory() {
  if (!confirm('确定要清空所有回测历史记录吗？此操作不可恢复。')) {
    return
  }
  
  try {
    const response = await axios.delete('/platform/api/backtest/history')
    if (response.data.success) {
      backtestHistory.value = []
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

onMounted(() => {
  // 加载选中的股票和扫描配置
  loadSelectedStocksAndConfig()
  // 初始化日期（会使用扫描配置中的扫描日期作为默认回测日）
  initDates()
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

