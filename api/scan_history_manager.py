"""
Scan history management module.
Manages scan history records stored in database.
"""
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, date
from .stock_database import get_stock_database
from .json_utils import sanitize_float_for_json, convert_numpy_types, sanitize_kline_data

# Maximum number of history records to keep
MAX_HISTORY_RECORDS = 100


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


def sanitize_scan_history_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize scan history record for JSON serialization.
    Removes invalid float values (NaN, Infinity) and converts NumPy types.
    
    Args:
        record: The scan history record to sanitize
    
    Returns:
        Sanitized scan history record
    """
    if not record:
        return record
    
    try:
        # First convert NumPy types, then sanitize floats
        # This ensures we handle nested structures properly
        sanitized = convert_numpy_types(record)
        sanitized = sanitize_float_for_json(sanitized)
        
        # Special handling for scannedStocks (if present)
        if 'scannedStocks' in sanitized and isinstance(sanitized['scannedStocks'], list):
            sanitized_stocks = []
            for stock in sanitized['scannedStocks']:
                # Stock data might already be sanitized, but ensure kline_data is handled
                if isinstance(stock, dict) and 'kline_data' in stock:
                    if stock['kline_data']:
                        stock['kline_data'] = sanitize_kline_data(stock['kline_data'])
                sanitized_stocks.append(stock)
            sanitized['scannedStocks'] = sanitized_stocks
        
        return sanitized
    except Exception as e:
        # If sanitization fails, return the original record
        # This prevents the API from crashing, but may still cause JSON errors
        print(f"Warning: Failed to sanitize scan history record: {e}")
        return record


def get_scan_history_list(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    use_current_quarter: bool = True
) -> List[Dict[str, Any]]:
    """
    Get list of all scan history records (metadata only).
    
    Args:
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
    
    records = db.get_scan_history_list(
        MAX_HISTORY_RECORDS,
        start_date=start_date,
        end_date=end_date
    )
    # Sanitize all records before returning
    return [sanitize_scan_history_record(record) for record in records]


def get_scan_history(cache_key: str) -> Optional[Dict[str, Any]]:
    """
    Get a specific scan history record by cache_key.
    
    Args:
        cache_key: The cache key of the scan record
    
    Returns:
        Full scan history record if found, None otherwise
    """
    db = get_stock_database()
    record = db.get_scan_history(cache_key)
    if record:
        return sanitize_scan_history_record(record)
    return None


def delete_scan_history(cache_key: str) -> bool:
    """
    Delete a scan history record.
    
    Args:
        cache_key: The cache key of the scan record to delete
    
    Returns:
        True if deleted successfully, False otherwise
    """
    db = get_stock_database()
    success = db.delete_scan_history(cache_key)
    if success:
        print(f"Scan history deleted: {cache_key}")
    return success


def clear_all_scan_history() -> int:
    """
    Clear all scan history records.
    
    Returns:
        Number of records deleted
    """
    db = get_stock_database()
    count = db.clear_scan_cache()
    print(f"All scan history cleared: {count} records deleted")
    return count

