"""
Platform Scanner module for scanning stocks for platform consolidation patterns.
"""
import pandas as pd
import numpy as np
import math
from typing import List, Dict, Any, Optional, Tuple
import time
from datetime import datetime, timedelta
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed, CancelledError
from tqdm import tqdm
from colorama import Fore, Style
import platform as platform_module

from .data_fetcher import fetch_kline_data, baostock_login, get_data_source_stats, clear_data_source_stats, BaostockConnectionManager
from .industry_filter import apply_industry_diversity_filter
from .config import ScanConfig

# Import analyzers
from .analyzers.price_analyzer import analyze_price
from .analyzers.volume_analyzer import analyze_volume
from .analyzers.combined_analyzer import analyze_stock
from .analyzers.fundamental_analyzer import analyze_fundamentals


def should_use_process_pool() -> bool:
    """
    Determine whether to use ProcessPoolExecutor or ThreadPoolExecutor.
    Linux servers should use ThreadPoolExecutor to avoid SQLite connection issues.
    
    Returns:
        True if ProcessPoolExecutor should be used, False for ThreadPoolExecutor
    """
    system = platform_module.system()
    
    # Use ThreadPoolExecutor on Linux to avoid fork-related database issues
    # ProcessPoolExecutor is fine on macOS/Windows
    if system == 'Linux':
        return False  # Use ThreadPoolExecutor
    else:
        return True  # Use ProcessPoolExecutor


def prepare_stock_list(stock_basics_df: pd.DataFrame,
                       industry_df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Prepare a list of stocks for scanning, excluding indices, bonds, and merging industry data.

    Args:
        stock_basics_df: DataFrame containing stock basic information
        industry_df: DataFrame containing industry classification

    Returns:
        List of dictionaries with stock information
    """
    # Filter out indices (type=2), non-active stocks (status=0), and convertible bonds
    stock_list = []
    filtered_bonds_count = 0

    for _, row in stock_basics_df.iterrows():
        code = row['code']
        
        # Skip indices and inactive stocks
        if row['type'] == '2' or row['status'] == '0':
            continue
        
        # Filter out convertible bonds (可转债)
        # Shanghai: 11xxxx (convertible bonds)
        # Shenzhen: 12xxxx (convertible bonds)
        code_num = code.split('.')[-1] if '.' in code else code
        if code_num.startswith('11') or code_num.startswith('12'):
            filtered_bonds_count += 1
            continue

        # Support both 'code_name' (from API) and 'name' (from database)
        stock_name = row.get('code_name') or row.get('name', '')

        stock_info = {
            'code': code,
            'name': stock_name,
            'type': row['type'],
            'status': row['status'],
            'industry': 'Unknown'  # Default value
        }

        # Add to list
        stock_list.append(stock_info)
    
    # Log filtered bonds count
    if filtered_bonds_count > 0:
        print(f"{Fore.CYAN}[SCAN_CHECKPOINT] Filtered out {filtered_bonds_count} convertible bonds (11xxxx/12xxxx codes){Style.RESET_ALL}")

    # Add industry information if available
    if not industry_df.empty:
        industry_dict = dict(zip(industry_df['code'], industry_df['industry']))
        for stock in stock_list:
            if stock['code'] in industry_dict:
                stock['industry'] = industry_dict[stock['code']]

    return stock_list


def _fetch_kline_with_tracking(code: str, name: str, start_date: str, end_date: str,
                                retry_attempts: int, retry_delay: int, api_timeout: float = 5.0,
                                use_local_database_first: bool = True):
    """
    Module-level function to fetch K-line data (can be pickled for ProcessPoolExecutor).
    This is a wrapper around fetch_kline_data that can be used in multiprocessing.
    Returns (DataFrame, source) tuple where source is 'db', 'api', or 'mixed'.
    """
    from .data_fetcher import fetch_kline_data
    try:
        result, source = fetch_kline_data(code, start_date, end_date, retry_attempts, retry_delay, api_timeout, use_local_database_first=use_local_database_first, return_source=True)
        return result, source
    except Exception as e:
        # Re-raise to preserve error information
        raise


def scan_stocks(stock_list: List[Dict[str, Any]],
                config: ScanConfig,
                update_progress: Optional[callable] = None,
                end_date: Optional[str] = None,
                return_stats: bool = False) -> List[Dict[str, Any]]:
    """
    Scan stocks for platform consolidation patterns.

    Args:
        stock_list: List of stocks to scan
        config: Scan configuration
        update_progress: Optional callback for updating progress
        end_date: Optional end date in 'YYYY-MM-DD' format. If not provided, uses current date.

    Returns:
        List of stocks that meet platform criteria
    """
    # Calculate date range
    if end_date is None:
        end_date = datetime.now().strftime('%Y-%m-%d')
    # Use the maximum window size plus some buffer for the start date
    max_window = max(config.windows) if config.windows else 90
    end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
    
    # Ensure minimum data range for proper analysis
    # Even if window is small (e.g., 30), we need enough data for:
    # - MA calculations (max MA period is 60 days for window > 60)
    # - Volume analysis (needs comparison period)
    # - Other technical indicators
    # Minimum: 180 days to ensure sufficient data for all analyses
    min_data_days = max(max_window * 2, 180)
    start_date = (end_date_obj - timedelta(days=min_data_days)
                  ).strftime('%Y-%m-%d')

    print(f"{Fore.CYAN}======================================{Style.RESET_ALL}")
    print(f"{Fore.CYAN}[SCAN_CHECKPOINT] Starting stock platform scan{Style.RESET_ALL}")
    print(f"{Fore.CYAN}======================================{Style.RESET_ALL}")
    
    # Clear data source statistics at the start of scan
    clear_data_source_stats()
    
    # Fetch market index data for relative strength calculation (if enabled)
    market_df = pd.DataFrame()
    if getattr(config, 'check_relative_strength', False):
        try:
            print(f"{Fore.CYAN}[SCAN_CHECKPOINT] Fetching market index data (sh.000001) for relative strength calculation...{Style.RESET_ALL}")
            market_index_code = "sh.000001"  # 上证指数
            with BaostockConnectionManager():
                market_df = fetch_kline_data(market_index_code, start_date, end_date)
            if not market_df.empty:
                print(f"{Fore.GREEN}[SCAN_CHECKPOINT] ✓ Market index data fetched: {len(market_df)} records{Style.RESET_ALL}")
            else:
                print(f"{Fore.YELLOW}[SCAN_CHECKPOINT] ⚠️ Failed to fetch market index data, relative strength calculation will be skipped{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.YELLOW}[SCAN_CHECKPOINT] ⚠️ Error fetching market index data: {e}, relative strength calculation will be skipped{Style.RESET_ALL}")
            market_df = pd.DataFrame()
    print(f"{Fore.YELLOW}Scan parameters:{Style.RESET_ALL}")
    print(
        f"  - Date range: {Fore.GREEN}{start_date} to {end_date}{Style.RESET_ALL}")
    print(f"  - Windows: {Fore.GREEN}{config.windows}{Style.RESET_ALL}")
    print(
        f"  - Box threshold: {Fore.GREEN}{config.box_threshold}{Style.RESET_ALL}")
    print(
        f"  - MA diff threshold: {Fore.GREEN}{config.ma_diff_threshold}{Style.RESET_ALL}")
    print(
        f"  - Volatility threshold: {Fore.GREEN}{config.volatility_threshold}{Style.RESET_ALL}")

    # Print volume analysis parameters if enabled
    if config.use_volume_analysis:
        print(f"  - Volume analysis: {Fore.GREEN}Enabled{Style.RESET_ALL}")
        print(
            f"  - Volume change threshold: {Fore.GREEN}{config.volume_change_threshold}{Style.RESET_ALL}")
        print(
            f"  - Volume stability threshold: {Fore.GREEN}{config.volume_stability_threshold}{Style.RESET_ALL}")
        print(
            f"  - Volume increase threshold: {Fore.GREEN}{config.volume_increase_threshold}{Style.RESET_ALL}")
    else:
        print(f"  - Volume analysis: {Fore.YELLOW}Disabled{Style.RESET_ALL}")

    # Print window weights if enabled
    if config.use_window_weights:
        print(f"  - Window weights: {Fore.GREEN}Enabled{Style.RESET_ALL}")
        for window, weight in config.window_weights.items():
            print(
                f"    - {window} days: {Fore.GREEN}{weight}{Style.RESET_ALL}")
    else:
        print(f"  - Window weights: {Fore.YELLOW}Disabled{Style.RESET_ALL}")

    print(
        f"  - Max workers: {Fore.GREEN}{config.max_workers}{Style.RESET_ALL}")
    print(f"  - Stock count: {Fore.GREEN}{len(stock_list)}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}======================================{Style.RESET_ALL}")

    # Choose executor based on platform
    if should_use_process_pool():
        executor_class = ProcessPoolExecutor
        print(
            f"{Fore.GREEN}Using ProcessPoolExecutor for concurrent data fetching{Style.RESET_ALL}")
    else:
        executor_class = ThreadPoolExecutor
        print(
            f"{Fore.GREEN}Using ThreadPoolExecutor for concurrent data fetching (better for Linux/SQLite){Style.RESET_ALL}")

    # Initialize counters
    success_count = 0
    empty_count = 0
    error_count = 0
    platform_count = 0
    
    # Data source statistics (collected from worker processes/threads)
    collected_data_sources = {}  # {code: 'db'|'api'|'mixed'}
    
    # Data source statistics (thread-safe)
    import threading as threading_module
    db_fetch_count = 0  # Stocks fetched entirely from database
    api_fetch_count = 0  # Stocks fetched entirely from API
    mixed_fetch_count = 0  # Stocks fetched from both database and API
    data_source_lock = threading_module.Lock()

    # List to store platform stocks
    platform_stocks = []
    
    # Initialize variables that may be accessed in finally block
    processed_count = 0
    total_stocks = len(stock_list)

    # Initialize variables that may be accessed in finally block
    processed_count = 0
    total_stocks = len(stock_list)
    future_to_stock = {}  # Initialize outside executor block for access after executor closes
    all_futures = set()  # Initialize outside executor block
    
    # Use executor for concurrent processing
    # Wrap in try-finally to ensure filtering logic always executes
    executor = None  # Initialize outside try block for access in finally
    try:
        executor = executor_class(max_workers=config.max_workers, initializer=baostock_login)
        # Don't use 'with' statement to avoid blocking shutdown
        # We'll manually manage executor lifecycle
        
        # Track submitted tasks for debugging (thread-safe)
        import threading as threading_module
        submitted_stocks = {s['code']: s['name'] for s in stock_list}
        started_stocks = set()
        completed_stocks = set()
        stocks_lock = threading_module.Lock()
        
        # Use module-level function for ProcessPoolExecutor compatibility
        # For ThreadPoolExecutor, we can still track execution
        if executor_class == ThreadPoolExecutor:
            # For ThreadPoolExecutor, use a wrapper with tracking
            # Get use_local_database_first from config
            use_db_first = getattr(config, 'use_local_database_first', True)
            
            def fetch_with_tracking(code, name, start_date, end_date, retry_attempts, retry_delay, api_timeout=5.0):
                """Wrapper to track when task actually starts executing in thread pool"""
                import threading
                from .data_fetcher import fetch_kline_data
                with stocks_lock:
                    started_stocks.add(code)
                print(f"{Fore.MAGENTA}[SCAN_CHECKPOINT] 🚀 TASK STARTED in thread {threading.current_thread().name} for {code} ({name}){Style.RESET_ALL}")
                try:
                    result, source = fetch_kline_data(code, start_date, end_date, retry_attempts, retry_delay, api_timeout, use_local_database_first=use_db_first, return_source=True)
                    with stocks_lock:
                        completed_stocks.add(code)
                    print(f"{Fore.MAGENTA}[SCAN_CHECKPOINT] ✅ TASK FINISHED for {code} ({name}), returning {len(result)} rows{Style.RESET_ALL}")
                    return result, source
                except Exception as e:
                    with stocks_lock:
                        completed_stocks.add(code)  # Mark as completed even if failed
                    print(f"{Fore.RED}[SCAN_CHECKPOINT] 💥 TASK EXCEPTION for {code} ({name}): {e}{Style.RESET_ALL}")
                    raise
            fetch_func = fetch_with_tracking
        else:
            # For ProcessPoolExecutor, use module-level function (can be pickled)
            fetch_func = _fetch_kline_with_tracking
        
        # Submit tasks
        print(f"{Fore.CYAN}[SCAN_CHECKPOINT] Submitting {len(stock_list)} tasks to executor{Style.RESET_ALL}")
        # Use 5 second timeout for each API call
        api_timeout = 5.0
        use_db_first = getattr(config, 'use_local_database_first', True)
        
        if executor_class == ThreadPoolExecutor:
            # For ThreadPoolExecutor, use fetch_with_tracking (already has use_db_first)
            future_to_stock = {
                executor.submit(fetch_func, s['code'], s['name'], start_date, end_date,
                                config.retry_attempts, config.retry_delay, api_timeout): s
                for s in stock_list
            }
        else:
            # For ProcessPoolExecutor, use _fetch_kline_with_tracking with use_db_first
            future_to_stock = {
                executor.submit(_fetch_kline_with_tracking, s['code'], s['name'], start_date, end_date,
                                config.retry_attempts, config.retry_delay, api_timeout, use_db_first): s
                for s in stock_list
            }
        all_futures = set(future_to_stock.keys())  # Store reference outside executor block

        # Create progress bar
        total_stocks = len(future_to_stock)
        print(f"{Fore.GREEN}[SCAN_CHECKPOINT] All {total_stocks} tasks submitted, starting to process results{Style.RESET_ALL}")
        
        pbar = tqdm(total=total_stocks, desc="Fetching stock data",
                    bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]")

        # Process results as they complete with timeout
        import time as time_module
        import threading
        
        processed_count = 0
        hang_detected = [False]  # Use list to allow modification in thread
        
        def watchdog():
                """Monitor progress and detect hangs"""
                last_count = 0
                no_progress_cycles = 0
                max_wait_time = 900  # 15 minutes total timeout
                start_time = time_module.time()
                
                while processed_count < total_stocks and not hang_detected[0]:
                    time_module.sleep(10)  # Check every 10 seconds
                    current_count = processed_count
                    completion_rate = current_count / total_stocks
                    elapsed = time_module.time() - start_time
                    
                    # Always log watchdog heartbeat
                    print(f"{Fore.CYAN}[SCAN_CHECKPOINT] 🐕 Watchdog: {current_count}/{total_stocks} ({completion_rate*100:.1f}%), elapsed: {elapsed:.0f}s{Style.RESET_ALL}")
                    
                    # If no progress in 10s and 95%+ complete, consider it hung
                    if current_count == last_count:
                        no_progress_cycles += 1
                        if completion_rate >= 0.95 and no_progress_cycles >= 1:
                            remaining = total_stocks - current_count
                            print(f"{Fore.YELLOW}[SCAN_CHECKPOINT] ⚠️ Watchdog: No progress for {10*no_progress_cycles}s, {remaining} tasks stuck (95%+ done){Style.RESET_ALL}")
                            
                            # List stuck tasks (with lock for thread safety)
                            with stocks_lock:
                                not_started = [code for code in submitted_stocks.keys() if code not in started_stocks]
                                started_not_completed = [code for code in started_stocks if code not in completed_stocks]
                            
                            if not_started:
                                print(f"{Fore.YELLOW}[SCAN_CHECKPOINT] ⚠️ Tasks NEVER STARTED ({len(not_started)}): {', '.join(not_started[:10])}{Style.RESET_ALL}")
                            
                            if started_not_completed:
                                print(f"{Fore.YELLOW}[SCAN_CHECKPOINT] ⚠️ Tasks STARTED but NOT COMPLETED ({len(started_not_completed)}): {', '.join(started_not_completed[:10])}{Style.RESET_ALL}")
                            
                            hang_detected[0] = True
                            
                            # Cancel all pending futures to unblock as_completed()
                            print(f"{Fore.YELLOW}[SCAN_CHECKPOINT] Watchdog cancelling {remaining} stuck futures...{Style.RESET_ALL}")
                            cancelled_count = 0
                            for future in future_to_stock:
                                if not future.done():
                                    try:
                                        if future.cancel():
                                            cancelled_count += 1
                                    except:
                                        pass
                            print(f"{Fore.YELLOW}[SCAN_CHECKPOINT] Watchdog cancelled {cancelled_count} futures{Style.RESET_ALL}")
                            break
                    else:
                        no_progress_cycles = 0
                    
                    # Global timeout check
                    if elapsed > max_wait_time:
                        print(f"{Fore.RED}[SCAN_CHECKPOINT] ⚠️ Watchdog: Total timeout {max_wait_time}s exceeded{Style.RESET_ALL}")
                        hang_detected[0] = True
                        
                        # Cancel all pending futures
                        for future in future_to_stock:
                            if not future.done():
                                try:
                                    future.cancel()
                                except:
                                    pass
                        break
                        
                    last_count = current_count
        
        # Start watchdog thread
        watchdog_thread = threading.Thread(target=watchdog, daemon=True)
        watchdog_thread.start()
        
        print(f"{Fore.CYAN}[SCAN_CHECKPOINT] Watchdog started, beginning to process results...{Style.RESET_ALL}")
        
        # Process results with timeout handling
        # Use a timeout wrapper for as_completed to prevent indefinite blocking
        completed_futures = set()
        last_completion_time = time_module.time()
        max_wait_between_completions = 30.0  # Max time to wait for next completion
        max_total_wait_time = 60.0  # Max time to wait for any single completion
        
        # Process completed futures, with timeout handling
        # Wrap as_completed with timeout to prevent indefinite blocking
        remaining_futures = set(future_to_stock.keys())
        
        while remaining_futures and processed_count < total_stocks:
                # Check if watchdog triggered and we should exit
                if hang_detected[0] and processed_count >= total_stocks * 0.95:
                    print(f"{Fore.YELLOW}[SCAN_CHECKPOINT] Watchdog timeout reached ({processed_count}/{total_stocks} processed), marking remaining as errors...{Style.RESET_ALL}")
                    # Mark all remaining futures as errors
                    remaining_to_mark = list(remaining_futures)  # Create a copy to iterate over
                    for future in remaining_to_mark:
                        if future not in completed_futures:  # Only mark if not already processed
                            stock = future_to_stock[future]
                            error_count += 1
                            processed_count += 1
                            completed_futures.add(future)  # Mark as processed
                            print(f"{Fore.YELLOW}[SCAN_CHECKPOINT] ⚠️ Marking {stock['code']} ({stock['name']}) as error (watchdog timeout){Style.RESET_ALL}")
                            pbar.set_postfix(success=success_count, empty=empty_count,
                                             error=error_count, platform=platform_count)
                            pbar.update(1)
                    remaining_futures.clear()  # Clear remaining futures since all are marked
                    # Immediately update progress to reflect the error-marked tasks
                    if update_progress:
                        progress_pct = processed_count / total_stocks * 100
                        update_progress(
                            progress=int(progress_pct),
                            message=f"Processed {processed_count}/{total_stocks} stocks. Found {platform_count} platform stocks. ({error_count} errors due to timeout)"
                        )
                        break
                
                # Try to get a completed future with timeout
                done_futures = [f for f in remaining_futures if f.done()]
                
                if done_futures:
                    # Process completed futures
                    for future in done_futures:
                        remaining_futures.discard(future)
                        completed_futures.add(future)
                        last_completion_time = time_module.time()
                        
                        # Process this future
                        break  # Process one at a time
                else:
                    # No completed futures yet, wait a bit
                    if hang_detected[0]:
                        # If watchdog triggered, check if we should wait
                        elapsed = time_module.time() - last_completion_time
                        if elapsed > max_wait_between_completions:
                            print(f"{Fore.YELLOW}[SCAN_CHECKPOINT] No completion for {max_wait_between_completions}s, marking remaining as errors ({len(remaining_futures)} tasks){Style.RESET_ALL}")
                            # Mark remaining as errors
                            for future in remaining_futures:
                                stock = future_to_stock[future]
                                error_count += 1
                                processed_count += 1
                                print(f"{Fore.YELLOW}[SCAN_CHECKPOINT] ⚠️ Marking {stock['code']} as error (timeout){Style.RESET_ALL}")
                                pbar.update(1)
                            break
                    
                    # Wait a short time for completion
                    time_module.sleep(0.5)
                    continue
                
                # Process the completed future
                future = done_futures[0]
                
                stock = future_to_stock[future]
                stock_code = stock['code']
                stock_name = stock['name']
                processed_count += 1
                
                # Log first task completion
                if processed_count == 1:
                    print(f"{Fore.CYAN}[SCAN_CHECKPOINT] First task completed: {stock_code} ({stock_name}){Style.RESET_ALL}")
                
                # Log first task completion
                if processed_count == 1:
                    print(f"{Fore.CYAN}[SCAN_CHECKPOINT] First task completed: {stock_code} ({stock_name}){Style.RESET_ALL}")

                try:
                    # Get K-line data with timeout to prevent indefinite waiting
                    # Use shorter timeout if watchdog has triggered
                    result_timeout = 5.0 if hang_detected[0] else 10.0
                    result = future.result(timeout=result_timeout)
                    
                    # Handle both old format (DataFrame) and new format (DataFrame, source)
                    if isinstance(result, tuple) and len(result) == 2:
                        df, source = result
                        collected_data_sources[stock_code] = source
                    else:
                        # Backward compatibility: if not tuple, assume it's just DataFrame
                        df = result
                        # Try to get source from global stats (works for ThreadPoolExecutor)
                        data_source_stats = get_data_source_stats()
                        if stock_code in data_source_stats:
                            collected_data_sources[stock_code] = data_source_stats[stock_code]

                    if df.empty:
                        empty_count += 1
                        if processed_count % 100 == 0:
                            print(f"{Fore.CYAN}[SCAN_CHECKPOINT] {stock_code}: Empty data (Total empty: {empty_count}){Style.RESET_ALL}")
                        pbar.set_postfix(success=success_count, empty=empty_count,
                                         error=error_count, platform=platform_count)
                        pbar.update(1)
                        continue

                    # Analyze for platform periods
                    print(f"{Fore.CYAN}[SCAN_CHECKPOINT] 🔬 Starting analysis for {stock_code} ({stock_name})...{Style.RESET_ALL}")
                    analysis_result = analyze_stock(
                        df,
                        config.windows,
                        config.box_threshold,
                        config.ma_diff_threshold,
                        config.volatility_threshold,
                        config.volume_change_threshold,
                        config.volume_stability_threshold,
                        config.volume_increase_threshold,
                        config.use_volume_analysis,
                        config.use_breakthrough_prediction,
                        config.use_window_weights,
                        config.window_weights,
                        config.use_low_position,
                        config.high_point_lookback_days,
                        config.decline_period_days,
                        config.decline_threshold,
                        config.use_rapid_decline_detection,
                        config.rapid_decline_days,
                        config.rapid_decline_threshold,
                        config.use_breakthrough_confirmation,
                        config.breakthrough_confirmation_days,
                        config.use_box_detection,
                        config.box_quality_threshold,
                        config.max_turnover_rate,
                        config.allow_turnover_spikes,
                        getattr(config, 'check_relative_strength', False),
                        getattr(config, 'outperform_index_threshold', None),
                        market_df,
                        end_date
                    )
                    print(f"{Fore.CYAN}[SCAN_CHECKPOINT] ✓ Analysis completed for {stock_code}, is_platform: {analysis_result['is_platform']}{Style.RESET_ALL}")

                    success_count += 1

                    # If it's a platform stock, add to results
                    if analysis_result["is_platform"]:
                        platform_count += 1
                        print(f"{Fore.GREEN}[SCAN_CHECKPOINT] ✓ Platform found: {stock_code} ({stock_name}) - Total platforms: {platform_count}{Style.RESET_ALL}")

                        # Create result object
                        outperform_index = analysis_result.get("outperform_index")
                        stock_return = analysis_result.get("stock_return")
                        market_return = analysis_result.get("market_return")
                        print(f"[RELATIVE_STRENGTH_DEBUG] Stock {stock_code} ({stock_name}): outperform_index={outperform_index}, stock_return={stock_return}, market_return={market_return}")
                        
                        platform_stock = {
                            'code': stock_code,
                            'name': stock_name,
                            'industry': stock.get('industry', 'Unknown'),
                            'platform_windows': analysis_result["platform_windows"],
                            'details': analysis_result["details"],
                            'selection_reasons': analysis_result["selection_reasons"],
                            'kline_data': df.to_dict(orient='records'),
                            'outperform_index': outperform_index,
                            'stock_return': stock_return,
                            'market_return': market_return
                        }

                        # Add mark lines if available
                        if "mark_lines" in analysis_result:
                            platform_stock['mark_lines'] = analysis_result["mark_lines"]
                            print(
                                f"{Fore.GREEN}添加标记线数据到股票 {stock_code}: {analysis_result['mark_lines']}{Style.RESET_ALL}")

                        # Add volume analysis results if available
                        if config.use_volume_analysis and "volume_analysis" in analysis_result:
                            platform_stock['volume_analysis'] = analysis_result["volume_analysis"]

                        # Add turnover analysis results if available
                        if "turnover_analysis" in analysis_result:
                            platform_stock['turnover_analysis'] = analysis_result["turnover_analysis"]

                        # Add breakthrough prediction results if available
                        if config.use_breakthrough_prediction and "breakthrough_prediction" in analysis_result:
                            platform_stock['breakthrough_prediction'] = analysis_result["breakthrough_prediction"]

                        # Add breakthrough confirmation results if available
                        if config.use_breakthrough_confirmation:
                            if "has_breakthrough_confirmation" in analysis_result:
                                platform_stock['has_breakthrough_confirmation'] = analysis_result["has_breakthrough_confirmation"]
                            if "has_breakthrough" in analysis_result:
                                platform_stock['has_breakthrough'] = analysis_result["has_breakthrough"]
                            if "breakthrough_confirmation_details" in analysis_result:
                                platform_stock['breakthrough_confirmation_details'] = analysis_result["breakthrough_confirmation_details"]

                        # Add window weight results if available
                        if config.use_window_weights and "weighted_score" in analysis_result:
                            platform_stock['weighted_score'] = analysis_result["weighted_score"]
                            platform_stock['weight_details'] = analysis_result.get(
                                "weight_details", {})

                        # Add box analysis results if available (for sorting by box quality)
                        if config.use_box_detection and "box_analysis" in analysis_result:
                            platform_stock['box_analysis'] = analysis_result["box_analysis"]

                        platform_stocks.append(platform_stock)

                    # Update progress
                    if update_progress and processed_count % 10 == 0:  # Update every 10 stocks
                        progress_pct = processed_count / total_stocks * 100
                        update_progress(
                            progress=int(progress_pct),
                            message=f"Processed {processed_count}/{total_stocks} stocks. Found {platform_count} platform stocks."
                        )
                    
                    # Log progress every 100 stocks and at key milestones
                    if processed_count % 100 == 0 or processed_count in [50, 5500, 5550]:
                        progress_pct = processed_count / total_stocks * 100
                        print(f"{Fore.CYAN}[SCAN_CHECKPOINT] Progress: {processed_count}/{total_stocks} ({progress_pct:.1f}%), {platform_count} platforms, {success_count} success, {empty_count} empty, {error_count} errors{Style.RESET_ALL}")

                except CancelledError:
                    error_count += 1
                    print(f"{Fore.YELLOW}[SCAN_CHECKPOINT] 🚫 Cancelled: {stock_code} ({stock_name}) by watchdog{Style.RESET_ALL}")
                except TimeoutError:
                    error_count += 1
                    print(f"{Fore.YELLOW}[SCAN_CHECKPOINT] ⏱️ Timeout (15s) processing stock {stock_code} ({stock_name}), processed: {processed_count}/{total_stocks}{Style.RESET_ALL}")
                except Exception as e:
                    error_count += 1
                    print(f"{Fore.RED}[SCAN_CHECKPOINT] ❌ Error processing stock {stock_code} ({stock_name}): {e}{Style.RESET_ALL}")
                    import traceback
                    traceback.print_exc()

                # Update progress bar
                pbar.set_postfix(success=success_count, empty=empty_count,
                                 error=error_count, platform=platform_count)
                pbar.update(1)
                
                # If watchdog triggered and we've processed enough, exit the loop
                if hang_detected[0] and processed_count >= total_stocks * 0.95:
                    print(f"{Fore.YELLOW}[SCAN_CHECKPOINT] Exiting main loop after watchdog timeout ({processed_count}/{total_stocks} processed){Style.RESET_ALL}")
                    print(f"{Fore.CYAN}[SCAN_CHECKPOINT] Platform stocks collected before exit: {len(platform_stocks)}{Style.RESET_ALL}")
                    break
        
        # After loop, mark any remaining incomplete futures as errors
        # Check all futures to ensure we haven't missed any
        # all_futures is already set above, no need to recreate
        remaining_incomplete = [f for f in all_futures if f not in completed_futures and not f.done()]
        if remaining_incomplete:
            print(f"{Fore.YELLOW}[SCAN_CHECKPOINT] Marking {len(remaining_incomplete)} remaining incomplete futures as errors...{Style.RESET_ALL}")
            for future in remaining_incomplete:
                stock = future_to_stock[future]
                # Only mark if not already processed
                if future not in completed_futures:
                    error_count += 1
                    processed_count += 1
                    completed_futures.add(future)  # Mark as processed
                    print(f"{Fore.YELLOW}[SCAN_CHECKPOINT] ⚠️ Marking {stock['code']} ({stock['name']}) as error (incomplete){Style.RESET_ALL}")
                    pbar.set_postfix(success=success_count, empty=empty_count,
                                     error=error_count, platform=platform_count)
                    pbar.update(1)
            # Update progress after marking incomplete futures
            if update_progress:
                progress_pct = processed_count / total_stocks * 100
                update_progress(
                    progress=int(progress_pct),
                    message=f"Processed {processed_count}/{total_stocks} stocks. Found {platform_count} platform stocks. ({error_count} errors)"
                )
        
        # Ensure all tasks are accounted for - mark any missing ones as errors
        if processed_count < total_stocks:
            missing_count = total_stocks - processed_count
            print(f"{Fore.YELLOW}[SCAN_CHECKPOINT] ⚠️ Found {missing_count} missing tasks, marking as errors to complete scan...{Style.RESET_ALL}")
            for future in all_futures:
                if future not in completed_futures:
                    stock = future_to_stock[future]
                    error_count += 1
                    processed_count += 1
                    completed_futures.add(future)
                    print(f"{Fore.YELLOW}[SCAN_CHECKPOINT] ⚠️ Marking {stock['code']} ({stock['name']}) as error (missing){Style.RESET_ALL}")
                    pbar.set_postfix(success=success_count, empty=empty_count,
                                     error=error_count, platform=platform_count)
                    pbar.update(1)
                    if processed_count >= total_stocks:
                        break
            # Update progress after marking missing tasks
            if update_progress:
                progress_pct = processed_count / total_stocks * 100
                update_progress(
                    progress=int(progress_pct),
                    message=f"Processed {processed_count}/{total_stocks} stocks. Found {platform_count} platform stocks. ({error_count} errors)"
                )
        
        # Process any remaining completed futures if watchdog triggered
        if hang_detected[0]:
            print(f"{Fore.YELLOW}[SCAN_CHECKPOINT] ========================================{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}[SCAN_CHECKPOINT] Processing remaining completed futures after watchdog timeout...{Style.RESET_ALL}")
            remaining_completed = [f for f in future_to_stock.keys() if f.done() and f not in completed_futures]
            print(f"{Fore.YELLOW}[SCAN_CHECKPOINT] Found {len(remaining_completed)} remaining completed futures{Style.RESET_ALL}")
            print(f"{Fore.CYAN}[SCAN_CHECKPOINT] Platform stocks before processing remaining: {len(platform_stocks)}{Style.RESET_ALL}")
            
            for future in remaining_completed[:50]:  # Limit to 50 to avoid too long cleanup
                try:
                    stock = future_to_stock[future]
                    stock_code = stock['code']
                    stock_name = stock['name']
                    processed_count += 1
                    
                    df = future.result(timeout=2.0)  # Quick timeout
                    if not df.empty:
                        # Quick analysis
                        analysis_result = analyze_stock(
                            df, config.windows, config.box_threshold,
                            config.ma_diff_threshold, config.volatility_threshold,
                            config.volume_change_threshold, config.volume_stability_threshold,
                            config.volume_increase_threshold, config.use_volume_analysis,
                            config.use_breakthrough_prediction, config.use_window_weights,
                            config.window_weights, config.use_low_position,
                            config.high_point_lookback_days, config.decline_period_days,
                            config.decline_threshold, config.use_rapid_decline_detection,
                            config.rapid_decline_days, config.rapid_decline_threshold,
                            config.use_breakthrough_confirmation,
                            config.breakthrough_confirmation_days,
                            config.use_box_detection, config.box_quality_threshold,
                            config.max_turnover_rate, config.allow_turnover_spikes,
                            getattr(config, 'check_relative_strength', False),
                            getattr(config, 'outperform_index_threshold', 0.0),
                            market_df,
                            end_date
                        )
                        if analysis_result["is_platform"]:
                            platform_count += 1
                            outperform_index = analysis_result.get("outperform_index")
                            stock_return = analysis_result.get("stock_return")
                            market_return = analysis_result.get("market_return")
                            print(f"[RELATIVE_STRENGTH_DEBUG] Stock {stock_code} ({stock_name}): outperform_index={outperform_index}, stock_return={stock_return}, market_return={market_return}")
                            
                            platform_stock = {
                                'code': stock_code, 'name': stock_name,
                                'industry': stock.get('industry', 'Unknown'),
                                'platform_windows': analysis_result["platform_windows"],
                                'details': analysis_result["details"],
                                'selection_reasons': analysis_result["selection_reasons"],
                                'kline_data': df.to_dict(orient='records'),
                                'outperform_index': outperform_index,
                                'stock_return': stock_return,
                                'market_return': market_return
                            }
                            if "mark_lines" in analysis_result:
                                platform_stock['mark_lines'] = analysis_result["mark_lines"]
                            if "turnover_analysis" in analysis_result:
                                platform_stock['turnover_analysis'] = analysis_result["turnover_analysis"]
                            platform_stocks.append(platform_stock)
                            success_count += 1
                        else:
                            success_count += 1
                    else:
                        empty_count += 1
                    pbar.update(1)
                except Exception as e:
                    error_count += 1
                    print(f"{Fore.YELLOW}[SCAN_CHECKPOINT] ⚠️ Error processing remaining future: {e}{Style.RESET_ALL}")
                    pbar.update(1)

            # Close progress bar
            print(f"{Fore.GREEN}[SCAN_CHECKPOINT] Main processing loop completed{Style.RESET_ALL}")
            pbar.close()
            
            print(f"{Fore.CYAN}[SCAN_CHECKPOINT] Platform stocks collected so far: {len(platform_stocks)}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}[SCAN_CHECKPOINT] Stats before executor shutdown: processed={processed_count}/{total_stocks}, platforms={platform_count}{Style.RESET_ALL}")
            
            # Manually shutdown executor - don't wait if watchdog triggered to avoid blocking
            if executor:
                try:
                    if hang_detected[0]:
                        print(f"{Fore.YELLOW}[SCAN_CHECKPOINT] Watchdog timeout detected, calling executor.shutdown(wait=False) to avoid blocking...{Style.RESET_ALL}")
                        executor.shutdown(wait=False)  # Don't wait for stuck tasks
                        print(f"{Fore.GREEN}[SCAN_CHECKPOINT] Executor shutdown(wait=False) completed{Style.RESET_ALL}")
                    else:
                        print(f"{Fore.CYAN}[SCAN_CHECKPOINT] Normal shutdown, calling executor.shutdown(wait=True)...{Style.RESET_ALL}")
                        executor.shutdown(wait=True)  # Normal shutdown, wait for tasks
                        print(f"{Fore.GREEN}[SCAN_CHECKPOINT] Executor shutdown(wait=True) completed{Style.RESET_ALL}")
                except Exception as e:
                    print(f"{Fore.YELLOW}[SCAN_CHECKPOINT] Warning: Error shutting down executor: {e}{Style.RESET_ALL}")
                    # Continue anyway - we have the results
    except Exception as e:
        print(f"{Fore.RED}[SCAN_CHECKPOINT] ⚠️ Exception during executor execution: {e}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()
        # Continue with filtering even if executor had issues
    finally:
        # Ensure we always reach this point even if executor shutdown had issues
        print(f"{Fore.GREEN}[SCAN_CHECKPOINT] ========================================{Style.RESET_ALL}")
        print(f"{Fore.GREEN}[SCAN_CHECKPOINT] Executor context exited, proceeding with filtering...{Style.RESET_ALL}")
        print(f"{Fore.CYAN}[SCAN_CHECKPOINT] Platform stocks before filtering: {len(platform_stocks)}{Style.RESET_ALL}")
        # Safely access variables that may not be initialized if exception occurred early
        try:
            print(f"{Fore.GREEN}[SCAN_CHECKPOINT] Final stats - Processed: {processed_count}/{total_stocks}, Success: {success_count}, Empty: {empty_count}, Errors: {error_count}, Platforms: {platform_count}{Style.RESET_ALL}")
        except (UnboundLocalError, NameError):
            # Variables not initialized, use defaults
            processed_count = processed_count if 'processed_count' in locals() else 0
            total_stocks = total_stocks if 'total_stocks' in locals() else len(stock_list)
            success_count = success_count if 'success_count' in locals() else 0
            empty_count = empty_count if 'empty_count' in locals() else 0
            error_count = error_count if 'error_count' in locals() else 0
            platform_count = platform_count if 'platform_count' in locals() else 0
            print(f"{Fore.YELLOW}[SCAN_CHECKPOINT] Final stats (partial) - Processed: {processed_count}/{total_stocks}, Success: {success_count}, Empty: {empty_count}, Errors: {error_count}, Platforms: {platform_count}{Style.RESET_ALL}")
    
    # Check if there are incomplete tasks
    incomplete = total_stocks - processed_count
    scan_was_incomplete = incomplete > 0
    if incomplete > 0:
        print(f"{Fore.YELLOW}[SCAN_CHECKPOINT] ⚠️ Warning: {incomplete} tasks did not complete{Style.RESET_ALL}")
        # These should already be marked as errors above, but log for clarity
        # Only check a limited number to avoid blocking on large futures sets
        if future_to_stock and all_futures:
            try:
                # Limit to first 20 incomplete futures to avoid blocking
                incomplete_futures = [f for f in list(all_futures)[:50] if not f.done()][:20]
                for future in incomplete_futures:
                    if future in future_to_stock:
                        stock = future_to_stock[future]
                        print(f"{Fore.YELLOW}[SCAN_CHECKPOINT] ⚠️ Task {stock['code']} ({stock['name']}) did not complete{Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.YELLOW}[SCAN_CHECKPOINT] ⚠️ Could not check incomplete tasks: {e}{Style.RESET_ALL}")
    
    print(f"{Fore.GREEN}[SCAN_CHECKPOINT] Data fetching completed: {success_count} success, {empty_count} empty, {error_count} errors{Style.RESET_ALL}")
    print(f"{Fore.GREEN}[SCAN_CHECKPOINT] Found {platform_count} platform stocks, starting filters...{Style.RESET_ALL}")
    print(f"{Fore.CYAN}[SCAN_CHECKPOINT] Platform stocks list length: {len(platform_stocks)}{Style.RESET_ALL}")

    # Apply fundamental analysis filter if enabled
    if config.use_fundamental_filter:
        print(f"{Fore.CYAN}Applying fundamental analysis filter...{Style.RESET_ALL}")
        fundamental_filtered_stocks = analyze_fundamentals(
            platform_stocks,
            use_fundamental_filter=config.use_fundamental_filter,
            revenue_growth_percentile=config.revenue_growth_percentile,
            profit_growth_percentile=config.profit_growth_percentile,
            roe_percentile=config.roe_percentile,
            liability_percentile=config.liability_percentile,
            pe_percentile=config.pe_percentile,
            pb_percentile=config.pb_percentile,
            years_to_check=config.fundamental_years_to_check
        )
        fundamental_count = len(fundamental_filtered_stocks)
        print(f"{Fore.GREEN}Fundamental analysis complete. {fundamental_count} stocks passed out of {platform_count}.{Style.RESET_ALL}")
    else:
        fundamental_filtered_stocks = platform_stocks
        fundamental_count = platform_count
        print(f"{Fore.YELLOW}Fundamental analysis filter disabled.{Style.RESET_ALL}")

    # Apply industry diversity filter
    # IMPORTANT: Sort stocks by code before filtering to ensure deterministic results
    # This is necessary because concurrent processing may produce different orders
    print(f"{Fore.CYAN}[SCAN_CHECKPOINT] Sorting stocks by code for deterministic filtering...{Style.RESET_ALL}")
    fundamental_filtered_stocks_sorted = sorted(
        fundamental_filtered_stocks,
        key=lambda s: s.get('code', '')
    )
    print(f"{Fore.CYAN}[SCAN_CHECKPOINT] Applying industry diversity filter on {len(fundamental_filtered_stocks_sorted)} stocks (expected_count={config.expected_count}){Style.RESET_ALL}")
    try:
        filtered_stocks = apply_industry_diversity_filter(
            fundamental_filtered_stocks_sorted,
            expected_count=config.expected_count
        )
        print(f"{Fore.GREEN}[SCAN_CHECKPOINT] Industry filter complete, selected {len(filtered_stocks)} stocks{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}[SCAN_CHECKPOINT] ⚠️ Error in industry filter: {e}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()
        # Fallback: return all stocks if filter fails (use sorted version for consistency)
        filtered_stocks = fundamental_filtered_stocks_sorted
        print(f"{Fore.YELLOW}[SCAN_CHECKPOINT] Using all {len(filtered_stocks)} stocks as fallback{Style.RESET_ALL}")

    # Sort by breakthrough & breakthrough precursor signals, then by box quality
    # Priority order (higher priority first):
    # 1. Breakthrough confirmation & breakthrough precursor signals
    # 2. Box quality
    print(f"{Fore.CYAN}[SCAN_CHECKPOINT] Starting multi-criteria sorting...{Style.RESET_ALL}")
    
    def calculate_sort_score(stock: Dict[str, Any]) -> Tuple[int, int, float]:
        """
        Calculate a composite score for sorting stocks.
        Returns: (has_confirmation, signal_count, box_quality)
        - has_confirmation: 1 if has breakthrough confirmation, 0 otherwise (highest priority)
        - signal_count: number of breakthrough precursor indicators (second priority)
        - box_quality: box quality score (third priority, higher is better)
        """
        has_confirmation = 0
        signal_count = 0
        box_quality = 0.0
        
        # Check for breakthrough confirmation (highest priority)
        if config.use_breakthrough_confirmation:
            if stock.get('has_breakthrough_confirmation', False):
                has_confirmation = 1
        
        # Check for breakthrough prediction signals
        if config.use_breakthrough_prediction and 'breakthrough_prediction' in stock:
            breakthrough_pred = stock['breakthrough_prediction']
            if isinstance(breakthrough_pred, dict):
                signal_count = breakthrough_pred.get('signal_count', 0)
        
        # Get box quality score (third priority)
        if config.use_box_detection and 'box_analysis' in stock:
            box_analysis = stock['box_analysis']
            if isinstance(box_analysis, dict):
                box_quality = box_analysis.get('box_quality', 0.0)
                # Ensure box_quality is a valid number
                if not isinstance(box_quality, (int, float)) or (isinstance(box_quality, float) and (math.isnan(box_quality) or math.isinf(box_quality))):
                    box_quality = 0.0
        
        return (has_confirmation, signal_count, box_quality)
    
    # Sort stocks: first by has_confirmation (descending), then by signal_count (descending), then by box_quality (descending)
    filtered_stocks.sort(
        key=lambda stock: calculate_sort_score(stock),
        reverse=True
    )
    
    sorted_count = len(filtered_stocks)
    print(f"{Fore.GREEN}Sorted {sorted_count} stocks by breakthrough signals and box quality.{Style.RESET_ALL}")
    
    # Log sorting details for first few stocks
    if sorted_count > 0:
        print(f"{Fore.CYAN}Top 5 stocks after sorting:{Style.RESET_ALL}")
        for i, stock in enumerate(filtered_stocks[:5], 1):
            score = calculate_sort_score(stock)
            print(f"  {i}. {stock.get('code', 'unknown')} ({stock.get('name', 'unknown')}): "
                  f"confirmation={score[0]}, signals={score[1]}, box_quality={score[2]:.2f}")
    
    print(f"{Fore.GREEN}[SCAN_CHECKPOINT] Sorting complete, preparing to return results{Style.RESET_ALL}")

    # Get data source statistics
    # For ProcessPoolExecutor, use collected_data_sources (from return values)
    # For ThreadPoolExecutor, also check global stats as fallback
    data_source_stats = collected_data_sources.copy()
    global_stats = get_data_source_stats()
    # Merge global stats (for ThreadPoolExecutor) with collected stats
    for code, source in global_stats.items():
        if code not in data_source_stats:
            data_source_stats[code] = source
    
    # Count data sources
    db_only_count = sum(1 for source in data_source_stats.values() if source == 'db')
    api_only_count = sum(1 for source in data_source_stats.values() if source == 'api')
    mixed_count = sum(1 for source in data_source_stats.values() if source == 'mixed')
    
    # Clear stats for next scan
    clear_data_source_stats()

    # Print summary
    print(f"{Fore.CYAN}======================================{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Scan completed{Style.RESET_ALL}")
    print(f"{Fore.CYAN}======================================{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Scan configuration:{Style.RESET_ALL}")
    print(f"  - Date range: {Fore.GREEN}{start_date} to {end_date}{Style.RESET_ALL}")
    print(f"  - Data range: {Fore.GREEN}{min_data_days} days{Style.RESET_ALL}")
    print(f"  - Windows: {Fore.GREEN}{config.windows}{Style.RESET_ALL}")
    print(f"  - Max window: {Fore.GREEN}{max_window} days{Style.RESET_ALL}")
    print(
        f"Total stocks processed: {Fore.GREEN}{success_count + empty_count + error_count}{Style.RESET_ALL}")
    print(f"  - Success: {Fore.GREEN}{success_count}{Style.RESET_ALL}")
    print(f"  - Empty data: {Fore.YELLOW}{empty_count}{Style.RESET_ALL}")
    print(f"  - Errors: {Fore.RED}{error_count}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Data source statistics:{Style.RESET_ALL}")
    print(f"  - From database only: {Fore.GREEN}{db_only_count}{Style.RESET_ALL}")
    print(f"  - From API only: {Fore.BLUE}{api_only_count}{Style.RESET_ALL}")
    print(f"  - Mixed (database + API): {Fore.YELLOW}{mixed_count}{Style.RESET_ALL}")
    print(
        f"Platform stocks found: {Fore.GREEN}{platform_count}{Style.RESET_ALL}")
    if config.use_fundamental_filter:
        print(
            f"Fundamental filtered stocks: {Fore.GREEN}{fundamental_count}{Style.RESET_ALL}")
    print(
        f"Filtered stocks (industry diversity): {Fore.GREEN}{len(filtered_stocks)}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}======================================{Style.RESET_ALL}")

    # Final progress update - always mark as 100% since all tasks are accounted for (even if some are errors)
    print(f"{Fore.CYAN}[SCAN_CHECKPOINT] Updating final progress{Style.RESET_ALL}")
    if update_progress:
        # Ensure processed_count equals total_stocks (all tasks accounted for, even if some are errors)
        if processed_count < total_stocks:
            print(f"{Fore.YELLOW}[SCAN_CHECKPOINT] ⚠️ Adjusting processed_count from {processed_count} to {total_stocks}{Style.RESET_ALL}")
            # Mark any remaining tasks as errors
            missing_count = total_stocks - processed_count
            if missing_count > 0 and future_to_stock and all_futures:
                try:
                    for future in all_futures:
                        if future not in completed_futures:
                            error_count += 1
                            processed_count += 1
                            completed_futures.add(future)
                            if missing_count <= 5 and future in future_to_stock:  # Only log if few missing
                                stock = future_to_stock[future]
                                print(f"{Fore.YELLOW}[SCAN_CHECKPOINT] ⚠️ Final cleanup: Marking {stock['code']} as error{Style.RESET_ALL}")
                            if processed_count >= total_stocks:
                                break
                except Exception as e:
                    print(f"{Fore.YELLOW}[SCAN_CHECKPOINT] ⚠️ Error in final cleanup: {e}{Style.RESET_ALL}")
            # Force to total_stocks if still not equal
            if processed_count < total_stocks:
                processed_count = total_stocks
        
        # Always mark as 100% complete since all tasks have been processed (successfully or as errors)
        if error_count > 0:
            update_progress(
                progress=100,
                message=f"Scan completed. Processed {processed_count}/{total_stocks} stocks ({error_count} errors). Found {platform_count} platform stocks, filtered to {len(filtered_stocks)}."
            )
        else:
            update_progress(
                progress=100,
                message=f"Scan completed. Processed {processed_count}/{total_stocks} stocks. Found {platform_count} platform stocks, filtered to {len(filtered_stocks)}."
            )
    
    print(f"{Fore.GREEN}[SCAN_CHECKPOINT] ✓ Scan complete! Returning {len(filtered_stocks)} stocks{Style.RESET_ALL}")
    print(f"{Fore.CYAN}[SCAN_CHECKPOINT] Final return: {len(filtered_stocks)} filtered stocks, {processed_count}/{total_stocks} processed{Style.RESET_ALL}")
    
    # Ensure we return even if there were incomplete tasks
    if scan_was_incomplete:
        print(f"{Fore.YELLOW}[SCAN_CHECKPOINT] ⚠️ Scan was incomplete ({incomplete} tasks), but returning results anyway{Style.RESET_ALL}")
    
    # Final verification before return
    print(f"{Fore.CYAN}[SCAN_CHECKPOINT] About to return from scan_stocks: {len(filtered_stocks)} stocks, type: {type(filtered_stocks)}{Style.RESET_ALL}")
    if filtered_stocks:
        print(f"{Fore.CYAN}[SCAN_CHECKPOINT] First stock code: {filtered_stocks[0].get('code', 'unknown') if isinstance(filtered_stocks[0], dict) else 'N/A'}{Style.RESET_ALL}")
    
    # Return statistics if requested
    if return_stats:
        return filtered_stocks, {
            'total_scanned': total_stocks,
            'success_count': success_count
        }
    
    return filtered_stocks
