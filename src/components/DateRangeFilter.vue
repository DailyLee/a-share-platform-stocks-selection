<template>
  <div class="flex flex-wrap items-center gap-3">
    <!-- 年度筛选 -->
    <div class="flex items-center space-x-2">
      <label class="text-sm text-muted-foreground whitespace-nowrap">
        <i class="fas fa-filter mr-1"></i>
        年度：
      </label>
      <select
        :value="selectedYear"
        @change="handleYearChange"
        class="input text-sm px-3 py-1.5 min-w-[120px]"
      >
        <option value="">全部年度</option>
        <option v-for="year in availableYears" :key="year" :value="year">
          {{ year }}年
        </option>
      </select>
    </div>
    <!-- 季度筛选 -->
    <div class="flex items-center space-x-2" v-if="selectedYear">
      <label class="text-sm text-muted-foreground whitespace-nowrap">
        季度：
      </label>
      <select
        :value="selectedQuarter"
        @change="handleQuarterChange"
        class="input text-sm px-3 py-1.5 min-w-[120px]"
      >
        <option value="">全部季度</option>
        <option v-for="quarter in availableQuarters" :key="quarter" :value="quarter">
          {{ quarter }}
        </option>
      </select>
    </div>
    <!-- 月度筛选 -->
    <div class="flex items-center space-x-2" v-if="selectedYear">
      <label class="text-sm text-muted-foreground whitespace-nowrap">
        月度：
      </label>
      <select
        :value="selectedMonth"
        @change="handleMonthChange"
        class="input text-sm px-3 py-1.5 min-w-[120px]"
      >
        <option value="">全部月度</option>
        <option v-for="month in availableMonths" :key="month" :value="month">
          {{ month }}月
        </option>
      </select>
    </div>
    <!-- 查询按钮 -->
    <button
      @click="handleQuery"
      :disabled="loading"
      class="px-4 py-1.5 rounded-md bg-primary text-primary-foreground hover:bg-primary/80 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm flex items-center"
    >
      <i class="fas fa-search mr-2"></i>
      查询
    </button>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  // 已加载的数据列表（用于计算可用的年度/季度/月度）
  data: {
    type: Array,
    default: () => []
  },
  // 数据中的日期字段名（用于提取日期）
  dateField: {
    type: String,
    default: 'scanDate' // 或 'backtestDate'
  },
  // 加载状态
  loading: {
    type: Boolean,
    default: false
  },
  // 默认选中的年度
  defaultYear: {
    type: String,
    default: null
  },
  // 默认选中的季度
  defaultQuarter: {
    type: String,
    default: null
  }
})

const emit = defineEmits(['query', 'year-change', 'quarter-change', 'month-change'])

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

// 初始化默认值
const currentQuarter = getCurrentQuarter()
const selectedYear = ref(props.defaultYear || currentQuarter.year)
const selectedQuarter = ref(props.defaultQuarter || currentQuarter.quarter)
const selectedMonth = ref('')

// 获取可用的年度列表
const availableYears = computed(() => {
  const years = new Set()
  
  // 从已加载的数据中提取年度
  props.data.forEach(record => {
    const date = record[props.dateField] || ''
    if (date && date !== '未知日期') {
      const year = date.substring(0, 4)
      if (year && /^\d{4}$/.test(year)) {
        years.add(year)
      }
    }
  })
  
  // 如果当前年度不在列表中，添加当前年度（确保至少有一个选项）
  const currentYear = currentQuarter.year
  if (!years.has(currentYear)) {
    years.add(currentYear)
  }
  
  // 如果列表为空，至少添加当前年度和最近几年
  if (years.size === 0) {
    const now = new Date()
    const currentYearNum = now.getFullYear()
    for (let i = 0; i < 3; i++) {
      years.add((currentYearNum - i).toString())
    }
  }
  
  return Array.from(years).sort((a, b) => b.localeCompare(a))
})

// 获取可用的季度列表（基于选中的年度）
const availableQuarters = computed(() => {
  if (!selectedYear.value) {
    return []
  }
  const quarters = new Set()
  
  // 从已加载的数据中提取季度
  props.data.forEach(record => {
    const date = record[props.dateField] || ''
    if (date && date !== '未知日期' && date.startsWith(selectedYear.value)) {
      const month = parseInt(date.substring(5, 7))
      if (month >= 1 && month <= 12) {
        const quarter = Math.ceil(month / 3)
        quarters.add(`Q${quarter}`)
      }
    }
  })
  
  // 如果是当前年度，确保当前季度在列表中
  if (selectedYear.value === currentQuarter.year) {
    quarters.add(currentQuarter.quarter)
  }
  
  // 如果列表为空，至少添加所有季度选项
  if (quarters.size === 0) {
    quarters.add('Q1')
    quarters.add('Q2')
    quarters.add('Q3')
    quarters.add('Q4')
  }
  
  return Array.from(quarters).sort()
})

// 获取可用的月度列表（基于选中的年度和季度）
const availableMonths = computed(() => {
  if (!selectedYear.value) {
    return []
  }
  const months = new Set()
  let targetMonths = []
  
  // 如果选择了季度，只显示该季度的月份
  if (selectedQuarter.value) {
    const quarterNum = parseInt(selectedQuarter.value.substring(1))
    if (quarterNum === 1) targetMonths = [1, 2, 3]
    else if (quarterNum === 2) targetMonths = [4, 5, 6]
    else if (quarterNum === 3) targetMonths = [7, 8, 9]
    else if (quarterNum === 4) targetMonths = [10, 11, 12]
  } else {
    // 如果没有选择季度，显示该年度所有月份
    targetMonths = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
  }
  
  // 从已加载的数据中提取月份
  props.data.forEach(record => {
    const date = record[props.dateField] || ''
    if (date && date !== '未知日期' && date.startsWith(selectedYear.value)) {
      const month = parseInt(date.substring(5, 7))
      if (month >= 1 && month <= 12 && targetMonths.includes(month)) {
        months.add(month)
      }
    }
  })
  
  // 如果列表为空，至少显示目标月份范围内的所有月份
  if (months.size === 0) {
    targetMonths.forEach(month => months.add(month))
  }
  
  return Array.from(months).sort((a, b) => a - b)
})

// 根据筛选条件计算日期范围
function calculateDateRange() {
  // 如果没有选择年度，使用当前季度（默认）
  if (!selectedYear.value) {
    const year = parseInt(currentQuarter.year)
    const quarterNum = currentQuarter.quarterNum
    
    let startMonth = (quarterNum - 1) * 3 + 1
    let endMonth = quarterNum * 3
    
    const startDate = `${year}-${String(startMonth).padStart(2, '0')}-01`
    // 计算结束日期（季度最后一天）
    const endDateObj = new Date(year, endMonth, 0)
    const endDate = `${year}-${String(endMonth).padStart(2, '0')}-${String(endDateObj.getDate()).padStart(2, '0')}`
    
    return { startDate, endDate, useCurrentQuarter: true }
  }
  
  const year = parseInt(selectedYear.value)
  let startMonth = 1
  let endMonth = 12
  
  // 如果选择了季度
  if (selectedQuarter.value) {
    const quarterNum = parseInt(selectedQuarter.value.substring(1))
    startMonth = (quarterNum - 1) * 3 + 1
    endMonth = quarterNum * 3
  }
  
  // 如果选择了月份
  if (selectedMonth.value) {
    startMonth = parseInt(selectedMonth.value)
    endMonth = parseInt(selectedMonth.value)
  }
  
  const startDate = `${year}-${String(startMonth).padStart(2, '0')}-01`
  // 计算结束日期（月份最后一天）
  const endDateObj = new Date(year, endMonth, 0)
  const endDate = `${year}-${String(endMonth).padStart(2, '0')}-${String(endDateObj.getDate()).padStart(2, '0')}`
  
  return { startDate, endDate, useCurrentQuarter: false }
}

// 处理年度变化
function handleYearChange(event) {
  selectedYear.value = event.target.value
  selectedQuarter.value = ''
  selectedMonth.value = ''
  emit('year-change', selectedYear.value)
}

// 处理季度变化
function handleQuarterChange(event) {
  selectedQuarter.value = event.target.value
  selectedMonth.value = ''
  emit('quarter-change', selectedQuarter.value)
}

// 处理月度变化
function handleMonthChange(event) {
  selectedMonth.value = event.target.value
  emit('month-change', selectedMonth.value)
}

// 处理查询
function handleQuery() {
  const dateRange = calculateDateRange()
  emit('query', {
    year: selectedYear.value,
    quarter: selectedQuarter.value,
    month: selectedMonth.value,
    ...dateRange
  })
}

// 暴露方法供父组件调用
defineExpose({
  selectedYear,
  selectedQuarter,
  selectedMonth,
  calculateDateRange,
  reset: () => {
    const current = getCurrentQuarter()
    selectedYear.value = current.year
    selectedQuarter.value = current.quarter
    selectedMonth.value = ''
  }
})
</script>

