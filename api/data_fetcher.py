"""
Data Fetcher module for retrieving stock data from Baostock.
Implements robust connection handling and retry logic with database-first strategy.
"""
import baostock as bs
import pandas as pd
import time
import threading
from typing import List, Dict, Any, Optional
from colorama import Fore, Style
import traceback
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError

# Import database manager
try:
    from .stock_database import get_stock_database
except ImportError:
    from api.stock_database import get_stock_database

# Thread-local storage for Baostock connections
_thread_local = threading.local()

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

def fetch_stock_basics() -> pd.DataFrame:
    """
    Fetch basic information for all stocks.
    First checks database, then fetches from API if needed.
    
    Returns:
        pd.DataFrame: DataFrame containing stock basic information
    
    Raises:
        ConnectionError: If Baostock connection fails
        ValueError: If no data is returned
    """
    db = get_stock_database()
    
    # Try to get from database first
    df = db.get_stock_basics()
    if df is not None and not df.empty:
        print(f"{Fore.GREEN}Loaded stock basics from database ({len(df)} stocks){Style.RESET_ALL}")
        return df
    
    # Database is empty or doesn't have data, fetch from API
    print(f"{Fore.CYAN}Database is empty, fetching stock basic information from API...{Style.RESET_ALL}")
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
        
        # Save to database
        db.save_stock_basics(df)
        print(f"{Fore.GREEN}Saved {len(df)} stocks to database{Style.RESET_ALL}")
        
        return df

def fetch_industry_data() -> pd.DataFrame:
    """
    Fetch industry classification data for all stocks.
    First checks database, then fetches from API if needed.
    
    Returns:
        pd.DataFrame: DataFrame containing industry classification
    
    Raises:
        ConnectionError: If Baostock connection fails
        ValueError: If no data is returned
    """
    db = get_stock_database()
    
    # Try to get from database first
    df = db.get_industry_data()
    if df is not None and not df.empty:
        print(f"{Fore.GREEN}Loaded industry data from database ({len(df)} stocks){Style.RESET_ALL}")
        return df
    
    # Database is empty or doesn't have data, fetch from API
    print(f"{Fore.CYAN}Database is empty, fetching industry classification data from API...{Style.RESET_ALL}")
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
        
        # Save to database
        db.save_industry_data(df)
        print(f"{Fore.GREEN}Saved industry data to database{Style.RESET_ALL}")
        
        return df

def fetch_kline_data(code: str, start_date: str, end_date: str,
                     retry_attempts: int = 3,
                     retry_delay: int = 1,
                     api_timeout: float = 5.0) -> pd.DataFrame:
    """
    Fetch K-line data for a specific stock with retry logic.
    First checks database, then fetches missing data from API.
    
    Args:
        code: Stock code (e.g., 'sh.600000')
        start_date: Start date in 'YYYY-MM-DD' format
        end_date: End date in 'YYYY-MM-DD' format
        retry_attempts: Maximum number of retry attempts
        retry_delay: Delay between retries in seconds
    
    Returns:
        pd.DataFrame: DataFrame containing K-line data
    """
    import threading
    print(f"{Fore.CYAN}[SCAN_CHECKPOINT] 📥 START fetch_kline_data for {code} (thread: {threading.current_thread().name}){Style.RESET_ALL}")
    
    db = get_stock_database()
    
    # Try to get from database first
    print(f"{Fore.CYAN}[SCAN_CHECKPOINT] 🔍 Querying database for {code}...{Style.RESET_ALL}")
    df = db.get_kline_data(code, start_date, end_date)
    print(f"{Fore.CYAN}[SCAN_CHECKPOINT] ✓ Database query completed for {code}, got {len(df)} records{Style.RESET_ALL}")
    
    # Check if we have all the data we need
    if not df.empty:
        # Check if we have data for the full date range
        df_dates = pd.to_datetime(df['date'])
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)
        
        min_date = df_dates.min()
        max_date = df_dates.max()
        
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
    
    # Fetch missing data from API
    all_data = []
    
    for range_start, range_end in missing_ranges:
        print(f"{Fore.CYAN}[SCAN_CHECKPOINT] 🌐 Fetching missing K-line data for {code} from {range_start} to {range_end}...{Style.RESET_ALL}")
        
        fetched_df = _fetch_kline_data_from_api(
            code, range_start, range_end, retry_attempts, retry_delay, api_timeout
        )
        print(f"{Fore.CYAN}[SCAN_CHECKPOINT] ✓ API fetch completed for {code}, got {len(fetched_df)} records{Style.RESET_ALL}")
        
        if not fetched_df.empty:
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
            return combined_df
        else:
            # Only newly fetched data
            combined_df = pd.concat(all_data, ignore_index=True)
            combined_df = combined_df.drop_duplicates(subset=['date'], keep='last')
            combined_df = combined_df.sort_values('date').reset_index(drop=True)
            return combined_df
    
    # If we couldn't fetch new data but have database data, return it
    if not df.empty:
        return df
    
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
                print(f"{Fore.CYAN}[SCAN_CHECKPOINT] ✓ Baostock API call returned for {code}, error_code: {rs.error_code}{Style.RESET_ALL}")
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
                print(f"{Fore.YELLOW}[SCAN_CHECKPOINT] ⚠️ No data returned for {code} from {start_date} to {end_date}{Style.RESET_ALL}")
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
