"""
Turnover Rate Analyzer module for analyzing stock turnover rate patterns.
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple, Optional

# Import default values from config to ensure consistency
from ..config import (
    DEFAULT_MAX_TURNOVER_RATE, DEFAULT_ALLOW_TURNOVER_SPIKES
)


def calculate_turnover_features(df: pd.DataFrame, window: int, 
                                exclude_recent_days: int = 5) -> Dict[str, float]:
    """
    Calculate turnover rate-related features for a given window.
    
    For platform period detection, we exclude the most recent days to avoid
    interference from potential breakthrough signals, similar to volume analysis.
    
    Args:
        df: DataFrame containing stock price and volume data (must have 'turn' column)
        window: Window size in days
        exclude_recent_days: Number of recent days to exclude from platform analysis
    
    Returns:
        Dict containing calculated turnover features:
            - avg_turnover_rate: Average turnover rate in the platform period (%)
            - max_turnover_rate: Maximum turnover rate in the platform period (%)
            - turnover_stability: Stability of turnover rate (coefficient of variation)
            - spike_count: Number of days with turnover rate exceeding 2x average
    """
    if len(df) < window:
        return {
            'avg_turnover_rate': float('nan'),
            'max_turnover_rate': float('nan'),
            'turnover_stability': float('nan'),
            'spike_count': 0
        }
    
    # For platform period analysis, exclude recent days to separate from breakthrough
    # Get the platform period data (excluding recent days)
    if exclude_recent_days > 0 and len(df) > window:
        platform_df = df.iloc[-window:-exclude_recent_days].copy()
    else:
        platform_df = df.iloc[-window:].copy()
    
    # Check if 'turn' column exists
    if 'turn' not in platform_df.columns:
        return {
            'avg_turnover_rate': float('nan'),
            'max_turnover_rate': float('nan'),
            'turnover_stability': float('nan'),
            'spike_count': 0
        }
    
    # Filter out invalid turnover rates (NaN, negative, or extremely large values)
    valid_turnover = platform_df['turn'].dropna()
    valid_turnover = valid_turnover[(valid_turnover >= 0) & (valid_turnover <= 100)]
    
    if len(valid_turnover) == 0:
        return {
            'avg_turnover_rate': float('nan'),
            'max_turnover_rate': float('nan'),
            'turnover_stability': float('nan'),
            'spike_count': 0
        }
    
    # Calculate average turnover rate
    avg_turnover_rate = valid_turnover.mean()
    max_turnover_rate = valid_turnover.max()
    
    # Calculate turnover stability (coefficient of variation)
    if avg_turnover_rate > 0:
        turnover_stability = valid_turnover.std() / avg_turnover_rate
    else:
        turnover_stability = float('nan')
    
    # Count spikes (days with turnover rate exceeding 2x average)
    spike_threshold = avg_turnover_rate * 2
    spike_count = (valid_turnover > spike_threshold).sum()
    
    return {
        'avg_turnover_rate': avg_turnover_rate,
        'max_turnover_rate': max_turnover_rate,
        'turnover_stability': turnover_stability,
        'spike_count': spike_count
    }


def check_turnover_rate(df: pd.DataFrame, window: int,
                        max_turnover_rate: float = None,
                        allow_turnover_spikes: bool = None,
                        exclude_recent_days: int = 5) -> Tuple[bool, Dict[str, Any]]:
    """
    Check if a stock's turnover rate meets the platform period criteria.
    
    Platform period requires low average turnover rate. If allow_turnover_spikes is True,
    occasional spikes are allowed as long as the average is within threshold.
    
    Args:
        df: DataFrame containing stock price and volume data (must have 'turn' column)
        window: Window size in days
        max_turnover_rate: Maximum allowed average turnover rate (%)
        allow_turnover_spikes: Whether to allow occasional turnover spikes
        exclude_recent_days: Number of recent days to exclude (default 5, for breakthrough detection)
    
    Returns:
        Tuple of (meets_criteria, details)
    """
    # Apply default values from config if not provided
    if max_turnover_rate is None:
        max_turnover_rate = DEFAULT_MAX_TURNOVER_RATE
    if allow_turnover_spikes is None:
        allow_turnover_spikes = DEFAULT_ALLOW_TURNOVER_SPIKES

    if len(df) < window:
        return False, {
            "status": "数据不足",
            "window": window,
            "data_points": len(df)
        }
    
    # Check if 'turn' column exists
    if 'turn' not in df.columns:
        return False, {
            "status": "无换手率数据",
            "window": window
        }
    
    # Calculate turnover features (excluding recent days for platform analysis)
    features = calculate_turnover_features(df, window, exclude_recent_days=exclude_recent_days)
    
    # Check if average turnover rate is valid
    if pd.isna(features['avg_turnover_rate']):
        return False, {
            "status": "无法计算换手率",
            "window": window,
            "avg_turnover_rate": None
        }
    
    # Check if average turnover rate meets criteria
    avg_turnover = features['avg_turnover_rate']
    meets_criteria = avg_turnover <= max_turnover_rate
    
    # If allow_turnover_spikes is False, also check max turnover rate
    if not allow_turnover_spikes and not pd.isna(features['max_turnover_rate']):
        max_turnover = features['max_turnover_rate']
        # Allow some tolerance (e.g., 1.5x threshold) for max rate even if spikes not allowed
        max_threshold = max_turnover_rate * 1.5
        if max_turnover > max_threshold:
            meets_criteria = False
    
    # Prepare details
    details = {
        "window": window,
        "avg_turnover_rate": round(avg_turnover, 2) if not pd.isna(avg_turnover) else None,
        "max_turnover_rate": round(features['max_turnover_rate'], 2) if not pd.isna(features['max_turnover_rate']) else None,
        "max_turnover_rate_threshold": max_turnover_rate,
        "turnover_stability": round(features['turnover_stability'], 4) if not pd.isna(features['turnover_stability']) else None,
        "spike_count": features['spike_count'],
        "allow_turnover_spikes": allow_turnover_spikes,
        "exclude_recent_days": exclude_recent_days,
        "platform_period_days": window - exclude_recent_days if exclude_recent_days > 0 else window
    }
    
    # Add reason if not meeting criteria
    if not meets_criteria:
        if avg_turnover > max_turnover_rate:
            details["status"] = f"平均换手率过高 ({avg_turnover:.2f}% > {max_turnover_rate}%)"
        elif not allow_turnover_spikes and not pd.isna(features['max_turnover_rate']) and features['max_turnover_rate'] > max_turnover_rate * 1.5:
            details["status"] = f"存在异常放量 ({features['max_turnover_rate']:.2f}%)"
        else:
            details["status"] = "不符合换手率条件"
    else:
        details["status"] = "符合条件"
    
    return meets_criteria, details


def analyze_turnover(df: pd.DataFrame, window: int,
                     max_turnover_rate: float = None,
                     allow_turnover_spikes: bool = None,
                     exclude_recent_days: int = 5) -> Dict[str, Any]:
    """
    Analyze turnover rate patterns for a stock.
    
    This function analyzes the platform period (excluding recent days) to check
    if the average turnover rate meets the criteria for platform consolidation.
    
    Args:
        df: DataFrame containing stock price and volume data (must have 'turn' column)
        window: Window size in days for platform consolidation analysis
        max_turnover_rate: Maximum allowed average turnover rate (%)
        allow_turnover_spikes: Whether to allow occasional turnover spikes
        exclude_recent_days: Number of recent days to exclude (default 5, for breakthrough detection)
    
    Returns:
        Dict containing turnover analysis results
    """
    # Apply default values from config if not provided
    if max_turnover_rate is None:
        max_turnover_rate = DEFAULT_MAX_TURNOVER_RATE
    if allow_turnover_spikes is None:
        allow_turnover_spikes = DEFAULT_ALLOW_TURNOVER_SPIKES

    if df.empty or 'turn' not in df.columns:
        return {
            "meets_criteria": False,
            "avg_turnover_rate": None,
            "details": {"status": "无数据"}
        }
    
    # Check turnover rate criteria
    meets_criteria, details = check_turnover_rate(
        df, window, max_turnover_rate, allow_turnover_spikes,
        exclude_recent_days=exclude_recent_days
    )
    
    return {
        "meets_criteria": meets_criteria,
        "avg_turnover_rate": details.get("avg_turnover_rate"),
        "details": details
    }

