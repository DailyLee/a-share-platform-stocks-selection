/**
 * 计算整体收益率的公共工具函数
 * 与 BacktestStatistics.vue 中的计算方法保持一致
 */

/**
 * 计算单个或多个回测记录的整体收益率
 * @param {Array|Object} recordsOrRecord - 回测记录数组或单个记录，每个记录应包含 config 和 result.summary
 * @returns {Object} - 包含 totalReturnRate, totalInvestment, totalProfit 的对象
 */
export function calculateTotalReturnRate(recordsOrRecord) {
  // 统一转换为数组
  const records = Array.isArray(recordsOrRecord) ? recordsOrRecord : [recordsOrRecord]
  
  if (!records || records.length === 0) {
    return {
      totalReturnRate: 0,
      totalInvestment: 0,
      totalProfit: 0
    }
  }

  // 获取策略类型
  const buyStrategy = records[0]?.config?.buy_strategy || null
  
  // 计算总投入和总收益
  let totalInvestment = 0
  let totalProfit = 0
  
  // 对于 equal_distribution_fixed 和 equal_distribution 策略，需要计算额外投入资金
  if (buyStrategy === 'equal_distribution_fixed' || buyStrategy === 'equal_distribution') {
    let cumulativeAdditionalInvestment = 0  // 累计额外投入
    let cumulativeProfit = 0  // 累计收益
    
    records.forEach((record, index) => {
      const config = record.config || {}
      const summary = record.result?.summary || {}
      
      // 获取该周期的收益
      const periodProfit = summary.totalProfit || 0
      cumulativeProfit += periodProfit
      
      if (index === 0) {
        // 第一个周期：额外投入 = 总投入
        const periodInvestment = summary.totalInvestment || 0
        cumulativeAdditionalInvestment = periodInvestment
        totalInvestment = periodInvestment
      } else {
        // 后续周期：根据策略计算额外投入
        if (buyStrategy === 'equal_distribution_fixed') {
          // 固定金额策略：额外投入 = max(0, 固定金额 - 累计结算余额)
          const fixedCapital = config.initial_capital !== undefined && config.initial_capital !== null
            ? config.initial_capital
            : 100000
          const cumulativeSettlementBalance = cumulativeAdditionalInvestment + cumulativeProfit
          const periodAdditionalInvestment = Math.max(0, fixedCapital - cumulativeSettlementBalance)
          cumulativeAdditionalInvestment += periodAdditionalInvestment
          totalInvestment += periodAdditionalInvestment
        } else if (buyStrategy === 'equal_distribution') {
          // 累计余额策略：后续周期没有额外投入
          // totalInvestment 不变（保持第一个周期的投入）
        }
      }
      
      totalProfit += periodProfit
    })
    
    // 重新计算总投入（基于额外投入资金）
    if (buyStrategy === 'equal_distribution_fixed') {
      totalInvestment = cumulativeAdditionalInvestment
    } else if (buyStrategy === 'equal_distribution') {
      // 累计余额策略：总投入就是第一个周期的投入（已经在上面设置了）
    }
  } else {
    // 其他策略：直接累加总投入和总收益
    records.forEach(record => {
      const summary = record.result?.summary || {}
      totalInvestment += summary.totalInvestment || 0
      totalProfit += summary.totalProfit || 0
    })
  }

  // 计算整体收益率
  let totalReturnRate = 0
  if (totalInvestment > 0) {
    totalReturnRate = (totalProfit / totalInvestment) * 100
  }

  return {
    totalReturnRate,
    totalInvestment,
    totalProfit
  }
}

