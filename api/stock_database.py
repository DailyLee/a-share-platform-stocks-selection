"""
Stock Database Manager module for storing and retrieving historical stock data.
Implements SQLite-based storage with thread-safe operations.
"""
import os
import sqlite3
import pandas as pd
from typing import Optional, List, Tuple, Dict, Any
from datetime import datetime, timedelta, date
from threading import Lock
import threading
from contextlib import contextmanager

# Define database directory and file
DB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
DB_FILE = os.path.join(DB_DIR, 'stocks.db')

# Ensure database directory exists
os.makedirs(DB_DIR, exist_ok=True)


class StockDatabase:
    """
    Thread-safe SQLite database manager for stock historical data.
    """
    
    def __init__(self, db_path: str = DB_FILE):
        """
        Initialize the database manager.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self._lock = Lock()
        self._local = threading.local()
        
        # Initialize database on first use
        self._initialize_database()
    
    def _get_connection(self) -> sqlite3.Connection:
        """
        Get a thread-local database connection.
        
        Returns:
            SQLite connection
        """
        if not hasattr(self._local, 'connection') or self._local.connection is None:
            self._local.connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                timeout=30.0
            )
            # Enable WAL mode for better concurrency
            self._local.connection.execute('PRAGMA journal_mode=WAL')
            # Set foreign keys
            self._local.connection.execute('PRAGMA foreign_keys=ON')
        return self._local.connection
    
    @contextmanager
    def _transaction(self):
        """
        Context manager for database transactions.
        """
        conn = self._get_connection()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
    
    def _initialize_database(self):
        """
        Initialize database tables if they don't exist.
        """
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Create stock_basics table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS stock_basics (
                    code TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    type TEXT,
                    status TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create industry_data table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS industry_data (
                    code TEXT PRIMARY KEY,
                    industry TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (code) REFERENCES stock_basics(code)
                )
            ''')
            
            # Create kline_data table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS kline_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT NOT NULL,
                    date DATE NOT NULL,
                    open REAL,
                    high REAL,
                    low REAL,
                    close REAL,
                    volume REAL,
                    turn REAL,
                    preclose REAL,
                    pctChg REAL,
                    peTTM REAL,
                    pbMRQ REAL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(code, date),
                    FOREIGN KEY (code) REFERENCES stock_basics(code)
                )
            ''')
            
            # Create indexes for better query performance
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_kline_code_date 
                ON kline_data(code, date)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_kline_date 
                ON kline_data(date)
            ''')
            
            conn.commit()
    
    def is_empty(self) -> bool:
        """
        Check if the database is empty (no stock basics data).
        
        Returns:
            True if database is empty, False otherwise
        """
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM stock_basics')
            count = cursor.fetchone()[0]
            return count == 0
    
    def save_stock_basics(self, df: pd.DataFrame) -> None:
        """
        Save stock basics data to database.
        
        Args:
            df: DataFrame containing stock basic information
        """
        with self._lock:
            with self._transaction() as conn:
                # Clear existing data
                conn.execute('DELETE FROM stock_basics')
                
                # Insert new data
                for _, row in df.iterrows():
                    conn.execute('''
                        INSERT OR REPLACE INTO stock_basics 
                        (code, name, type, status, updated_at)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (
                        row['code'],
                        row.get('code_name', ''),
                        row.get('type', ''),
                        row.get('status', ''),
                        datetime.now()
                    ))
    
    def get_stock_basics(self) -> Optional[pd.DataFrame]:
        """
        Get stock basics data from database.
        
        Returns:
            DataFrame containing stock basic information, or None if empty
        """
        with self._lock:
            conn = self._get_connection()
            df = pd.read_sql_query('SELECT * FROM stock_basics', conn)
            if df.empty:
                return None
            # Rename 'name' column to 'code_name' to match API format
            if 'name' in df.columns:
                df = df.rename(columns={'name': 'code_name'})
            return df
    
    def save_industry_data(self, df: pd.DataFrame) -> None:
        """
        Save industry data to database.
        
        Args:
            df: DataFrame containing industry classification
        """
        with self._lock:
            with self._transaction() as conn:
                # Clear existing data
                conn.execute('DELETE FROM industry_data')
                
                # Insert new data
                for _, row in df.iterrows():
                    conn.execute('''
                        INSERT OR REPLACE INTO industry_data 
                        (code, industry, updated_at)
                        VALUES (?, ?, ?)
                    ''', (
                        row['code'],
                        row.get('industry', ''),
                        datetime.now()
                    ))
    
    def get_industry_data(self) -> Optional[pd.DataFrame]:
        """
        Get industry data from database.
        
        Returns:
            DataFrame containing industry classification, or None if empty
        """
        with self._lock:
            conn = self._get_connection()
            df = pd.read_sql_query('SELECT * FROM industry_data', conn)
            if df.empty:
                return None
            return df
    
    def get_kline_data(self, code: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        Get K-line data from database for a specific stock and date range.
        
        Args:
            code: Stock code (e.g., 'sh.600000')
            start_date: Start date in 'YYYY-MM-DD' format
            end_date: End date in 'YYYY-MM-DD' format
        
        Returns:
            DataFrame containing K-line data
        """
        with self._lock:
            conn = self._get_connection()
            query = '''
                SELECT date, open, high, low, close, volume, turn, 
                       preclose, pctChg, peTTM, pbMRQ
                FROM kline_data
                WHERE code = ? AND date >= ? AND date <= ?
                ORDER BY date ASC
            '''
            df = pd.read_sql_query(query, conn, params=(code, start_date, end_date))
            
            if not df.empty:
                # Convert date column to datetime
                df['date'] = pd.to_datetime(df['date'])
                # Convert numeric columns
                numeric_cols = ['open', 'high', 'low', 'close', 'volume', 'turn', 
                              'preclose', 'pctChg', 'peTTM', 'pbMRQ']
                for col in numeric_cols:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
            
            return df
    
    def get_kline_date_range(self, code: str) -> Optional[Tuple[str, str]]:
        """
        Get the date range of available K-line data for a stock.
        
        Args:
            code: Stock code
        
        Returns:
            Tuple of (min_date, max_date) in 'YYYY-MM-DD' format, or None if no data
        """
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT MIN(date), MAX(date) 
                FROM kline_data 
                WHERE code = ?
            ''', (code,))
            result = cursor.fetchone()
            if result and result[0] and result[1]:
                return (result[0], result[1])
            return None
    
    def save_kline_data(self, code: str, df: pd.DataFrame) -> None:
        """
        Save K-line data to database for a specific stock.
        Uses INSERT OR REPLACE to handle duplicates.
        
        Args:
            code: Stock code
            df: DataFrame containing K-line data
        """
        if df.empty:
            return
        
        with self._lock:
            with self._transaction() as conn:
                for _, row in df.iterrows():
                    # Convert date to string if it's a datetime
                    date_str = str(row['date'])
                    if isinstance(row['date'], pd.Timestamp):
                        date_str = row['date'].strftime('%Y-%m-%d')
                    
                    conn.execute('''
                        INSERT OR REPLACE INTO kline_data 
                        (code, date, open, high, low, close, volume, turn, 
                         preclose, pctChg, peTTM, pbMRQ, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        code,
                        date_str,
                        row.get('open'),
                        row.get('high'),
                        row.get('low'),
                        row.get('close'),
                        row.get('volume'),
                        row.get('turn'),
                        row.get('preclose'),
                        row.get('pctChg'),
                        row.get('peTTM'),
                        row.get('pbMRQ'),
                        datetime.now()
                    ))
    
    def get_missing_date_ranges(self, code: str, start_date: str, end_date: str) -> List[Tuple[str, str]]:
        """
        Get missing date ranges in the database for a stock.
        
        Args:
            code: Stock code
            start_date: Start date in 'YYYY-MM-DD' format
            end_date: End date in 'YYYY-MM-DD' format
        
        Returns:
            List of tuples (gap_start, gap_end) representing missing date ranges
        """
        # Get existing data range
        existing_range = self.get_kline_date_range(code)
        
        if existing_range is None:
            # No data at all, return the full range
            return [(start_date, end_date)]
        
        existing_start, existing_end = existing_range
        missing_ranges = []
        
        # Check for gap before existing data
        if start_date < existing_start:
            missing_ranges.append((start_date, existing_start))
        
        # Check for gap after existing data
        if end_date > existing_end:
            missing_ranges.append((existing_end, end_date))
        
        # Check for gaps within existing data
        # This is a simplified version - in production, you might want to check for actual gaps
        # For now, we'll assume continuous data within the existing range
        
        return missing_ranges
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get database statistics.
        
        Returns:
            Dictionary with database statistics
        """
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Count stocks
            cursor.execute('SELECT COUNT(*) FROM stock_basics')
            stock_count = cursor.fetchone()[0]
            
            # Count industry records
            cursor.execute('SELECT COUNT(*) FROM industry_data')
            industry_count = cursor.fetchone()[0]
            
            # Count K-line records
            cursor.execute('SELECT COUNT(*) FROM kline_data')
            kline_count = cursor.fetchone()[0]
            
            # Count unique stocks with K-line data
            cursor.execute('SELECT COUNT(DISTINCT code) FROM kline_data')
            stocks_with_data = cursor.fetchone()[0]
            
            # Get date range
            cursor.execute('SELECT MIN(date), MAX(date) FROM kline_data')
            date_range = cursor.fetchone()
            
            return {
                'stock_count': stock_count,
                'industry_count': industry_count,
                'kline_records': kline_count,
                'stocks_with_data': stocks_with_data,
                'date_range': {
                    'min_date': date_range[0] if date_range[0] else None,
                    'max_date': date_range[1] if date_range[1] else None
                }
            }
    
    def close(self):
        """
        Close all database connections.
        """
        with self._lock:
            if hasattr(self._local, 'connection') and self._local.connection:
                self._local.connection.close()
                self._local.connection = None


# Global database instance
_db_instance = None
_db_lock = Lock()


def get_stock_database() -> StockDatabase:
    """
    Get the global stock database instance (thread-safe singleton).
    
    Returns:
        StockDatabase instance
    """
    global _db_instance
    if _db_instance is None:
        with _db_lock:
            if _db_instance is None:
                _db_instance = StockDatabase()
    return _db_instance

