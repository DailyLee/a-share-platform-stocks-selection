/**
 * 扫描配置默认值
 * 用于统一管理扫描工具的默认配置参数
 */

/**
 * 获取默认扫描配置
 * @returns {Object} 默认配置对象
 */
export function getDefaultScanConfig() {
  return {
    // 扫描日期
    scan_date: new Date().toISOString().split('T')[0], // 扫描日期，默认为今天
    
    // 基本参数
    windowsInput: '30,60,90', // 中期窗口期设置（默认）
    expected_count: 30, // 期望返回的股票数量，默认为30

    // 价格参数
    box_threshold: 0.3, // 箱体阈值
    ma_diff_threshold: 0.03, // 均线粘合度阈值
    volatility_threshold: 0.03, // 波动率阈值

    // 成交量参数
    use_volume_analysis: true, // 是否启用成交量分析
    volume_change_threshold: 0.5, // 成交量变化阈值
    volume_stability_threshold: 0.5, // 成交量稳定性阈值
    volume_increase_threshold: 1.5, // 成交量突破阈值

    // 技术指标参数
    use_technical_indicators: false, // 是否启用技术指标
    use_breakthrough_prediction: true, // 是否启用突破前兆识别

    // 位置参数
    use_low_position: true, // 是否启用低位判断
    high_point_lookback_days: 365, // 高点查找时间范围
    decline_period_days: 180, // 下跌时间范围
    decline_threshold: 0.3, // 下跌阈值

    // 快速下跌判断参数
    use_rapid_decline_detection: true, // 是否启用快速下跌判断
    rapid_decline_days: 30, // 快速下跌窗口
    rapid_decline_threshold: 0.15, // 快速下跌阈值

    // 突破确认参数
    use_breakthrough_confirmation: true, // 是否启用突破确认
    breakthrough_confirmation_days: 1, // 确认天数，默认为1天，这样启用时不需要手动修改

    // 箱体检测参数
    use_box_detection: true, // 是否启用箱体检测
    box_quality_threshold: 0.94, // 箱体质量阈值

    // 进入平台期后的换手率参数
    max_turnover_rate: 5.0, // 平台期平均换手率不超过
    allow_turnover_spikes: true, // 是否允许偶尔的异常放量

    // 进入平台期后的相对强度参数
    check_relative_strength: true, // 启用相对大盘强度检查（计算并保存相对强度值）
    outperform_index_threshold: null, // 相对强度阈值，null表示不过滤（计算并保存但不作为筛选条件）

    // 基本面筛选参数
    use_fundamental_filter: false, // 是否启用基本面筛选
    revenue_growth_percentile: 0.3, // 营收增长率行业百分位
    profit_growth_percentile: 0.3, // 净利润增长率行业百分位
    roe_percentile: 0.3, // ROE行业百分位
    liability_percentile: 0.3, // 资产负债率行业百分位
    pe_percentile: 0.7, // PE行业百分位
    pb_percentile: 0.7, // PB行业百分位
    fundamental_years_to_check: 3, // 检查连续增长的年数

    // 窗口权重参数
    use_window_weights: true, // 是否使用窗口权重
    window_weights: {}, // 窗口权重
    
    // 系统设置
    use_scan_cache: false, // 是否使用扫描结果缓存，默认为关闭
    max_stock_count: null, // 扫描股票数量限制，null或0表示全量扫描
    use_local_database_first: true // 优先使用本地数据库数据，默认为开启
  }
}

