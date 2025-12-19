"""
Data Fetcher module for retrieving stock data from Baostock.
Implements robust connection handling and retry logic with database-first strategy.
"""
import baostock as bs
import pandas as pd
import time
import threading
from typing import List, Dict, Any, Optional, Tuple
from colorama import Fore, Style
import traceback
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError

# Import database manager
try:
    from .stock_database import get_stock_database
except ImportError:
    from api.stock_database import get_stock_database

# Global flag for database-first strategy (can be overridden per call)
_USE_LOCAL_DATABASE_FIRST = True

def set_use_local_database_first(value: bool) -> None:
    """
    Set the global default for use_local_database_first.
    
    Args:
        value: If True, check database first. If False, fetch from API directly.
    """
    global _USE_LOCAL_DATABASE_FIRST
    _USE_LOCAL_DATABASE_FIRST = value
    print(f"{Fore.CYAN}[DATA_FETCHER] Global use_local_database_first set to {value}{Style.RESET_ALL}")

# Thread-local storage for Baostock connections
_thread_local = threading.local()

# Global data source tracking (thread-safe)
_data_source_stats = {}  # {code: 'db'|'api'|'mixed'}
_data_source_lock = threading.Lock()

def get_data_source_stats() -> Dict[str, str]:
    """
    Get data source statistics for all stocks fetched.
    
    Returns:
        Dictionary mapping stock codes to data source ('db', 'api', or 'mixed')
    """
    with _data_source_lock:
        return _data_source_stats.copy()

def clear_data_source_stats() -> None:
    """
    Clear data source statistics.
    """
    with _data_source_lock:
        _data_source_stats.clear()

def baostock_login() -> None:
    """
    Login to Baostock API with thread-local connection.
    Each thread/process will have its own connection.
    """
    import os
    
    # Track process ID to detect fork
    current_pid = os.getpid()
    
    # Check if we're in a different process (after fork)
    if hasattr(_thread_local, 'pid') and _thread_local.pid != current_pid:
        # Reset login state after fork
        _thread_local.logged_in = False
    
    _thread_local.pid = current_pid
    
    # Check if already logged in in this thread
    if hasattr(_thread_local, 'logged_in') and _thread_local.logged_in:
        return
    
    # Login
    lg = bs.login()
    if lg.error_code != '0':
        print(f"{Fore.RED}Baostock login failed: {lg.error_msg}{Style.RESET_ALL}")
        raise ConnectionError(f"Baostock login failed: {lg.error_msg}")
    
    _thread_local.logged_in = True
    print(f"{Fore.GREEN}Baostock login successful in thread {threading.current_thread().name} (PID: {current_pid}){Style.RESET_ALL}")

def baostock_logout() -> None:
    """
    Logout from Baostock API and clean up thread-local connection.
    """
    if hasattr(_thread_local, 'logged_in') and _thread_local.logged_in:
        bs.logout()
        _thread_local.logged_in = False
        print(f"{Fore.GREEN}Baostock logout successful in thread {threading.current_thread().name}{Style.RESET_ALL}")

def baostock_relogin() -> None:
    """
    Re-login to Baostock API (logout first, then login again).
    """
    baostock_logout()
    baostock_login()


def is_trading_day(date_str: str) -> bool:
    """
    Check if a date is a trading day (exclude weekends).
    Note: This is a simple check that only excludes weekends.
    For a complete check including holidays, a trading calendar would be needed.
    
    Args:
        date_str: Date string in 'YYYY-MM-DD' format
    
    Returns:
        True if the date is a weekday (Monday-Friday), False otherwise
    """
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        # Monday = 0, Sunday = 6
        # Trading days are Monday (0) through Friday (4)
        weekday = date_obj.weekday()
        return weekday < 5  # 0-4 are Monday-Friday
    except (ValueError, TypeError):
        return False


def adjust_date_range_to_trading_days(start_date: str, end_date: str) -> Optional[Tuple[str, str]]:
    """
    Adjust date range to only include trading days (exclude weekends).
    Returns None if the entire range contains no trading days.
    
    Args:
        start_date: Start date in 'YYYY-MM-DD' format
        end_date: End date in 'YYYY-MM-DD' format
    
    Returns:
        Tuple of (adjusted_start_date, adjusted_end_date) or None if no trading days
    """
    try:
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        
        # Find the first trading day from start_date
        adjusted_start = start_dt
        while adjusted_start <= end_dt:
            if is_trading_day(adjusted_start.strftime('%Y-%m-%d')):
                break
            adjusted_start += timedelta(days=1)
        
        # Find the last trading day up to end_date
        adjusted_end = end_dt
        while adjusted_end >= start_dt:
            if is_trading_day(adjusted_end.strftime('%Y-%m-%d')):
                break
            adjusted_end -= timedelta(days=1)
        
        # Check if we found any trading days
        if adjusted_start > adjusted_end:
            return None
        
        adjusted_start_str = adjusted_start.strftime('%Y-%m-%d')
        adjusted_end_str = adjusted_end.strftime('%Y-%m-%d')
        
        return (adjusted_start_str, adjusted_end_str)
    except (ValueError, TypeError) as e:
        print(f"{Fore.YELLOW}[SCAN_CHECKPOINT] ⚠️ Error adjusting date range: {e}{Style.RESET_ALL}")
        return None

class BaostockConnectionManager:
    """
    Context manager for Baostock connections.
    Ensures proper login/logout handling.
    """
    def __enter__(self):
        baostock_login()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        baostock_logout()
        return False  # Don't suppress exceptions

def fetch_stock_basics(use_local_database_first: Optional[bool] = None) -> pd.DataFrame:
    """
    Fetch basic information for all stocks.
    First checks database (if enabled), then fetches from API if needed.
    
    Args:
        use_local_database_first: If True, check database first. If False, fetch from API directly.
                                 If None, use global default.
    
    Returns:
        pd.DataFrame: DataFrame containing stock basic information
    
    Raises:
        ConnectionError: If Baostock connection fails
        ValueError: If no data is returned
    """
    # Use parameter if provided, otherwise use global default
    use_db_first = use_local_database_first if use_local_database_first is not None else _USE_LOCAL_DATABASE_FIRST
    
    db = get_stock_database()
    
    # Try to get from database first (if enabled)
    if use_db_first:
        df = db.get_stock_basics()
        if df is not None and not df.empty:
            print(f"{Fore.GREEN}Loaded stock basics from database ({len(df)} stocks){Style.RESET_ALL}")
            return df
        print(f"{Fore.CYAN}Database is empty, fetching stock basic information from API...{Style.RESET_ALL}")
    else:
        print(f"{Fore.CYAN}use_local_database_first=False, fetching stock basic information directly from API...{Style.RESET_ALL}")
    
    # Fetch from API
    with BaostockConnectionManager():
        rs = bs.query_stock_basic()
        
        if rs.error_code != '0':
            raise ConnectionError(f"Failed to query stock basics: {rs.error_msg}")
        
        stock_basics_list = []
        while rs.next():
            stock_basics_list.append(rs.get_row_data())
        
        if not stock_basics_list:
            raise ValueError("No stock basic information retrieved")
        
        df = pd.DataFrame(stock_basics_list, columns=rs.fields)
        
        # Always save to database (even if use_local_database_first=False)
        db.save_stock_basics(df)
        print(f"{Fore.GREEN}Saved {len(df)} stocks to database{Style.RESET_ALL}")
        
        return df

def fetch_industry_data(use_local_database_first: Optional[bool] = None) -> pd.DataFrame:
    """
    Fetch industry classification data for all stocks.
    First checks database (if enabled), then fetches from API if needed.
    
    Args:
        use_local_database_first: If True, check database first. If False, fetch from API directly.
                                 If None, use global default.
    
    Returns:
        pd.DataFrame: DataFrame containing industry classification
    
    Raises:
        ConnectionError: If Baostock connection fails
        ValueError: If no data is returned
    """
    # Use parameter if provided, otherwise use global default
    use_db_first = use_local_database_first if use_local_database_first is not None else _USE_LOCAL_DATABASE_FIRST
    
    db = get_stock_database()
    
    # Try to get from database first (if enabled)
    if use_db_first:
        df = db.get_industry_data()
        if df is not None and not df.empty:
            print(f"{Fore.GREEN}Loaded industry data from database ({len(df)} stocks){Style.RESET_ALL}")
            return df
        print(f"{Fore.CYAN}Database is empty, fetching industry classification data from API...{Style.RESET_ALL}")
    else:
        print(f"{Fore.CYAN}use_local_database_first=False, fetching industry classification data directly from API...{Style.RESET_ALL}")
    
    # Fetch from API
    with BaostockConnectionManager():
        rs = bs.query_stock_industry()
        
        if rs.error_code != '0':
            raise ConnectionError(f"Failed to query industry data: {rs.error_msg}")
        
        industry_list = []
        while rs.next():
            industry_list.append(rs.get_row_data())
        
        if not industry_list:
            raise ValueError("No industry classification data retrieved")
        
        df = pd.DataFrame(industry_list, columns=rs.fields)
        
        # Always save to database (even if use_local_database_first=False)
        db.save_industry_data(df)
        print(f"{Fore.GREEN}Saved industry data to database{Style.RESET_ALL}")
        
        return df

def fetch_kline_data(code: str, start_date: str, end_date: str,
                     retry_attempts: int = 3,
                     retry_delay: int = 1,
                     api_timeout: float = 5.0,
                     use_local_database_first: Optional[bool] = None,
                     return_source: bool = False) -> pd.DataFrame:
    """
    Fetch K-line data for a specific stock with retry logic.
    First checks database (if enabled), then fetches missing data from API.
    
    Args:
        code: Stock code (e.g., 'sh.600000')
        start_date: Start date in 'YYYY-MM-DD' format
        end_date: End date in 'YYYY-MM-DD' format
        retry_attempts: Maximum number of retry attempts
        retry_delay: Delay between retries in seconds
        api_timeout: Timeout for each API call in seconds
        use_local_database_first: If True, check database first. If False, fetch from API directly.
                                 If None, use global default.
        return_source: If True, return tuple (DataFrame, source) where source is 'db', 'api', or 'mixed'.
                      If False, return only DataFrame (default for backward compatibility).
    
    Returns:
        pd.DataFrame or tuple: DataFrame containing K-line data, or (DataFrame, source) if return_source=True
    """
    import threading
    # Use parameter if provided, otherwise use global default
    use_db_first = use_local_database_first if use_local_database_first is not None else _USE_LOCAL_DATABASE_FIRST
    
    print(f"{Fore.CYAN}[SCAN_CHECKPOINT] 📥 START fetch_kline_data for {code} (thread: {threading.current_thread().name}, use_db_first={use_db_first}){Style.RESET_ALL}")
    
    db = get_stock_database()
    
    # Try to get from database first (if enabled)
    df = pd.DataFrame()
    if use_db_first:
        print(f"{Fore.CYAN}[SCAN_CHECKPOINT] 🔍 Querying database for {code} (requested range: {start_date} to {end_date})...{Style.RESET_ALL}")
        df = db.get_kline_data(code, start_date, end_date)
        print(f"{Fore.CYAN}[SCAN_CHECKPOINT] ✓ Database query completed for {code}, got {len(df)} records{Style.RESET_ALL}")
    else:
        print(f"{Fore.CYAN}[SCAN_CHECKPOINT] ⏭️ Skipping database query (use_local_database_first=False) for {code}{Style.RESET_ALL}")
    
    # Track data sources for logging
    db_date_ranges = []
    api_date_ranges = []
    
    # Check if we have all the data we need
    if not df.empty:
        # Check if we have data for the full date range
        df_dates = pd.to_datetime(df['date'])
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)
        
        min_date = df_dates.min()
        max_date = df_dates.max()
        
        # Log database date range
        min_date_str = min_date.strftime('%Y-%m-%d')
        max_date_str = max_date.strftime('%Y-%m-%d')
        db_date_ranges.append((min_date_str, max_date_str))
        print(f"{Fore.GREEN}[DATA_SOURCE] 📊 Database data for {code}: {min_date_str} to {max_date_str} ({len(df)} records){Style.RESET_ALL}")
        
        # Check if we need to fetch additional data
        # Use a small tolerance (1 day) to account for date comparison edge cases
        need_earlier = (min_date - start_dt).days > 1
        need_later = (end_dt - max_date).days > 1
        
        # Check if data completeness is reasonable
        # Estimate expected trading days: approximately 70% of calendar days (accounting for weekends and holidays)
        date_range_days = (end_dt - start_dt).days + 1
        expected_min_trading_days = max(1, int(date_range_days * 0.3))  # At least 30% should be trading days
        actual_records = len(df)
        
        # If date range looks complete but record count is suspiciously low, re-fetch
        # This handles cases where database has partial data (e.g., only 5 records for a month range)
        data_seems_incomplete = False
        if not need_earlier and not need_later:
            # Date range looks complete, but check if record count is reasonable
            if date_range_days > 7 and actual_records < expected_min_trading_days:
                # For ranges longer than a week, if records are less than expected minimum, likely incomplete
                print(f"{Fore.YELLOW}[SCAN_CHECKPOINT] ⚠️ Suspicious data completeness for {code}: {actual_records} records for {date_range_days} days (expected at least {expected_min_trading_days} trading days){Style.RESET_ALL}")
                data_seems_incomplete = True
            elif (max_date - min_date).days > 7 and actual_records < 10:
                # If data spans more than a week but has very few records, likely incomplete
                print(f"{Fore.YELLOW}[SCAN_CHECKPOINT] ⚠️ Suspicious data completeness for {code}: {actual_records} records spanning {(max_date - min_date).days} days{Style.RESET_ALL}")
                data_seems_incomplete = True
        
        if not need_earlier and not need_later and not data_seems_incomplete:
            # We have all the data we need
            print(f"{Fore.GREEN}[SCAN_CHECKPOINT] ✓ Complete data for {code} from database ({len(df)} records){Style.RESET_ALL}")
            print(f"{Fore.GREEN}[DATA_SOURCE] ✅ All data from DATABASE: {min_date_str} to {max_date_str} ({len(df)} records){Style.RESET_ALL}")
            # Track data source: all from database
            source = 'db'
            with _data_source_lock:
                _data_source_stats[code] = source
            if return_source:
                return df, source
            return df
        
        # We need to fetch additional data
        missing_ranges = []
        if data_seems_incomplete:
            # Data seems incomplete, re-fetch the entire range
            print(f"{Fore.CYAN}[SCAN_CHECKPOINT] 🔄 Re-fetching data for {code} due to suspected incompleteness{Style.RESET_ALL}")
            missing_ranges.append((start_date, end_date))
        else:
            # Fetch missing ranges at the edges
            if need_earlier:
                # Fetch from start_date to one day before min_date
                earlier_end = (min_date - timedelta(days=1)).strftime('%Y-%m-%d')
                missing_ranges.append((start_date, earlier_end))
            if need_later:
                # Fetch from one day after max_date to end_date
                later_start = (max_date + timedelta(days=1)).strftime('%Y-%m-%d')
                missing_ranges.append((later_start, end_date))
    else:
        # No data in database, need to fetch all
        missing_ranges = [(start_date, end_date)]
        print(f"{Fore.YELLOW}[DATA_SOURCE] ⚠️ No database data for {code}, will fetch all from API: {start_date} to {end_date}{Style.RESET_ALL}")
    
    # Fetch missing data from API
    all_data = []
    
    for range_start, range_end in missing_ranges:
        # Check if the date range contains any trading days
        adjusted_range = adjust_date_range_to_trading_days(range_start, range_end)
        
        if adjusted_range is None:
            # No trading days in this range (e.g., weekend only)
            print(f"{Fore.YELLOW}[SCAN_CHECKPOINT] ⏭️ Skipping API request for {code}: no trading days in range {range_start} to {range_end} (likely weekend){Style.RESET_ALL}")
            continue
        
        adjusted_start, adjusted_end = adjusted_range
        
        # Log if we adjusted the range
        if adjusted_start != range_start or adjusted_end != range_end:
            print(f"{Fore.CYAN}[SCAN_CHECKPOINT] 📅 Adjusted date range for {code}: {range_start}~{range_end} -> {adjusted_start}~{adjusted_end} (excluded non-trading days){Style.RESET_ALL}")
        
        print(f"{Fore.CYAN}[SCAN_CHECKPOINT] 🌐 Fetching missing K-line data for {code} from {adjusted_start} to {adjusted_end}...{Style.RESET_ALL}")
        
        fetched_df = _fetch_kline_data_from_api(
            code, adjusted_start, adjusted_end, retry_attempts, retry_delay, api_timeout
        )
        print(f"{Fore.CYAN}[SCAN_CHECKPOINT] ✓ API fetch completed for {code}, got {len(fetched_df)} records{Style.RESET_ALL}")
        
        if not fetched_df.empty:
            # Log API date range
            api_dates = pd.to_datetime(fetched_df['date'])
            api_min_date = api_dates.min().strftime('%Y-%m-%d')
            api_max_date = api_dates.max().strftime('%Y-%m-%d')
            api_date_ranges.append((api_min_date, api_max_date))
            print(f"{Fore.BLUE}[DATA_SOURCE] 🌐 API data for {code}: {api_min_date} to {api_max_date} ({len(fetched_df)} records){Style.RESET_ALL}")
            
            # Save to database
            print(f"{Fore.CYAN}[SCAN_CHECKPOINT] 💾 Saving {len(fetched_df)} records to database for {code}...{Style.RESET_ALL}")
            db.save_kline_data(code, fetched_df)
            all_data.append(fetched_df)
            print(f"{Fore.GREEN}[SCAN_CHECKPOINT] ✓ Saved {len(fetched_df)} records to database for {code}{Style.RESET_ALL}")
    
    # Combine all data
    if all_data:
        if not df.empty:
            # Combine database data with newly fetched data
            combined_df = pd.concat([df] + all_data, ignore_index=True)
            # Remove duplicates and sort by date
            combined_df = combined_df.drop_duplicates(subset=['date'], keep='last')
            combined_df = combined_df.sort_values('date').reset_index(drop=True)
            
            # Log final data source summary
            final_dates = pd.to_datetime(combined_df['date'])
            final_min = final_dates.min().strftime('%Y-%m-%d')
            final_max = final_dates.max().strftime('%Y-%m-%d')
            print(f"{Fore.GREEN}[DATA_SOURCE] 📋 Final combined data for {code}: {final_min} to {final_max} ({len(combined_df)} records){Style.RESET_ALL}")
            if db_date_ranges:
                db_ranges_str = ", ".join([f"{s}~{e}" for s, e in db_date_ranges])
                print(f"{Fore.GREEN}[DATA_SOURCE]   └─ From DATABASE: {db_ranges_str}{Style.RESET_ALL}")
            if api_date_ranges:
                api_ranges_str = ", ".join([f"{s}~{e}" for s, e in api_date_ranges])
                print(f"{Fore.BLUE}[DATA_SOURCE]   └─ From API: {api_ranges_str}{Style.RESET_ALL}")
            
            # Track data source: mixed (database + API)
            source = 'mixed'
            with _data_source_lock:
                _data_source_stats[code] = source
            
            if return_source:
                return combined_df, source
            return combined_df
        else:
            # Only newly fetched data
            combined_df = pd.concat(all_data, ignore_index=True)
            combined_df = combined_df.drop_duplicates(subset=['date'], keep='last')
            combined_df = combined_df.sort_values('date').reset_index(drop=True)
            
            # Log final data source summary (API only)
            final_dates = pd.to_datetime(combined_df['date'])
            final_min = final_dates.min().strftime('%Y-%m-%d')
            final_max = final_dates.max().strftime('%Y-%m-%d')
            print(f"{Fore.BLUE}[DATA_SOURCE] 📋 Final data for {code} (API only): {final_min} to {final_max} ({len(combined_df)} records){Style.RESET_ALL}")
            if api_date_ranges:
                api_ranges_str = ", ".join([f"{s}~{e}" for s, e in api_date_ranges])
                print(f"{Fore.BLUE}[DATA_SOURCE]   └─ All from API: {api_ranges_str}{Style.RESET_ALL}")
            
            # Track data source: all from API
            source = 'api'
            with _data_source_lock:
                _data_source_stats[code] = source
            
            if return_source:
                return combined_df, source
            return combined_df
    
    # If we couldn't fetch new data but have database data, return it
    if not df.empty:
        # Recalculate date range for logging
        df_dates_final = pd.to_datetime(df['date'])
        final_min_db = df_dates_final.min().strftime('%Y-%m-%d')
        final_max_db = df_dates_final.max().strftime('%Y-%m-%d')
        print(f"{Fore.GREEN}[DATA_SOURCE] 📋 Final data for {code} (Database only): {final_min_db} to {final_max_db} ({len(df)} records){Style.RESET_ALL}")
        # Track data source: all from database (partial data, but no API fetch)
        source = 'db'
        with _data_source_lock:
            _data_source_stats[code] = source
        
        if return_source:
            return df, source
        return df
    
    print(f"{Fore.RED}[DATA_SOURCE] ❌ No data available for {code} (requested: {start_date} to {end_date}){Style.RESET_ALL}")
    if return_source:
        return pd.DataFrame(), 'api'  # No data, but attempted API fetch
    return pd.DataFrame()


def _call_baostock_api_with_timeout(code: str, start_date: str, end_date: str, timeout: float = 5.0):
    """
    Call Baostock API with timeout protection.
    
    Args:
        code: Stock code (e.g., 'sh.600000')
        start_date: Start date in 'YYYY-MM-DD' format
        end_date: End date in 'YYYY-MM-DD' format
        timeout: Timeout in seconds (default: 5.0)
    
    Returns:
        Baostock result object
    
    Raises:
        FutureTimeoutError: If the API call exceeds the timeout
    """
    def _api_call():
        """Internal function to make the actual API call"""
        return bs.query_history_k_data_plus(
            code,
            "date,open,high,low,close,volume,turn,preclose,pctChg,peTTM,pbMRQ",
            start_date=start_date,
            end_date=end_date,
            frequency="d",     # Daily frequency
            adjustflag="2"     # Forward adjusted prices
        )
    
    # Use ThreadPoolExecutor to implement timeout
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(_api_call)
        try:
            result = future.result(timeout=timeout)
            return result
        except FutureTimeoutError:
            print(f"{Fore.RED}[SCAN_CHECKPOINT] ⏱️ Timeout ({timeout}s) calling Baostock API for {code}{Style.RESET_ALL}")
            raise


def _fetch_kline_data_from_api(code: str, start_date: str, end_date: str,
                               retry_attempts: int = 3,
                               retry_delay: int = 1,
                               api_timeout: float = 5.0) -> pd.DataFrame:
    """
    Internal function to fetch K-line data from Baostock API.
    
    Args:
        code: Stock code (e.g., 'sh.600000')
        start_date: Start date in 'YYYY-MM-DD' format
        end_date: End date in 'YYYY-MM-DD' format
        retry_attempts: Maximum number of retry attempts
        retry_delay: Delay between retries in seconds
        api_timeout: Timeout for each API call in seconds (default: 5.0)
    
    Returns:
        pd.DataFrame: DataFrame containing K-line data
    """
    retries = 0
    
    while True:
        try:
            # Ensure we're logged in
            print(f"{Fore.CYAN}[SCAN_CHECKPOINT] 🔐 Ensuring Baostock login for {code}...{Style.RESET_ALL}")
            baostock_login()
            print(f"{Fore.CYAN}[SCAN_CHECKPOINT] ✓ Login check completed for {code}{Style.RESET_ALL}")
            
            # Query historical K-line data with timeout protection
            print(f"{Fore.CYAN}[SCAN_CHECKPOINT] 📡 Calling Baostock API for {code} (timeout: {api_timeout}s)...{Style.RESET_ALL}")
            try:
                rs = _call_baostock_api_with_timeout(code, start_date, end_date, timeout=api_timeout)
                # Log error message even if error_code is '0' (might contain useful info)
                error_msg = getattr(rs, 'error_msg', 'N/A')
                print(f"{Fore.CYAN}[SCAN_CHECKPOINT] ✓ Baostock API call returned for {code}, error_code: {rs.error_code}, error_msg: {error_msg}{Style.RESET_ALL}")
            except FutureTimeoutError:
                # Timeout occurred, treat as error
                retries += 1
                print(f"{Fore.RED}[SCAN_CHECKPOINT] ⏱️ Timeout ({api_timeout}s) for {code} (attempt {retries}/{retry_attempts}){Style.RESET_ALL}")
                
                if retries >= retry_attempts:
                    print(f"{Fore.RED}Failed to fetch data for {code} after {retry_attempts} attempts (timeout){Style.RESET_ALL}")
                    return pd.DataFrame()
                
                # Retry with re-login
                time.sleep(retry_delay * (1 + retries * 0.5))
                baostock_relogin()
                continue
            
            # Check for API errors
            if rs.error_code != '0':
                retries += 1
                print(f"{Fore.YELLOW}Attempt {retries}/{retry_attempts}: Baostock query failed for {code}. Error: {rs.error_msg}{Style.RESET_ALL}")
                
                if retries >= retry_attempts:
                    print(f"{Fore.RED}Failed to fetch data for {code} after {retry_attempts} attempts{Style.RESET_ALL}")
                    return pd.DataFrame()
                
                # Retry with re-login
                time.sleep(retry_delay * (1 + retries * 0.5))
                baostock_relogin()
                continue
            
            # Process the data if query was successful
            print(f"{Fore.CYAN}[SCAN_CHECKPOINT] 📊 Processing result data for {code}...{Style.RESET_ALL}")
            data_list = []
            
            # Process results with safety limits to prevent infinite loops
            # Add timeout protection by limiting iterations and using time check
            max_rows = 10000  # Safety limit to prevent processing too many rows
            start_process_time = time.time()
            max_process_time = api_timeout  # Use same timeout for processing
            
            row_count = 0
            while (rs.error_code == '0') & rs.next():
                # Check timeout during processing
                if time.time() - start_process_time > max_process_time:
                    print(f"{Fore.RED}[SCAN_CHECKPOINT] ⏱️ Timeout ({max_process_time}s) processing results for {code} (processed {row_count} rows){Style.RESET_ALL}")
                    raise FutureTimeoutError(f"Timeout processing results after {row_count} rows")
                
                # Safety limit on row count
                if row_count >= max_rows:
                    print(f"{Fore.YELLOW}[SCAN_CHECKPOINT] ⚠️ Reached max rows limit ({max_rows}) for {code}{Style.RESET_ALL}")
                    break
                
                data_list.append(rs.get_row_data())
                row_count += 1
                
                # Periodic check every 100 rows to avoid too frequent time checks
                if row_count % 100 == 0:
                    elapsed = time.time() - start_process_time
                    if elapsed > max_process_time:
                        print(f"{Fore.RED}[SCAN_CHECKPOINT] ⏱️ Timeout ({max_process_time}s) processing results for {code} (processed {row_count} rows){Style.RESET_ALL}")
                        raise FutureTimeoutError(f"Timeout processing results after {row_count} rows")
            
            print(f"{Fore.CYAN}[SCAN_CHECKPOINT] ✓ Collected {len(data_list)} rows for {code}{Style.RESET_ALL}")
            
            # Convert to DataFrame
            if not data_list:
                # Get error message for diagnosis
                error_msg = getattr(rs, 'error_msg', 'N/A')
                
                # Check if this might be a non-stock code (bond, fund, etc.)
                code_num = code.split('.')[-1] if '.' in code else code
                is_likely_bond = code_num.startswith('11') or code_num.startswith('12')
                is_likely_fund = code_num.startswith('15') or code_num.startswith('16')
                
                diagnosis = []
                if is_likely_bond:
                    diagnosis.append("可能是债券代码（11xxxx/12xxxx），Baostock可能不提供债券K线数据")
                if is_likely_fund:
                    diagnosis.append("可能是基金代码（15xxxx/16xxxx），Baostock可能不提供基金K线数据")
                if not is_likely_bond and not is_likely_fund:
                    # Check if it's a valid stock code format
                    if len(code_num) != 6 or not code_num.isdigit():
                        diagnosis.append("股票代码格式异常（应为6位数字）")
                    else:
                        diagnosis.append("可能是股票代码，但该日期范围内无数据（可能已退市、停牌或代码不存在）")
                
                diagnosis_str = " | ".join(diagnosis) if diagnosis else "未知原因"
                
                print(f"{Fore.YELLOW}[SCAN_CHECKPOINT] ⚠️ No data returned for {code} from {start_date} to {end_date}{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}[SCAN_CHECKPOINT]   诊断: {diagnosis_str}{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}[SCAN_CHECKPOINT]   API错误消息: {error_msg}{Style.RESET_ALL}")
                
                # Try to check if code exists in stock basics
                try:
                    db = get_stock_database()
                    stock_basics_df = db.get_stock_basics()
                    if stock_basics_df is not None and not stock_basics_df.empty:
                        code_exists = code in stock_basics_df['code'].values
                        if code_exists:
                            stock_info = stock_basics_df[stock_basics_df['code'] == code].iloc[0]
                            stock_type = stock_info.get('type', 'N/A')
                            stock_status = stock_info.get('status', 'N/A')
                            stock_name = stock_info.get('code_name') or stock_info.get('name', 'N/A')
                            print(f"{Fore.CYAN}[SCAN_CHECKPOINT]   股票信息: 名称={stock_name}, 类型={stock_type}, 状态={stock_status}{Style.RESET_ALL}")
                            if stock_type == '2':
                                print(f"{Fore.YELLOW}[SCAN_CHECKPOINT]   ⚠️ 这是指数代码（type=2），不提供K线数据{Style.RESET_ALL}")
                            if stock_status == '0':
                                print(f"{Fore.YELLOW}[SCAN_CHECKPOINT]   ⚠️ 股票状态为0（非活跃），可能已退市或停牌{Style.RESET_ALL}")
                        else:
                            print(f"{Fore.YELLOW}[SCAN_CHECKPOINT]   ⚠️ 代码不在股票基本信息列表中，可能不存在或不是股票代码{Style.RESET_ALL}")
                except Exception as e:
                    print(f"{Fore.YELLOW}[SCAN_CHECKPOINT]   ⚠️ 无法检查股票基本信息: {e}{Style.RESET_ALL}")
                
                return pd.DataFrame()
            
            print(f"{Fore.CYAN}[SCAN_CHECKPOINT] 🔄 Converting to DataFrame for {code}...{Style.RESET_ALL}")
            df = pd.DataFrame(data_list, columns=rs.fields)
            
            # Convert date column to datetime
            df['date'] = pd.to_datetime(df['date'])
            
            # Convert numeric columns
            numeric_cols = ['open', 'high', 'low', 'close', 'volume', 'turn', 'preclose', 'pctChg', 'peTTM', 'pbMRQ']
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            print(f"{Fore.GREEN}[SCAN_CHECKPOINT] ✓ COMPLETE fetch_kline_data for {code}, returning {len(df)} records{Style.RESET_ALL}")
            return df
            
        except FutureTimeoutError:
            # Timeout exception (should be caught above, but handle here as backup)
            retries += 1
            print(f"{Fore.RED}Attempt {retries}/{retry_attempts}: Timeout while fetching data for {code}{Style.RESET_ALL}")
            
            if retries >= retry_attempts:
                print(f"{Fore.RED}Failed to fetch data for {code} after {retry_attempts} attempts (timeout){Style.RESET_ALL}")
                return pd.DataFrame()
            
            # Retry with re-login
            time.sleep(retry_delay * (1 + retries * 0.5))
            baostock_relogin()
            continue
        except Exception as e:
            retries += 1
            print(f"{Fore.RED}Attempt {retries}/{retry_attempts}: Exception while fetching data for {code}: {e}{Style.RESET_ALL}")
            
            if retries >= retry_attempts:
                print(f"{Fore.RED}Failed to fetch data for {code} after {retry_attempts} attempts{Style.RESET_ALL}")
                return pd.DataFrame()
            
            # Retry with re-login
            time.sleep(retry_delay * (1 + retries * 0.5))
            baostock_relogin()


def build_historical_data(stock_codes: Optional[List[str]] = None,
                          start_date: Optional[str] = None,
                          end_date: Optional[str] = None,
                          progress_callback: Optional[callable] = None) -> None:
    """
    Build historical data for all stocks or specified stocks.
    This function is called when the database is empty on first access.
    
    Args:
        stock_codes: Optional list of stock codes to build data for. If None, uses all stocks.
        start_date: Optional start date in 'YYYY-MM-DD' format. If None, uses 5 years ago.
        end_date: Optional end date in 'YYYY-MM-DD' format. If None, uses today.
        progress_callback: Optional callback function(progress, message) for progress updates.
    """
    db = get_stock_database()
    
    # Check if database is already populated
    if not db.is_empty():
        print(f"{Fore.YELLOW}Database is not empty, skipping historical data build{Style.RESET_ALL}")
        return
    
    print(f"{Fore.CYAN}Building historical data for stocks...{Style.RESET_ALL}")
    
    # Get stock list
    if stock_codes is None:
        stock_basics_df = fetch_stock_basics()
        stock_codes = stock_basics_df['code'].tolist()
    
    # Set date range
    if end_date is None:
        end_date = datetime.now().strftime('%Y-%m-%d')
    if start_date is None:
        start_date = (datetime.now() - timedelta(days=5*365)).strftime('%Y-%m-%d')
    
    total_stocks = len(stock_codes)
    print(f"{Fore.CYAN}Building historical data for {total_stocks} stocks from {start_date} to {end_date}{Style.RESET_ALL}")
    
    # Fetch data for each stock
    with BaostockConnectionManager():
        for idx, code in enumerate(stock_codes):
            if progress_callback:
                progress = int((idx + 1) / total_stocks * 100)
                progress_callback(progress, f"Building data for {code} ({idx+1}/{total_stocks})...")
            
            try:
                df = _fetch_kline_data_from_api(code, start_date, end_date, api_timeout=5.0)
                if not df.empty:
                    db.save_kline_data(code, df)
                    print(f"{Fore.GREEN}Saved {len(df)} records for {code}{Style.RESET_ALL}")
                else:
                    print(f"{Fore.YELLOW}No data for {code}{Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.RED}Error building data for {code}: {e}{Style.RESET_ALL}")
                continue
    
    print(f"{Fore.GREEN}Historical data build completed{Style.RESET_ALL}")
