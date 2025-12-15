"""
Cache Manager module for caching stock data to improve API response speed.
Implements file-based cache with JSON storage and automatic expiration.
Since data is from yesterday, cache entries are valid for the entire day.
"""
import os
import time
import hashlib
import json
from typing import Any, Optional, Dict
from datetime import datetime, timedelta, date
from threading import Lock
from functools import wraps
import pandas as pd

# Import JSON utilities for handling special values
try:
    from .json_utils import convert_numpy_types, sanitize_float_for_json
except ImportError:
    from api.json_utils import convert_numpy_types, sanitize_float_for_json

# Define cache directory
CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'cache')

# Ensure cache directory exists
os.makedirs(CACHE_DIR, exist_ok=True)


class CacheEntry:
    """Represents a single cache entry with data and expiration time."""
    
    def __init__(self, data: Any, expires_at: float, cache_date: str = None):
        """
        Initialize a cache entry.
        
        Args:
            data: The data to cache
            expires_at: Expiration timestamp
            cache_date: Date string (YYYY-MM-DD) when cache was created
        """
        self.data = data
        self.created_at = time.time()
        self.expires_at = expires_at
        self.cache_date = cache_date or date.today().isoformat()
    
    def is_expired(self) -> bool:
        """Check if the cache entry has expired."""
        return time.time() > self.expires_at
    
    def is_valid_for_today(self) -> bool:
        """
        Check if cache is valid for today.
        Since data is from yesterday, cache is valid for the entire day.
        """
        today = date.today().isoformat()
        return self.cache_date == today
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert cache entry to dictionary for JSON serialization."""
        return {
            'data': self.data,
            'created_at': self.created_at,
            'expires_at': self.expires_at,
            'cache_date': self.cache_date
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CacheEntry':
        """Create cache entry from dictionary."""
        return cls(
            data=data['data'],
            expires_at=data['expires_at'],
            cache_date=data.get('cache_date', date.today().isoformat())
        )


class CacheManager:
    """
    Thread-safe file-based cache manager with time-based expiration.
    Cache files are stored as JSON in the cache/ directory.
    """
    
    def __init__(self, cache_dir: str = CACHE_DIR):
        """
        Initialize the cache manager.
        
        Args:
            cache_dir: Directory to store cache files
        """
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        
        # In-memory cache for faster access (optional optimization)
        self._memory_cache: Dict[str, CacheEntry] = {}
        self._lock = Lock()
        self._stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'file_reads': 0,
            'file_writes': 0
        }
    
    def _get_cache_file_path(self, key: str) -> str:
        """
        Get the file path for a cache key.
        
        Args:
            key: Cache key
        
        Returns:
            Full path to cache file
        """
        # Use key as filename (it's already a hash, so safe)
        return os.path.join(self.cache_dir, f"{key}.json")
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """
        Generate a cache key from arguments.
        
        Args:
            prefix: Key prefix
            *args: Positional arguments
            **kwargs: Keyword arguments
        
        Returns:
            Cache key string
        """
        # Create a hashable representation of the arguments
        key_parts = [prefix]
        
        # Add positional arguments
        for arg in args:
            key_parts.append(str(arg))
        
        # Add keyword arguments (sorted for consistency)
        if kwargs:
            sorted_kwargs = sorted(kwargs.items())
            key_parts.append(json.dumps(sorted_kwargs, sort_keys=True))
        
        # Create a hash of the key parts
        key_string = '|'.join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _load_from_file(self, key: str) -> Optional[CacheEntry]:
        """
        Load cache entry from file.
        
        Args:
            key: Cache key
        
        Returns:
            CacheEntry or None if not found or expired
        """
        file_path = self._get_cache_file_path(key)
        
        if not os.path.exists(file_path):
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            entry = CacheEntry.from_dict(cache_data)
            self._stats['file_reads'] += 1
            
            # Check if expired
            if entry.is_expired() or not entry.is_valid_for_today():
                # Delete expired file
                try:
                    os.remove(file_path)
                except Exception:
                    pass
                self._stats['evictions'] += 1
                return None
            
            return entry
        except Exception as e:
            # If file is corrupted, delete it
            try:
                os.remove(file_path)
            except Exception:
                pass
            print(f"Error loading cache file {file_path}: {e}")
            return None
    
    def _save_to_file(self, key: str, entry: CacheEntry) -> bool:
        """
        Save cache entry to file.
        
        Args:
            key: Cache key
            entry: CacheEntry to save
        
        Returns:
            True if successful, False otherwise
        """
        file_path = self._get_cache_file_path(key)
        
        try:
            # Convert data to JSON-serializable format
            cache_dict = entry.to_dict()
            
            # Sanitize data for JSON (handle NaN, Infinity, etc.)
            cache_dict['data'] = self._prepare_data_for_json(cache_dict['data'])
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(cache_dict, f, ensure_ascii=False, indent=2)
            
            self._stats['file_writes'] += 1
            return True
        except Exception as e:
            print(f"Error saving cache file {file_path}: {e}")
            return False
    
    def _prepare_data_for_json(self, data: Any) -> Any:
        """
        Prepare data for JSON serialization.
        Handles pandas DataFrames and special values.
        
        Args:
            data: Data to prepare
        
        Returns:
            JSON-serializable data
        """
        # Handle pandas DataFrame
        if isinstance(data, pd.DataFrame):
            # Convert DataFrame to list of records
            data = data.to_dict(orient='records')
        
        # Convert NumPy types and sanitize floats
        data = convert_numpy_types(data)
        data = sanitize_float_for_json(data)
        
        return data
    
    def _restore_data_from_json(self, data: Any) -> Any:
        """
        Restore data from JSON format.
        Converts list of records back to DataFrame if needed.
        
        Args:
            data: JSON data
        
        Returns:
            Restored data (DataFrame or original format)
        """
        # If data is a list of dicts and looks like DataFrame records, convert back
        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
            # Check if it has DataFrame-like structure
            if 'date' in data[0] or any(col in data[0] for col in ['open', 'high', 'low', 'close', 'volume']):
                try:
                    return pd.DataFrame(data)
                except Exception:
                    pass
        
        return data
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get data from cache (checks memory first, then file).
        
        Args:
            key: Cache key
        
        Returns:
            Cached data or None if not found or expired
        """
        with self._lock:
            # Check memory cache first
            if key in self._memory_cache:
                entry = self._memory_cache[key]
                if not entry.is_expired() and entry.is_valid_for_today():
                    self._stats['hits'] += 1
                    return entry.data.copy() if hasattr(entry.data, 'copy') else entry.data
                else:
                    # Remove expired entry from memory
                    del self._memory_cache[key]
            
            # Load from file
            entry = self._load_from_file(key)
            
            if entry is None:
                self._stats['misses'] += 1
                return None
            
            # Store in memory cache for faster access
            self._memory_cache[key] = entry
            
            # Restore DataFrame if needed
            data = entry.data
            if isinstance(data, list) and len(data) > 0:
                data = self._restore_data_from_json(data)
            
            self._stats['hits'] += 1
            return data.copy() if hasattr(data, 'copy') else data
    
    def set(self, key: str, data: Any, ttl_seconds: int) -> None:
        """
        Store data in cache (saves to file and memory).
        
        Args:
            key: Cache key
            data: Data to cache
            ttl_seconds: Time to live in seconds (not used, cache is valid for the entire day)
        """
        with self._lock:
            # Calculate expiration time
            # Since data is from yesterday, cache is valid until end of today
            now = datetime.now()
            end_of_today = datetime.combine(now.date() + timedelta(days=1), datetime.min.time())
            # Cache is valid until end of today (23:59:59.999)
            expires_at = end_of_today.timestamp()
            
            # Create cache entry
            entry = CacheEntry(
                data=data,
                expires_at=expires_at,
                cache_date=date.today().isoformat()
            )
            
            # Save to file
            self._save_to_file(key, entry)
            
            # Store in memory cache
            self._memory_cache[key] = entry
    
    def delete(self, key: str) -> bool:
        """
        Delete a cache entry (from both file and memory).
        
        Args:
            key: Cache key
        
        Returns:
            True if deleted, False if not found
        """
        with self._lock:
            deleted = False
            
            # Delete from memory
            if key in self._memory_cache:
                del self._memory_cache[key]
                deleted = True
            
            # Delete from file
            file_path = self._get_cache_file_path(key)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    deleted = True
                except Exception as e:
                    print(f"Error deleting cache file {file_path}: {e}")
            
            return deleted
    
    def clear(self) -> None:
        """Clear all cache entries (from both file and memory)."""
        with self._lock:
            # Clear memory cache
            self._memory_cache.clear()
            
            # Clear file cache
            try:
                for filename in os.listdir(self.cache_dir):
                    if filename.endswith('.json'):
                        file_path = os.path.join(self.cache_dir, filename)
                        try:
                            os.remove(file_path)
                        except Exception as e:
                            print(f"Error deleting cache file {file_path}: {e}")
            except Exception as e:
                print(f"Error clearing cache directory: {e}")
    
    def cleanup_expired(self) -> int:
        """
        Remove expired entries from cache (both file and memory).
        
        Returns:
            Number of entries removed
        """
        with self._lock:
            removed_count = 0
            
            # Clean memory cache
            expired_keys = [
                key for key, entry in self._memory_cache.items()
                if entry.is_expired() or not entry.is_valid_for_today()
            ]
            for key in expired_keys:
                del self._memory_cache[key]
                removed_count += 1
            
            # Clean file cache
            try:
                for filename in os.listdir(self.cache_dir):
                    if filename.endswith('.json'):
                        file_path = os.path.join(self.cache_dir, filename)
                        key = filename[:-5]  # Remove .json extension
                        entry = self._load_from_file(key)
                        if entry is None:  # File was deleted because expired
                            removed_count += 1
            except Exception as e:
                print(f"Error cleaning cache directory: {e}")
            
            self._stats['evictions'] += removed_count
            return removed_count
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        with self._lock:
            # Count file cache entries
            file_count = 0
            try:
                file_count = len([f for f in os.listdir(self.cache_dir) if f.endswith('.json')])
            except Exception:
                pass
            
            total_requests = self._stats['hits'] + self._stats['misses']
            hit_rate = (self._stats['hits'] / total_requests * 100) if total_requests > 0 else 0
            
            return {
                'hits': self._stats['hits'],
                'misses': self._stats['misses'],
                'evictions': self._stats['evictions'],
                'hit_rate': round(hit_rate, 2),
                'size': max(len(self._memory_cache), file_count),  # Use max of memory and file count
                'total_requests': total_requests,
                'file_reads': self._stats['file_reads'],
                'file_writes': self._stats['file_writes'],
                'memory_cache_size': len(self._memory_cache),
                'file_cache_size': file_count
            }
    
    def get_size(self) -> int:
        """Get the number of entries in the cache."""
        with self._lock:
            try:
                return len([f for f in os.listdir(self.cache_dir) if f.endswith('.json')])
            except Exception:
                return len(self._memory_cache)


# Global cache manager instance
_cache_manager = CacheManager()


def get_cache_manager() -> CacheManager:
    """Get the global cache manager instance."""
    return _cache_manager


# Cache TTL constants (in seconds)
# Note: These are kept for interface compatibility but not actually used.
# Since data is from yesterday, cache is valid for the entire day (until 23:59:59).
# All cache entries expire at the end of the day regardless of these values.
CACHE_TTL_STOCK_BASICS = 3600  # 保留用于接口兼容性 - 股票基本信息
CACHE_TTL_INDUSTRY_DATA = 3600  # 保留用于接口兼容性 - 行业数据
CACHE_TTL_KLINE_DATA = 300  # 保留用于接口兼容性 - K线数据


def cache_stock_basics(func):
    """
    Decorator to cache stock basics data.
    
    Usage:
        @cache_stock_basics
        def fetch_stock_basics():
            ...
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        cache_key = _cache_manager._generate_key('stock_basics')
        cached_data = _cache_manager.get(cache_key)
        
        if cached_data is not None:
            return cached_data.copy() if hasattr(cached_data, 'copy') else cached_data
        
        # Fetch fresh data
        data = func(*args, **kwargs)
        
        # Cache the data
        _cache_manager.set(cache_key, data.copy() if hasattr(data, 'copy') else data, CACHE_TTL_STOCK_BASICS)
        
        return data
    
    return wrapper


def cache_industry_data(func):
    """
    Decorator to cache industry data.
    
    Usage:
        @cache_industry_data
        def fetch_industry_data():
            ...
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        cache_key = _cache_manager._generate_key('industry_data')
        cached_data = _cache_manager.get(cache_key)
        
        if cached_data is not None:
            return cached_data.copy() if hasattr(cached_data, 'copy') else cached_data
        
        # Fetch fresh data
        data = func(*args, **kwargs)
        
        # Cache the data
        _cache_manager.set(cache_key, data.copy() if hasattr(data, 'copy') else data, CACHE_TTL_INDUSTRY_DATA)
        
        return data
    
    return wrapper


def cache_kline_data(func):
    """
    Decorator to cache K-line data based on stock code and date range.
    
    Usage:
        @cache_kline_data
        def fetch_kline_data(code, start_date, end_date, ...):
            ...
    """
    @wraps(func)
    def wrapper(code: str, start_date: str, end_date: str, *args, **kwargs):
        # Generate cache key based on code and date range
        # Include retry_attempts and retry_delay in key to handle different retry configs
        cache_key = _cache_manager._generate_key(
            'kline_data',
            code,
            start_date,
            end_date,
            retry_attempts=kwargs.get('retry_attempts', 3),
            retry_delay=kwargs.get('retry_delay', 1)
        )
        
        cached_data = _cache_manager.get(cache_key)
        
        if cached_data is not None:
            return cached_data.copy() if hasattr(cached_data, 'copy') else cached_data
        
        # Fetch fresh data
        data = func(code, start_date, end_date, *args, **kwargs)
        
        # Only cache non-empty data
        if not data.empty:
            _cache_manager.set(cache_key, data.copy(), CACHE_TTL_KLINE_DATA)
        
        return data
    
    return wrapper
