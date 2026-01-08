"""
Relative Strength Analyzer module for calculating stock performance relative to market index.
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Tuple


def calculate_relative_strength(
    stock_df: pd.DataFrame,
    market_df: pd.DataFrame,
    window: int,
    end_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    Calculate relative strength (outperform_index) for a stock compared to market index.
    
    Relative strength is calculated as: (stock_return - market_return) * 100
    where returns are calculated over the platform period window.
    
    Args:
        stock_df: DataFrame containing stock price data with 'date' and 'close' columns
        market_df: DataFrame containing market index data with 'date' and 'close' columns
        window: Platform period window size in days
        end_date: End date for calculation (default: last date in stock_df)
    
    Returns:
        Dict containing:
            - outperform_index: float, relative strength percentage
            - stock_return: float, stock return percentage
            - market_return: float, market return percentage
            - start_date: str, calculation start date
            - end_date: str, calculation end date
            - status: str, status message
    """
    if stock_df.empty or market_df.empty:
        print(f"[RELATIVE_STRENGTH_DEBUG] Data insufficient: stock_df.empty={stock_df.empty}, market_df.empty={market_df.empty}")
        return {
            "outperform_index": None,
            "stock_return": None,
            "market_return": None,
            "start_date": None,
            "end_date": None,
            "status": "数据不足"
        }
    
    # Ensure dataframes are sorted by date
    stock_df = stock_df.sort_values('date').reset_index(drop=True)
    market_df = market_df.sort_values('date').reset_index(drop=True)
    
    # Convert date column to datetime if needed
    if not pd.api.types.is_datetime64_any_dtype(stock_df['date']):
        stock_df['date'] = pd.to_datetime(stock_df['date'])
    if not pd.api.types.is_datetime64_any_dtype(market_df['date']):
        market_df['date'] = pd.to_datetime(market_df['date'])
    
    # Determine end date
    if end_date:
        end_date_dt = pd.to_datetime(end_date)
    else:
        end_date_dt = stock_df['date'].max()
    
    # Find the end date index in stock dataframe
    end_idx = stock_df[stock_df['date'] <= end_date_dt].index
    if len(end_idx) == 0:
        print(f"[RELATIVE_STRENGTH_DEBUG] Cannot find end date: end_date_dt={end_date_dt}, stock_df date range: {stock_df['date'].min()} to {stock_df['date'].max()}")
        return {
            "outperform_index": None,
            "stock_return": None,
            "market_return": None,
            "start_date": None,
            "end_date": None,
            "status": "无法找到结束日期"
        }
    
    end_idx = end_idx[-1]
    
    # Calculate start index (window days before end)
    start_idx = max(0, end_idx - window + 1)
    
    # Get the window data
    window_stock_df = stock_df.iloc[start_idx:end_idx + 1].copy()
    
    if len(window_stock_df) < 2:
        print(f"[RELATIVE_STRENGTH_DEBUG] Window data insufficient: window={window}, data_points={len(window_stock_df)}, start_idx={start_idx}, end_idx={end_idx}")
        return {
            "outperform_index": None,
            "stock_return": None,
            "market_return": None,
            "start_date": None,
            "end_date": None,
            "status": "窗口数据不足"
        }
    
    # Get start and end dates
    start_date_dt = window_stock_df['date'].iloc[0]
    end_date_actual = window_stock_df['date'].iloc[-1]
    
    # Calculate stock return
    start_price = float(window_stock_df['close'].iloc[0])
    end_price = float(window_stock_df['close'].iloc[-1])
    
    if start_price == 0 or pd.isna(start_price) or pd.isna(end_price):
        print(f"[RELATIVE_STRENGTH_DEBUG] Invalid price data: start_price={start_price}, end_price={end_price}, start_date={start_date_dt}, end_date={end_date_actual}")
        return {
            "outperform_index": None,
            "stock_return": None,
            "market_return": None,
            "start_date": str(start_date_dt.date()) if hasattr(start_date_dt, 'date') else str(start_date_dt),
            "end_date": str(end_date_actual.date()) if hasattr(end_date_actual, 'date') else str(end_date_actual),
            "status": "价格数据无效"
        }
    
    stock_return = ((end_price - start_price) / start_price) * 100
    
    # Find corresponding market data for the same date range
    market_start_idx = market_df[market_df['date'] <= start_date_dt].index
    market_end_idx = market_df[market_df['date'] <= end_date_actual].index
    
    if len(market_start_idx) == 0 or len(market_end_idx) == 0:
        print(f"[RELATIVE_STRENGTH_DEBUG] Cannot find market data: start_date={start_date_dt}, end_date={end_date_actual}, market_df date range: {market_df['date'].min()} to {market_df['date'].max()}, market_start_idx={len(market_start_idx)}, market_end_idx={len(market_end_idx)}")
        return {
            "outperform_index": None,
            "stock_return": stock_return,
            "market_return": None,
            "start_date": str(start_date_dt.date()) if hasattr(start_date_dt, 'date') else str(start_date_dt),
            "end_date": str(end_date_actual.date()) if hasattr(end_date_actual, 'date') else str(end_date_actual),
            "status": "无法找到对应的大盘数据"
        }
    
    market_start_idx = market_start_idx[-1]
    market_end_idx = market_end_idx[-1]
    
    # Get market prices
    market_start_price = float(market_df.iloc[market_start_idx]['close'])
    market_end_price = float(market_df.iloc[market_end_idx]['close'])
    
    if market_start_price == 0 or pd.isna(market_start_price) or pd.isna(market_end_price):
        print(f"[RELATIVE_STRENGTH_DEBUG] Invalid market price data: market_start_price={market_start_price}, market_end_price={market_end_price}, start_date={start_date_dt}, end_date={end_date_actual}")
        return {
            "outperform_index": None,
            "stock_return": stock_return,
            "market_return": None,
            "start_date": str(start_date_dt.date()) if hasattr(start_date_dt, 'date') else str(start_date_dt),
            "end_date": str(end_date_actual.date()) if hasattr(end_date_actual, 'date') else str(end_date_actual),
            "status": "大盘价格数据无效"
        }
    
    # Calculate market return
    market_return = ((market_end_price - market_start_price) / market_start_price) * 100
    
    # Calculate relative strength (outperform_index)
    outperform_index = stock_return - market_return
    
    print(f"[RELATIVE_STRENGTH_DEBUG] Calculation successful: window={window}, stock_return={stock_return:.2f}%, market_return={market_return:.2f}%, outperform_index={outperform_index:.2f}%, start_date={start_date_dt}, end_date={end_date_actual}")
    
    return {
        "outperform_index": outperform_index,
        "stock_return": stock_return,
        "market_return": market_return,
        "start_date": str(start_date_dt.date()) if hasattr(start_date_dt, 'date') else str(start_date_dt),
        "end_date": str(end_date_actual.date()) if hasattr(end_date_actual, 'date') else str(end_date_actual),
        "status": "计算成功"
    }


def analyze_relative_strength_for_windows(
    stock_df: pd.DataFrame,
    market_df: pd.DataFrame,
    windows: list,
    end_date: Optional[str] = None
) -> Dict[int, Dict[str, Any]]:
    """
    Calculate relative strength for multiple windows.
    
    Args:
        stock_df: DataFrame containing stock price data
        market_df: DataFrame containing market index data
        windows: List of window sizes to analyze
        end_date: End date for calculation
    
    Returns:
        Dict mapping window size to relative strength analysis results
    """
    results = {}
    
    for window in windows:
        result = calculate_relative_strength(stock_df, market_df, window, end_date)
        results[window] = result
    
    return results

