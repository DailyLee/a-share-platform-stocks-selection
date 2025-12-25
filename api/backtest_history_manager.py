"""
Backtest history management module.
Manages backtest history records stored in database.
"""
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, date
from .stock_database import get_stock_database

# Maximum number of history records to keep
# 增加到10000以支持更多回测名称的历史记录，避免数据被截断
MAX_HISTORY_RECORDS = 10000


def get_current_quarter_range() -> Tuple[str, str]:
    """
    获取当前季度的开始和结束日期。
    
    Returns:
        Tuple of (start_date, end_date) in 'YYYY-MM-DD' format
    """
    now = datetime.now()
    year = now.year
    month = now.month
    
    # 计算当前季度的开始月份
    if month in [1, 2, 3]:
        quarter_start_month = 1
    elif month in [4, 5, 6]:
        quarter_start_month = 4
    elif month in [7, 8, 9]:
        quarter_start_month = 7
    else:  # 10, 11, 12
        quarter_start_month = 10
    
    # 季度开始日期
    start_date = date(year, quarter_start_month, 1)
    
    # 季度结束日期（下个季度的第一天减1天）
    if quarter_start_month == 10:
        end_date = date(year + 1, 1, 1)
    else:
        end_date = date(year, quarter_start_month + 3, 1)
    
    # 转换为字符串格式
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = (end_date - date.resolution).strftime('%Y-%m-%d')
    
    return start_date_str, end_date_str


def save_backtest_history(config: Dict[str, Any], result: Dict[str, Any], batch_task_id: Optional[str] = None) -> str:
    """
    Save a backtest history record.
    
    Args:
        config: Backtest configuration (BacktestRequest data)
        result: Backtest result (BacktestResponse data)
        batch_task_id: Optional batch task ID for batch backtests
    
    Returns:
        The ID of the saved history record
    """
    db = get_stock_database()
    history_id = db.save_backtest_history(config, result, batch_task_id)
    print(f"Backtest history saved: {history_id}")
    return history_id


def get_backtest_history_list(
    batch_task_id: Optional[str] = None, 
    backtest_name: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    use_current_quarter: bool = True
) -> List[Dict[str, Any]]:
    """
    Get list of all backtest history records (metadata only).
    
    Args:
        batch_task_id: Optional filter by batch task ID
        backtest_name: Optional filter by backtest name
        start_date: Optional start date filter (YYYY-MM-DD). If None and use_current_quarter=True, uses current quarter start.
        end_date: Optional end date filter (YYYY-MM-DD). If None and use_current_quarter=True, uses current quarter end.
        use_current_quarter: If True and start_date/end_date not provided, only query current quarter data (default: True)
    
    Returns:
        List of history record metadata
    """
    db = get_stock_database()
    
    # 如果没有指定日期范围，且 use_current_quarter=True，则使用当前季度
    if use_current_quarter and start_date is None and end_date is None:
        start_date, end_date = get_current_quarter_range()
    
    return db.get_backtest_history_list(
        MAX_HISTORY_RECORDS, 
        batch_task_id, 
        backtest_name,
        start_date=start_date,
        end_date=end_date
    )


def get_backtest_history(history_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a specific backtest history record by ID.
    
    Args:
        history_id: The ID of the history record
    
    Returns:
        Full history record if found, None otherwise
    """
    db = get_stock_database()
    return db.get_backtest_history(history_id)


def delete_backtest_history(history_id: str) -> bool:
    """
    Delete a backtest history record.
    
    Args:
        history_id: The ID of the history record to delete
    
    Returns:
        True if deleted successfully, False otherwise
    """
    db = get_stock_database()
    success = db.delete_backtest_history(history_id)
    if success:
        print(f"Backtest history deleted: {history_id}")
    return success


def clear_all_backtest_history() -> int:
    """
    Clear all backtest history records.
    
    Returns:
        Number of records deleted
    """
    db = get_stock_database()
    count = db.clear_all_backtest_history()
    print(f"All backtest history cleared: {count} records deleted")
    return count


def check_backtest_exists(config: Dict[str, Any]) -> Optional[str]:
    """
    Check if a backtest record already exists based on configuration.
    
    Args:
        config: Backtest configuration dictionary
    
    Returns:
        The ID of existing record if found, None otherwise
    """
    db = get_stock_database()
    return db.check_backtest_exists(config)


def delete_backtest_history_by_date(backtest_date: str) -> int:
    """
    Delete all backtest history records for a specific backtest date.
    
    Args:
        backtest_date: Backtest date string (YYYY-MM-DD)
    
    Returns:
        Number of records deleted
    """
    db = get_stock_database()
    count = db.delete_backtest_history_by_date(backtest_date)
    print(f"Deleted {count} backtest history records for date: {backtest_date}")
    return count

