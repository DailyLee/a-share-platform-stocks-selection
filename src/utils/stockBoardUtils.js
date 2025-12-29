/**
 * 股票板块工具函数
 */

/**
 * 判断股票代码所属的板块
 * @param {string} code - 股票代码，格式如 'sz.300001' 或 'sh.688001'
 * @returns {string|null} - '创业板' | '科创板' | '主板' | null
 */
export function getStockBoard(code) {
  if (!code || typeof code !== 'string') {
    return null
  }
  
  // 提取数字部分（去掉交易所前缀）
  const codeNum = code.split('.').pop() || code
  
  // 创业板：300开头
  if (codeNum.startsWith('300')) {
    return '创业板'
  }
  
  // 科创板：688开头
  if (codeNum.startsWith('688')) {
    return '科创板'
  }
  
  // 其他为主板
  return '主板'
}

/**
 * 判断股票是否是创业板
 * @param {string} code - 股票代码
 * @returns {boolean}
 */
export function isChiNext(code) {
  return getStockBoard(code) === '创业板'
}

/**
 * 判断股票是否是科创板
 * @param {string} code - 股票代码
 * @returns {boolean}
 */
export function isSTAR(code) {
  return getStockBoard(code) === '科创板'
}

/**
 * 判断股票是否是主板
 * @param {string} code - 股票代码
 * @returns {boolean}
 */
export function isMainBoard(code) {
  return getStockBoard(code) === '主板'
}

