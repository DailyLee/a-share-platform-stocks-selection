"""
Backtest history management module.
Manages backtest history records stored as JSON files.
"""
import os
import json
from datetime import datetime
from typing import Dict, List, Any, Optional

# Define the backtest history directory
BACKTEST_HISTORY_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backtest_history')

# Ensure the directory exists
os.makedirs(BACKTEST_HISTORY_DIR, exist_ok=True)

# Define the index file path
INDEX_FILE = os.path.join(BACKTEST_HISTORY_DIR, 'index.json')

# Maximum number of history records to keep
MAX_HISTORY_RECORDS = 100


def _load_index() -> Dict[str, Any]:
    """Load the index file."""
    # Ensure directory exists
    os.makedirs(BACKTEST_HISTORY_DIR, exist_ok=True)
    
    if not os.path.exists(INDEX_FILE):
        return {'records': [], 'lastUpdated': datetime.now().isoformat()}
    
    try:
        with open(INDEX_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading backtest history index: {e}")
        return {'records': [], 'lastUpdated': datetime.now().isoformat()}


def _save_index(data: Dict[str, Any]):
    """Save the index file."""
    # Ensure directory exists
    os.makedirs(BACKTEST_HISTORY_DIR, exist_ok=True)
    
    try:
        data['lastUpdated'] = datetime.now().isoformat()
        with open(INDEX_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving backtest history index: {e}")
        raise


def save_backtest_history(config: Dict[str, Any], result: Dict[str, Any]) -> str:
    """
    Save a backtest history record.
    
    Args:
        config: Backtest configuration (BacktestRequest data)
        result: Backtest result (BacktestResponse data)
    
    Returns:
        The ID of the saved history record
    """
    # Generate a unique ID
    history_id = f"backtest_{int(datetime.now().timestamp() * 1000)}"
    
    # Create history record
    history_record = {
        'id': history_id,
        'createdAt': datetime.now().isoformat(),
        'config': config,
        'result': result
    }
    
    # Ensure directory exists before saving
    os.makedirs(BACKTEST_HISTORY_DIR, exist_ok=True)
    
    # Save the record to a JSON file
    record_file = os.path.join(BACKTEST_HISTORY_DIR, f"{history_id}.json")
    try:
        with open(record_file, 'w', encoding='utf-8') as f:
            json.dump(history_record, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving backtest history record: {e}")
        raise
    
    # Update index
    index_data = _load_index()
    records = index_data.get('records', [])
    
    # Add metadata to index (without full result data)
    record_meta = {
        'id': history_id,
        'createdAt': history_record['createdAt'],
        'backtestDate': config.get('backtest_date', ''),
        'statDate': config.get('stat_date', ''),
        'useStopLoss': config.get('use_stop_loss', False),
        'useTakeProfit': config.get('use_take_profit', False),
        'stopLossPercent': config.get('stop_loss_percent', -3.0),
        'takeProfitPercent': config.get('take_profit_percent', 10.0),
        'summary': result.get('summary', {})
    }
    
    # Add to beginning of list
    records.insert(0, record_meta)
    
    # Limit the number of records
    if len(records) > MAX_HISTORY_RECORDS:
        # Remove oldest records
        records_to_remove = records[MAX_HISTORY_RECORDS:]
        records = records[:MAX_HISTORY_RECORDS]
        
        # Delete old record files
        for old_record in records_to_remove:
            old_file = os.path.join(BACKTEST_HISTORY_DIR, f"{old_record['id']}.json")
            if os.path.exists(old_file):
                try:
                    os.remove(old_file)
                except Exception as e:
                    print(f"Error deleting old history record file: {e}")
    
    index_data['records'] = records
    _save_index(index_data)
    
    print(f"Backtest history saved: {history_id}")
    return history_id


def get_backtest_history_list() -> List[Dict[str, Any]]:
    """
    Get list of all backtest history records (metadata only).
    
    Returns:
        List of history record metadata
    """
    index_data = _load_index()
    return index_data.get('records', [])


def get_backtest_history(history_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a specific backtest history record by ID.
    
    Args:
        history_id: The ID of the history record
    
    Returns:
        Full history record if found, None otherwise
    """
    record_file = os.path.join(BACKTEST_HISTORY_DIR, f"{history_id}.json")
    
    if not os.path.exists(record_file):
        return None
    
    try:
        with open(record_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading backtest history record: {e}")
        return None


def delete_backtest_history(history_id: str) -> bool:
    """
    Delete a backtest history record.
    
    Args:
        history_id: The ID of the history record to delete
    
    Returns:
        True if deleted successfully, False otherwise
    """
    # Remove from index
    index_data = _load_index()
    records = index_data.get('records', [])
    records = [r for r in records if r.get('id') != history_id]
    index_data['records'] = records
    _save_index(index_data)
    
    # Delete record file
    record_file = os.path.join(BACKTEST_HISTORY_DIR, f"{history_id}.json")
    if os.path.exists(record_file):
        try:
            os.remove(record_file)
            print(f"Backtest history deleted: {history_id}")
            return True
        except Exception as e:
            print(f"Error deleting backtest history record file: {e}")
            return False
    
    return False


def clear_all_backtest_history() -> int:
    """
    Clear all backtest history records.
    
    Returns:
        Number of records deleted
    """
    index_data = _load_index()
    records = index_data.get('records', [])
    count = len(records)
    
    # Delete all record files
    for record in records:
        record_file = os.path.join(BACKTEST_HISTORY_DIR, f"{record['id']}.json")
        if os.path.exists(record_file):
            try:
                os.remove(record_file)
            except Exception as e:
                print(f"Error deleting history record file: {e}")
    
    # Clear index
    index_data['records'] = []
    _save_index(index_data)
    
    print(f"All backtest history cleared: {count} records deleted")
    return count

