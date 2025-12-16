"""
Backtest history management module.
Manages backtest history records stored in database.
"""
from typing import Dict, List, Any, Optional
from .stock_database import get_stock_database

# Maximum number of history records to keep
MAX_HISTORY_RECORDS = 100


def save_backtest_history(config: Dict[str, Any], result: Dict[str, Any]) -> str:
    """
    Save a backtest history record.
    
    Args:
        config: Backtest configuration (BacktestRequest data)
        result: Backtest result (BacktestResponse data)
    
    Returns:
        The ID of the saved history record
    """
    db = get_stock_database()
    history_id = db.save_backtest_history(config, result)
    print(f"Backtest history saved: {history_id}")
    return history_id


def get_backtest_history_list() -> List[Dict[str, Any]]:
    """
    Get list of all backtest history records (metadata only).
    
    Returns:
        List of history record metadata
    """
    db = get_stock_database()
    return db.get_backtest_history_list(MAX_HISTORY_RECORDS)


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

