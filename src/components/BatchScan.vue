<template>
  <div class="min-h-screen bg-background text-foreground p-4">
    <!-- 参数帮助管理器 -->
    <ParameterHelpManager />
    
    <div class="max-w-6xl mx-auto">
      <!-- 页面标题 -->
      <div class="mb-6">
        <div class="flex items-center justify-between mb-2">
          <h1 class="text-2xl font-bold flex items-center">
            <i class="fas fa-tasks mr-2 text-primary"></i>
            批量扫描
          </h1>
          <button
            @click="goBack"
            class="flex items-center justify-center px-2 sm:px-3 py-1.5 sm:py-2 rounded-md bg-gundam-blue text-white hover:bg-gundam-blue/80 transition-colors"
          >
            <i class="fas fa-arrow-left mr-1 sm:mr-2"></i>
            <span class="hidden sm:inline">返回</span>
          </button>
        </div>
        <p class="text-muted-foreground mt-2">
          设置时间区间和扫描周期，系统将按周期自动执行多次扫描
        </p>
      </div>

      <!-- 任务配置表单 -->
      <div class="card p-4 sm:p-6 mb-6">
        <h2 class="text-lg font-semibold mb-4 flex items-center">
          <i class="fas fa-cog mr-2 text-primary"></i>
          任务配置
        </h2>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
          <!-- 任务名称 -->
          <div>
            <label class="block text-sm font-medium mb-2">
              <i class="fas fa-tag mr-1 text-primary"></i>
              任务名称 *
            </label>
            <input
              v-model="taskName"
              type="text"
              class="input w-full"
              placeholder="例如: 2024年Q1批量扫描"
              required
            />
          </div>

          <!-- 扫描周期 -->
          <div>
            <label class="block text-sm font-medium mb-2">
              <i class="fas fa-calendar-week mr-1 text-primary"></i>
              扫描周期（天） *
            </label>
            <input
              v-model.number="scanPeriodDays"
              type="number"
              class="input w-full"
              min="1"
              placeholder="默认: 7"
              required
            />
            <p class="text-xs text-muted-foreground mt-1">
              每隔多少天执行一次扫描
            </p>
          </div>

          <!-- 开始日期 -->
          <div>
            <label class="block text-sm font-medium mb-2">
              <i class="fas fa-calendar-alt mr-1 text-primary"></i>
              开始日期 *
            </label>
            <input
              v-model="startDate"
              type="date"
              class="input w-full"
              :max="endDate || maxDate"
              required
            />
          </div>

          <!-- 结束日期 -->
          <div>
            <label class="block text-sm font-medium mb-2">
              <i class="fas fa-calendar-check mr-1 text-primary"></i>
              结束日期 *
            </label>
            <input
              v-model="endDate"
              type="date"
              class="input w-full"
              :min="startDate"
              :max="maxDate"
              required
            />
          </div>
        </div>

        <!-- 扫描参数配置 -->
        <div class="mt-6">
          <h3 class="text-md font-semibold mb-4 flex items-center">
            <i class="fas fa-sliders-h mr-2 text-primary"></i>
            扫描参数配置
          </h3>
          <ScanConfigForm
            v-model="scanConfig"
            :show-scan-date="false"
            ref="scanConfigFormRef"
          />
        </div>

        <!-- 提交按钮 -->
        <div class="mt-6 flex justify-end">
          <button
            @click="handleSubmitClick"
            :disabled="!canSubmit"
            class="btn btn-primary px-6 py-2"
            :class="{ 'opacity-50 cursor-not-allowed': !canSubmit }"
          >
            <i class="fas fa-play mr-2"></i>
            提交任务
          </button>
          <!-- 调试信息（开发时可见） -->
          <div v-if="false" class="text-xs text-muted-foreground ml-4">
            canSubmit: {{ canSubmit }}, taskName: {{ taskName }}, startDate: {{ startDate }}, endDate: {{ endDate }}
          </div>
        </div>
      </div>

      <!-- 任务列表 -->
      <div class="card p-4 sm:p-6">
        <div class="flex justify-between items-center mb-4">
          <h2 class="text-lg font-semibold flex items-center">
            <i class="fas fa-list mr-2 text-primary"></i>
            任务列表
          </h2>
          <button
            @click="loadTasks"
            class="btn btn-secondary px-4 py-2"
          >
            <i class="fas fa-sync-alt mr-2"></i>
            刷新
          </button>
        </div>

        <div v-if="loading" class="text-center py-8">
          <i class="fas fa-spinner fa-spin text-2xl text-primary"></i>
          <p class="text-muted-foreground mt-2">加载中...</p>
        </div>

        <div v-else-if="tasks.length === 0" class="text-center py-8">
          <i class="fas fa-inbox text-4xl text-muted-foreground"></i>
          <p class="text-muted-foreground mt-2">暂无任务</p>
        </div>

        <div v-else class="space-y-4">
          <div
            v-for="task in tasks"
            :key="task.id"
            class="border border-border rounded-lg p-4 hover:bg-muted/30 transition-colors"
          >
            <div class="flex justify-between items-start">
              <div class="flex-1">
                <div class="flex items-center mb-2">
                  <h3 class="font-semibold mr-2">{{ task.taskName }}</h3>
                  <span
                    :class="[
                      'px-2 py-1 rounded text-xs font-medium',
                      getStatusClass(task.status)
                    ]"
                  >
                    {{ getStatusText(task.status) }}
                  </span>
                </div>
                <div class="text-sm text-muted-foreground space-y-1">
                  <div>
                    <i class="fas fa-calendar-alt mr-1"></i>
                    时间区间: {{ task.startDate }} 至 {{ task.endDate }}
                  </div>
                  <div>
                    <i class="fas fa-calendar-week mr-1"></i>
                    扫描周期: {{ task.scanPeriodDays }} 天
                  </div>
                  <div>
                    <i class="fas fa-tasks mr-1"></i>
                    进度: {{ task.completedScans }}/{{ task.totalScans }} ({{ task.progress }}%)
                  </div>
                  <div>
                    <i class="fas fa-clock mr-1"></i>
                    创建时间: {{ formatDate(task.createdAt) }}
                  </div>
                </div>
              </div>
              <div class="flex flex-col gap-2 ml-4">
                <button
                  v-if="task.status === 'running'"
                  @click="cancelTask(task.id)"
                  class="btn btn-danger px-3 py-1 text-sm"
                >
                  <i class="fas fa-stop mr-1"></i>
                  取消
                </button>
                <button
                  v-if="task.status === 'completed'"
                  @click="openBacktestDialog(task)"
                  :disabled="loadingBacktestTaskId === task.id"
                  class="btn btn-primary px-3 py-1 text-sm"
                  :class="{ 'opacity-50 cursor-not-allowed': loadingBacktestTaskId === task.id }"
                >
                  <i v-if="loadingBacktestTaskId === task.id" class="fas fa-spinner fa-spin mr-1"></i>
                  <i v-else class="fas fa-chart-line mr-1"></i>
                  {{ loadingBacktestTaskId === task.id ? '加载中...' : '一键回测' }}
                </button>
                <button
                  v-if="task.status === 'completed'"
                  @click="openTaskBacktestHistory(task)"
                  class="btn btn-secondary px-3 py-1 text-sm"
                >
                  <i class="fas fa-history mr-1"></i>
                  回测历史
                </button>
                <button
                  @click="viewTaskDetails(task.id)"
                  class="btn btn-secondary px-3 py-1 text-sm"
                >
                  <i class="fas fa-eye mr-1"></i>
                  查看
                </button>
                <button
                  @click="deleteTask(task.id)"
                  class="btn btn-danger px-3 py-1 text-sm"
                >
                  <i class="fas fa-trash mr-1"></i>
                  删除
                </button>
              </div>
            </div>

            <!-- 进度条 -->
            <div v-if="task.status === 'running'" class="mt-4">
              <div class="flex justify-between text-xs text-muted-foreground mb-1">
                <span>扫描进度</span>
                <span>{{ task.progress }}%</span>
              </div>
              <div class="w-full bg-muted rounded-full h-2">
                <div
                  class="bg-primary h-2 rounded-full transition-all"
                  :style="{ width: task.progress + '%' }"
                ></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 确认对话框 - 提交任务 -->
    <ConfirmDialog
      :show="showConfirmDialog"
      @update:show="showConfirmDialog = $event"
      title="确认提交批量扫描任务"
      :message="confirmMessage"
      confirm-text="确认提交"
      cancel-text="取消"
      @confirm="submitTask"
    />

    <!-- 确认对话框 - 取消任务 -->
    <ConfirmDialog
      :show="showCancelConfirmDialog"
      @update:show="showCancelConfirmDialog = $event"
      title="确认取消任务"
      message="确定要取消此任务吗？"
      confirm-text="确认取消"
      cancel-text="取消"
      type="warning"
      @confirm="handleCancelTaskConfirm"
    />

    <!-- 确认对话框 - 删除任务 -->
    <ConfirmDialog
      :show="showDeleteConfirmDialog"
      @update:show="showDeleteConfirmDialog = $event"
      title="确认删除任务"
      message="确定要删除此任务吗？删除后将无法恢复。"
      confirm-text="确认删除"
      cancel-text="取消"
      type="danger"
      @confirm="handleDeleteTaskConfirm"
    />

    <!-- 任务详情对话框 -->
    <div
      v-if="showTaskDetailsDialog"
      class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
    >
      <div class="bg-card border border-border rounded-lg shadow-lg max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col" @click.stop>
        <div class="p-4 sm:p-6 border-b border-border">
          <div class="flex justify-between items-center">
            <h2 class="text-lg font-semibold">任务详情</h2>
            <button
              @click="showTaskDetailsDialog = false"
              class="text-muted-foreground hover:text-foreground"
            >
              <i class="fas fa-times text-xl"></i>
            </button>
          </div>
        </div>
        <div class="flex-1 overflow-auto p-4 sm:p-6">
          <TaskDetails
            v-if="selectedTaskId"
            :task-id="selectedTaskId"
            @close="showTaskDetailsDialog = false"
          />
        </div>
      </div>
    </div>

    <!-- 批量回测对话框 -->
    <div
      v-if="showBacktestDialog"
      class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
      @click.self="showBacktestDialog = false"
    >
      <div class="bg-card border border-border rounded-lg shadow-lg max-w-2xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        <div class="p-4 sm:p-6 border-b border-border">
          <div class="flex justify-between items-center">
            <h2 class="text-lg font-semibold">批量回测配置</h2>
            <div class="flex items-center gap-2">
              <button
                @click="openBacktestHistoryDialog"
                class="btn btn-secondary px-3 py-1.5 text-sm"
                :disabled="!selectedTaskForBacktest"
              >
                <i class="fas fa-history mr-1"></i>
                回测历史
              </button>
              <button
                @click="showBacktestDialog = false"
                class="text-muted-foreground hover:text-foreground"
              >
                <i class="fas fa-times text-xl"></i>
              </button>
            </div>
          </div>
        </div>
        <div class="flex-1 overflow-auto p-4 sm:p-6">
          <div v-if="selectedTaskForBacktest">
            <div class="mb-4 p-3 bg-muted/30 rounded-lg">
              <p class="text-sm text-muted-foreground mb-1">任务名称</p>
              <p class="font-medium">{{ selectedTaskForBacktest.taskName }}</p>
            </div>

            <!-- 回测参数配置 -->
            <div class="space-y-4">
              <!-- 回测名称 -->
              <div>
                <label class="block text-sm font-medium mb-2">
                  <i class="fas fa-tag mr-1 text-primary"></i>
                  回测名称 *
                </label>
                <input
                  v-model="backtestConfig.backtestName"
                  type="text"
                  class="input w-full"
                  placeholder="例如: 2024年Q1回测"
                  required
                />
                <p class="text-xs text-muted-foreground mt-1">
                  用于归类回测历史记录，相同名称的回测会分组显示
                </p>
              </div>
              <!-- 各周期统计日配置 -->
              <div>
                <h3 class="text-sm font-medium mb-3 flex items-center">
                  <i class="fas fa-calendar-check mr-2 text-primary"></i>
                  各周期统计日配置
                </h3>
                <!-- 周期统计日天数偏移设置 -->
                <div class="mb-4 p-3 bg-muted/30 rounded-lg">
                  <label class="block text-sm font-medium mb-2">
                    <i class="fas fa-calendar-day mr-1 text-primary"></i>
                    周期统计日天数偏移设置
                  </label>
                  <div class="flex items-center gap-2">
                    <input
                      v-model.number="backtestConfig.periodStatDaysOffset"
                      @input="updatePeriodStatDates"
                      type="number"
                      min="1"
                      class="input w-24 text-sm"
                      placeholder="5"
                    />
                    <span class="text-sm text-muted-foreground">天</span>
                  </div>
                  <p class="text-xs text-muted-foreground mt-1">
                    设置后，所有周期的统计日将自动更新为回测日之后的指定天数（默认5天）
                  </p>
                </div>
                <div v-if="backtestLoading" class="text-center py-4 text-muted-foreground">
                  <i class="fas fa-spinner fa-spin mr-2"></i>
                  加载扫描结果中...
                </div>
                <div v-else-if="scanResultsForBacktest.length === 0" class="text-center py-4 text-muted-foreground">
                  <i class="fas fa-info-circle mr-2"></i>
                  该任务还没有扫描结果
                </div>
                <div v-else class="space-y-3 max-h-60 overflow-y-auto">
                  <div
                    v-for="result in scanResultsForBacktest"
                    :key="result.id"
                    class="border border-border rounded-lg p-3 bg-muted/20"
                  >
                    <div class="flex items-center justify-between mb-2">
                      <div>
                        <span class="text-sm font-medium">回测日（扫描日期）:</span>
                        <span class="text-sm ml-2">{{ result.scanDate }}</span>
                      </div>
                      <div class="text-xs text-muted-foreground">
                        成功/总数: {{ result.successCount || 0 }}/{{ result.totalScanned || 0 }} 结果：{{ result.stockCount || 0 }}只
                      </div>
                    </div>
                    <div>
                      <label class="block text-xs text-muted-foreground mb-1">统计日 *</label>
                      <input
                        v-model="backtestConfig.periodStatDates[result.scanDate]"
                        type="date"
                        class="input w-full text-sm"
                        :min="result.scanDate"
                        :max="maxDate"
                        required
                      />
                      <p class="text-xs text-muted-foreground mt-1">
                        默认值：回测日之后{{ backtestConfig.periodStatDaysOffset }}天
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              <!-- 买入卖出策略 -->
              <BuySellStrategy
                v-model="backtestConfig"
                unique-id="batch"
                :show-help-text="false"
                stop-loss-placeholder="-1.6"
                take-profit-placeholder="16"
                :show-buy-conditions="scanResultsForBacktest.length > 0"
                :available-platform-periods="availablePlatformPeriods"
                :selected-platform-periods="selectedPlatformPeriods"
                @update:selected-platform-periods="selectedPlatformPeriods = $event"
                :selected-boards="selectedBoards"
                @update:selected-boards="selectedBoards = $event"
                :available-stocks="allStocksForBacktest"
                :show-percent-b-filter="scanResultsForBacktest.length > 0"
                :percent-b-range="percentBRange"
                :selected-percent-b-range="selectedPercentBRange"
                @update:selected-percent-b-range="selectedPercentBRange = $event"
                :available-stocks-for-levels="allStocksForBacktest"
              />

              <div class="p-3 bg-blue-500/10 border border-blue-500/20 rounded-lg">
                <p class="text-sm text-blue-700 dark:text-blue-400">
                  <i class="fas fa-info-circle mr-1"></i>
                  回测将使用每个周期的开始日（扫描日期）作为回测日，每个周期可以单独设置统计日（默认为回测日之后{{ backtestConfig.periodStatDaysOffset }}天）。
                </p>
              </div>
            </div>
          </div>
        </div>
        <div class="p-4 sm:p-6 border-t border-border flex justify-between items-center">
          <button
            @click="exportScanResultsToCSV"
            :disabled="scanResultsForBacktest.length === 0 || backtestLoading"
            class="btn btn-secondary px-4 py-2"
            :class="{ 'opacity-50 cursor-not-allowed': scanResultsForBacktest.length === 0 || backtestLoading }"
          >
            <i class="fas fa-download mr-2"></i>
            导出扫描结果 (CSV)
          </button>
          <div class="flex gap-2">
            <button
              @click="showBacktestDialog = false"
              class="btn btn-secondary px-4 py-2"
            >
              取消
            </button>
            <button
              @click="runBatchBacktest"
              :disabled="!canRunBatchBacktest || backtestLoading"
              class="btn btn-primary px-4 py-2"
              :class="{ 'opacity-50 cursor-not-allowed': !canRunBatchBacktest || backtestLoading }"
            >
              <i v-if="backtestLoading" class="fas fa-spinner fa-spin mr-2"></i>
              <i v-else class="fas fa-play mr-2"></i>
              {{ backtestLoading ? '回测中...' : '开始回测' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 批量回测历史对话框 -->
    <div
      v-if="showBacktestHistoryDialog"
      class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
      @click.self="showBacktestHistoryDialog = false"
    >
      <div class="bg-card border border-border rounded-lg shadow-lg max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        <div class="p-4 sm:p-6 border-b border-border">
          <div class="flex justify-between items-center">
            <h2 class="text-lg font-semibold flex items-center">
              <i class="fas fa-history mr-2 text-primary"></i>
              批量回测历史记录
            </h2>
            <button
              @click="showBacktestHistoryDialog = false"
              class="text-muted-foreground hover:text-foreground"
            >
              <i class="fas fa-times text-xl"></i>
            </button>
          </div>
        </div>
        <div class="flex-1 overflow-auto p-4 sm:p-6">
          <div v-if="backtestHistoryLoading" class="text-center py-8">
            <i class="fas fa-spinner fa-spin text-2xl text-primary"></i>
            <p class="text-muted-foreground mt-2">加载中...</p>
          </div>
          <div v-else-if="backtestHistory.length === 0" class="text-center py-8 text-muted-foreground">
            <i class="fas fa-inbox text-4xl mb-2"></i>
            <p>暂无回测历史记录</p>
          </div>
          <div v-else class="space-y-4">
            <div v-for="(group, nameKey) in groupedBacktestHistory" :key="nameKey" class="space-y-2">
              <div 
                class="flex items-center justify-between px-3 py-2 bg-muted/30 rounded-t-lg border-b border-border cursor-pointer hover:bg-muted/50 transition-colors"
                @click="toggleDateExpanded(nameKey)"
              >
                <div class="text-sm font-semibold text-foreground flex items-center flex-1 flex-wrap gap-2">
                  <i 
                    :class="['fas mr-2 text-primary transition-transform', expandedDates.has(nameKey) ? 'fa-chevron-down' : 'fa-chevron-right']"
                  ></i>
                  <i class="fas fa-tag mr-2 text-primary"></i>
                  <span>{{ nameKey }}</span>
                  <span class="text-xs text-muted-foreground font-normal">
                    ({{ group.length }}条记录)
                  </span>
                  <span v-if="getDateConfig(group)" class="text-xs text-muted-foreground font-normal flex items-center gap-2 ml-2">
                    <span v-if="getDateConfig(group).buyStrategy" class="flex items-center">
                      <i class="fas fa-shopping-cart mr-1 text-primary"></i>
                      买入策略: {{ getBuyStrategyLabel(getDateConfig(group).buyStrategy) }}
                    </span>
                    <span v-if="getDateConfig(group).useStopLoss" class="flex items-center">
                      <i class="fas fa-arrow-down mr-1 text-blue-600 dark:text-blue-400"></i>
                      止损: {{ getDateConfig(group).stopLossPercent }}%
                    </span>
                    <span v-if="getDateConfig(group).useTakeProfit" class="flex items-center">
                      <i class="fas fa-arrow-up mr-1 text-red-600 dark:text-red-400"></i>
                      止盈: {{ getDateConfig(group).takeProfitPercent }}%
                    </span>
                    <span v-if="getGroupReturnRate(group) !== null" class="flex items-center font-medium" :class="getGroupReturnRate(group) >= 0 ? 'text-red-600 dark:text-red-400' : 'text-green-600 dark:text-green-400'">
                      <i class="fas fa-chart-line mr-1"></i>
                      收益率: {{ getGroupReturnRate(group) >= 0 ? '+' : '' }}{{ getGroupReturnRate(group).toFixed(2) }}%
                    </span>
                    <span v-if="getGroupWinRate(group) !== null" class="flex items-center font-medium" :class="getGroupWinRate(group) >= 50 ? 'text-red-600 dark:text-red-400' : 'text-green-600 dark:text-green-400'">
                      <i class="fas fa-trophy mr-1"></i>
                      胜率: {{ getGroupWinRate(group).toFixed(1) }}%
                    </span>
                  </span>
                </div>
                <div class="flex gap-2">
                  <button
                    @click.stop="openDateStatistics(group)"
                    class="btn btn-primary px-3 py-1 text-xs"
                  >
                    <i class="fas fa-chart-bar mr-1"></i>
                    数据统计
                  </button>
                  <button
                    @click.stop="showDeleteBacktestNameConfirm(nameKey, group)"
                    class="btn btn-danger px-3 py-1 text-xs"
                  >
                    <i class="fas fa-trash mr-1"></i>
                    删除全部
                  </button>
                </div>
              </div>
              <div v-show="expandedDates.has(nameKey)" class="space-y-1">
                <div
                  v-for="record in group"
                  :key="record.id"
                  class="flex items-center justify-between px-3 py-2 rounded hover:bg-muted/30 transition-colors"
                  :class="record.status === 'failed' ? 'bg-red-500/10 border-l-2 border-red-500' : ''"
                >
                  <div class="flex-1 flex items-center gap-4 text-sm">
                    <span class="font-medium w-24">{{ record.backtestDate }}</span>
                    <span class="text-muted-foreground w-24">{{ record.statDate || '-' }}</span>
                    <span v-if="record.status === 'failed'" class="text-red-600 dark:text-red-400 flex-1">
                      <i class="fas fa-exclamation-circle mr-1"></i>
                      {{ record.error || '回测失败' }}
                    </span>
                    <template v-else>
                      <span class="whitespace-nowrap min-w-0">
                        收益率: 
                        <span :class="getRecordReturnRate(record) >= 0 ? 'text-red-600 dark:text-red-400' : 'text-blue-600 dark:text-blue-400'">
                          {{ getRecordReturnRate(record) >= 0 ? '+' : '' }}{{ getRecordReturnRate(record).toFixed(2) || '0.00' }}%
                        </span>
                      </span>
                      <span class="whitespace-nowrap min-w-0">
                        收益: 
                        <span :class="record.summary?.totalProfit >= 0 ? 'text-red-600 dark:text-red-400' : 'text-blue-600 dark:text-blue-400'">
                          {{ record.summary?.totalProfit >= 0 ? '+' : '' }}¥{{ formatNumber(record.summary?.totalProfit || 0) }}
                        </span>
                      </span>
                      <span class="text-muted-foreground whitespace-nowrap">{{ record.summary?.totalStocks || 0 }}只</span>
                    </template>
                  </div>
                  <div class="flex gap-2 ml-4">
                    <button
                      v-if="record.status === 'failed'"
                      @click="retryFailedBacktest(record.id)"
                      :disabled="retryingHistoryId === record.id"
                      class="btn btn-primary px-3 py-1 text-sm"
                      :class="{ 'opacity-50 cursor-not-allowed': retryingHistoryId === record.id }"
                    >
                      <i v-if="retryingHistoryId === record.id" class="fas fa-spinner fa-spin mr-1"></i>
                      <i v-else class="fas fa-redo mr-1"></i>
                      {{ retryingHistoryId === record.id ? '重试中...' : '重试' }}
                    </button>
                    <button
                      v-if="record.status !== 'failed'"
                      @click="viewBacktestHistoryDetail(record.id)"
                      class="btn btn-secondary px-3 py-1 text-sm"
                    >
                      <i class="fas fa-eye mr-1"></i>
                      查看
                    </button>
                    <button
                      @click="showDeleteBacktestHistoryConfirm(record.id)"
                      :disabled="deletingHistoryId === record.id"
                      class="btn btn-danger px-3 py-1 text-sm"
                      :class="{ 'opacity-50 cursor-not-allowed': deletingHistoryId === record.id }"
                    >
                      <i v-if="deletingHistoryId === record.id" class="fas fa-spinner fa-spin mr-1"></i>
                      <i v-else class="fas fa-trash mr-1"></i>
                      {{ deletingHistoryId === record.id ? '删除中...' : '删除' }}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 确认对话框 - 删除回测历史记录 -->
    <ConfirmDialog
      :show="showDeleteBacktestHistoryConfirmDialog"
      @update:show="showDeleteBacktestHistoryConfirmDialog = $event"
      title="确认删除回测历史记录"
      message="确定要删除这条回测历史记录吗？删除后将无法恢复。"
      confirm-text="确认删除"
      cancel-text="取消"
      type="danger"
      @confirm="handleDeleteBacktestHistoryConfirm"
    />

    <!-- 确认对话框 - 删除同名称的所有回测历史记录 -->
    <ConfirmDialog
      :show="showDeleteBacktestNameConfirmDialog"
      @update:show="showDeleteBacktestNameConfirmDialog = $event"
      title="确认删除回测历史记录"
      :message="`确定要删除回测名称「${pendingDeleteBacktestName}」下的所有 ${pendingDeleteBacktestNameRecords.length} 条回测历史记录吗？删除后将无法恢复。`"
      confirm-text="确认删除"
      cancel-text="取消"
      type="danger"
      @confirm="handleDeleteBacktestNameConfirm"
    />

    <!-- 批量回测数据统计对话框 -->
    <BacktestStatistics
      v-if="showBacktestStatisticsDialog"
      :history-records="selectedDateRecords.length > 0 ? selectedDateRecords : backtestHistory"
      @close="showBacktestStatisticsDialog = false"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import ScanConfigForm from './ScanConfigForm.vue'
import ConfirmDialog from './ConfirmDialog.vue'
import { ParameterHelpManager } from './parameter-help'
import TaskDetails from './batch-scan/TaskDetails.vue'
import BacktestStatistics from './BacktestStatistics.vue'
import BuySellStrategy from './BuySellStrategy.vue'
import { calculateTotalReturnRate } from '../utils/returnRateCalculator.js'
import { getStockBoard } from '../utils/stockBoardUtils.js'
import { getDefaultScanConfig } from '../config/scanConfig.js' // 默认扫描配置
import { calculatePercentBRange, extractPercentB } from '../utils/selectionReasonsParser.js'
import { exportStocksToCSV } from '../utils/stockExportUtils.js'

const router = useRouter()

const taskName = ref('')
const startDate = ref('')
const endDate = ref('')
const scanPeriodDays = ref(7)
const scanConfig = ref(getDefaultScanConfig()) // 扫描配置，使用默认配置初始化
const scanConfigFormRef = ref(null) // 扫描配置表单引用

const tasks = ref([])
const loading = ref(false)
const showConfirmDialog = ref(false)
const showTaskDetailsDialog = ref(false)
const selectedTaskId = ref(null)

// 确认对话框相关
const showCancelConfirmDialog = ref(false)
const showDeleteConfirmDialog = ref(false)
const pendingTaskId = ref(null)

// 批量回测相关
const showBacktestDialog = ref(false)
const selectedTaskForBacktest = ref(null)
const backtestLoading = ref(false)
const loadingBacktestTaskId = ref(null) // 正在加载回测的任务ID
const scanResultsForBacktest = ref([])
const backtestConfig = ref({
  backtestName: '', // 回测名称
  buyStrategy: 'equal_distribution_fixed', // 默认使用固定金额平均分配策略
  initialCapital: 100000,
  useStopLoss: true,
  useTakeProfit: true,
  stopLossPercent: -1.6,
  takeProfitPercent: 16.0,
  periodStatDates: {}, // 每个周期对应的统计日 { scanDate: statDate }
  periodStatDaysOffset: 5, // 周期统计日天数偏移，回测日之后多少天，默认5天
  sellPriceType: 'close', // 卖出价格类型：'open' 开盘价，'close' 收盘价（默认）
  stopLossPercent: -1.6, // 止损百分比（负数）
  stopLossType: 'percent', // 止损类型：'percent' 固定百分比，'level' 基于支撑位
  stopLossSupportIndex: 2, // 止损使用的支撑位点位序号（1、2），默认点位2
  takeProfitPercent: 16.0, // 止盈百分比（正数）
  takeProfitType: 'percent', // 止盈类型：'percent' 固定百分比，'level' 基于压力位
  takeProfitResistanceIndex: 2 // 止盈使用的压力位点位序号（1、2），默认点位2
})

// 买入条件配置 - 平台期筛选
const availablePlatformPeriods = ref([]) // 可用的平台期列表（从所有扫描结果的股票中统计）
const selectedPlatformPeriods = ref([]) // 选中的平台期列表（默认全选）
const selectedBoards = ref(['创业板', '科创板', '主板']) // 选中的板块列表（默认选中所有板块）
const percentBRange = ref({ minPercentB: 0, maxPercentB: 1 }) // %B 范围
const selectedPercentBRange = ref({ min: null, max: null }) // 选中的 %B 范围

// 批量回测历史相关
const showBacktestHistoryDialog = ref(false)
const backtestHistoryLoading = ref(false)
const backtestHistory = ref([])
const showBacktestStatisticsDialog = ref(false)
const selectedDateRecords = ref([]) // 选中日期的记录，用于数据统计
const retryingHistoryId = ref(null)
const expandedDates = ref(new Set()) // 展开的日期集合
const showDeleteBacktestHistoryConfirmDialog = ref(false)
const pendingDeleteHistoryId = ref(null)
const deletingHistoryId = ref(null)
const showDeleteBacktestNameConfirmDialog = ref(false)
const pendingDeleteBacktestName = ref(null)
const pendingDeleteBacktestNameRecords = ref([])
const deletingBacktestName = ref(null)

// 获取回测名称（如果没有名称，返回特殊标识）
const getBacktestName = (record) => {
  if (record.backtestName && record.backtestName.trim() !== '') {
    return record.backtestName
  }
  // 没有名称的记录统一归为一个分组
  return '__NO_NAME__'
}

// 按回测名称分组的历史记录（但按日期排序）
const groupedBacktestHistory = computed(() => {
  const groups = {}
  backtestHistory.value.forEach(record => {
    const name = getBacktestName(record)
    if (!groups[name]) {
      groups[name] = []
    }
    groups[name].push(record)
  })
  
  // 对每个组内的记录按创建时间倒序排序（最新的在前）
  Object.keys(groups).forEach(name => {
    groups[name].sort((a, b) => {
      const dateA = new Date(a.createdAt)
      const dateB = new Date(b.createdAt)
      return dateB - dateA
    })
  })
  
  // 按组内第一条记录的创建时间倒序排序（最新的在前）
  const sortedGroups = {}
  Object.keys(groups).sort((a, b) => {
    const dateA = new Date(groups[a][0].createdAt)
    const dateB = new Date(groups[b][0].createdAt)
    return dateB - dateA
  }).forEach(key => {
    // 将特殊标识转换为显示名称
    const displayKey = key === '__NO_NAME__' ? '未命名回测' : key
    sortedGroups[displayKey] = groups[key]
  })
  return sortedGroups
})

// 根据回测名称获取所有记录
const getRecordsByBacktestName = (nameKey) => {
  // 如果显示名称是"未命名回测"，需要匹配所有没有名称的记录
  const targetName = nameKey === '未命名回测' ? '__NO_NAME__' : nameKey
  return backtestHistory.value.filter(record => {
    const recordName = getBacktestName(record)
    return recordName === targetName
  })
}

const maxDate = computed(() => {
  const today = new Date()
  return today.toISOString().split('T')[0]
})

// 计算当前年份的第一个周日
const getFirstSundayOfYear = () => {
  const today = new Date()
  const year = today.getFullYear()
  const firstDay = new Date(year, 0, 1) // 1月1日
  const dayOfWeek = firstDay.getDay() // 0=周日, 1=周一, ..., 6=周六
  // 如果1月1日是周日，返回1月1日；否则找到第一个周日
  const daysToAdd = dayOfWeek === 0 ? 0 : 7 - dayOfWeek
  const firstSunday = new Date(year, 0, 1 + daysToAdd)
  // 使用本地时间格式化日期，避免时区问题
  const yearStr = firstSunday.getFullYear()
  const monthStr = String(firstSunday.getMonth() + 1).padStart(2, '0')
  const dayStr = String(firstSunday.getDate()).padStart(2, '0')
  return `${yearStr}-${monthStr}-${dayStr}`
}

// 解析窗口期
const parsedWindows = computed(() => {
  // 优先从 ScanConfigForm 组件获取 parsedWindows
  if (scanConfigFormRef.value && scanConfigFormRef.value.parsedWindows) {
    return scanConfigFormRef.value.parsedWindows
  }
  
  // 如果没有组件引用，则从 scanConfig 中解析
  // 添加安全检查，确保 windowsInput 存在且有效
  const windowsInput = scanConfig.value?.windowsInput || '30,60,90'
  const windows = windowsInput
    .split(',')
    .map(w => parseInt(w.trim(), 10))
    .filter(w => !isNaN(w) && w > 0)
  
  // 如果解析结果为空，返回默认值
  if (windows.length === 0) {
    return [30, 60, 90]
  }
  
  return windows
})

const canSubmit = computed(() => {
  return taskName.value.trim() !== '' &&
    startDate.value !== '' &&
    endDate.value !== '' &&
    scanPeriodDays.value > 0 &&
    startDate.value <= endDate.value
})

const confirmMessage = computed(() => {
  if (!canSubmit.value) return ''
  
  const start = new Date(startDate.value)
  const end = new Date(endDate.value)
  const days = Math.ceil((end - start) / (1000 * 60 * 60 * 24))
  const scanCount = Math.ceil(days / scanPeriodDays.value) + 1
  
  return `
    <div class="space-y-2">
      <p><strong>任务名称:</strong> ${taskName.value}</p>
      <p><strong>时间区间:</strong> ${startDate.value} 至 ${endDate.value}</p>
      <p><strong>扫描周期:</strong> ${scanPeriodDays.value} 天</p>
      <p><strong>预计扫描次数:</strong> ${scanCount} 次</p>
      <p class="text-sm text-muted-foreground mt-2">确认提交此批量扫描任务吗？</p>
    </div>
  `
})

// 初始化默认日期
onMounted(() => {
  startDate.value = getFirstSundayOfYear()
  endDate.value = maxDate.value
  loadTasks()
  
  // 定时刷新运行中的任务
  setInterval(() => {
    const hasRunningTask = tasks.value.some(t => t.status === 'running')
    if (hasRunningTask) {
      loadTasks()
    }
  }, 5000) // 每5秒刷新一次
})

const loadTasks = async () => {
  loading.value = true
  try {
    const response = await axios.get('/platform/api/batch-scan/tasks')
    if (response.data.success) {
      tasks.value = response.data.data
    }
  } catch (error) {
    console.error('加载任务列表失败:', error)
    alert('加载任务列表失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    loading.value = false
  }
}

// 构建扫描配置 payload 的辅助函数
// 从 config 中提取所有扫描相关参数，排除不需要的字段
function buildScanPayload(config, options = {}) {
  const {
    includeScanDate = false, // 批量扫描不包含 scan_date
    windows = null // 自定义 windows（如果提供则使用，否则从 config 解析）
  } = options

  // 需要排除的字段（这些字段不应该发送到后端）
  const excludeFields = ['windowsInput', 'scan_date'] // windowsInput 需要转换为 windows 数组，scan_date 批量扫描不需要

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
  if (includeScanDate && config.scan_date) {
    payload.scan_date = config.scan_date
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

const submitTask = async () => {
  try {
    // 使用辅助函数构建扫描配置 payload
    const scanPayload = buildScanPayload(scanConfig.value, {
      includeScanDate: false, // 批量扫描不包含 scan_date
      windows: parsedWindows.value
    })
    
    // 添加批量扫描特有的字段
    const payload = {
      task_name: taskName.value,
      start_date: startDate.value,
      end_date: endDate.value,
      scan_period_days: scanPeriodDays.value,
      ...scanPayload // 合并扫描配置
    }
    
    const response = await axios.post('/platform/api/batch-scan/start', payload)
    if (response.data.task_id) {
      alert('批量扫描任务已创建并启动')
      showConfirmDialog.value = false
      loadTasks()
    }
  } catch (error) {
    console.error('提交任务失败:', error)
    alert('提交任务失败: ' + (error.response?.data?.detail || error.message))
  }
}

const cancelTask = (taskId) => {
  pendingTaskId.value = taskId
  showCancelConfirmDialog.value = true
}

const handleCancelTaskConfirm = async () => {
  const taskId = pendingTaskId.value
  if (!taskId) return
  
  try {
    await axios.post(`/platform/api/batch-scan/tasks/${taskId}/cancel`)
    alert('任务已取消')
    loadTasks()
  } catch (error) {
    console.error('取消任务失败:', error)
    alert('取消任务失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    pendingTaskId.value = null
  }
}

const deleteTask = (taskId) => {
  pendingTaskId.value = taskId
  showDeleteConfirmDialog.value = true
}

const handleDeleteTaskConfirm = async () => {
  const taskId = pendingTaskId.value
  if (!taskId) return
  
  try {
    await axios.delete(`/platform/api/batch-scan/tasks/${taskId}`)
    alert('任务已删除')
    loadTasks()
  } catch (error) {
    console.error('删除任务失败:', error)
    alert('删除任务失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    pendingTaskId.value = null
  }
}

const viewTaskDetails = (taskId) => {
  selectedTaskId.value = taskId
  showTaskDetailsDialog.value = true
}

const getStatusText = (status) => {
  const statusMap = {
    'pending': '等待中',
    'running': '进行中',
    'completed': '已完成',
    'failed': '失败',
    'cancelled': '已取消'
  }
  return statusMap[status] || status
}

const getStatusClass = (status) => {
  const classMap = {
    'pending': 'bg-yellow-500/20 text-yellow-600 dark:text-yellow-400',
    'running': 'bg-blue-500/20 text-blue-600 dark:text-blue-400',
    'completed': 'bg-green-500/20 text-green-600 dark:text-green-400',
    'failed': 'bg-red-500/20 text-red-600 dark:text-red-400',
    'cancelled': 'bg-gray-500/20 text-gray-600 dark:text-gray-400'
  }
  return classMap[status] || 'bg-gray-500/20 text-gray-600 dark:text-gray-400'
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

const formatNumber = (num, decimals = 0) => {
  if (num === null || num === undefined) return '0'
  return Number(num).toLocaleString('zh-CN', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  })
}


const handleSubmitClick = () => {
  if (!canSubmit.value) {
    alert('请填写完整的任务信息（任务名称、开始日期、结束日期、扫描周期）')
    return
  }
  showConfirmDialog.value = true
}

// 计算指定日期之后指定天数的日期
// daysOffset: 天数偏移，回测日之后多少天
const getDateAfterDays = (dateStr, daysOffset = 5) => {
  const date = new Date(dateStr)
  const targetDate = new Date(date)
  targetDate.setDate(date.getDate() + daysOffset)
  // 格式化为 YYYY-MM-DD
  const year = targetDate.getFullYear()
  const month = String(targetDate.getMonth() + 1).padStart(2, '0')
  const day = String(targetDate.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

// 计算指定日期后的第一个周五（保持向后兼容，用于其他地方）
const getNextFriday = (dateStr) => {
  const date = new Date(dateStr)
  const dayOfWeek = date.getDay() // 0=周日, 1=周一, ..., 5=周五, 6=周六
  // 计算到下一个周五需要加的天数
  let daysToAdd = 5 - dayOfWeek
  if (daysToAdd <= 0) {
    daysToAdd += 7 // 如果已经是周五或之后，加7天到下周五
  }
  const nextFriday = new Date(date)
  nextFriday.setDate(date.getDate() + daysToAdd)
  // 格式化为 YYYY-MM-DD
  const year = nextFriday.getFullYear()
  const month = String(nextFriday.getMonth() + 1).padStart(2, '0')
  const day = String(nextFriday.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

const openBacktestDialog = async (task) => {
  selectedTaskForBacktest.value = task
  scanResultsForBacktest.value = []
  backtestConfig.value.periodStatDates = {}
  backtestConfig.value.backtestName = '' // 重置回测名称
  backtestConfig.value.periodStatDaysOffset = 5 // 重置为默认5天
  availablePlatformPeriods.value = [] // 清空可用平台期
  selectedPlatformPeriods.value = [] // 清空选中的平台期
  percentBRange.value = { minPercentB: 0, maxPercentB: 1 } // 重置 %B 范围
  selectedPercentBRange.value = { min: null, max: null } // 重置选中的 %B 范围
  loadingBacktestTaskId.value = task.id
  backtestLoading.value = true
  
  try {
    // 加载扫描结果
    const response = await axios.get(`/platform/api/batch-scan/tasks/${task.id}/results`)
    if (response.data.success) {
      scanResultsForBacktest.value = response.data.data
      
      // 统计可用平台期并设置默认全选
      await updateAvailablePlatformPeriods()
      
      // 为每个周期设置默认统计日（回测日之后指定天数）
      updatePeriodStatDates()
    } else {
      alert('加载扫描结果失败: ' + (response.data.message || '未知错误'))
    }
  } catch (error) {
    console.error('加载扫描结果失败:', error)
    alert('加载扫描结果失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    backtestLoading.value = false
    loadingBacktestTaskId.value = null
  }
  
  showBacktestDialog.value = true
}

// 根据配置的天数偏移更新所有周期的统计日
const updatePeriodStatDates = () => {
  const periodStatDates = {}
  const daysOffset = backtestConfig.value.periodStatDaysOffset ?? 5
  scanResultsForBacktest.value.forEach(result => {
    const scanDate = result.scanDate
    if (scanDate) {
      periodStatDates[scanDate] = getDateAfterDays(scanDate, daysOffset)
    }
  })
  backtestConfig.value.periodStatDates = periodStatDates
}

// 统计可用平台期（从所有扫描结果的股票中提取）
async function updateAvailablePlatformPeriods() {
  const periodsSet = new Set()
  
  // 遍历所有扫描结果，加载每个结果的详情以获取股票数据
  for (const result of scanResultsForBacktest.value) {
    try {
      // 如果结果中没有完整的股票数据，需要获取详情
      let scanResult = result
      if (!result.scannedStocks || result.scannedStocks.length === 0) {
        const response = await axios.get(`/platform/api/batch-scan/results/${result.id}`)
        if (response.data.success) {
          scanResult = response.data.data
        }
      }
      
      // 从股票数据中提取平台期
      if (scanResult.scannedStocks && Array.isArray(scanResult.scannedStocks)) {
        scanResult.scannedStocks.forEach(stock => {
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
      }
    } catch (error) {
      console.warn(`加载扫描结果 ${result.id} 详情失败:`, error)
    }
  }
  
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
  
  // 计算 %B 范围（从所有股票中）
  const allStocks = []
  for (const result of scanResultsForBacktest.value) {
    try {
      let scanResult = result
      if (!result.scannedStocks || result.scannedStocks.length === 0) {
        const response = await axios.get(`/platform/api/batch-scan/results/${result.id}`)
        if (response.data.success) {
          scanResult = response.data.data
        }
      }
      if (scanResult.scannedStocks && Array.isArray(scanResult.scannedStocks)) {
        allStocks.push(...scanResult.scannedStocks)
      }
    } catch (error) {
      console.warn(`加载扫描结果 ${result.id} 详情失败:`, error)
    }
  }
  
  if (allStocks.length > 0) {
    const percentBRangeResult = calculatePercentBRange(allStocks)
    percentBRange.value = percentBRangeResult
    // 默认设置为全范围（不筛选）
    if (selectedPercentBRange.value.min === null || selectedPercentBRange.value.max === null) {
      selectedPercentBRange.value = {
        min: percentBRangeResult.minPercentB,
        max: percentBRangeResult.maxPercentB
      }
    }
  }
}

// 获取所有扫描结果中的所有股票（用于 %B 筛选）
const allStocksForBacktest = computed(() => {
  const allStocks = []
  for (const result of scanResultsForBacktest.value) {
    if (result.scannedStocks && Array.isArray(result.scannedStocks)) {
      allStocks.push(...result.scannedStocks)
    }
  }
  return allStocks
})

const canRunBatchBacktest = computed(() => {
  // 检查回测名称是否填写
  if (!backtestConfig.value.backtestName || backtestConfig.value.backtestName.trim() === '') {
    return false
  }
  // 检查所有周期是否都设置了统计日
  if (scanResultsForBacktest.value.length === 0) {
    return false
  }
  return scanResultsForBacktest.value.every(result => {
    const scanDate = result.scanDate
    return scanDate && backtestConfig.value.periodStatDates[scanDate]
  })
})

const runBatchBacktest = async () => {
  if (!canRunBatchBacktest.value) {
    if (!backtestConfig.value.backtestName || backtestConfig.value.backtestName.trim() === '') {
      alert('请填写回测名称')
    } else {
      alert('请为所有周期设置统计日')
    }
    return
  }

  if (!selectedTaskForBacktest.value) {
    alert('未选择任务')
    return
  }

  backtestLoading.value = true
  try {
    const requestData = {
      task_id: selectedTaskForBacktest.value.id,
      backtest_name: backtestConfig.value.backtestName.trim(),
      period_stat_dates: backtestConfig.value.periodStatDates,
      buy_strategy: backtestConfig.value.buyStrategy,
      initial_capital: backtestConfig.value.initialCapital,
      sell_price_type: backtestConfig.value.sellPriceType || 'close'
    }
    
    // 初始化 stock_level_prices 对象
    if (!requestData.stock_level_prices) {
      requestData.stock_level_prices = {}
    }
    
    // 处理止损设置
    if (backtestConfig.value.useStopLoss) {
      requestData.use_stop_loss = true
      if (backtestConfig.value.stopLossType === 'level') {
        // 基于支撑位的止损
        requestData.stop_loss_type = 'level'
        
        // 前端计算每只股票的支撑位价格
        const stockLevelPrices = requestData.stock_level_prices
        const stopLossIndex = backtestConfig.value.stopLossSupportIndex || 2
        
        for (const result of scanResultsForBacktest.value) {
          if (result.scannedStocks && Array.isArray(result.scannedStocks)) {
            for (const stock of result.scannedStocks) {
              const code = stock.code
              if (!stockLevelPrices[code]) {
                stockLevelPrices[code] = {}
              }
              
              // 获取支撑位数组
              let supportLevels = []
              if (stock.box_analysis && stock.box_analysis.support_levels) {
                if (Array.isArray(stock.box_analysis.support_levels)) {
                  supportLevels = stock.box_analysis.support_levels
                } else if (typeof stock.box_analysis.support_levels === 'number') {
                  supportLevels = [stock.box_analysis.support_levels]
                }
              } else if (stock.details) {
                for (const window in stock.details) {
                  if (stock.details[window] && stock.details[window].box_analysis && stock.details[window].box_analysis.support_levels) {
                    const boxAnalysis = stock.details[window].box_analysis
                    if (Array.isArray(boxAnalysis.support_levels)) {
                      supportLevels = boxAnalysis.support_levels
                    } else if (typeof boxAnalysis.support_levels === 'number') {
                      supportLevels = [boxAnalysis.support_levels]
                    }
                    break
                  }
                }
              }
              
              // 根据点位序号计算对应的价格
              if (supportLevels.length > 0) {
                const sortedSupportLevels = [...supportLevels].sort((a, b) => b - a) // 从高到低
                const index = stopLossIndex - 1
                if (sortedSupportLevels.length > index && index >= 0) {
                  stockLevelPrices[code].support_level = sortedSupportLevels[index]
                  console.log(`[止损] 股票 ${code}: 支撑位价格 = ${sortedSupportLevels[index]}, 点位序号 = ${stopLossIndex}`)
                } else {
                  console.warn(`[止损] 股票 ${code}: 支撑位数组长度(${sortedSupportLevels.length})不足，无法获取点位${stopLossIndex}`)
                }
              } else {
                console.warn(`[止损] 股票 ${code}: 未找到支撑位数据`)
              }
            }
          }
        }
      } else {
        // 基于百分比的止损
        requestData.stop_loss_type = 'percent'
        requestData.stop_loss_percent = backtestConfig.value.stopLossPercent
      }
    }
    
    // 处理止盈设置
    if (backtestConfig.value.useTakeProfit) {
      requestData.use_take_profit = true
      if (backtestConfig.value.takeProfitType === 'level') {
        // 基于压力位的止盈
        requestData.take_profit_type = 'level'
        
        // 前端计算每只股票的压力位价格
        const stockLevelPrices = requestData.stock_level_prices
        const takeProfitIndex = backtestConfig.value.takeProfitResistanceIndex || 2
        
        for (const result of scanResultsForBacktest.value) {
          if (result.scannedStocks && Array.isArray(result.scannedStocks)) {
            for (const stock of result.scannedStocks) {
              const code = stock.code
              if (!stockLevelPrices[code]) {
                stockLevelPrices[code] = {}
              }
              
              // 获取压力位数组
              let resistanceLevels = []
              if (stock.box_analysis && stock.box_analysis.resistance_levels) {
                if (Array.isArray(stock.box_analysis.resistance_levels)) {
                  resistanceLevels = stock.box_analysis.resistance_levels
                } else if (typeof stock.box_analysis.resistance_levels === 'number') {
                  resistanceLevels = [stock.box_analysis.resistance_levels]
                }
              } else if (stock.details) {
                for (const window in stock.details) {
                  if (stock.details[window] && stock.details[window].box_analysis && stock.details[window].box_analysis.resistance_levels) {
                    const boxAnalysis = stock.details[window].box_analysis
                    if (Array.isArray(boxAnalysis.resistance_levels)) {
                      resistanceLevels = boxAnalysis.resistance_levels
                    } else if (typeof boxAnalysis.resistance_levels === 'number') {
                      resistanceLevels = [boxAnalysis.resistance_levels]
                    }
                    break
                  }
                }
              }
              
              // 根据点位序号计算对应的价格
              if (resistanceLevels.length > 0) {
                const sortedResistanceLevels = [...resistanceLevels].sort((a, b) => a - b) // 从低到高
                const index = takeProfitIndex - 1
                if (sortedResistanceLevels.length > index && index >= 0) {
                  stockLevelPrices[code].resistance_level = sortedResistanceLevels[index]
                  console.log(`[止盈] 股票 ${code}: 压力位价格 = ${sortedResistanceLevels[index]}, 点位序号 = ${takeProfitIndex}`)
                } else {
                  console.warn(`[止盈] 股票 ${code}: 压力位数组长度(${sortedResistanceLevels.length})不足，无法获取点位${takeProfitIndex}`)
                }
              } else {
                console.warn(`[止盈] 股票 ${code}: 未找到压力位数据`)
              }
            }
          }
        }
      } else {
        // 基于百分比的止盈
        requestData.take_profit_type = 'percent'
        requestData.take_profit_percent = backtestConfig.value.takeProfitPercent
      }
    }
    
    // 如果设置了平台期筛选，添加平台期筛选参数
    if (selectedPlatformPeriods.value.length > 0 && selectedPlatformPeriods.value.length < availablePlatformPeriods.value.length) {
      requestData.platform_periods = selectedPlatformPeriods.value
    }
    
    // 如果设置了板块筛选，添加板块筛选参数
    if (selectedBoards.value.length > 0 && selectedBoards.value.length < 3) {
      requestData.boards = selectedBoards.value
    }
    
    // 如果设置了 %B 筛选，添加 %B 筛选参数
    if (selectedPercentBRange.value.min !== null && selectedPercentBRange.value.max !== null) {
      const minPercentB = percentBRange.value.minPercentB
      const maxPercentB = percentBRange.value.maxPercentB
      // 只有当用户设置的范围比全范围更窄时才添加筛选参数
      if (selectedPercentBRange.value.min > minPercentB || selectedPercentBRange.value.max < maxPercentB) {
        requestData.percent_b_range = {
          min: selectedPercentBRange.value.min,
          max: selectedPercentBRange.value.max
        }
      }
    }
    
    const response = await axios.post(
      `/platform/api/batch-scan/tasks/${selectedTaskForBacktest.value.id}/backtest`,
      requestData
    )

    if (response.data) {
      const result = response.data
      alert(`批量回测完成！\n总计: ${result.total}\n完成: ${result.completed}\n失败: ${result.failed}`)
      // 不关闭批量回测配置弹窗，让用户可以继续操作
      // 如果回测历史对话框已打开，刷新历史记录
      if (showBacktestHistoryDialog.value) {
        loadBacktestHistory()
      }
    }
  } catch (error) {
    console.error('批量回测失败:', error)
    alert('批量回测失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    backtestLoading.value = false
  }
}

// 打开任务的回测历史（从任务列表快捷入口）
const openTaskBacktestHistory = async (task) => {
  selectedTaskForBacktest.value = task
  showBacktestHistoryDialog.value = true
  // 默认折叠所有回测名称分组
  expandedDates.value.clear()
  await loadBacktestHistory()
}

const openBacktestHistoryDialog = async () => {
  if (!selectedTaskForBacktest.value) return
  
  showBacktestHistoryDialog.value = true
  // 默认折叠所有回测名称分组
  expandedDates.value.clear()
  await loadBacktestHistory()
}

const loadBacktestHistory = async () => {
  if (!selectedTaskForBacktest.value) return
  
  backtestHistoryLoading.value = true
  try {
    const response = await axios.get(
      `/platform/api/backtest/history?batch_task_id=${selectedTaskForBacktest.value.id}`
    )
    if (response.data.success) {
      backtestHistory.value = response.data.data || []
    } else {
      alert('加载回测历史失败: ' + (response.data.message || '未知错误'))
    }
  } catch (error) {
    console.error('加载回测历史失败:', error)
    alert('加载回测历史失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    backtestHistoryLoading.value = false
  }
}

const viewBacktestHistoryDetail = (historyId) => {
  // 跳转到回测页面并显示历史记录详情
  router.push(`/platform/backtest?historyId=${historyId}`)
}

const toggleDateExpanded = (nameKey) => {
  if (expandedDates.value.has(nameKey)) {
    expandedDates.value.delete(nameKey)
  } else {
    expandedDates.value.add(nameKey)
  }
}

// 获取日期分组的配置信息（从第一条记录获取）
const getDateConfig = (records) => {
  if (!records || records.length === 0) return null
  const firstRecord = records[0]
  return {
    useStopLoss: firstRecord.useStopLoss !== undefined ? firstRecord.useStopLoss : false,
    useTakeProfit: firstRecord.useTakeProfit !== undefined ? firstRecord.useTakeProfit : false,
    stopLossPercent: firstRecord.stopLossPercent !== undefined ? firstRecord.stopLossPercent : -1.6,
    takeProfitPercent: firstRecord.takeProfitPercent !== undefined ? firstRecord.takeProfitPercent : 16.0,
    buyStrategy: firstRecord.config?.buy_strategy || null
  }
}

// 获取买入策略的中文显示名称
const getBuyStrategyLabel = (buyStrategy) => {
  if (!buyStrategy) return ''
  switch (buyStrategy) {
    case 'fixed_amount':
      return '每只1万'
    case 'equal_distribution':
      return '累计余额'
    case 'equal_distribution_fixed':
      return '固定金额'
    default:
      return buyStrategy
  }
}

// 计算单个record的收益率（使用和BacktestStatistics.vue一样的方法）
const getRecordReturnRate = (record) => {
  if (!record || record.status === 'failed' || !record.summary) {
    return 0
  }
  
  // 使用公共函数计算收益率
  const result = calculateTotalReturnRate(record)
  return result.totalReturnRate
}

// 获取日期分组的累计收益率（使用和BacktestStatistics.vue一样的方法）
const getGroupReturnRate = (records) => {
  if (!records || records.length === 0) return null
  
  // 过滤出有收益率的记录（排除失败的记录）
  const validRecords = records.filter(record => 
    record.summary && 
    record.status !== 'failed'
  )
  
  if (validRecords.length === 0) return null
  
  // 使用公共函数计算累计收益率
  const result = calculateTotalReturnRate(validRecords)
  return result.totalReturnRate
}

// 获取日期分组的胜率（基于股票数量，与数据统计保持一致）
const getGroupWinRate = (records) => {
  if (!records || records.length === 0) return null
  
  // 统计所有股票中的盈利、亏损和平的股票数
  let profitableStocks = 0
  let lossStocks = 0
  let breakEvenStocks = 0
  
  records.forEach(record => {
    // 跳过失败的记录
    if (record.status === 'failed') return
    
    // 批量回测历史记录列表只包含summary，不包含完整的result.stockDetails
    // 需要从summary中获取股票统计信息，或者需要加载完整记录
    // 但为了性能，我们先尝试从summary中获取
    
    // 方式1: 尝试从record.result.stockDetails获取（如果API返回了完整数据）
    if (record.result && record.result.stockDetails && Array.isArray(record.result.stockDetails)) {
      record.result.stockDetails.forEach(detail => {
        const profit = detail.profit
        if (profit !== null && profit !== undefined) {
          if (profit > 0) {
            profitableStocks++
          } else if (profit < 0) {
            lossStocks++
          } else if (profit === 0) {
            breakEvenStocks++
          }
        }
      })
    }
    // 方式2: 从summary中获取（批量回测历史记录列表通常只有summary）
    else if (record.summary) {
      // summary中可能包含profitableStocks、lossStocks和breakEvenStocks字段
      const summaryProfitable = record.summary.profitableStocks
      const summaryLoss = record.summary.lossStocks
      const summaryBreakEven = record.summary.breakEvenStocks || 0
      
      if (summaryProfitable !== null && summaryProfitable !== undefined && 
          summaryLoss !== null && summaryLoss !== undefined) {
        profitableStocks += summaryProfitable
        lossStocks += summaryLoss
        breakEvenStocks += summaryBreakEven
      }
      // 如果summary中没有这些字段，无法计算准确的股票胜率
    }
  })
  
  // 计算胜率（基于股票数量）
  const totalStocks = profitableStocks + lossStocks
  if (totalStocks === 0) return null
  
  return (profitableStocks / totalStocks) * 100
}

const openAllStatistics = () => {
  // 统计全部数据
  selectedDateRecords.value = []
  showBacktestStatisticsDialog.value = true
}

const openDateStatistics = (records) => {
  // 只统计该日期下的记录
  selectedDateRecords.value = records
  showBacktestStatisticsDialog.value = true
}

const retryFailedBacktest = async (historyId) => {
  if (!selectedTaskForBacktest.value) {
    alert('未选择任务')
    return
  }
  
  if (!confirm('确定要重试这个失败的回测周期吗？')) {
    return
  }
  
  retryingHistoryId.value = historyId
  try {
    const response = await axios.post(
      `/platform/api/batch-scan/tasks/${selectedTaskForBacktest.value.id}/backtest/retry/${historyId}`
    )
    if (response.data.success) {
      alert('重试成功！')
      // 刷新历史记录
      await loadBacktestHistory()
    } else {
      alert('重试失败: ' + (response.data.message || '未知错误'))
    }
  } catch (error) {
    console.error('重试失败回测失败:', error)
    alert('重试失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    retryingHistoryId.value = null
  }
}

const showDeleteBacktestHistoryConfirm = (historyId) => {
  pendingDeleteHistoryId.value = historyId
  showDeleteBacktestHistoryConfirmDialog.value = true
}

const handleDeleteBacktestHistoryConfirm = async () => {
  const historyId = pendingDeleteHistoryId.value
  if (!historyId) return
  
  deletingHistoryId.value = historyId
  try {
    const response = await axios.delete(`/platform/api/backtest/history/${historyId}`)
    if (response.data.success) {
      // 从列表中移除
      backtestHistory.value = backtestHistory.value.filter(r => r.id !== historyId)
      alert('删除成功！')
    } else {
      alert('删除失败: ' + (response.data.message || '未知错误'))
    }
  } catch (error) {
    console.error('删除回测历史记录失败:', error)
    alert('删除失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    deletingHistoryId.value = null
    pendingDeleteHistoryId.value = null
    showDeleteBacktestHistoryConfirmDialog.value = false
  }
}

const showDeleteBacktestNameConfirm = (nameKey, records) => {
  // 确保获取所有同名称的记录（包括可能不在当前分组中的）
  const allRecords = getRecordsByBacktestName(nameKey)
  pendingDeleteBacktestName.value = nameKey
  pendingDeleteBacktestNameRecords.value = allRecords
  showDeleteBacktestNameConfirmDialog.value = true
}

const handleDeleteBacktestNameConfirm = async () => {
  const nameKey = pendingDeleteBacktestName.value
  const records = pendingDeleteBacktestNameRecords.value
  if (!nameKey || !records || records.length === 0) return
  
  deletingBacktestName.value = nameKey
  try {
    // 批量删除所有记录
    const deletePromises = records.map(record => 
      axios.delete(`/platform/api/backtest/history/${record.id}`)
    )
    
    const results = await Promise.allSettled(deletePromises)
    const successCount = results.filter(r => r.status === 'fulfilled' && r.value.data.success).length
    const failCount = results.length - successCount
    
    // 从列表中移除已成功删除的记录
    const deletedIds = results
      .map((r, index) => r.status === 'fulfilled' && r.value.data.success ? records[index].id : null)
      .filter(id => id !== null)
    
    backtestHistory.value = backtestHistory.value.filter(r => !deletedIds.includes(r.id))
    
    if (failCount === 0) {
      alert(`删除成功！已删除 ${successCount} 条记录。`)
    } else {
      alert(`部分删除成功：成功 ${successCount} 条，失败 ${failCount} 条。`)
    }
  } catch (error) {
    console.error('批量删除回测历史记录失败:', error)
    alert('删除失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    deletingBacktestName.value = null
    pendingDeleteBacktestName.value = null
    pendingDeleteBacktestNameRecords.value = []
    showDeleteBacktestNameConfirmDialog.value = false
  }
}

// 导出扫描结果为CSV
const exportScanResultsToCSV = async () => {
  if (scanResultsForBacktest.value.length === 0) {
    alert('没有可导出的扫描结果')
    return
  }

  try {
    // 收集所有股票数据
    const allStocks = []
    
    // 遍历所有扫描结果
    for (const result of scanResultsForBacktest.value) {
      const originalScanDate = result.scanDate // 原始扫描日期（用于查找统计日）
      const statDate = backtestConfig.value.periodStatDates[originalScanDate] || '' // 卖出日期（统计日）
      
      // 获取扫描结果的完整数据（如果还没有加载）
      let scanResult = result
      if (!result.scannedStocks || result.scannedStocks.length === 0) {
        try {
          const response = await axios.get(`/platform/api/batch-scan/results/${result.id}`)
          if (response.data.success) {
            scanResult = response.data.data
          }
        } catch (error) {
          console.warn(`加载扫描结果 ${result.id} 详情失败:`, error)
          continue // 跳过这个结果
        }
      }
      
      // 遍历该扫描结果中的所有股票
      if (scanResult.scannedStocks && Array.isArray(scanResult.scannedStocks)) {
        for (const stock of scanResult.scannedStocks) {
          // 为每只股票添加买入和卖出日期信息
          allStocks.push({
            stock,
            buyDate: originalScanDate, // 原始扫描日期，工具函数会自动处理周末
            sellDate: statDate
          })
        }
      }
    }
    
    if (allStocks.length === 0) {
      alert('没有可导出的股票数据')
      return
    }
    
    // 使用工具函数导出
    const result = await exportStocksToCSV(
      allStocks.map(item => item.stock),
      {
        filename: `${selectedTaskForBacktest.value?.taskName || '批量扫描'}_扫描结果.csv`,
        includeBuySellDates: true,
        getBuyDate: (stock, index) => allStocks[index].buyDate,
        getSellDate: (stock, index) => allStocks[index].sellDate
      }
    )
    
    // 显示成功消息
    alert(`成功导出 ${result.count} 条扫描结果\n\n文件名: ${result.filename}\n\n请检查浏览器的下载文件夹。\n如果未看到文件，请检查浏览器是否阻止了下载。`)
  } catch (error) {
    console.error('导出CSV失败:', error)
    alert('导出CSV失败: ' + (error.message || '未知错误'))
  }
}

// 返回上一页
function goBack() {
  // 返回到首页（扫描页面）
  router.push('/platform')
}
</script>


