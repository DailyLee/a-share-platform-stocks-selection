<template>
  <div>
    <div v-if="loading" class="text-center py-8">
      <i class="fas fa-spinner fa-spin text-2xl text-primary"></i>
      <p class="text-muted-foreground mt-2">加载中...</p>
    </div>

    <div v-else-if="task">
      <!-- 任务基本信息 -->
      <div class="mb-6">
        <h3 class="text-md font-semibold mb-3">任务信息</h3>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <span class="text-sm text-muted-foreground">任务名称:</span>
            <p class="font-medium">{{ task.taskName }}</p>
          </div>
          <div>
            <span class="text-sm text-muted-foreground">状态:</span>
            <span :class="['px-2 py-1 rounded text-xs font-medium ml-2', getStatusClass(task.status)]">
              {{ getStatusText(task.status) }}
            </span>
          </div>
          <div>
            <span class="text-sm text-muted-foreground">时间区间:</span>
            <p class="font-medium">{{ task.startDate }} 至 {{ task.endDate }}</p>
          </div>
          <div>
            <span class="text-sm text-muted-foreground">扫描周期:</span>
            <p class="font-medium">{{ task.scanPeriodDays }} 天</p>
          </div>
          <div>
            <span class="text-sm text-muted-foreground">进度:</span>
            <p class="font-medium">{{ task.completedScans }}/{{ task.totalScans }} ({{ task.progress }}%)</p>
          </div>
          <div>
            <span class="text-sm text-muted-foreground">失败次数:</span>
            <p class="font-medium">{{ task.failedScans }}</p>
          </div>
          <div v-if="task.currentScanDate">
            <span class="text-sm text-muted-foreground">当前扫描日期:</span>
            <p class="font-medium">{{ task.currentScanDate }}</p>
          </div>
          <div v-if="task.message">
            <span class="text-sm text-muted-foreground">消息:</span>
            <p class="font-medium">{{ task.message }}</p>
          </div>
          <div v-if="task.error">
            <span class="text-sm text-muted-foreground">错误信息:</span>
            <p class="font-medium text-red-600 dark:text-red-400">{{ task.error }}</p>
          </div>
        </div>
      </div>

      <!-- 扫描参数配置（可折叠） -->
      <div class="mb-6">
        <button
          @click="showScanConfig = !showScanConfig"
          class="w-full flex items-center justify-between mb-3 hover:opacity-80 transition-opacity"
        >
          <h3 class="text-md font-semibold">扫描参数配置</h3>
          <i 
            :class="['fas transition-transform', showScanConfig ? 'fa-chevron-up' : 'fa-chevron-down']"
          ></i>
        </button>
        <div v-show="showScanConfig" class="bg-muted/30 rounded-lg p-4">
          <pre class="text-xs overflow-auto">{{ JSON.stringify(task.scanConfig, null, 2) }}</pre>
        </div>
      </div>

      <!-- 扫描结果列表 -->
      <div>
        <h3 class="text-md font-semibold mb-3">扫描结果</h3>
        <div v-if="resultsLoading" class="text-center py-4">
          <i class="fas fa-spinner fa-spin text-xl text-primary"></i>
        </div>
        <div v-else-if="results.length === 0" class="text-center py-8 text-muted-foreground">
          暂无扫描结果
        </div>
        <div v-else class="space-y-3">
          <div
            v-for="result in results"
            :key="result.id"
            class="border border-border rounded-lg p-4 hover:bg-muted/30 transition-colors"
          >
            <div class="flex justify-between items-start">
              <div class="flex-1">
                <div class="flex items-center mb-2">
                  <h4 class="font-medium mr-2">{{ result.scanDate }}</h4>
                  <span class="text-sm text-muted-foreground">
                    ({{ result.stockCount }} 只股票)
                  </span>
                </div>
                <div class="text-sm text-muted-foreground space-y-1">
                  <div>
                    <i class="fas fa-chart-line mr-1"></i>
                    扫描数量: {{ result.totalScanned }}
                  </div>
                  <div>
                    <i class="fas fa-check-circle mr-1"></i>
                    成功数量: {{ result.successCount }}
                  </div>
                  <div>
                    <i class="fas fa-clock mr-1"></i>
                    创建时间: {{ formatDate(result.createdAt) }}
                  </div>
                </div>
              </div>
              <button
                @click="viewResult(result.id)"
                class="btn btn-secondary px-3 py-1 text-sm ml-4"
              >
                <i class="fas fa-eye mr-1"></i>
                查看详情
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="text-center py-8 text-muted-foreground">
      任务不存在
    </div>

    <!-- 结果详情对话框 -->
    <div
      v-if="showResultDetail"
      class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
    >
      <div class="bg-card border border-border rounded-lg shadow-lg max-w-6xl w-full max-h-[90vh] overflow-hidden flex flex-col" @click.stop>
        <div class="p-4 sm:p-6 border-b border-border">
          <div class="flex justify-between items-center">
            <h2 class="text-lg font-semibold">扫描结果详情 - {{ selectedResult?.scanDate }}</h2>
            <button
              @click="showResultDetail = false"
              class="text-muted-foreground hover:text-foreground"
            >
              <i class="fas fa-times text-xl"></i>
            </button>
          </div>
        </div>
        <div class="flex-1 overflow-auto p-4 sm:p-6">
          <div v-if="selectedResult">
            <div class="mb-4 grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div>
                <span class="text-sm text-muted-foreground">扫描日期:</span>
                <p class="font-medium">{{ selectedResult.scanDate }}</p>
              </div>
              <div>
                <span class="text-sm text-muted-foreground">扫描数量:</span>
                <p class="font-medium">{{ selectedResult.totalScanned }}</p>
              </div>
              <div>
                <span class="text-sm text-muted-foreground">成功数量:</span>
                <p class="font-medium">{{ selectedResult.successCount }}</p>
              </div>
              <div>
                <span class="text-sm text-muted-foreground">股票数量:</span>
                <p class="font-medium">{{ selectedResult.stockCount }}</p>
              </div>
              <div>
                <span class="text-sm text-muted-foreground">创建时间:</span>
                <p class="font-medium">{{ formatDate(selectedResult.createdAt) }}</p>
              </div>
            </div>
            
            <div v-if="selectedResult.scannedStocks && selectedResult.scannedStocks.length > 0" class="mt-4">
              <h3 class="text-md font-semibold mb-3">扫描到的股票 ({{ selectedResult.scannedStocks.length }} 只)</h3>
              <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                <div
                  v-for="stock in selectedResult.scannedStocks"
                  :key="stock.code"
                  class="border border-border rounded-lg p-3 hover:bg-muted/30 transition-colors"
                >
                  <div class="font-medium">{{ stock.name }}</div>
                  <div class="text-sm text-muted-foreground">{{ stock.code }}</div>
                  <div v-if="stock.industry" class="text-xs text-muted-foreground mt-1">
                    {{ stock.industry }}
                  </div>
                </div>
              </div>
            </div>
            <div v-else class="text-center py-8 text-muted-foreground">
              本次扫描未找到符合条件的股票
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import axios from 'axios'

const props = defineProps({
  taskId: {
    type: String,
    required: true
  }
})

const emit = defineEmits(['close'])

const task = ref(null)
const results = ref([])
const loading = ref(true)
const resultsLoading = ref(false)
const showScanConfig = ref(false) // 扫描参数配置折叠状态
const showResultDetail = ref(false) // 结果详情对话框显示状态
const selectedResult = ref(null) // 选中的结果

const loadTask = async () => {
  loading.value = true
  try {
    const response = await axios.get(`/platform/api/batch-scan/tasks/${props.taskId}`)
    if (response.data.success) {
      task.value = response.data.data
      loadResults()
    }
  } catch (error) {
    console.error('加载任务详情失败:', error)
    alert('加载任务详情失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    loading.value = false
  }
}

const loadResults = async () => {
  resultsLoading.value = true
  try {
    const response = await axios.get(`/platform/api/batch-scan/tasks/${props.taskId}/results`)
    if (response.data.success) {
      results.value = response.data.data
    }
  } catch (error) {
    console.error('加载扫描结果失败:', error)
  } finally {
    resultsLoading.value = false
  }
}

const viewResult = async (resultId) => {
  // 加载结果详情并在对话框中显示
  try {
    const response = await axios.get(`/platform/api/batch-scan/results/${resultId}`)
    if (response.data.success) {
      selectedResult.value = response.data.data
      showResultDetail.value = true
    }
  } catch (error) {
    console.error('加载结果详情失败:', error)
    alert('加载结果详情失败: ' + (error.response?.data?.detail || error.message))
  }
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

watch(() => props.taskId, () => {
  if (props.taskId) {
    loadTask()
  }
}, { immediate: true })

onMounted(() => {
  if (props.taskId) {
    loadTask()
  }
  
  // 如果任务正在运行，定时刷新
  const interval = setInterval(() => {
    if (task.value && task.value.status === 'running') {
      loadTask()
    } else {
      clearInterval(interval)
    }
  }, 3000)
  
  // 组件卸载时清除定时器
  return () => clearInterval(interval)
})
</script>

