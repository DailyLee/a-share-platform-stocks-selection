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
            <input
              :id="`stopLossPercent-${uniqueId}`"
              :value="modelValue.stopLossPercent"
              @input="handleNumberInput('stopLossPercent', $event)"
              type="number"
              step="0.1"
              min="-100"
              max="0"
              class="input w-24"
              :placeholder="stopLossPlaceholder"
            />
            <span class="text-sm text-muted-foreground">%</span>
            <p v-if="showHelpText" class="text-xs text-muted-foreground ml-2">
              (负数，例如：-3 表示下跌3%时止损)
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
      stopLossPercent: -2.0,
      takeProfitPercent: 18.0
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
    default: '-2'
  },
  // 止盈占位符
  takeProfitPlaceholder: {
    type: String,
    default: '18'
  }
})

const emit = defineEmits(['update:modelValue'])

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
</script>

