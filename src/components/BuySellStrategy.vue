<template>
  <div>
    <!-- 买入策略 -->
    <div class="mb-6">
      <h3 class="text-sm font-medium mb-3 flex items-center">
        <i class="fas fa-shopping-cart mr-2 text-primary"></i>
        买入策略
      </h3>
      <div class="bg-muted/30 p-4 rounded-md space-y-3">
        <div class="flex items-center space-x-2">
          <input
            type="radio"
            :id="`buyStrategy1-${uniqueId}`"
            :checked="modelValue.buyStrategy === 'fixed_amount'"
            @change="updateBuyStrategy('fixed_amount')"
            class="radio"
          />
          <label :for="`buyStrategy1-${uniqueId}`" class="text-sm">
            根据扫描结果，每只当日开盘价买入1万元
          </label>
        </div>
        <div class="flex items-center space-x-2">
          <input
            type="radio"
            :id="`buyStrategy2-${uniqueId}`"
            :checked="modelValue.buyStrategy === 'equal_distribution'"
            @change="updateBuyStrategy('equal_distribution')"
            class="radio"
          />
          <label :for="`buyStrategy2-${uniqueId}`" class="text-sm">
            设置初始资金，每次平均买入每个股票（下个周期的资金是上个周期的结算余额）
          </label>
        </div>
        <div v-if="modelValue.buyStrategy === 'equal_distribution'" class="ml-6 mt-2 flex items-center space-x-2">
          <label :for="`initialCapital-${uniqueId}`" class="text-sm text-muted-foreground whitespace-nowrap">初始资金：</label>
          <input
            :id="`initialCapital-${uniqueId}`"
            :value="modelValue.initialCapital"
            @input="handleNumberInput('initialCapital', $event)"
            type="number"
            step="1000"
            min="1000"
            class="input w-32"
            placeholder="100000"
          />
          <span class="text-sm text-muted-foreground">元</span>
          <p v-if="showHelpText" class="text-xs text-muted-foreground ml-2">
            (每个周期平均分配资金买入所有股票，下个周期使用上期结算余额)
          </p>
        </div>
        <div class="flex items-center space-x-2">
          <input
            type="radio"
            :id="`buyStrategy3-${uniqueId}`"
            :checked="modelValue.buyStrategy === 'equal_distribution_fixed'"
            @change="updateBuyStrategy('equal_distribution_fixed')"
            class="radio"
          />
          <label :for="`buyStrategy3-${uniqueId}`" class="text-sm">
            设置初始资金，每个周期都用这个固定的金额平均购买股票
          </label>
        </div>
        <div v-if="modelValue.buyStrategy === 'equal_distribution_fixed'" class="ml-6 mt-2 flex items-center space-x-2">
          <label :for="`initialCapitalFixed-${uniqueId}`" class="text-sm text-muted-foreground whitespace-nowrap">初始资金：</label>
          <input
            :id="`initialCapitalFixed-${uniqueId}`"
            :value="modelValue.initialCapital"
            @input="handleNumberInput('initialCapital', $event)"
            type="number"
            step="1000"
            min="1000"
            class="input w-32"
            placeholder="100000"
          />
          <span class="text-sm text-muted-foreground">元</span>
          <p v-if="showHelpText" class="text-xs text-muted-foreground ml-2">
            (每个周期都用固定金额平均分配资金买入所有股票，不累计余额)
          </p>
        </div>
      </div>
    </div>

    <!-- 买入条件配置 -->
    <div v-if="showBuyConditions && availablePlatformPeriods && availablePlatformPeriods.length > 0" class="mb-6">
      <h3 class="text-sm font-medium mb-3 flex items-center">
        <i class="fas fa-filter mr-2 text-primary"></i>
        买入条件配置
      </h3>
      <div class="bg-muted/30 p-4 rounded-md">
        <!-- 平台期筛选 -->
        <div>
          <label class="block text-sm font-medium mb-2">
            <i class="fas fa-calendar-week mr-1 text-primary"></i>
            平台期筛选
          </label>
          <p class="text-xs text-muted-foreground mb-2">
            只买入选中平台期的股票，不选中的平台期中的股票不参与买入
          </p>
          <div class="flex flex-wrap gap-2 mb-2">
            <label 
              v-for="period in availablePlatformPeriods" 
              :key="period"
              class="flex items-center cursor-pointer px-2 py-1 rounded border border-border hover:bg-muted/50 transition-colors"
              :class="selectedPlatformPeriods.includes(period) ? 'bg-primary/20 border-primary' : ''"
            >
              <input
                type="checkbox"
                :value="period"
                :checked="selectedPlatformPeriods.includes(period)"
                @change="handlePlatformPeriodChange(period, $event.target.checked)"
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
          <p class="text-xs text-muted-foreground">
            已选择 {{ selectedPlatformPeriods.length }} / {{ availablePlatformPeriods.length }} 个平台期
          </p>
        </div>

        <!-- 板块筛选 -->
        <div class="mt-4">
          <label class="block text-sm font-medium mb-2">
            <i class="fas fa-building mr-1 text-primary"></i>
            板块筛选
          </label>
          <p class="text-xs text-muted-foreground mb-2">
            只买入选中板块的股票，不选中的板块中的股票不参与买入
          </p>
          <div class="flex flex-wrap gap-2 mb-2">
            <label 
              class="flex items-center cursor-pointer px-2 py-1 rounded border border-border hover:bg-muted/50 transition-colors"
              :class="selectedBoards.includes('创业板') ? 'bg-primary/20 border-primary' : ''"
            >
              <input
                type="checkbox"
                value="创业板"
                :checked="selectedBoards.includes('创业板')"
                @change="handleBoardChange('创业板', $event.target.checked)"
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
                :checked="selectedBoards.includes('科创板')"
                @change="handleBoardChange('科创板', $event.target.checked)"
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
                :checked="selectedBoards.includes('主板')"
                @change="handleBoardChange('主板', $event.target.checked)"
                class="checkbox mr-1.5"
              />
              <span class="text-xs">主板</span>
            </label>
            <button
              @click="selectAllBoards"
              class="px-2 py-1 text-xs rounded border border-border hover:bg-muted/50 transition-colors"
            >
              全选
            </button>
            <button
              @click="clearBoardFilter"
              class="px-2 py-1 text-xs rounded border border-border hover:bg-muted/50 transition-colors"
            >
              清空
            </button>
          </div>
          <p class="text-xs text-muted-foreground">
            已选择 {{ selectedBoards.length }} / 3 个板块
          </p>
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
              :id="`sellStrategyStopLoss-${uniqueId}`"
              :checked="modelValue.useStopLoss"
              @change="updateField('useStopLoss', $event.target.checked)"
              class="checkbox"
            />
            <label :for="`sellStrategyStopLoss-${uniqueId}`" class="text-sm">
              止损
            </label>
          </div>
          <div v-if="modelValue.useStopLoss" class="ml-6 flex items-center space-x-2">
            <label :for="`stopLossPercent-${uniqueId}`" class="text-sm text-muted-foreground whitespace-nowrap">百分比：</label>
            <div class="flex items-center">
              <span class="text-sm text-muted-foreground mr-1">-</span>
              <input
                :id="`stopLossPercent-${uniqueId}`"
                :value="Math.abs(modelValue.stopLossPercent)"
                @input="handleStopLossInput($event)"
                type="number"
                step="0.1"
                min="0"
                max="100"
                class="input w-24"
                :placeholder="stopLossPlaceholder ? Math.abs(parseFloat(stopLossPlaceholder) || 2) : '2'"
              />
            </div>
            <span class="text-sm text-muted-foreground">%</span>
            <p v-if="showHelpText" class="text-xs text-muted-foreground ml-2">
              (只需输入数字，系统自动转换为负数，例如：输入 3 表示下跌3%时止损)
            </p>
          </div>
        </div>
        
        <!-- 止盈设置 -->
        <div class="space-y-2">
          <div class="flex items-center space-x-2">
            <input
              type="checkbox"
              :id="`sellStrategyTakeProfit-${uniqueId}`"
              :checked="modelValue.useTakeProfit"
              @change="updateField('useTakeProfit', $event.target.checked)"
              class="checkbox"
            />
            <label :for="`sellStrategyTakeProfit-${uniqueId}`" class="text-sm">
              止盈
            </label>
          </div>
          <div v-if="modelValue.useTakeProfit" class="ml-6 flex items-center space-x-2">
            <label :for="`takeProfitPercent-${uniqueId}`" class="text-sm text-muted-foreground whitespace-nowrap">百分比：</label>
            <input
              :id="`takeProfitPercent-${uniqueId}`"
              :value="modelValue.takeProfitPercent"
              @input="handleNumberInput('takeProfitPercent', $event)"
              type="number"
              step="0.1"
              min="0"
              max="1000"
              class="input w-24"
              :placeholder="takeProfitPlaceholder"
            />
            <span class="text-sm text-muted-foreground">%</span>
            <p v-if="showHelpText" class="text-xs text-muted-foreground ml-2">
              (正数，例如：10 表示上涨10%时止盈)
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  modelValue: {
    type: Object,
    required: true,
    default: () => ({
      buyStrategy: 'equal_distribution_fixed', // 默认使用固定金额平均分配策略
      initialCapital: 100000,
      useStopLoss: true,
      useTakeProfit: true,
      stopLossPercent: -1.6,
      takeProfitPercent: 16.0
    })
  },
  // 用于生成唯一的ID，避免多个实例冲突
  uniqueId: {
    type: String,
    default: () => Math.random().toString(36).substr(2, 9)
  },
  // 是否显示帮助文本
  showHelpText: {
    type: Boolean,
    default: false
  },
  // 止损占位符
  stopLossPlaceholder: {
    type: String,
    default: '-1.6'
  },
  // 止盈占位符
  takeProfitPlaceholder: {
    type: String,
    default: '16'
  },
  // 是否显示买入条件配置
  showBuyConditions: {
    type: Boolean,
    default: false
  },
  // 可用的平台期列表（从股票中统计）
  availablePlatformPeriods: {
    type: Array,
    default: () => []
  },
  // 选中的平台期列表（默认全选）
  selectedPlatformPeriods: {
    type: Array,
    default: () => []
  },
  // 选中的板块列表（默认选中所有板块）
  selectedBoards: {
    type: Array,
    default: () => ['创业板', '科创板', '主板']
  }
})

const emit = defineEmits(['update:modelValue', 'update:selectedPlatformPeriods', 'update:selectedBoards'])

const updateBuyStrategy = (value) => {
  emit('update:modelValue', {
    ...props.modelValue,
    buyStrategy: value
  })
}

const updateField = (field, value) => {
  emit('update:modelValue', {
    ...props.modelValue,
    [field]: value
  })
}

const handleNumberInput = (field, event) => {
  const value = event.target.value
  if (value === '') {
    // 如果输入为空，保持原值
    return
  }
  const numValue = parseFloat(value)
  if (!isNaN(numValue)) {
    updateField(field, numValue)
  }
}

// 专门处理止损百分比输入：用户只需输入正数，自动转换为负数
const handleStopLossInput = (event) => {
  const value = event.target.value
  if (value === '') {
    // 如果输入为空，保持原值
    return
  }
  const numValue = parseFloat(value)
  if (!isNaN(numValue) && numValue >= 0) {
    // 将正数转换为负数
    updateField('stopLossPercent', -numValue)
  }
}

// 处理平台期选择变化
const handlePlatformPeriodChange = (period, checked) => {
  const newSelected = [...props.selectedPlatformPeriods]
  if (checked) {
    if (!newSelected.includes(period)) {
      newSelected.push(period)
    }
  } else {
    const index = newSelected.indexOf(period)
    if (index > -1) {
      newSelected.splice(index, 1)
    }
  }
  emit('update:selectedPlatformPeriods', newSelected)
}

// 全选平台期
const selectAllPlatformPeriods = () => {
  emit('update:selectedPlatformPeriods', [...props.availablePlatformPeriods])
}

// 清空平台期筛选
const clearPlatformPeriodFilter = () => {
  emit('update:selectedPlatformPeriods', [])
}

// 处理板块选择变化
const handleBoardChange = (board, checked) => {
  const newSelected = [...props.selectedBoards]
  if (checked) {
    if (!newSelected.includes(board)) {
      newSelected.push(board)
    }
  } else {
    const index = newSelected.indexOf(board)
    if (index > -1) {
      newSelected.splice(index, 1)
    }
  }
  emit('update:selectedBoards', newSelected)
}

// 全选板块
const selectAllBoards = () => {
  emit('update:selectedBoards', ['创业板', '科创板', '主板'])
}

// 清空板块筛选
const clearBoardFilter = () => {
  emit('update:selectedBoards', [])
}
</script>

