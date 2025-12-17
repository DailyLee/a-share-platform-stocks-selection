"""
Database Manager module for managing SQLite database.
Provides a lightweight database solution to replace JSON file storage.
"""
import os
import sqlite3
import json
from typing import Any, Dict, List, Optional
from datetime import datetime
from threading import Lock
import contextlib

# Define database directory and file path
DB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
DB_FILE = os.path.join(DB_DIR, 'app.db')

# Ensure database directory exists
os.makedirs(DB_DIR, exist_ok=True)


class DatabaseManager:
    """
    Thread-safe SQLite database manager.
    Provides connection pooling and transaction management.
    """
    
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        """Singleton pattern to ensure only one DatabaseManager exists."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(DatabaseManager, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the database manager and create tables if needed."""
        if hasattr(self, '_initialized') and self._initialized:
            return
        
        self._initialized = True
        self._init_database()
    
    def _init_database(self):
        """Initialize database schema."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Create cases table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cases (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    stock_code TEXT NOT NULL,
                    stock_name TEXT NOT NULL,
                    description TEXT,
                    tags TEXT,  -- JSON array
                    analysis TEXT,  -- JSON object
                    kline_data TEXT,  -- JSON object
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            ''')
            
            # Create backtest_history table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS backtest_history (
                    id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    config TEXT NOT NULL,  -- JSON object
                    result TEXT NOT NULL,  -- JSON object
                    backtest_date TEXT,
                    stat_date TEXT,
                    use_stop_loss INTEGER DEFAULT 0,
                    use_take_profit INTEGER DEFAULT 0,
                    stop_loss_percent REAL DEFAULT -3.0,
                    take_profit_percent REAL DEFAULT 10.0,
                    summary TEXT  -- JSON object
                )
            ''')
            
            # Create indexes for better query performance
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_cases_stock_code ON cases(stock_code)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_cases_created_at ON cases(created_at)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_backtest_created_at ON backtest_history(created_at)
            ''')
            
            conn.commit()
    
    @contextlib.contextmanager
    def get_connection(self):
        """
        Get a database connection with automatic commit/rollback.
        
        Usage:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(...)
                # Auto-commit on success, auto-rollback on exception
        """
        # Set timeout to 30 seconds to avoid hanging
        try:
            conn = sqlite3.connect(
                DB_FILE, 
                check_same_thread=False, 
                timeout=30.0,
                isolation_level='DEFERRED'  # Better for concurrent access
            )
            conn.row_factory = sqlite3.Row  # Enable column access by name
            # Enable WAL mode and set busy timeout for better concurrency
            conn.execute('PRAGMA journal_mode=WAL')
            conn.execute('PRAGMA busy_timeout=30000')
            try:
                yield conn
                conn.commit()
            except Exception as e:
                conn.rollback()
                from colorama import Fore, Style
                print(f"{Fore.RED}[DatabaseManager] Transaction error: {e}{Style.RESET_ALL}")
                raise
            finally:
                conn.close()
        except Exception as e:
            from colorama import Fore, Style
            print(f"{Fore.RED}[DatabaseManager] Connection error: {e}{Style.RESET_ALL}")
            raise
    
    def execute_query(self, query: str, params: tuple = ()) -> List[sqlite3.Row]:
        """
        Execute a SELECT query and return results.
        
        Args:
            query: SQL query string
            params: Query parameters
        
        Returns:
            List of row objects
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                results = cursor.fetchall()
                return results
        except Exception as e:
            from colorama import Fore, Style
            print(f"{Fore.RED}[DatabaseManager] Query error: {e}{Style.RESET_ALL}")
            import traceback
            traceback.print_exc()
            return []
    
    def execute_update(self, query: str, params: tuple = ()) -> int:
        """
        Execute an INSERT/UPDATE/DELETE query.
        
        Args:
            query: SQL query string
            params: Query parameters
        
        Returns:
            Number of rows affected
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.rowcount
    
    def execute_many(self, query: str, params_list: List[tuple]) -> int:
        """
        Execute a query multiple times with different parameters.
        
        Args:
            query: SQL query string
            params_list: List of parameter tuples
        
        Returns:
            Total number of rows affected
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(query, params_list)
            return cursor.rowcount
    
    def get_table_count(self, table_name: str) -> int:
        """
        Get the number of rows in a table.
        
        Args:
            table_name: Name of the table
        
        Returns:
            Number of rows
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f'SELECT COUNT(*) FROM {table_name}')
            return cursor.fetchone()[0]
    
    def vacuum(self):
        """Optimize database by running VACUUM."""
        with self.get_connection() as conn:
            conn.execute('VACUUM')


# Global database manager instance
_db_manager = None


def get_database_manager() -> DatabaseManager:
    """Get the global database manager instance."""
    global _db_manager
    if _db_manager is None:
        with DatabaseManager._lock:
            if _db_manager is None:
                _db_manager = DatabaseManager()
    return _db_manager

