/**
 * 从 selection_reasons 字符串中解析指标的公共工具函数
 */

/**
 * 从选择理由字符串中提取数值
 * @param {string} reason - 选择理由字符串
 * @param {string} key - 要提取的键名（如"价格区间"、"均线收敛"等）
 * @param {boolean} returnString - 是否返回字符串格式（默认false，返回数字）
 * @returns {number|string|null} - 提取的数值或字符串，如果未找到返回null
 */
export function extractValue(reason, key, returnString = false) {
  if (!reason || typeof reason !== 'string') return returnString ? '' : null
  // 匹配 "价格区间0.20" 或 "价格区间: 0.20" 格式
  const regex = new RegExp(`${key}[：:]?\\s*([\\d.]+)`)
  const match = reason.match(regex)
  if (!match) return returnString ? '' : null
  return returnString ? match[1].trim() : parseFloat(match[1])
}

/**
 * 从选择理由字符串中提取文本值
 * @param {string} reason - 选择理由字符串
 * @param {string} key - 要提取的键名
 * @returns {string} - 提取的文本值
 */
export function extractTextValue(reason, key) {
  if (!reason || typeof reason !== 'string') return ''
  // 匹配 "标准模式: 低位+快速下跌后形成平台期" 格式
  const regex = new RegExp(`${key}[：:]?\\s*([^,，]+)`)
  const match = reason.match(regex)
  return match ? match[1].trim() : ''
}

/**
 * 提取价格区间（从所有平台期的 selection_reasons 中取最小值）
 * @param {Object} selectionReasons - selection_reasons 对象，键为平台期，值为理由字符串
 * @returns {number|null} - 价格区间的最小值，如果未找到返回null
 */
export function extractBoxRange(selectionReasons) {
  if (!selectionReasons || typeof selectionReasons !== 'object') return null
  const values = []
  Object.values(selectionReasons).forEach(reason => {
    if (typeof reason === 'string') {
      const value = extractValue(reason, '价格区间', false)
      if (value !== null) {
        values.push(value)
      }
    }
  })
  return values.length > 0 ? Math.min(...values) : null
}

/**
 * 提取均线收敛（从所有平台期的 selection_reasons 中取最小值）
 * @param {Object} selectionReasons - selection_reasons 对象
 * @returns {number|null} - 均线收敛的最小值，如果未找到返回null
 */
export function extractMaDiff(selectionReasons) {
  if (!selectionReasons || typeof selectionReasons !== 'object') return null
  const values = []
  Object.values(selectionReasons).forEach(reason => {
    if (typeof reason === 'string') {
      const value = extractValue(reason, '均线收敛', false)
      if (value !== null) {
        values.push(value)
      }
    }
  })
  return values.length > 0 ? Math.min(...values) : null
}

/**
 * 提取波动率（从所有平台期的 selection_reasons 中取最小值）
 * @param {Object} selectionReasons - selection_reasons 对象
 * @returns {number|null} - 波动率的最小值，如果未找到返回null
 */
export function extractVolatility(selectionReasons) {
  if (!selectionReasons || typeof selectionReasons !== 'object') return null
  const values = []
  Object.values(selectionReasons).forEach(reason => {
    if (typeof reason === 'string') {
      const value = extractValue(reason, '波动率', false)
      if (value !== null) {
        values.push(value)
      }
    }
  })
  return values.length > 0 ? Math.min(...values) : null
}

/**
 * 提取低位判断百分比（从高点下跌的百分比）
 * @param {Object} selectionReasons - selection_reasons 对象
 * @returns {number|null} - 从高点下跌的百分比，如果未找到返回null
 */
export function extractLowPositionPercent(selectionReasons) {
  if (!selectionReasons || typeof selectionReasons !== 'object') return null
  const values = []
  Object.values(selectionReasons).forEach(reason => {
    if (typeof reason === 'string') {
      // 匹配 "从高点下跌XX%" 格式
      const match = reason.match(/从高点下跌([\d.]+)%/)
      if (match) {
        const percent = parseFloat(match[1])
        if (!isNaN(percent)) {
          values.push(percent)
        }
      }
    }
  })
  return values.length > 0 ? Math.max(...values) : null // 取最大值，表示最大跌幅
}

/**
 * 提取快速下跌百分比
 * @param {Object} selectionReasons - selection_reasons 对象
 * @returns {number|null} - 快速下跌的百分比，如果未找到返回null
 */
export function extractRapidDeclinePercent(selectionReasons) {
  if (!selectionReasons || typeof selectionReasons !== 'object') return null
  const values = []
  Object.values(selectionReasons).forEach(reason => {
    if (typeof reason === 'string') {
      // 匹配 "快速下跌XX%" 格式
      const match = reason.match(/快速下跌[：:]?\s*([\d.]+)%/)
      if (match) {
        const percent = parseFloat(match[1])
        if (!isNaN(percent)) {
          values.push(percent)
        }
      }
    }
  })
  return values.length > 0 ? Math.max(...values) : null // 取最大值，表示最大跌幅
}

/**
 * 提取低位判断（检查是否有"低位"关键词）- 保留用于向后兼容
 * @param {Object} selectionReasons - selection_reasons 对象
 * @returns {boolean|null} - 如果找到"低位"返回true，如果未找到返回null（用于区分"没有数据"和"不是低位"）
 */
export function extractIsLowPosition(selectionReasons) {
  if (!selectionReasons || typeof selectionReasons !== 'object') return null
  for (const reason of Object.values(selectionReasons)) {
    if (typeof reason === 'string' && reason.includes('低位')) {
      return true
    }
  }
  return false
}

/**
 * 提取快速下跌（检查是否有"快速下跌"关键词）- 保留用于向后兼容
 * @param {Object} selectionReasons - selection_reasons 对象
 * @returns {boolean|null} - 如果找到"快速下跌"返回true，如果未找到返回null
 */
export function extractHasRapidDecline(selectionReasons) {
  if (!selectionReasons || typeof selectionReasons !== 'object') return null
  for (const reason of Object.values(selectionReasons)) {
    if (typeof reason === 'string' && reason.includes('快速下跌')) {
      return true
    }
  }
  return false
}

/**
 * 提取低位判断信息（格式化字符串，用于显示）
 * @param {string} reason - 选择理由字符串
 * @returns {string} - 格式化的低位信息字符串
 */
export function extractLowPositionInfo(reason) {
  if (!reason || typeof reason !== 'string') return ''
  const declineMatch = reason.match(/从高点下跌([\d.]+)%/)
  const dateMatch = reason.match(/高点日期([\d-]+)/)
  const parts = []
  if (declineMatch) {
    parts.push(`从高点下跌${declineMatch[1]}%`)
  }
  if (dateMatch) {
    parts.push(`高点日期: ${dateMatch[1]}`)
  }
  return parts.length > 0 ? parts.join('，') : ''
}

/**
 * 提取快速下跌信息（格式化字符串，用于显示）
 * @param {string} reason - 选择理由字符串
 * @returns {string} - 格式化的快速下跌信息字符串
 */
export function extractRapidDeclineInfo(reason) {
  if (!reason || typeof reason !== 'string') return ''
  const match = reason.match(/快速下跌[：:]?\s*([\d.]+)%\s*\(([^)]+)\)/)
  if (match) {
    return `${match[1]}% (${match[2]})`
  }
  return ''
}

/**
 * 提取突破前兆信息（格式化字符串，用于显示）
 * @param {string} reason - 选择理由字符串
 * @returns {string} - 格式化的突破前兆信息字符串
 */
export function extractBreakthroughInfo(reason) {
  if (!reason || typeof reason !== 'string') return ''
  const match = reason.match(/突破前兆[：:]?\s*(\d+)个指标\s*\(([^)]+)\)/)
  if (match) {
    return `${match[1]}个指标 (${match[2]})`
  }
  return ''
}

/**
 * 计算布林带指标
 * @param {Array} klineData - K线数据数组，每个元素包含 close 价格
 * @param {number} period - 周期，默认20
 * @param {number} stdDev - 标准差倍数，默认2.0
 * @returns {Object|null} - 包含 bb_upper, bb_middle, bb_lower 的对象，如果数据不足返回null
 */
function calculateBollingerBands(klineData, period = 20, stdDev = 2.0) {
  if (!klineData || !Array.isArray(klineData) || klineData.length < period) {
    return null
  }
  
  // 获取最近 period 天的收盘价
  const closes = klineData.slice(-period).map(item => {
    const close = item.close
    return typeof close === 'number' && !isNaN(close) ? close : null
  }).filter(close => close !== null)
  
  if (closes.length < period) {
    return null
  }
  
  // 计算移动平均（中轨）
  const sum = closes.reduce((acc, val) => acc + val, 0)
  const bb_middle = sum / period
  
  // 计算标准差（使用样本标准差，除以 n-1，与后端 pandas 默认行为保持一致）
  const variance = closes.reduce((acc, val) => acc + Math.pow(val - bb_middle, 2), 0) / (period - 1)
  const std = Math.sqrt(variance)
  
  // 计算上轨和下轨
  const bb_upper = bb_middle + (std * stdDev)
  const bb_lower = bb_middle - (std * stdDev)
  
  return {
    bb_upper,
    bb_middle,
    bb_lower
  }
}

/**
 * 从股票数据中提取 %B (Percent B) 值
 * %B = (收盘价 - 布林下轨) / (布林上轨 - 布林下轨)
 * @param {Object} stock - 股票对象，包含 kline_data
 * @returns {number|null} - %B 值，如果无法计算返回null
 */
export function extractPercentB(stock) {
  if (!stock || !stock.kline_data || !Array.isArray(stock.kline_data) || stock.kline_data.length === 0) {
    return null
  }
  
  // 计算布林带（使用默认参数：周期20，标准差2.0）
  const bb = calculateBollingerBands(stock.kline_data, 20, 2.0)
  if (!bb) {
    return null
  }
  
  // 获取最新收盘价
  const lastKline = stock.kline_data[stock.kline_data.length - 1]
  const close = lastKline?.close
  if (typeof close !== 'number' || isNaN(close)) {
    return null
  }
  
  // 计算 %B
  const bandWidth = bb.bb_upper - bb.bb_lower
  if (bandWidth === 0) {
    // 如果带宽为0，返回0.5（中位）
    return 0.5
  }
  
  const percentB = (close - bb.bb_lower) / bandWidth
  
  return percentB
}

/**
 * 计算股票列表中 %B 的最小值和最大值
 * @param {Array} stocks - 股票对象数组
 * @returns {Object} - 包含 minPercentB 和 maxPercentB 的对象
 */
export function calculatePercentBRange(stocks) {
  if (!stocks || !Array.isArray(stocks) || stocks.length === 0) {
    return { minPercentB: 0, maxPercentB: 1 }
  }
  
  const percentBs = []
  stocks.forEach(stock => {
    const percentB = extractPercentB(stock)
    if (percentB !== null && typeof percentB === 'number' && !isNaN(percentB) && isFinite(percentB)) {
      percentBs.push(percentB)
    }
  })
  
  if (percentBs.length === 0) {
    return { minPercentB: 0, maxPercentB: 1 }
  }
  
  return {
    minPercentB: Math.min(...percentBs),
    maxPercentB: Math.max(...percentBs)
  }
}

