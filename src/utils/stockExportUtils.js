import { extractPercentB } from './selectionReasonsParser.js'

/**
 * 将周末日期调整为下一个周一
 * @param {string} dateStr - 日期字符串 (YYYY-MM-DD)
 * @returns {string} 调整后的日期字符串
 */
export function adjustWeekendToMonday(dateStr) {
  if (!dateStr) return dateStr
  
  const date = new Date(dateStr)
  if (isNaN(date.getTime())) {
    return dateStr // 无效日期，返回原值
  }
  
  const dayOfWeek = date.getDay() // 0=周日, 1=周一, ..., 6=周六
  
  // 如果是周末（周六=6 或 周日=0），调整为下一个周一
  if (dayOfWeek === 0) {
    // 周日，加1天到周一
    date.setDate(date.getDate() + 1)
  } else if (dayOfWeek === 6) {
    // 周六，加2天到周一
    date.setDate(date.getDate() + 2)
  }
  
  // 格式化为 YYYY-MM-DD
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

/**
 * CSV值转义函数（处理包含逗号、引号或换行符的值）
 * @param {any} value - 要转义的值
 * @returns {string} 转义后的字符串
 */
export function escapeCSVValue(value) {
  if (value === null || value === undefined) {
    return ''
  }
  
  const str = String(value)
  
  // 如果值包含逗号、引号或换行符，需要用引号包裹并转义引号
  if (str.includes(',') || str.includes('"') || str.includes('\n') || str.includes('\r')) {
    return `"${str.replace(/"/g, '""')}"`
  }
  
  return str
}

/**
 * 提取 box_quality
 * @param {Object} stock - 股票对象
 * @returns {number|null} box_quality 值
 */
function extractBoxQuality(stock) {
  let boxQuality = null
  if (stock.box_analysis && stock.box_analysis.box_quality !== undefined) {
    boxQuality = stock.box_analysis.box_quality
  } else if (stock.details && typeof stock.details === 'object') {
    // 从 details 中查找最大的 box_quality
    Object.values(stock.details).forEach(windowDetail => {
      if (windowDetail && typeof windowDetail === 'object') {
        if (windowDetail.box_analysis && typeof windowDetail.box_analysis === 'object' && windowDetail.box_analysis.box_quality !== undefined) {
          const quality = windowDetail.box_analysis.box_quality
          if (typeof quality === 'number' && !isNaN(quality)) {
            if (boxQuality === null || quality > boxQuality) {
              boxQuality = quality
            }
          }
        }
        if (windowDetail.box_quality !== undefined) {
          const quality = windowDetail.box_quality
          if (typeof quality === 'number' && !isNaN(quality)) {
            if (boxQuality === null || quality > boxQuality) {
              boxQuality = quality
            }
          }
        }
      }
    })
  }
  return boxQuality
}

/**
 * 提取 windows（平台期）
 * @param {Object} stock - 股票对象
 * @returns {string} 平台期字符串（逗号分隔）
 */
function extractWindows(stock) {
  let windows = ''
  if (stock.platform_windows) {
    if (Array.isArray(stock.platform_windows) && stock.platform_windows.length > 0) {
      // 如果是数组，过滤掉无效值，排序后用逗号连接
      const validWindows = stock.platform_windows
        .filter(w => typeof w === 'number' && !isNaN(w) && w > 0)
        .sort((a, b) => a - b)
      if (validWindows.length > 0) {
        windows = validWindows.join(',')
      }
    } else if (typeof stock.platform_windows === 'string') {
      // 如果已经是字符串，直接使用
      windows = stock.platform_windows
    } else if (typeof stock.platform_windows === 'number') {
      // 如果是单个数字，转换为字符串
      windows = String(stock.platform_windows)
    }
  }
  return windows
}

/**
 * 提取支撑位
 * @param {Object} stock - 股票对象
 * @returns {string} 支撑位字符串（逗号分隔，从高到低）
 */
function extractSupportLevels(stock) {
  let supportLevels = []
  if (stock.box_analysis && stock.box_analysis.support_levels) {
    if (Array.isArray(stock.box_analysis.support_levels)) {
      supportLevels = stock.box_analysis.support_levels
    } else if (typeof stock.box_analysis.support_levels === 'number') {
      supportLevels = [stock.box_analysis.support_levels]
    }
  } else if (stock.details && typeof stock.details === 'object') {
    // 从 details 中查找支撑位
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
  // 格式化支撑位：排序后（从高到低）用逗号连接，保留2位小数
  return supportLevels.length > 0
    ? supportLevels
        .filter(level => typeof level === 'number' && !isNaN(level))
        .sort((a, b) => b - a) // 从高到低排序
        .map(level => level.toFixed(2))
        .join(',')
    : ''
}

/**
 * 提取压力位
 * @param {Object} stock - 股票对象
 * @returns {string} 压力位字符串（逗号分隔，从低到高）
 */
function extractResistanceLevels(stock) {
  let resistanceLevels = []
  if (stock.box_analysis && stock.box_analysis.resistance_levels) {
    if (Array.isArray(stock.box_analysis.resistance_levels)) {
      resistanceLevels = stock.box_analysis.resistance_levels
    } else if (typeof stock.box_analysis.resistance_levels === 'number') {
      resistanceLevels = [stock.box_analysis.resistance_levels]
    }
  } else if (stock.details && typeof stock.details === 'object') {
    // 从 details 中查找压力位
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
  // 格式化压力位：排序后（从低到高）用逗号连接，保留2位小数
  return resistanceLevels.length > 0
    ? resistanceLevels
        .filter(level => typeof level === 'number' && !isNaN(level))
        .sort((a, b) => a - b) // 从低到高排序
        .map(level => level.toFixed(2))
        .join(',')
    : ''
}

/**
 * 提取 volume_analysis 字段
 * @param {Object} stock - 股票对象
 * @returns {Object} volume_analysis 字段对象
 */
function extractVolumeAnalysis(stock) {
  let volumeAnalysis = {}
  if (stock.volume_analysis && typeof stock.volume_analysis === 'object') {
    // volume_analysis 可能是按窗口期的字典，取第一个或合并所有
    if (Array.isArray(stock.volume_analysis) || !isNaN(parseInt(Object.keys(stock.volume_analysis)[0]))) {
      // 如果是按窗口期的字典，取第一个窗口期的数据或合并
      const firstWindow = Object.keys(stock.volume_analysis)[0]
      if (firstWindow && stock.volume_analysis[firstWindow]) {
        const va = stock.volume_analysis[firstWindow]
        volumeAnalysis = {
          has_consolidation_volume: va.has_consolidation_volume !== undefined ? (va.has_consolidation_volume ? '1' : '0') : '',
          has_breakthrough: va.has_breakthrough !== undefined ? (va.has_breakthrough ? '1' : '0') : '',
          volume_change_ratio: va.consolidation_details?.volume_change_ratio !== undefined && va.consolidation_details?.volume_change_ratio !== null
            ? va.consolidation_details.volume_change_ratio.toFixed(4)
            : '',
          volume_stability: va.consolidation_details?.volume_stability !== undefined && va.consolidation_details?.volume_stability !== null
            ? va.consolidation_details.volume_stability.toFixed(4)
            : '',
          volume_trend: va.consolidation_details?.volume_trend !== undefined && va.consolidation_details?.volume_trend !== null
            ? va.consolidation_details.volume_trend.toFixed(4)
            : '',
          volume_increase_ratio: va.breakthrough_details?.volume_increase_ratio !== undefined && va.breakthrough_details?.volume_increase_ratio !== null
            ? va.breakthrough_details.volume_increase_ratio.toFixed(4)
            : ''
        }
      }
    } else {
      // 直接是对象
      volumeAnalysis = {
        has_consolidation_volume: stock.volume_analysis.has_consolidation_volume !== undefined ? (stock.volume_analysis.has_consolidation_volume ? '1' : '0') : '',
        has_breakthrough: stock.volume_analysis.has_breakthrough !== undefined ? (stock.volume_analysis.has_breakthrough ? '1' : '0') : '',
        volume_change_ratio: stock.volume_analysis.consolidation_details?.volume_change_ratio !== undefined && stock.volume_analysis.consolidation_details?.volume_change_ratio !== null
          ? stock.volume_analysis.consolidation_details.volume_change_ratio.toFixed(4)
          : '',
        volume_stability: stock.volume_analysis.consolidation_details?.volume_stability !== undefined && stock.volume_analysis.consolidation_details?.volume_stability !== null
          ? stock.volume_analysis.consolidation_details.volume_stability.toFixed(4)
          : '',
        volume_trend: stock.volume_analysis.consolidation_details?.volume_trend !== undefined && stock.volume_analysis.consolidation_details?.volume_trend !== null
          ? stock.volume_analysis.consolidation_details.volume_trend.toFixed(4)
          : '',
        volume_increase_ratio: stock.volume_analysis.breakthrough_details?.volume_increase_ratio !== undefined && stock.volume_analysis.breakthrough_details?.volume_increase_ratio !== null
          ? stock.volume_analysis.breakthrough_details.volume_increase_ratio.toFixed(4)
          : ''
      }
    }
  }
  return volumeAnalysis
}

/**
 * 提取 turnover_analysis 字段
 * @param {Object} stock - 股票对象
 * @returns {Object} turnover_analysis 字段对象
 */
function extractTurnoverAnalysis(stock) {
  let turnoverAnalysis = {}
  if (stock.turnover_analysis && typeof stock.turnover_analysis === 'object') {
    // turnover_analysis 可能是按窗口期的字典
    if (Array.isArray(stock.turnover_analysis) || !isNaN(parseInt(Object.keys(stock.turnover_analysis)[0]))) {
      const firstWindow = Object.keys(stock.turnover_analysis)[0]
      if (firstWindow && stock.turnover_analysis[firstWindow]) {
        const ta = stock.turnover_analysis[firstWindow]
        turnoverAnalysis = {
          meets_criteria: ta.meets_criteria !== undefined ? (ta.meets_criteria ? '1' : '0') : '',
          avg_turnover_rate: ta.avg_turnover_rate !== undefined && ta.avg_turnover_rate !== null
            ? ta.avg_turnover_rate.toFixed(2)
            : ta.details?.avg_turnover_rate !== undefined && ta.details?.avg_turnover_rate !== null
              ? ta.details.avg_turnover_rate.toFixed(2)
              : '',
          max_turnover_rate: ta.details?.max_turnover_rate !== undefined && ta.details?.max_turnover_rate !== null
            ? ta.details.max_turnover_rate.toFixed(2)
            : '',
          turnover_stability: ta.details?.turnover_stability !== undefined && ta.details?.turnover_stability !== null
            ? ta.details.turnover_stability.toFixed(4)
            : '',
          spike_count: ta.details?.spike_count !== undefined && ta.details?.spike_count !== null
            ? String(ta.details.spike_count)
            : ''
        }
      }
    } else {
      turnoverAnalysis = {
        meets_criteria: stock.turnover_analysis.meets_criteria !== undefined ? (stock.turnover_analysis.meets_criteria ? '1' : '0') : '',
        avg_turnover_rate: stock.turnover_analysis.avg_turnover_rate !== undefined && stock.turnover_analysis.avg_turnover_rate !== null
          ? stock.turnover_analysis.avg_turnover_rate.toFixed(2)
          : stock.turnover_analysis.details?.avg_turnover_rate !== undefined && stock.turnover_analysis.details?.avg_turnover_rate !== null
            ? stock.turnover_analysis.details.avg_turnover_rate.toFixed(2)
            : '',
        max_turnover_rate: stock.turnover_analysis.details?.max_turnover_rate !== undefined && stock.turnover_analysis.details?.max_turnover_rate !== null
          ? stock.turnover_analysis.details.max_turnover_rate.toFixed(2)
          : '',
        turnover_stability: stock.turnover_analysis.details?.turnover_stability !== undefined && stock.turnover_analysis.details?.turnover_stability !== null
          ? stock.turnover_analysis.details.turnover_stability.toFixed(4)
          : '',
        spike_count: stock.turnover_analysis.details?.spike_count !== undefined && stock.turnover_analysis.details?.spike_count !== null
          ? String(stock.turnover_analysis.details.spike_count)
          : ''
      }
    }
  }
  return turnoverAnalysis
}

/**
 * 提取技术指标（从 breakthrough_prediction）
 * @param {Object} stock - 股票对象
 * @returns {Object} 技术指标对象
 */
function extractTechnicalIndicators(stock) {
  let technicalIndicators = {
    macd_signal: '',
    rsi_signal: '',
    kdj_signal: '',
    bollinger_signal: '',
    macd_value: '',
    macd_signal_value: '',
    macd_hist: '',
    rsi_value: '',
    k_value: '',
    d_value: '',
    j_value: '',
    bb_upper: '',
    bb_middle: '',
    bb_lower: ''
  }
  if (stock.breakthrough_prediction && typeof stock.breakthrough_prediction === 'object') {
    // 提取信号（布尔值）
    if (stock.breakthrough_prediction.signals) {
      technicalIndicators.macd_signal = stock.breakthrough_prediction.signals.MACD ? '1' : '0'
      technicalIndicators.rsi_signal = stock.breakthrough_prediction.signals.RSI ? '1' : '0'
      technicalIndicators.kdj_signal = stock.breakthrough_prediction.signals.KDJ ? '1' : '0'
      technicalIndicators.bollinger_signal = stock.breakthrough_prediction.signals['布林带'] ? '1' : '0'
    }
    // 提取指标值（从 details）
    if (stock.breakthrough_prediction.details) {
      const details = stock.breakthrough_prediction.details
      if (details.MACD) {
        technicalIndicators.macd_value = details.MACD.macd !== undefined && details.MACD.macd !== null ? details.MACD.macd.toFixed(4) : ''
        technicalIndicators.macd_signal_value = details.MACD.macd_signal !== undefined && details.MACD.macd_signal !== null ? details.MACD.macd_signal.toFixed(4) : ''
        technicalIndicators.macd_hist = details.MACD.macd_hist !== undefined && details.MACD.macd_hist !== null ? details.MACD.macd_hist.toFixed(4) : ''
      }
      if (details.RSI) {
        technicalIndicators.rsi_value = details.RSI.current_rsi !== undefined && details.RSI.current_rsi !== null ? details.RSI.current_rsi.toFixed(2) : ''
      }
      if (details.KDJ) {
        technicalIndicators.k_value = details.KDJ.current_k !== undefined && details.KDJ.current_k !== null ? details.KDJ.current_k.toFixed(2) : ''
        technicalIndicators.d_value = details.KDJ.current_d !== undefined && details.KDJ.current_d !== null ? details.KDJ.current_d.toFixed(2) : ''
        technicalIndicators.j_value = details.KDJ.current_j !== undefined && details.KDJ.current_j !== null ? details.KDJ.current_j.toFixed(2) : ''
      }
      if (details['布林带']) {
        technicalIndicators.bb_upper = details['布林带'].bb_upper !== undefined && details['布林带'].bb_upper !== null ? details['布林带'].bb_upper.toFixed(2) : ''
        technicalIndicators.bb_middle = details['布林带'].bb_middle !== undefined && details['布林带'].bb_middle !== null ? details['布林带'].bb_middle.toFixed(2) : ''
        technicalIndicators.bb_lower = details['布林带'].bb_lower !== undefined && details['布林带'].bb_lower !== null ? details['布林带'].bb_lower.toFixed(2) : ''
      }
    }
  }
  return technicalIndicators
}

/**
 * 将股票数据转换为导出格式
 * @param {Object} stock - 股票对象
 * @param {Object} options - 导出选项
 * @param {string} options.buyDate - 买入日期（可选，批量扫描时使用）
 * @param {string} options.sellDate - 卖出日期（可选，批量扫描时使用）
 * @returns {Object} 导出数据对象
 */
export function convertStockToExportData(stock, options = {}) {
  const { buyDate = '', sellDate = '' } = options
  
  // 提取 box_quality
  const boxQuality = extractBoxQuality(stock)
  
  // 提取 windows（平台期）
  const windows = extractWindows(stock)
  
  // 提取 %B
  const percentB = extractPercentB(stock)
  const percentBStr = percentB !== null && typeof percentB === 'number' && !isNaN(percentB) 
    ? percentB.toFixed(4) 
    : ''
  
  // 提取支撑位
  const supportLevelsStr = extractSupportLevels(stock)
  
  // 提取压力位
  const resistanceLevelsStr = extractResistanceLevels(stock)
  
  // 提取基础信息
  const industry = stock.industry || ''
  const outperformIndex = stock.outperform_index !== null && stock.outperform_index !== undefined
    ? stock.outperform_index.toFixed(4)
    : ''
  const stockReturn = stock.stock_return !== null && stock.stock_return !== undefined
    ? stock.stock_return.toFixed(4)
    : ''
  const weightedScore = stock.weighted_score !== null && stock.weighted_score !== undefined
    ? stock.weighted_score.toFixed(4)
    : ''
  
  // 提取 has_breakthrough 和 has_breakthrough_confirmation
  const hasBreakthrough = stock.has_breakthrough !== null && stock.has_breakthrough !== undefined
    ? (stock.has_breakthrough ? '1' : '0')
    : ''
  const hasBreakthroughConfirmation = stock.has_breakthrough_confirmation !== null && stock.has_breakthrough_confirmation !== undefined
    ? (stock.has_breakthrough_confirmation ? '1' : '0')
    : ''
  
  // 提取 volume_analysis 字段
  const volumeAnalysis = extractVolumeAnalysis(stock)
  
  // 提取 turnover_analysis 字段
  const turnoverAnalysis = extractTurnoverAnalysis(stock)
  
  // 提取技术指标
  const technicalIndicators = extractTechnicalIndicators(stock)
  
  // 构建导出数据对象
  const exportData = {
    code: stock.code || '',
    name: stock.name || '',
    windows: windows,
    box_quality: boxQuality !== null && typeof boxQuality === 'number' && !isNaN(boxQuality)
      ? boxQuality.toFixed(4)
      : '',
    percentB: percentBStr,
    support_levels: supportLevelsStr,
    resistance_levels: resistanceLevelsStr,
    industry: industry,
    outperform_index: outperformIndex,
    stock_return: stockReturn,
    weighted_score: weightedScore,
    has_breakthrough: hasBreakthrough,
    has_breakthrough_confirmation: hasBreakthroughConfirmation,
    // volume_analysis 字段
    volume_has_consolidation: volumeAnalysis.has_consolidation_volume || '',
    volume_has_breakthrough: volumeAnalysis.has_breakthrough || '',
    volume_change_ratio: volumeAnalysis.volume_change_ratio || '',
    volume_stability: volumeAnalysis.volume_stability || '',
    volume_trend: volumeAnalysis.volume_trend || '',
    volume_increase_ratio: volumeAnalysis.volume_increase_ratio || '',
    // turnover_analysis 字段
    turnover_meets_criteria: turnoverAnalysis.meets_criteria || '',
    turnover_avg_rate: turnoverAnalysis.avg_turnover_rate || '',
    turnover_max_rate: turnoverAnalysis.max_turnover_rate || '',
    turnover_stability: turnoverAnalysis.turnover_stability || '',
    turnover_spike_count: turnoverAnalysis.spike_count || '',
    // 技术指标
    ...technicalIndicators
  }
  
  // 如果是批量扫描模式，添加买入和卖出日期
  if (buyDate) {
    exportData.buy_date = buyDate
  }
  if (sellDate) {
    exportData.sell_date = sellDate
  }
  
  return exportData
}

/**
 * 导出股票数据为CSV
 * @param {Array} stocks - 股票数组
 * @param {Object} options - 导出选项
 * @param {string} options.filename - 文件名（可选）
 * @param {boolean} options.includeBuySellDates - 是否包含买入卖出日期（批量扫描模式）
 * @param {Function} options.getBuyDate - 获取买入日期的函数 (stock, index) => string（可选）
 * @param {Function} options.getSellDate - 获取卖出日期的函数 (stock, index) => string（可选）
 * @returns {Promise<void>}
 */
export async function exportStocksToCSV(stocks, options = {}) {
  if (!stocks || stocks.length === 0) {
    throw new Error('没有可导出的股票数据')
  }

  const {
    filename = null,
    includeBuySellDates = false,
    getBuyDate = null,
    getSellDate = null
  } = options

  // 收集所有股票数据
  const exportData = []
  
  for (let i = 0; i < stocks.length; i++) {
    const stock = stocks[i]
    
    // 获取买入和卖出日期（如果启用）
    let buyDate = ''
    let sellDate = ''
    if (includeBuySellDates) {
      if (getBuyDate) {
        const originalBuyDate = getBuyDate(stock, i)
        buyDate = adjustWeekendToMonday(originalBuyDate)
      }
      if (getSellDate) {
        sellDate = getSellDate(stock, i) || ''
      }
    }
    
    // 转换为导出格式
    const stockExportData = convertStockToExportData(stock, {
      buyDate,
      sellDate
    })
    
    exportData.push(stockExportData)
  }
  
  if (exportData.length === 0) {
    throw new Error('没有可导出的股票数据')
  }
  
  // 生成CSV内容
  const headers = [
    'code', 'name'
  ]
  
  // 根据是否包含买入卖出日期决定表头
  if (includeBuySellDates) {
    headers.push('buy_date', 'sell_date')
  }
  
  headers.push(
    'windows', 'box_quality', '%B', 
    'support_levels', 'resistance_levels',
    'industry', 'outperform_index', 'stock_return', 'weighted_score',
    'has_breakthrough', 'has_breakthrough_confirmation',
    'volume_has_consolidation', 'volume_has_breakthrough', 'volume_change_ratio', 
    'volume_stability', 'volume_trend', 'volume_increase_ratio',
    'turnover_meets_criteria', 'turnover_avg_rate', 'turnover_max_rate', 
    'turnover_stability', 'turnover_spike_count',
    'macd_signal', 'rsi_signal', 'kdj_signal', 'bollinger_signal',
    'macd_value', 'macd_signal_value', 'macd_hist',
    'rsi_value', 'k_value', 'd_value', 'j_value',
    'bb_upper', 'bb_middle', 'bb_lower'
  )
  
  const csvRows = []
  
  // 添加表头
  csvRows.push(headers.join(','))
  
  // 添加数据行
  exportData.forEach(row => {
    const values = [
      escapeCSVValue(row.code),
      escapeCSVValue(row.name)
    ]
    
    // 根据是否包含买入卖出日期决定数据
    if (includeBuySellDates) {
      values.push(
        escapeCSVValue(row.buy_date || ''),
        escapeCSVValue(row.sell_date || '')
      )
    }
    
    values.push(
      escapeCSVValue(row.windows),
      escapeCSVValue(row.box_quality),
      escapeCSVValue(row.percentB),
      escapeCSVValue(row.support_levels),
      escapeCSVValue(row.resistance_levels),
      escapeCSVValue(row.industry),
      escapeCSVValue(row.outperform_index),
      escapeCSVValue(row.stock_return),
      escapeCSVValue(row.weighted_score),
      escapeCSVValue(row.has_breakthrough),
      escapeCSVValue(row.has_breakthrough_confirmation),
      escapeCSVValue(row.volume_has_consolidation),
      escapeCSVValue(row.volume_has_breakthrough),
      escapeCSVValue(row.volume_change_ratio),
      escapeCSVValue(row.volume_stability),
      escapeCSVValue(row.volume_trend),
      escapeCSVValue(row.volume_increase_ratio),
      escapeCSVValue(row.turnover_meets_criteria),
      escapeCSVValue(row.turnover_avg_rate),
      escapeCSVValue(row.turnover_max_rate),
      escapeCSVValue(row.turnover_stability),
      escapeCSVValue(row.turnover_spike_count),
      escapeCSVValue(row.macd_signal),
      escapeCSVValue(row.rsi_signal),
      escapeCSVValue(row.kdj_signal),
      escapeCSVValue(row.bollinger_signal),
      escapeCSVValue(row.macd_value),
      escapeCSVValue(row.macd_signal_value),
      escapeCSVValue(row.macd_hist),
      escapeCSVValue(row.rsi_value),
      escapeCSVValue(row.k_value),
      escapeCSVValue(row.d_value),
      escapeCSVValue(row.j_value),
      escapeCSVValue(row.bb_upper),
      escapeCSVValue(row.bb_middle),
      escapeCSVValue(row.bb_lower)
    )
    csvRows.push(values.join(','))
  })
  
  // 生成CSV字符串
  const csvContent = csvRows.join('\n')
  
  // 添加BOM以支持中文（UTF-8 with BOM）
  const BOM = '\uFEFF'
  const blob = new Blob([BOM + csvContent], { type: 'text/csv;charset=utf-8;' })
  
  // 创建下载链接
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.style.display = 'none' // 隐藏链接
  
  // 生成文件名
  let finalFilename = filename
  if (!finalFilename) {
    const date = new Date()
    const dateStr = `${date.getFullYear()}${String(date.getMonth() + 1).padStart(2, '0')}${String(date.getDate()).padStart(2, '0')}`
    finalFilename = includeBuySellDates 
      ? `批量扫描结果_${dateStr}.csv`
      : `平台股扫描结果_${dateStr}.csv`
  }
  
  // 清理文件名中的特殊字符
  const cleanFilename = finalFilename.replace(/[/\\:*?"<>|]/g, '_').trim()
  link.download = cleanFilename
  
  // 添加到DOM并触发下载
  document.body.appendChild(link)
  
  // 触发下载
  link.click()
  
  // 延迟清理，确保下载开始（给浏览器足够时间开始下载）
  setTimeout(() => {
    try {
      document.body.removeChild(link)
      URL.revokeObjectURL(url)
    } catch (e) {
      console.warn('清理下载链接时出错:', e)
    }
  }, 200)
  
  return {
    count: exportData.length,
    filename: cleanFilename
  }
}

