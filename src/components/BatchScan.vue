<template>
  <div class="min-h-screen bg-background text-foreground p-4">
    <div class="max-w-6xl mx-auto">
      <!-- 页面标题 -->
      <div class="mb-6">
        <h1 class="text-2xl font-bold flex items-center">
          <i class="fas fa-tasks mr-2 text-primary"></i>
          批量扫描
        </h1>
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
            :config="scanConfig"
            :show-scan-date="false"
            :window-weights="windowWeights"
            :parsed-windows="parsedWindows"
            @update:config="scanConfig = $event"
            @update-window-weights="updateWindowWeights"
            @show-tutorial="showParameterTutorial"
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

    <!-- 参数教程 -->
    <ParameterTutorial
      v-model:visible="showTutorialDialog"
      :parameter-id="tutorialParameterId"
    />

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
                      <span class="text-xs text-muted-foreground">
                        {{ result.stockCount }} 只股票
                      </span>
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
                        默认值：回测日后的第一个周五
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
                stop-loss-placeholder="-2"
                take-profit-placeholder="18"
              />

              <div class="p-3 bg-blue-500/10 border border-blue-500/20 rounded-lg">
                <p class="text-sm text-blue-700 dark:text-blue-400">
                  <i class="fas fa-info-circle mr-1"></i>
                  回测将使用每个周期的开始日（扫描日期）作为回测日，每个周期可以单独设置统计日（默认为回测日后的第一个周五）。
                </p>
              </div>
            </div>
          </div>
        </div>
        <div class="p-4 sm:p-6 border-t border-border flex justify-end gap-2">
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
                    <span v-if="getDateConfig(group).useStopLoss" class="flex items-center">
                      <i class="fas fa-arrow-down mr-1 text-blue-600 dark:text-blue-400"></i>
                      止损: {{ getDateConfig(group).stopLossPercent }}%
                    </span>
                    <span v-if="getDateConfig(group).useTakeProfit" class="flex items-center">
                      <i class="fas fa-arrow-up mr-1 text-red-600 dark:text-red-400"></i>
                      止盈: {{ getDateConfig(group).takeProfitPercent }}%
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
                        <span :class="record.summary?.totalReturnRate >= 0 ? 'text-red-600 dark:text-red-400' : 'text-blue-600 dark:text-blue-400'">
                          {{ record.summary?.totalReturnRate >= 0 ? '+' : '' }}{{ record.summary?.totalReturnRate?.toFixed(2) || '0.00' }}%
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
import ParameterTutorial from './parameter-help/ParameterTutorial.vue'
import TaskDetails from './batch-scan/TaskDetails.vue'
import BacktestStatistics from './BacktestStatistics.vue'
import BuySellStrategy from './BuySellStrategy.vue'

const router = useRouter()

const taskName = ref('')
const startDate = ref('')
const endDate = ref('')
const scanPeriodDays = ref(7)
const scanConfig = ref({
  windowsInput: '30,60,90',
  expected_count: 30,
  box_threshold: 0.3,
  ma_diff_threshold: 0.25,
  volatility_threshold: 0.4,
  use_volume_analysis: true,
  volume_change_threshold: 0.5,
  volume_stability_threshold: 0.5,
  volume_increase_threshold: 1.5,
  use_technical_indicators: false,
  use_breakthrough_prediction: true,
  use_low_position: true,
  high_point_lookback_days: 365,
  decline_period_days: 180,
  decline_threshold: 0.3,
  use_rapid_decline_detection: true,
  rapid_decline_days: 30,
  rapid_decline_threshold: 0.15,
  use_breakthrough_confirmation: true,
  breakthrough_confirmation_days: 1,
  use_box_detection: true,
  box_quality_threshold: 0.9,
  use_fundamental_filter: false,
  revenue_growth_percentile: 0.3,
  profit_growth_percentile: 0.3,
  roe_percentile: 0.3,
  liability_percentile: 0.3,
  pe_percentile: 0.7,
  pb_percentile: 0.7,
  fundamental_years_to_check: 3,
  use_window_weights: true,
  window_weights: {},
  use_scan_cache: false,
  max_stock_count: null,
  use_local_database_first: true
})

const tasks = ref([])
const loading = ref(false)
const showConfirmDialog = ref(false)
const showTaskDetailsDialog = ref(false)
const selectedTaskId = ref(null)
const showTutorialDialog = ref(false)
const tutorialParameterId = ref('')

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
  buyStrategy: 'equal_distribution', // 默认使用平均分配策略
  initialCapital: 100000,
  useStopLoss: true,
  useTakeProfit: true,
  stopLossPercent: -2.0,
  takeProfitPercent: 18.0,
  periodStatDates: {} // 每个周期对应的统计日 { scanDate: statDate }
})

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

// 窗口权重
const windowWeights = ref({})
const parsedWindows = computed(() => {
  const windows = scanConfig.value.windowsInput
    .split(',')
    .map(w => parseInt(w.trim(), 10))
    .filter(w => !isNaN(w) && w > 0)
  
  return windows
})

// 更新窗口权重
const updateWindowWeights = (window, value) => {
  if (window !== undefined && value !== undefined) {
    windowWeights.value[window] = parseInt(value, 10)
  }
  
  // 归一化权重
  const weights = {}
  let total = 0
  
  // 计算总和
  for (const [key, val] of Object.entries(windowWeights.value)) {
    if (parsedWindows.value.includes(parseInt(key, 10))) {
      total += val
    }
  }
  
  // 归一化
  if (total > 0) {
    for (const [key, val] of Object.entries(windowWeights.value)) {
      if (parsedWindows.value.includes(parseInt(key, 10))) {
        weights[key] = val / total
      }
    }
  }
  
  // 更新配置
  scanConfig.value.window_weights = weights
}

// 监听窗口期变化，初始化窗口权重
watch(parsedWindows, (newWindows) => {
  newWindows.forEach(window => {
    if (windowWeights.value[window] === undefined) {
      windowWeights.value[window] = 5 // 默认权重
    }
  })
  // 移除不在窗口列表中的权重
  Object.keys(windowWeights.value).forEach(key => {
    if (!newWindows.includes(parseInt(key, 10))) {
      delete windowWeights.value[key]
    }
  })
  // 更新配置中的窗口权重
  updateWindowWeights()
}, { immediate: true })

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

const submitTask = async () => {
  try {
    // 构建扫描配置
    const windows = scanConfig.value.windowsInput.split(',').map(w => parseInt(w.trim())).filter(w => !isNaN(w))
    // 使用已归一化的窗口权重
    const windowWeights = scanConfig.value.window_weights || {}
    
    const payload = {
      task_name: taskName.value,
      start_date: startDate.value,
      end_date: endDate.value,
      scan_period_days: scanPeriodDays.value,
      windows: windows,
      expected_count: scanConfig.value.expected_count,
      box_threshold: scanConfig.value.box_threshold,
      ma_diff_threshold: scanConfig.value.ma_diff_threshold,
      volatility_threshold: scanConfig.value.volatility_threshold,
      use_volume_analysis: scanConfig.value.use_volume_analysis,
      volume_change_threshold: scanConfig.value.volume_change_threshold,
      volume_stability_threshold: scanConfig.value.volume_stability_threshold,
      volume_increase_threshold: scanConfig.value.volume_increase_threshold,
      use_technical_indicators: scanConfig.value.use_technical_indicators,
      use_breakthrough_prediction: scanConfig.value.use_breakthrough_prediction,
      use_low_position: scanConfig.value.use_low_position,
      high_point_lookback_days: scanConfig.value.high_point_lookback_days,
      decline_period_days: scanConfig.value.decline_period_days,
      decline_threshold: scanConfig.value.decline_threshold,
      use_rapid_decline_detection: scanConfig.value.use_rapid_decline_detection,
      rapid_decline_days: scanConfig.value.rapid_decline_days,
      rapid_decline_threshold: scanConfig.value.rapid_decline_threshold,
      use_breakthrough_confirmation: scanConfig.value.use_breakthrough_confirmation,
      breakthrough_confirmation_days: scanConfig.value.breakthrough_confirmation_days,
      use_box_detection: scanConfig.value.use_box_detection,
      box_quality_threshold: scanConfig.value.box_quality_threshold,
      use_fundamental_filter: scanConfig.value.use_fundamental_filter,
      revenue_growth_percentile: scanConfig.value.revenue_growth_percentile,
      profit_growth_percentile: scanConfig.value.profit_growth_percentile,
      roe_percentile: scanConfig.value.roe_percentile,
      liability_percentile: scanConfig.value.liability_percentile,
      pe_percentile: scanConfig.value.pe_percentile,
      pb_percentile: scanConfig.value.pb_percentile,
      fundamental_years_to_check: scanConfig.value.fundamental_years_to_check,
      use_window_weights: scanConfig.value.use_window_weights,
      window_weights: windowWeights,
      use_scan_cache: scanConfig.value.use_scan_cache !== undefined ? scanConfig.value.use_scan_cache : true,
      max_stock_count: scanConfig.value.max_stock_count && scanConfig.value.max_stock_count > 0 ? scanConfig.value.max_stock_count : null,
      use_local_database_first: scanConfig.value.use_local_database_first !== undefined ? scanConfig.value.use_local_database_first : true
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

const showParameterTutorial = (parameterId) => {
  tutorialParameterId.value = parameterId
  showTutorialDialog.value = true
}

const handleSubmitClick = () => {
  if (!canSubmit.value) {
    alert('请填写完整的任务信息（任务名称、开始日期、结束日期、扫描周期）')
    return
  }
  showConfirmDialog.value = true
}

// 计算指定日期后的第一个周五
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
  loadingBacktestTaskId.value = task.id
  backtestLoading.value = true
  
  try {
    // 加载扫描结果
    const response = await axios.get(`/platform/api/batch-scan/tasks/${task.id}/results`)
    if (response.data.success) {
      scanResultsForBacktest.value = response.data.data
      
      // 为每个周期设置默认统计日（回测日后的第一个周五）
      const periodStatDates = {}
      scanResultsForBacktest.value.forEach(result => {
        const scanDate = result.scanDate
        if (scanDate) {
          periodStatDates[scanDate] = getNextFriday(scanDate)
        }
      })
      backtestConfig.value.periodStatDates = periodStatDates
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
    const response = await axios.post(
      `/platform/api/batch-scan/tasks/${selectedTaskForBacktest.value.id}/backtest`,
      {
        task_id: selectedTaskForBacktest.value.id,
        backtest_name: backtestConfig.value.backtestName.trim(),
        period_stat_dates: backtestConfig.value.periodStatDates,
        buy_strategy: backtestConfig.value.buyStrategy,
        initial_capital: backtestConfig.value.initialCapital,
        use_stop_loss: backtestConfig.value.useStopLoss,
        use_take_profit: backtestConfig.value.useTakeProfit,
        stop_loss_percent: backtestConfig.value.stopLossPercent,
        take_profit_percent: backtestConfig.value.takeProfitPercent
      }
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
    stopLossPercent: firstRecord.stopLossPercent !== undefined ? firstRecord.stopLossPercent : -2.0,
    takeProfitPercent: firstRecord.takeProfitPercent !== undefined ? firstRecord.takeProfitPercent : 18.0
  }
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
</script>


