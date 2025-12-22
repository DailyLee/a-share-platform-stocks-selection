"""
Stock Database Manager module for storing and retrieving historical stock data.
Implements SQLite-based storage with thread-safe operations.
"""
import os
import sqlite3
import pandas as pd
import json
from typing import Optional, List, Tuple, Dict, Any
from datetime import datetime, timedelta, date, timezone
from threading import Lock
import threading
from contextlib import contextmanager

# Define database directory and file
DB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
DB_FILE = os.path.join(DB_DIR, 'stocks.db')

# Ensure database directory exists
os.makedirs(DB_DIR, exist_ok=True)


def normalize_timestamp_to_utc(timestamp) -> str:
    """
    Normalize timestamp to UTC ISO format string.
    
    Args:
        timestamp: Timestamp value (datetime object or string)
    
    Returns:
        UTC ISO format string (e.g., '2024-01-01T12:00:00+00:00')
    """
    if timestamp is None:
        return None
    
    # If it's already a string, try to parse and convert to UTC
    if isinstance(timestamp, str):
        try:
            # Try parsing ISO format
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            # If timezone-naive, assume it's UTC
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            # Convert to UTC
            dt_utc = dt.astimezone(timezone.utc)
            return dt_utc.isoformat()
        except (ValueError, AttributeError):
            # If parsing fails, return as-is (fallback)
            return timestamp
    
    # If it's a datetime object
    if isinstance(timestamp, datetime):
        # If timezone-naive, assume it's UTC
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        # Convert to UTC
        dt_utc = timestamp.astimezone(timezone.utc)
        return dt_utc.isoformat()
    
    # Fallback: return as string
    return str(timestamp)


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
        self._pid = os.getpid()  # Track the process ID
        
        # Initialize database on first use
        self._initialize_database()
    
    def _get_connection(self) -> sqlite3.Connection:
        """
        Get a thread-local and process-local database connection.
        Ensures connections are recreated after fork.
        
        Returns:
            SQLite connection
        """
        current_pid = os.getpid()
        
        # Check if we're in a different process (after fork)
        if current_pid != self._pid:
            # We're in a forked child process, need to recreate connection
            self._pid = current_pid
            self._local = threading.local()  # Reset thread-local storage
        
        if not hasattr(self._local, 'connection') or self._local.connection is None:
            self._local.connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                timeout=5.0,  # Reduce to 5 seconds for faster timeout
                isolation_level='DEFERRED'  # Better for concurrent access
            )
            # Enable WAL mode for better concurrency
            self._local.connection.execute('PRAGMA journal_mode=WAL')
            # Set foreign keys
            self._local.connection.execute('PRAGMA foreign_keys=ON')
            # Set busy timeout to handle locks (5 seconds)
            self._local.connection.execute('PRAGMA busy_timeout=5000')
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
            
            # Create cases table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cases (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    stock_code TEXT NOT NULL,
                    stock_name TEXT NOT NULL,
                    tags TEXT,
                    description TEXT,
                    analysis TEXT,
                    kline_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create backtest_history table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS backtest_history (
                    id TEXT PRIMARY KEY,
                    config TEXT NOT NULL,
                    result TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    batch_task_id TEXT
                )
            ''')
            
            # Create indexes for cases
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_cases_stock_code 
                ON cases(stock_code)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_cases_created_at 
                ON cases(created_at)
            ''')
            
            # Create index for backtest_history
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_backtest_created_at 
                ON backtest_history(created_at)
            ''')
            
            # Create scan_cache table for storing scan results
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS scan_cache (
                    cache_key TEXT PRIMARY KEY,
                    scan_config TEXT NOT NULL,
                    backtest_date TEXT NOT NULL,
                    scanned_stocks TEXT NOT NULL,
                    total_scanned INTEGER,
                    success_count INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Add new columns if they don't exist (for existing databases)
            try:
                cursor.execute('ALTER TABLE scan_cache ADD COLUMN total_scanned INTEGER')
            except sqlite3.OperationalError:
                pass  # Column already exists
            
            try:
                cursor.execute('ALTER TABLE scan_cache ADD COLUMN success_count INTEGER')
            except sqlite3.OperationalError:
                pass  # Column already exists
            
            # Add batch_task_id column to backtest_history if it doesn't exist
            try:
                cursor.execute('ALTER TABLE backtest_history ADD COLUMN batch_task_id TEXT')
            except sqlite3.OperationalError:
                pass  # Column already exists
            
            # Create index for batch_task_id
            try:
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_backtest_batch_task_id 
                    ON backtest_history(batch_task_id)
                ''')
            except sqlite3.OperationalError:
                pass  # Index might already exist
            
            # Create index for scan_cache
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_scan_cache_backtest_date 
                ON scan_cache(backtest_date)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_scan_cache_created_at 
                ON scan_cache(created_at)
            ''')
            
            # Create batch_scan_tasks table for batch scanning
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS batch_scan_tasks (
                    id TEXT PRIMARY KEY,
                    task_name TEXT NOT NULL,
                    start_date TEXT NOT NULL,
                    end_date TEXT NOT NULL,
                    scan_period_days INTEGER NOT NULL DEFAULT 7,
                    scan_config TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    total_scans INTEGER DEFAULT 0,
                    completed_scans INTEGER DEFAULT 0,
                    failed_scans INTEGER DEFAULT 0,
                    current_scan_date TEXT,
                    progress INTEGER DEFAULT 0,
                    message TEXT,
                    error TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP
                )
            ''')
            
            # Create batch_scan_results table for storing individual scan results
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS batch_scan_results (
                    id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL,
                    scan_date TEXT NOT NULL,
                    scan_config TEXT NOT NULL,
                    scanned_stocks TEXT NOT NULL,
                    total_scanned INTEGER,
                    success_count INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (task_id) REFERENCES batch_scan_tasks(id) ON DELETE CASCADE
                )
            ''')
            
            # Create indexes for batch scan tables
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_batch_scan_tasks_status 
                ON batch_scan_tasks(status)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_batch_scan_tasks_created_at 
                ON batch_scan_tasks(created_at)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_batch_scan_results_task_id 
                ON batch_scan_results(task_id)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_batch_scan_results_scan_date 
                ON batch_scan_results(scan_date)
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
                # Get list of new stock codes
                new_codes = set(df['code'].tolist())
                
                # Get list of existing stock codes
                cursor = conn.cursor()
                cursor.execute('SELECT code FROM stock_basics')
                existing_codes = set(row[0] for row in cursor.fetchall())
                
                # Find codes that need to be removed (exist in DB but not in new data)
                codes_to_remove = existing_codes - new_codes
                
                # Disable foreign key constraints temporarily to avoid constraint errors
                conn.execute('PRAGMA foreign_keys=OFF')
                
                try:
                    # Delete industry_data for removed stocks (if any)
                    if codes_to_remove:
                        placeholders = ','.join(['?'] * len(codes_to_remove))
                        conn.execute(f'DELETE FROM industry_data WHERE code IN ({placeholders})', list(codes_to_remove))
                        # Note: We don't delete kline_data to preserve historical data
                        # K-line data can remain even if stock is removed from basics
                    
                    # Delete stock_basics for removed stocks (if any)
                    if codes_to_remove:
                        placeholders = ','.join(['?'] * len(codes_to_remove))
                        conn.execute(f'DELETE FROM stock_basics WHERE code IN ({placeholders})', list(codes_to_remove))
                    
                    # Re-enable foreign key constraints
                    conn.execute('PRAGMA foreign_keys=ON')
                    
                    # Insert or update new data
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
                finally:
                    # Always re-enable foreign key constraints
                    conn.execute('PRAGMA foreign_keys=ON')
    
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
        import time
        from colorama import Fore, Style
        start_time = time.time()
        print(f"{Fore.CYAN}[SCAN_CHECKPOINT] 🔒 Acquiring DB lock for get_kline_data({code})...{Style.RESET_ALL}")
        
        with self._lock:
            lock_acquired = time.time()
            print(f"{Fore.CYAN}[SCAN_CHECKPOINT] ✓ DB lock acquired for {code} (waited {lock_acquired - start_time:.3f}s){Style.RESET_ALL}")
            
            conn = self._get_connection()
            query = '''
                SELECT date, open, high, low, close, volume, turn, 
                       preclose, pctChg, peTTM, pbMRQ
                FROM kline_data
                WHERE code = ? AND date >= ? AND date <= ?
                ORDER BY date ASC
            '''
            print(f"{Fore.CYAN}[SCAN_CHECKPOINT] 📖 Executing SQL query for {code}...{Style.RESET_ALL}")
            df = pd.read_sql_query(query, conn, params=(code, start_date, end_date))
            query_end = time.time()
            print(f"{Fore.CYAN}[SCAN_CHECKPOINT] ✓ Query completed for {code} (took {query_end - lock_acquired:.3f}s, {len(df)} rows){Style.RESET_ALL}")
            
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
        
        import time
        from colorama import Fore, Style
        start_time = time.time()
        print(f"{Fore.CYAN}[SCAN_CHECKPOINT] 🔒 Acquiring DB lock for save_kline_data({code}, {len(df)} rows)...{Style.RESET_ALL}")
        
        with self._lock:
            lock_acquired = time.time()
            print(f"{Fore.CYAN}[SCAN_CHECKPOINT] ✓ DB lock acquired for save {code} (waited {lock_acquired - start_time:.3f}s){Style.RESET_ALL}")
            
            with self._transaction() as conn:
                print(f"{Fore.CYAN}[SCAN_CHECKPOINT] 💾 Starting transaction to save {len(df)} rows for {code}...{Style.RESET_ALL}")
                for idx, row in df.iterrows():
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
                
                save_end = time.time()
                print(f"{Fore.GREEN}[SCAN_CHECKPOINT] ✓ Transaction committed for {code} (took {save_end - lock_acquired:.3f}s){Style.RESET_ALL}")
    
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
    
    # ==================== Case Management Methods ====================
    
    def get_cases(self) -> List[Dict[str, Any]]:
        """
        Get all cases from database.
        
        Returns:
            List of case metadata
        """
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, title, stock_code, stock_name, tags, created_at, updated_at
                FROM cases
                ORDER BY created_at DESC
            ''')
            rows = cursor.fetchall()
            
            cases = []
            for row in rows:
                case = {
                    'id': row[0],
                    'title': row[1],
                    'stockCode': row[2],
                    'stockName': row[3],
                    'tags': json.loads(row[4]) if row[4] else [],
                    'createdAt': row[5],
                    'updatedAt': row[6]
                }
                cases.append(case)
            
            return cases
    
    def get_case(self, case_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific case by ID.
        
        Args:
            case_id: The ID of the case
        
        Returns:
            Case data if found, None otherwise
        """
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, title, stock_code, stock_name, tags, description, 
                       analysis, kline_data, created_at, updated_at
                FROM cases
                WHERE id = ?
            ''', (case_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            case = {
                'id': row[0],
                'title': row[1],
                'stockCode': row[2],
                'stockName': row[3],
                'tags': json.loads(row[4]) if row[4] else [],
                'createdAt': row[8],
                'updatedAt': row[9]
            }
            
            if row[5]:  # description
                case['description'] = row[5]
            if row[6]:  # analysis
                case['analysis'] = json.loads(row[6])
            if row[7]:  # kline_data
                case['kline_data'] = json.loads(row[7])
            
            return case
    
    def create_case(self, case_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new case.
        
        Args:
            case_data: The case data to create
        
        Returns:
            The created case data
        """
        with self._lock:
            with self._transaction() as conn:
                cursor = conn.cursor()
                
                # Generate case ID if not provided
                if 'id' not in case_data:
                    case_data['id'] = f"case_{int(datetime.now().timestamp())}"
                
                # Set timestamps
                now = datetime.now().isoformat()
                case_data['createdAt'] = now
                case_data['updatedAt'] = now
                
                # Ensure tags is a list
                if 'tags' not in case_data:
                    case_data['tags'] = []
                
                # Insert case
                cursor.execute('''
                    INSERT INTO cases 
                    (id, title, stock_code, stock_name, tags, description, analysis, kline_data, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    case_data['id'],
                    case_data['title'],
                    case_data['stockCode'],
                    case_data['stockName'],
                    json.dumps(case_data['tags'], ensure_ascii=False),
                    case_data.get('description'),
                    json.dumps(case_data.get('analysis'), ensure_ascii=False) if case_data.get('analysis') else None,
                    json.dumps(case_data.get('kline_data'), ensure_ascii=False) if case_data.get('kline_data') else None,
                    now,
                    now
                ))
                
                return case_data
    
    def update_case(self, case_id: str, case_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update an existing case.
        
        Args:
            case_id: The ID of the case to update
            case_data: The new case data
        
        Returns:
            The updated case data if successful, None otherwise
        """
        with self._lock:
            # Check if case exists
            existing = self.get_case(case_id)
            if not existing:
                return None
            
            with self._transaction() as conn:
                cursor = conn.cursor()
                now = datetime.now().isoformat()
                
                # Build update query dynamically
                updates = []
                values = []
                
                if 'title' in case_data:
                    updates.append('title = ?')
                    values.append(case_data['title'])
                
                if 'stockCode' in case_data:
                    updates.append('stock_code = ?')
                    values.append(case_data['stockCode'])
                
                if 'stockName' in case_data:
                    updates.append('stock_name = ?')
                    values.append(case_data['stockName'])
                
                if 'tags' in case_data:
                    updates.append('tags = ?')
                    values.append(json.dumps(case_data['tags'], ensure_ascii=False))
                
                if 'description' in case_data:
                    updates.append('description = ?')
                    values.append(case_data['description'])
                
                if 'analysis' in case_data:
                    updates.append('analysis = ?')
                    values.append(json.dumps(case_data['analysis'], ensure_ascii=False))
                
                if 'kline_data' in case_data:
                    updates.append('kline_data = ?')
                    values.append(json.dumps(case_data['kline_data'], ensure_ascii=False))
                
                updates.append('updated_at = ?')
                values.append(now)
                values.append(case_id)
                
                cursor.execute(f'''
                    UPDATE cases
                    SET {', '.join(updates)}
                    WHERE id = ?
                ''', values)
                
                return self.get_case(case_id)
    
    def delete_case(self, case_id: str) -> bool:
        """
        Delete a case.
        
        Args:
            case_id: The ID of the case to delete
        
        Returns:
            True if deleted, False otherwise
        """
        with self._lock:
            with self._transaction() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM cases WHERE id = ?', (case_id,))
                return cursor.rowcount > 0
    
    # ==================== Backtest History Methods ====================
    
    def save_backtest_history(self, config: Dict[str, Any], result: Dict[str, Any], batch_task_id: Optional[str] = None) -> str:
        """
        Save a backtest history record.
        
        Args:
            config: Backtest configuration
            result: Backtest result
            batch_task_id: Optional batch task ID for batch backtests
        
        Returns:
            The ID of the saved history record
        """
        with self._lock:
            with self._transaction() as conn:
                cursor = conn.cursor()
                
                # Generate a unique ID
                history_id = f"backtest_{int(datetime.now().timestamp() * 1000)}"
                now = datetime.now().isoformat()
                
                # Insert history record
                cursor.execute('''
                    INSERT INTO backtest_history (id, config, result, created_at, batch_task_id)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    history_id,
                    json.dumps(config, ensure_ascii=False),
                    json.dumps(result, ensure_ascii=False),
                    now,
                    batch_task_id
                ))
                
                return history_id
    
    def get_backtest_history_list(self, limit: int = 100, batch_task_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get list of all backtest history records (metadata only).
        
        Args:
            limit: Maximum number of records to return
            batch_task_id: Optional filter by batch task ID
        
        Returns:
            List of history record metadata
        """
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            if batch_task_id:
                cursor.execute('''
                    SELECT id, config, result, created_at, batch_task_id
                    FROM backtest_history
                    WHERE batch_task_id = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                ''', (batch_task_id, limit))
            else:
                cursor.execute('''
                    SELECT id, config, result, created_at, batch_task_id
                    FROM backtest_history
                    ORDER BY created_at DESC
                    LIMIT ?
                ''', (limit,))
            
            rows = cursor.fetchall()
            
            records = []
            for row in rows:
                config = json.loads(row[1])
                result = json.loads(row[2])
                
                # 检查是否是失败记录
                is_failed = result.get('status') == 'failed' or config.get('status') == 'failed'
                
                record = {
                    'id': row[0],
                    'createdAt': row[3],
                    'backtestDate': config.get('backtest_date', ''),
                    'statDate': config.get('stat_date', ''),
                    'backtestName': config.get('backtest_name'),  # 回测名称
                    'useStopLoss': config.get('use_stop_loss', False),
                    'useTakeProfit': config.get('use_take_profit', False),
                    'stopLossPercent': config.get('stop_loss_percent', -3.0),
                    'takeProfitPercent': config.get('take_profit_percent', 10.0),
                    'summary': result.get('summary', {}),
                    'batchTaskId': row[4] if len(row) > 4 else None,
                    'status': 'failed' if is_failed else 'completed',
                    'error': result.get('error') if is_failed else None
                }
                records.append(record)
            
            return records
    
    def get_backtest_history(self, history_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific backtest history record by ID.
        
        Args:
            history_id: The ID of the history record
        
        Returns:
            Full history record if found, None otherwise
        """
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, config, result, created_at, batch_task_id
                FROM backtest_history
                WHERE id = ?
            ''', (history_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            return {
                'id': row[0],
                'createdAt': row[3],
                'config': json.loads(row[1]),
                'result': json.loads(row[2]),
                'batchTaskId': row[4] if len(row) > 4 else None
            }
    
    def delete_backtest_history(self, history_id: str) -> bool:
        """
        Delete a backtest history record.
        
        Args:
            history_id: The ID of the history record to delete
        
        Returns:
            True if deleted successfully, False otherwise
        """
        with self._lock:
            with self._transaction() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM backtest_history WHERE id = ?', (history_id,))
                return cursor.rowcount > 0
    
    def clear_all_backtest_history(self) -> int:
        """
        Clear all backtest history records.
        
        Returns:
            Number of records deleted
        """
        with self._lock:
            with self._transaction() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM backtest_history')
                count = cursor.fetchone()[0]
                cursor.execute('DELETE FROM backtest_history')
                return count
    
    def delete_backtest_history_by_date(self, backtest_date: str) -> int:
        """
        Delete all backtest history records for a specific backtest date.
        
        Args:
            backtest_date: Backtest date string (YYYY-MM-DD)
        
        Returns:
            Number of records deleted
        """
        with self._lock:
            with self._transaction() as conn:
                cursor = conn.cursor()
                # Get all records and filter by backtest_date in config JSON
                cursor.execute('SELECT id, config FROM backtest_history')
                rows = cursor.fetchall()
                
                deleted_ids = []
                for row in rows:
                    try:
                        config = json.loads(row[1])
                        if config.get('backtest_date') == backtest_date:
                            deleted_ids.append(row[0])
                    except (json.JSONDecodeError, TypeError):
                        continue
                
                if deleted_ids:
                    placeholders = ','.join(['?'] * len(deleted_ids))
                    cursor.execute(f'DELETE FROM backtest_history WHERE id IN ({placeholders})', deleted_ids)
                    return len(deleted_ids)
                return 0
    
    def check_backtest_exists(self, config: Dict[str, Any]) -> Optional[str]:
        """
        Check if a backtest record already exists based on configuration.
        
        Args:
            config: Backtest configuration dictionary containing:
                - backtest_date: str
                - stat_date: str
                - use_stop_loss: bool
                - use_take_profit: bool
                - stop_loss_percent: float
                - take_profit_percent: float
                - selected_stocks: List[Dict] (optional, for comparison)
        
        Returns:
            The ID of existing record if found, None otherwise
        """
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Get all backtest history records
            cursor.execute('''
                SELECT id, config
                FROM backtest_history
            ''')
            rows = cursor.fetchall()
            
            # Compare each record's config
            for row in rows:
                try:
                    existing_config = json.loads(row[1])
                    
                    # Compare key fields
                    if (existing_config.get('backtest_date') == config.get('backtest_date') and
                        existing_config.get('stat_date') == config.get('stat_date') and
                        existing_config.get('use_stop_loss') == config.get('use_stop_loss') and
                        existing_config.get('use_take_profit') == config.get('use_take_profit') and
                        existing_config.get('stop_loss_percent') == config.get('stop_loss_percent') and
                        existing_config.get('take_profit_percent') == config.get('take_profit_percent')):
                        
                        # Optionally compare selected_stocks if provided
                        if 'selected_stocks' in config:
                            existing_stocks = existing_config.get('selected_stocks', [])
                            new_stocks = config.get('selected_stocks', [])
                            
                            # Compare stock codes
                            existing_codes = set(s.get('code') for s in existing_stocks if isinstance(s, dict))
                            new_codes = set(s.get('code') for s in new_stocks if isinstance(s, dict))
                            
                            if existing_codes == new_codes:
                                return row[0]  # Found matching record
                        else:
                            # If selected_stocks not provided in config, just match on other fields
                            return row[0]
                except (json.JSONDecodeError, TypeError):
                    continue  # Skip invalid records
            
            return None  # No matching record found
    
    def save_scan_cache(self, cache_key: str, scan_config: Dict[str, Any], 
                       backtest_date: str, scanned_stocks: List[Dict[str, Any]],
                       total_scanned: Optional[int] = None,
                       success_count: Optional[int] = None) -> None:
        """
        Save scan results to cache.
        
        Args:
            cache_key: Unique cache key (hash of scan_config + backtest_date)
            scan_config: Scan configuration dictionary
            backtest_date: Backtest date string (YYYY-MM-DD)
            scanned_stocks: List of scanned stock dictionaries
            total_scanned: Total number of stocks scanned
            success_count: Number of stocks successfully analyzed
        """
        with self._lock:
            with self._transaction() as conn:
                cursor = conn.cursor()
                # Use UTC time for timestamps
                now_utc = datetime.now(timezone.utc).isoformat()
                
                # Check if record exists
                cursor.execute('SELECT cache_key FROM scan_cache WHERE cache_key = ?', (cache_key,))
                exists = cursor.fetchone() is not None
                
                if exists:
                    # Update existing record, preserve created_at
                    cursor.execute('''
                        UPDATE scan_cache 
                        SET scan_config = ?, backtest_date = ?, scanned_stocks = ?, 
                            total_scanned = ?, success_count = ?, updated_at = ?
                        WHERE cache_key = ?
                    ''', (
                        json.dumps(scan_config, sort_keys=True, ensure_ascii=False),
                        backtest_date,
                        json.dumps(scanned_stocks, ensure_ascii=False, default=str),
                        total_scanned,
                        success_count,
                        now_utc,
                        cache_key
                    ))
                else:
                    # Insert new record with both created_at and updated_at
                    cursor.execute('''
                        INSERT INTO scan_cache 
                        (cache_key, scan_config, backtest_date, scanned_stocks, total_scanned, success_count, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        cache_key,
                        json.dumps(scan_config, sort_keys=True, ensure_ascii=False),
                        backtest_date,
                        json.dumps(scanned_stocks, ensure_ascii=False, default=str),
                        total_scanned,
                        success_count,
                        now_utc,
                        now_utc
                    ))
    
    def get_scan_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """
        Get scan results from cache.
        
        Args:
            cache_key: Unique cache key (hash of scan_config + backtest_date)
        
        Returns:
            Dictionary containing scan_config, backtest_date, and scanned_stocks,
            or None if not found
        """
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT scan_config, backtest_date, scanned_stocks, created_at
                FROM scan_cache
                WHERE cache_key = ?
            ''', (cache_key,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            return {
                'scan_config': json.loads(row[0]),
                'backtest_date': row[1],
                'scanned_stocks': json.loads(row[2]),
                'created_at': normalize_timestamp_to_utc(row[3])
            }
    
    def clear_scan_cache(self, cache_key: Optional[str] = None) -> int:
        """
        Clear scan cache. If cache_key is provided, clear only that entry.
        Otherwise, clear all cache entries.
        
        Args:
            cache_key: Optional cache key to clear specific entry
        
        Returns:
            Number of records deleted
        """
        with self._lock:
            with self._transaction() as conn:
                cursor = conn.cursor()
                if cache_key:
                    cursor.execute('DELETE FROM scan_cache WHERE cache_key = ?', (cache_key,))
                else:
                    cursor.execute('SELECT COUNT(*) FROM scan_cache')
                    count = cursor.fetchone()[0]
                    cursor.execute('DELETE FROM scan_cache')
                    return count
                return cursor.rowcount
    
    def get_scan_history_list(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get list of all scan history records (metadata only).
        
        Args:
            limit: Maximum number of records to return
        
        Returns:
            List of history record metadata
        """
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT cache_key, scan_config, backtest_date, scanned_stocks, total_scanned, success_count, created_at, updated_at
                FROM scan_cache
                ORDER BY created_at DESC
                LIMIT ?
            ''', (limit,))
            rows = cursor.fetchall()
            
            records = []
            for row in rows:
                try:
                    scan_config = json.loads(row[1])
                    scanned_stocks = json.loads(row[3])  # row[3] is scanned_stocks, row[2] is backtest_date
                except (json.JSONDecodeError, TypeError) as e:
                    # If JSON parsing fails, skip this record or use empty values
                    print(f"Warning: Failed to parse JSON for scan cache {row[0]}: {e}")
                    scan_config = {}
                    scanned_stocks = []
                
                record = {
                    'id': row[0],  # Use cache_key as id
                    'cacheKey': row[0],
                    'createdAt': normalize_timestamp_to_utc(row[6]),
                    'updatedAt': normalize_timestamp_to_utc(row[7]),
                    'scanDate': row[2],  # backtest_date is the scan date
                    'stockCount': len(scanned_stocks) if isinstance(scanned_stocks, list) else 0,
                    'scanConfig': scan_config,
                    'totalScanned': row[4],  # total_scanned
                    'successCount': row[5]  # success_count
                }
                records.append(record)
            
            return records
    
    def get_scan_history(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific scan history record by cache_key.
        
        Args:
            cache_key: The cache key of the scan record
        
        Returns:
            Full scan history record if found, None otherwise
        """
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT cache_key, scan_config, backtest_date, scanned_stocks, created_at, updated_at
                FROM scan_cache
                WHERE cache_key = ?
            ''', (cache_key,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            try:
                scan_config = json.loads(row[1])
                scanned_stocks = json.loads(row[3])  # row[3] is scanned_stocks, row[2] is backtest_date
            except (json.JSONDecodeError, TypeError) as e:
                print(f"Warning: Failed to parse JSON for scan cache {row[0]}: {e}")
                scan_config = {}
                scanned_stocks = []
            
            return {
                'id': row[0],
                'cacheKey': row[0],
                'createdAt': normalize_timestamp_to_utc(row[4]),
                'updatedAt': normalize_timestamp_to_utc(row[5]),
                'scanDate': row[2],  # backtest_date is the scan date
                'scanConfig': scan_config,
                'scannedStocks': scanned_stocks
            }
    
    def delete_scan_history(self, cache_key: str) -> bool:
        """
        Delete a scan history record.
        
        Args:
            cache_key: The cache key of the scan record to delete
        
        Returns:
            True if deleted successfully, False otherwise
        """
        with self._lock:
            with self._transaction() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM scan_cache WHERE cache_key = ?', (cache_key,))
                return cursor.rowcount > 0
    
    def save_batch_scan_task(self, task_id: str, task_name: str, start_date: str, 
                             end_date: str, scan_period_days: int, scan_config: Dict[str, Any]) -> None:
        """
        Save a batch scan task.
        
        Args:
            task_id: Unique task ID
            task_name: User-defined task name
            start_date: Start date in 'YYYY-MM-DD' format
            end_date: End date in 'YYYY-MM-DD' format
            scan_period_days: Number of days between scans
            scan_config: Scan configuration dictionary
        """
        with self._lock:
            with self._transaction() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO batch_scan_tasks 
                    (id, task_name, start_date, end_date, scan_period_days, scan_config, status, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, 'pending', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ''', (
                    task_id,
                    task_name,
                    start_date,
                    end_date,
                    scan_period_days,
                    json.dumps(scan_config, ensure_ascii=False)
                ))
    
    def get_batch_scan_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a batch scan task by ID.
        
        Args:
            task_id: Task ID
            
        Returns:
            Task dictionary if found, None otherwise
        """
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, task_name, start_date, end_date, scan_period_days, scan_config,
                       status, total_scans, completed_scans, failed_scans, current_scan_date,
                       progress, message, error, created_at, updated_at, started_at, completed_at
                FROM batch_scan_tasks
                WHERE id = ?
            ''', (task_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            try:
                scan_config = json.loads(row[5])
            except (json.JSONDecodeError, TypeError):
                scan_config = {}
            
            return {
                'id': row[0],
                'taskName': row[1],
                'startDate': row[2],
                'endDate': row[3],
                'scanPeriodDays': row[4],
                'scanConfig': scan_config,
                'status': row[6],
                'totalScans': row[7] or 0,
                'completedScans': row[8] or 0,
                'failedScans': row[9] or 0,
                'currentScanDate': row[10],
                'progress': row[11] or 0,
                'message': row[12],
                'error': row[13],
                'createdAt': normalize_timestamp_to_utc(row[14]),
                'updatedAt': normalize_timestamp_to_utc(row[15]),
                'startedAt': normalize_timestamp_to_utc(row[16]) if row[16] else None,
                'completedAt': normalize_timestamp_to_utc(row[17]) if row[17] else None
            }
    
    def get_batch_scan_task_list(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get list of all batch scan tasks.
        
        Args:
            limit: Maximum number of records to return
            
        Returns:
            List of task dictionaries
        """
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, task_name, start_date, end_date, scan_period_days, status,
                       total_scans, completed_scans, failed_scans, progress, created_at, updated_at
                FROM batch_scan_tasks
                ORDER BY created_at DESC
                LIMIT ?
            ''', (limit,))
            rows = cursor.fetchall()
            
            tasks = []
            for row in rows:
                tasks.append({
                    'id': row[0],
                    'taskName': row[1],
                    'startDate': row[2],
                    'endDate': row[3],
                    'scanPeriodDays': row[4],
                    'status': row[5],
                    'totalScans': row[6] or 0,
                    'completedScans': row[7] or 0,
                    'failedScans': row[8] or 0,
                    'progress': row[9] or 0,
                    'createdAt': normalize_timestamp_to_utc(row[10]),
                    'updatedAt': normalize_timestamp_to_utc(row[11])
                })
            
            return tasks
    
    def update_batch_scan_task(self, task_id: str, **kwargs) -> bool:
        """
        Update a batch scan task.
        
        Args:
            task_id: Task ID
            **kwargs: Fields to update (status, progress, message, error, etc.)
            
        Returns:
            True if updated successfully, False otherwise
        """
        with self._lock:
            with self._transaction() as conn:
                cursor = conn.cursor()
                
                # Build update query dynamically
                updates = []
                values = []
                
                allowed_fields = {
                    'status': 'status',
                    'total_scans': 'total_scans',
                    'completed_scans': 'completed_scans',
                    'failed_scans': 'failed_scans',
                    'current_scan_date': 'current_scan_date',
                    'progress': 'progress',
                    'message': 'message',
                    'error': 'error',
                    'started_at': 'started_at',
                    'completed_at': 'completed_at'
                }
                
                for key, value in kwargs.items():
                    if key in allowed_fields:
                        db_field = allowed_fields[key]
                        if key == 'started_at' or key == 'completed_at':
                            if value == 'now':
                                updates.append(f"{db_field} = CURRENT_TIMESTAMP")
                            else:
                                updates.append(f"{db_field} = ?")
                                values.append(value)
                        else:
                            updates.append(f"{db_field} = ?")
                            values.append(value)
                
                if not updates:
                    return False
                
                updates.append("updated_at = CURRENT_TIMESTAMP")
                values.append(task_id)
                
                query = f"UPDATE batch_scan_tasks SET {', '.join(updates)} WHERE id = ?"
                cursor.execute(query, values)
                
                return cursor.rowcount > 0
    
    def save_batch_scan_result(self, result_id: str, task_id: str, scan_date: str,
                               scan_config: Dict[str, Any], scanned_stocks: List[Dict[str, Any]],
                               total_scanned: int, success_count: int) -> None:
        """
        Save a batch scan result.
        
        Args:
            result_id: Unique result ID
            task_id: Task ID
            scan_date: Scan date in 'YYYY-MM-DD' format
            scan_config: Scan configuration dictionary
            scanned_stocks: List of scanned stocks
            total_scanned: Total number of stocks scanned
            success_count: Number of successful scans
        """
        with self._lock:
            with self._transaction() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO batch_scan_results 
                    (id, task_id, scan_date, scan_config, scanned_stocks, total_scanned, success_count, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (
                    result_id,
                    task_id,
                    scan_date,
                    json.dumps(scan_config, ensure_ascii=False),
                    json.dumps(scanned_stocks, ensure_ascii=False, default=str),
                    total_scanned,
                    success_count
                ))
    
    def get_batch_scan_results(self, task_id: str) -> List[Dict[str, Any]]:
        """
        Get all scan results for a batch scan task.
        
        Args:
            task_id: Task ID
            
        Returns:
            List of scan result dictionaries
        """
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, task_id, scan_date, scan_config, scanned_stocks, total_scanned, success_count, created_at
                FROM batch_scan_results
                WHERE task_id = ?
                ORDER BY scan_date ASC
            ''', (task_id,))
            rows = cursor.fetchall()
            
            results = []
            for row in rows:
                try:
                    scan_config = json.loads(row[3])
                    scanned_stocks = json.loads(row[4])
                except (json.JSONDecodeError, TypeError):
                    scan_config = {}
                    scanned_stocks = []
                
                results.append({
                    'id': row[0],
                    'taskId': row[1],
                    'scanDate': row[2],
                    'scanConfig': scan_config,
                    'scannedStocks': scanned_stocks,
                    'totalScanned': row[5] or 0,
                    'successCount': row[6] or 0,
                    'stockCount': len(scanned_stocks) if isinstance(scanned_stocks, list) else 0,
                    'createdAt': normalize_timestamp_to_utc(row[7])
                })
            
            return results
    
    def get_batch_scan_result(self, result_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific batch scan result by ID.
        
        Args:
            result_id: Result ID
            
        Returns:
            Result dictionary if found, None otherwise
        """
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, task_id, scan_date, scan_config, scanned_stocks, total_scanned, success_count, created_at
                FROM batch_scan_results
                WHERE id = ?
            ''', (result_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            try:
                scan_config = json.loads(row[3])
                scanned_stocks = json.loads(row[4])
            except (json.JSONDecodeError, TypeError):
                scan_config = {}
                scanned_stocks = []
            
            return {
                'id': row[0],
                'taskId': row[1],
                'scanDate': row[2],
                'scanConfig': scan_config,
                'scannedStocks': scanned_stocks,
                'totalScanned': row[5] or 0,
                'successCount': row[6] or 0,
                'stockCount': len(scanned_stocks) if isinstance(scanned_stocks, list) else 0,
                'createdAt': normalize_timestamp_to_utc(row[7])
            }
    
    def delete_batch_scan_task(self, task_id: str) -> bool:
        """
        Delete a batch scan task and all its results.
        
        Args:
            task_id: Task ID
            
        Returns:
            True if deleted successfully, False otherwise
        """
        with self._lock:
            with self._transaction() as conn:
                cursor = conn.cursor()
                # Delete results first (CASCADE should handle this, but explicit is better)
                cursor.execute('DELETE FROM batch_scan_results WHERE task_id = ?', (task_id,))
                # Delete task
                cursor.execute('DELETE FROM batch_scan_tasks WHERE id = ?', (task_id,))
                return cursor.rowcount > 0
    
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

