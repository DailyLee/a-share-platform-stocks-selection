"""
Configuration module for stock platform scanner.
"""
from typing import Dict, Any, List
from pydantic import BaseModel, Field


class ScanConfig(BaseModel):
    """Configuration model for stock platform scanner."""
    # Window settings - 基于安记食品平台期分析的最佳参数组合
    windows: List[int] = Field(default_factory=lambda: [
                               80, 100, 120])  # 使用安记食品平台期的最佳参数

    # Price pattern thresholds - 适合识别安记食品类型的平台期
    box_threshold: float = 0.3  # 降低箱体阈值
    ma_diff_threshold: float = 0.25  # 增加MA差异阈值
    volatility_threshold: float = 0.4  # 增加波动率阈值

    # Volume analysis settings - 适合识别安记食品类型的平台期
    use_volume_analysis: bool = True
    # Maximum volume change ratio for consolidation
    volume_change_threshold: float = 0.5  # 降低成交量变化阈值
    # Maximum volume stability for consolidation
    volume_stability_threshold: float = 0.5  # 降低成交量稳定性要求
    # Minimum volume increase ratio for breakthrough
    volume_increase_threshold: float = 1.5

    # Technical indicators
    use_technical_indicators: bool = False  # Whether to use technical indicators
    # Whether to use breakthrough prediction
    use_breakthrough_prediction: bool = False

    # Position analysis settings
    use_low_position: bool = True  # Whether to use low position analysis
    # Number of days to look back for finding the high point
    high_point_lookback_days: int = 365
    # Number of days within which the decline should have occurred
    decline_period_days: int = 180
    # Minimum decline percentage from high to be considered at low position
    decline_threshold: float = 0.3  # 适中的下跌阈值

    # Rapid decline detection settings
    # Whether to use rapid decline detection
    use_rapid_decline_detection: bool = True
    rapid_decline_days: int = 30  # 适中的快速下跌窗口
    # Minimum decline percentage within rapid_decline_days to be considered rapid
    rapid_decline_threshold: float = 0.15  # 适中的快速下跌阈值

    # Breakthrough confirmation settings
    # Whether to use breakthrough confirmation
    use_breakthrough_confirmation: bool = False
    # Number of days to look for confirmation
    breakthrough_confirmation_days: int = 1

    # Box pattern detection settings
    use_box_detection: bool = True  # Whether to use box pattern detection
    # Minimum quality score for a valid box pattern
    box_quality_threshold: float = 0.3  # 降低箱体质量要求

    # Fundamental analysis settings
    use_fundamental_filter: bool = False  # 是否启用基本面筛选
    # 营收增长率行业百分位要求（值越小要求越严格，如0.3表示要求位于行业前30%）
    revenue_growth_percentile: float = 0.3
    # 净利润增长率行业百分位要求（值越小要求越严格，如0.3表示要求位于行业前30%）
    profit_growth_percentile: float = 0.3
    # ROE行业百分位要求（值越小要求越严格，如0.3表示要求位于行业前30%）
    roe_percentile: float = 0.3
    # 资产负债率行业百分位要求（值越大要求越严格，如0.3表示要求位于行业后30%）
    liability_percentile: float = 0.3
    # PE行业百分位要求（值越大要求越宽松，如0.7表示要求不在行业前30%最高估值）
    pe_percentile: float = 0.7
    # PB行业百分位要求（值越大要求越宽松，如0.7表示要求不在行业前30%最高估值）
    pb_percentile: float = 0.7
    # 检查连续增长的年数
    fundamental_years_to_check: int = 3

    # Window weights
    use_window_weights: bool = False  # Whether to use window weights
    window_weights: Dict[int, float] = Field(
        default_factory=dict)  # Weights for different windows

    # System settings
    max_workers: int = 5
    retry_attempts: int = 2
    retry_delay: int = 1
    expected_count: int = 10


# Default configuration
DEFAULT_CONFIG = ScanConfig()

# Export default values as constants for use in other modules
# This ensures all modules use the same default values from a single source
DEFAULT_WINDOWS = DEFAULT_CONFIG.windows
DEFAULT_BOX_THRESHOLD = DEFAULT_CONFIG.box_threshold
DEFAULT_MA_DIFF_THRESHOLD = DEFAULT_CONFIG.ma_diff_threshold
DEFAULT_VOLATILITY_THRESHOLD = DEFAULT_CONFIG.volatility_threshold
DEFAULT_VOLUME_CHANGE_THRESHOLD = DEFAULT_CONFIG.volume_change_threshold
DEFAULT_VOLUME_STABILITY_THRESHOLD = DEFAULT_CONFIG.volume_stability_threshold
DEFAULT_VOLUME_INCREASE_THRESHOLD = DEFAULT_CONFIG.volume_increase_threshold
DEFAULT_BOX_QUALITY_THRESHOLD = DEFAULT_CONFIG.box_quality_threshold
DEFAULT_USE_VOLUME_ANALYSIS = DEFAULT_CONFIG.use_volume_analysis
DEFAULT_USE_BOX_DETECTION = DEFAULT_CONFIG.use_box_detection
DEFAULT_USE_LOW_POSITION = DEFAULT_CONFIG.use_low_position
DEFAULT_HIGH_POINT_LOOKBACK_DAYS = DEFAULT_CONFIG.high_point_lookback_days
DEFAULT_DECLINE_PERIOD_DAYS = DEFAULT_CONFIG.decline_period_days
DEFAULT_DECLINE_THRESHOLD = DEFAULT_CONFIG.decline_threshold
DEFAULT_USE_RAPID_DECLINE_DETECTION = DEFAULT_CONFIG.use_rapid_decline_detection
DEFAULT_RAPID_DECLINE_DAYS = DEFAULT_CONFIG.rapid_decline_days
DEFAULT_RAPID_DECLINE_THRESHOLD = DEFAULT_CONFIG.rapid_decline_threshold
DEFAULT_USE_BREAKTHROUGH_CONFIRMATION = DEFAULT_CONFIG.use_breakthrough_confirmation
DEFAULT_BREAKTHROUGH_CONFIRMATION_DAYS = DEFAULT_CONFIG.breakthrough_confirmation_days
DEFAULT_USE_BREAKTHROUGH_PREDICTION = DEFAULT_CONFIG.use_breakthrough_prediction
DEFAULT_USE_WINDOW_WEIGHTS = DEFAULT_CONFIG.use_window_weights


def merge_config(user_config: Dict[str, Any]) -> ScanConfig:
    """
    Merge user configuration with default configuration.

    Args:
        user_config: User-provided configuration

    Returns:
        Merged configuration
    """
    # Start with default config
    config_dict = DEFAULT_CONFIG.model_dump()

    # Update with user config
    for key, value in user_config.items():
        if key in config_dict and value is not None:
            config_dict[key] = value

    # Create new config object
    return ScanConfig(**config_dict)
