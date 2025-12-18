"""
Scan history management module.
Manages scan history records stored in database.
"""
from typing import Dict, List, Any, Optional
from .stock_database import get_stock_database
from .json_utils import sanitize_float_for_json, convert_numpy_types, sanitize_kline_data

# Maximum number of history records to keep
MAX_HISTORY_RECORDS = 100


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


def get_scan_history_list() -> List[Dict[str, Any]]:
    """
    Get list of all scan history records (metadata only).
    
    Returns:
        List of history record metadata
    """
    db = get_stock_database()
    records = db.get_scan_history_list(MAX_HISTORY_RECORDS)
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

