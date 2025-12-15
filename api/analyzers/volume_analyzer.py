"""
Volume Analyzer module for analyzing stock volume patterns.
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple, Optional

# Import default values from config to ensure consistency
from ..config import (
    DEFAULT_VOLUME_CHANGE_THRESHOLD, DEFAULT_VOLUME_STABILITY_THRESHOLD,
    DEFAULT_VOLUME_INCREASE_THRESHOLD
)

def calculate_volume_features(df: pd.DataFrame, window: int, 
                              exclude_recent_days: int = 5) -> Dict[str, float]:
    """
    Calculate volume-related features for a given window.
    
    For platform period detection, we exclude the most recent days to avoid
    interference from potential breakthrough signals. This allows us to:
    1. Judge platform consolidation using the main period (stable/decreasing volume)
    2. Judge breakthrough separately using only recent days (increasing volume)
    
    Args:
        df: DataFrame containing stock price and volume data
        window: Window size in days
        exclude_recent_days: Number of recent days to exclude from platform analysis
    
    Returns:
        Dict containing calculated volume features:
            - volume_change_ratio: Ratio of recent volume to historical volume
            - volume_stability: Stability of volume in the window
            - volume_trend: Trend of volume in the window (positive or negative)
    """
    if len(df) < window + 10:  # Need extra data for comparison
        return {
            'volume_change_ratio': float('nan'),
            'volume_stability': float('nan'),
            'volume_trend': float('nan')
        }
    
    # For platform period analysis, exclude recent days to separate from breakthrough
    # Use window - exclude_recent_days for platform consolidation judgment
    platform_window = max(window - exclude_recent_days, window // 2)  # At least half the window
    
    # Get the platform period data (excluding recent days) and previous data for comparison
    platform_df = df.iloc[-window:-exclude_recent_days].copy() if exclude_recent_days > 0 else df.iloc[-window:].copy()
    previous_df = df.iloc[-(window*2):-window].copy()
    
    # Calculate average volume
    platform_avg_volume = platform_df['volume'].mean()
    previous_avg_volume = previous_df['volume'].mean()
    
    # Calculate volume change ratio (for platform period, we want stable/decreasing)
    if previous_avg_volume > 0:
        volume_change_ratio = platform_avg_volume / previous_avg_volume
    else:
        volume_change_ratio = float('nan')
    
    # Calculate volume stability (coefficient of variation) for platform period
    if platform_avg_volume > 0:
        volume_stability = platform_df['volume'].std() / platform_avg_volume
    else:
        volume_stability = float('nan')
    
    # Calculate volume trend (linear regression slope) for platform period
    if len(platform_df) >= 5:
        x = np.arange(len(platform_df))
        y = platform_df['volume'].values
        slope, _ = np.polyfit(x, y, 1)
        volume_trend = slope / platform_avg_volume if platform_avg_volume > 0 else float('nan')
    else:
        volume_trend = float('nan')
    
    return {
        'volume_change_ratio': volume_change_ratio,
        'volume_stability': volume_stability,
        'volume_trend': volume_trend
    }

def check_volume_pattern(df: pd.DataFrame, window: int, 
                         volume_change_threshold: float = None,
                         volume_stability_threshold: float = None,
                         exclude_recent_days: int = 5) -> Tuple[bool, Dict[str, Any]]:
    """
    Check if a stock has a consolidation volume pattern (stable or decreasing volume).
    
    This function excludes recent days from analysis to separate platform consolidation
    judgment from breakthrough signals. Platform period requires stable/decreasing volume
    in the main period, while breakthrough is judged separately using only recent days.
    
    Args:
        df: DataFrame containing stock price and volume data
        window: Window size in days
        volume_change_threshold: Maximum allowed volume change ratio (for stable/decreasing)
        volume_stability_threshold: Maximum allowed volume stability
        exclude_recent_days: Number of recent days to exclude (default 5, for breakthrough detection)
    
    Returns:
        Tuple of (is_consolidation_volume, details)
    """
    # Apply default values from config if not provided
    if volume_change_threshold is None:
        volume_change_threshold = DEFAULT_VOLUME_CHANGE_THRESHOLD
    if volume_stability_threshold is None:
        volume_stability_threshold = DEFAULT_VOLUME_STABILITY_THRESHOLD

    if len(df) < window + 10:
        return False, {
            "status": "数据不足",
            "window": window,
            "data_points": len(df)
        }
    
    # Calculate volume features (excluding recent days for platform analysis)
    features = calculate_volume_features(df, window, exclude_recent_days=exclude_recent_days)
    
    # Check conditions for consolidation volume pattern
    # For platform period, we want stable or slightly decreasing volume
    # Note: volume_change_threshold can be >= 1.0 to allow stable volume (not just decreasing)
    # If threshold is < 1.0, it requires decreasing volume
    # If threshold is >= 1.0, it allows stable or slightly increasing volume
    is_stable_or_decreasing = features['volume_change_ratio'] <= volume_change_threshold
    is_stable_volume = features['volume_stability'] <= volume_stability_threshold
    
    # Platform consolidation requires stable volume, and optionally decreasing volume
    # If volume_change_threshold >= 1.0, we only check stability
    # If volume_change_threshold < 1.0, we require both stability and decrease
    if volume_change_threshold >= 1.0:
        # Only require stability, allow stable or slightly increasing volume
        is_consolidation_volume = is_stable_volume
    else:
        # Require both stability and decrease
        is_consolidation_volume = is_stable_or_decreasing and is_stable_volume
    
    # Prepare details
    details = {
        "window": window,
        "volume_change_ratio": round(features['volume_change_ratio'], 4) if not pd.isna(features['volume_change_ratio']) else None,
        "volume_change_threshold": volume_change_threshold,
        "volume_stability": round(features['volume_stability'], 4) if not pd.isna(features['volume_stability']) else None,
        "volume_stability_threshold": volume_stability_threshold,
        "volume_trend": round(features['volume_trend'], 4) if not pd.isna(features['volume_trend']) else None
    }
    
    # Add reason if not a consolidation volume pattern
    if not is_consolidation_volume:
        if volume_change_threshold < 1.0 and not is_stable_or_decreasing:
            details["status"] = "成交量未萎缩"
        elif not is_stable_volume:
            details["status"] = "成交量波动过大"
        else:
            details["status"] = "未知原因"
    else:
        details["status"] = "符合条件"
    
    # Add metadata about the analysis period
    details["exclude_recent_days"] = exclude_recent_days
    details["platform_period_days"] = window - exclude_recent_days if exclude_recent_days > 0 else window
    
    return is_consolidation_volume, details

def check_volume_breakthrough(df: pd.DataFrame, window: int = 5, 
                             volume_increase_threshold: float = None,
                             comparison_window: int = None) -> Tuple[bool, Dict[str, Any]]:
    """
    Check if a stock has a volume breakthrough pattern (increasing volume in recent days).
    
    This function analyzes ONLY the most recent days to detect breakthrough signals,
    which is separate from platform consolidation analysis. This allows:
    1. Platform period: judged by stable/decreasing volume in main period
    2. Breakthrough: judged by increasing volume in recent days only
    
    Args:
        df: DataFrame containing stock price and volume data
        window: Window size in days for recent volume (default 5)
        volume_increase_threshold: Minimum required volume increase ratio
        comparison_window: Window size for comparison period (default window*3)
    
    Returns:
        Tuple of (is_breakthrough, details)
    """
    # Apply default values from config if not provided
    if volume_increase_threshold is None:
        volume_increase_threshold = DEFAULT_VOLUME_INCREASE_THRESHOLD
    if comparison_window is None:
        comparison_window = window * 3

    if len(df) < window + comparison_window:
        return False, {
            "status": "数据不足",
            "window": window,
            "data_points": len(df)
        }
    
    # Get ONLY the most recent days for breakthrough detection
    # This is separate from platform period analysis
    recent_df = df.iloc[-window:].copy()
    # Compare with period before the recent window (not overlapping with platform analysis)
    previous_df = df.iloc[-(window + comparison_window):-window].copy()
    
    # Calculate average volume
    recent_avg_volume = recent_df['volume'].mean()
    previous_avg_volume = previous_df['volume'].mean()
    
    # Calculate volume increase ratio
    if previous_avg_volume > 0:
        volume_increase_ratio = recent_avg_volume / previous_avg_volume
    else:
        volume_increase_ratio = float('nan')
    
    # Check if there's a volume breakthrough
    is_breakthrough = volume_increase_ratio >= volume_increase_threshold
    
    # Prepare details
    details = {
        "window": window,
        "recent_avg_volume": round(recent_avg_volume, 2) if not pd.isna(recent_avg_volume) else None,
        "previous_avg_volume": round(previous_avg_volume, 2) if not pd.isna(previous_avg_volume) else None,
        "volume_increase_ratio": round(volume_increase_ratio, 4) if not pd.isna(volume_increase_ratio) else None,
        "volume_increase_threshold": volume_increase_threshold
    }
    
    if is_breakthrough:
        details["status"] = "成交量突破"
    else:
        details["status"] = "无成交量突破"
    
    return is_breakthrough, details

def analyze_volume(df: pd.DataFrame, window: int, 
                  volume_change_threshold: float = None,
                  volume_stability_threshold: float = None,
                  volume_increase_threshold: float = None,
                  breakthrough_window: int = 5) -> Dict[str, Any]:
    """
    Analyze volume patterns for a stock with time-separated logic.
    
    This function separates platform consolidation analysis from breakthrough detection:
    1. Platform consolidation: Analyzes main period (excluding recent days) for stable/decreasing volume
    2. Breakthrough: Analyzes only recent days for increasing volume
    
    This separation resolves the logical contradiction where platform period requires
    decreasing volume while breakthrough requires increasing volume.
    
    Args:
        df: DataFrame containing stock price and volume data
        window: Window size in days for platform consolidation analysis
        volume_change_threshold: Maximum allowed volume change ratio for consolidation
        volume_stability_threshold: Maximum allowed volume stability for consolidation
        volume_increase_threshold: Minimum required volume increase ratio for breakthrough
        breakthrough_window: Window size in days for breakthrough detection (default 5)
    
    Returns:
        Dict containing volume analysis results
    """
    # Apply default values from config if not provided
    if volume_change_threshold is None:
        volume_change_threshold = DEFAULT_VOLUME_CHANGE_THRESHOLD
    if volume_stability_threshold is None:
        volume_stability_threshold = DEFAULT_VOLUME_STABILITY_THRESHOLD
    if volume_increase_threshold is None:
        volume_increase_threshold = DEFAULT_VOLUME_INCREASE_THRESHOLD

    if df.empty or 'volume' not in df.columns:
        return {
            "has_consolidation_volume": False,
            "has_breakthrough": False,
            "consolidation_details": {"status": "无数据"},
            "breakthrough_details": {"status": "无数据"}
        }
    
    # Check for consolidation volume pattern (excludes recent days for breakthrough)
    # This analyzes the main period for stable/decreasing volume
    has_consolidation_volume, consolidation_details = check_volume_pattern(
        df, window, volume_change_threshold, volume_stability_threshold,
        exclude_recent_days=breakthrough_window
    )
    
    # Check for volume breakthrough (only analyzes recent days)
    # This is separate from platform consolidation analysis
    has_breakthrough, breakthrough_details = check_volume_breakthrough(
        df, breakthrough_window, volume_increase_threshold
    )
    
    return {
        "has_consolidation_volume": has_consolidation_volume,
        "has_breakthrough": has_breakthrough,
        "consolidation_details": consolidation_details,
        "breakthrough_details": breakthrough_details
    }
