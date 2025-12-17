"""
Platform Scanner module for scanning stocks for platform consolidation patterns.
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import time
from datetime import datetime, timedelta
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed, CancelledError
from tqdm import tqdm
from colorama import Fore, Style
import platform as platform_module

from .data_fetcher import fetch_kline_data, baostock_login
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
    Prepare a list of stocks for scanning, excluding indices and merging industry data.

    Args:
        stock_basics_df: DataFrame containing stock basic information
        industry_df: DataFrame containing industry classification

    Returns:
        List of dictionaries with stock information
    """
    # Filter out indices (type=2) and non-active stocks (status=0)
    stock_list = []

    for _, row in stock_basics_df.iterrows():
        # Skip indices and inactive stocks
        if row['type'] == '2' or row['status'] == '0':
            continue

        # Support both 'code_name' (from API) and 'name' (from database)
        stock_name = row.get('code_name') or row.get('name', '')

        stock_info = {
            'code': row['code'],
            'name': stock_name,
            'type': row['type'],
            'status': row['status'],
            'industry': 'Unknown'  # Default value
        }

        # Add to list
        stock_list.append(stock_info)

    # Add industry information if available
    if not industry_df.empty:
        industry_dict = dict(zip(industry_df['code'], industry_df['industry']))
        for stock in stock_list:
            if stock['code'] in industry_dict:
                stock['industry'] = industry_dict[stock['code']]

    return stock_list


def scan_stocks(stock_list: List[Dict[str, Any]],
                config: ScanConfig,
                update_progress: Optional[callable] = None,
                end_date: Optional[str] = None) -> List[Dict[str, Any]]:
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
    start_date = (end_date_obj - timedelta(days=max_window * 2)
                  ).strftime('%Y-%m-%d')

    print(f"{Fore.CYAN}======================================{Style.RESET_ALL}")
    print(f"{Fore.CYAN}[SCAN_CHECKPOINT] Starting stock platform scan{Style.RESET_ALL}")
    print(f"{Fore.CYAN}======================================{Style.RESET_ALL}")
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

    # List to store platform stocks
    platform_stocks = []

    # Use executor for concurrent processing
    with executor_class(max_workers=config.max_workers, initializer=baostock_login) as executor:
        # Track submitted tasks for debugging (thread-safe)
        import threading as threading_module
        submitted_stocks = {s['code']: s['name'] for s in stock_list}
        started_stocks = set()
        completed_stocks = set()
        stocks_lock = threading_module.Lock()
        
        # Create a wrapper to track task execution
        def fetch_with_tracking(code, name, start_date, end_date, retry_attempts, retry_delay):
            """Wrapper to track when task actually starts executing in thread pool"""
            import threading
            with stocks_lock:
                started_stocks.add(code)
            print(f"{Fore.MAGENTA}[SCAN_CHECKPOINT] 🚀 TASK STARTED in thread {threading.current_thread().name} for {code} ({name}){Style.RESET_ALL}")
            try:
                result = fetch_kline_data(code, start_date, end_date, retry_attempts, retry_delay)
                with stocks_lock:
                    completed_stocks.add(code)
                print(f"{Fore.MAGENTA}[SCAN_CHECKPOINT] ✅ TASK FINISHED for {code} ({name}), returning {len(result)} rows{Style.RESET_ALL}")
                return result
            except Exception as e:
                with stocks_lock:
                    completed_stocks.add(code)  # Mark as completed even if failed
                print(f"{Fore.RED}[SCAN_CHECKPOINT] 💥 TASK EXCEPTION for {code} ({name}): {e}{Style.RESET_ALL}")
                raise
        
        # Submit tasks
        print(f"{Fore.CYAN}[SCAN_CHECKPOINT] Submitting {len(stock_list)} tasks to executor{Style.RESET_ALL}")
        future_to_stock = {
            executor.submit(fetch_with_tracking, s['code'], s['name'], start_date, end_date,
                            config.retry_attempts, config.retry_delay): s
            for s in stock_list
        }

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
                time_module.sleep(30)  # Check every 30 seconds
                current_count = processed_count
                completion_rate = current_count / total_stocks
                elapsed = time_module.time() - start_time
                
                # Always log watchdog heartbeat
                print(f"{Fore.CYAN}[SCAN_CHECKPOINT] 🐕 Watchdog: {current_count}/{total_stocks} ({completion_rate*100:.1f}%), elapsed: {elapsed:.0f}s{Style.RESET_ALL}")
                
                # If no progress in 30s and 95%+ complete, consider it hung
                if current_count == last_count:
                    no_progress_cycles += 1
                    if completion_rate >= 0.95 and no_progress_cycles >= 1:
                        remaining = total_stocks - current_count
                        print(f"{Fore.YELLOW}[SCAN_CHECKPOINT] ⚠️ Watchdog: No progress for {30*no_progress_cycles}s, {remaining} tasks stuck (95%+ done){Style.RESET_ALL}")
                        
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
        
        for future in as_completed(future_to_stock):
            # Check hang status - will break on next completed future after watchdog triggers
            if hang_detected[0]:
                print(f"{Fore.YELLOW}[SCAN_CHECKPOINT] Breaking loop due to watchdog timeout{Style.RESET_ALL}")
                break
                
            stock = future_to_stock[future]
            stock_code = stock['code']
            stock_name = stock['name']
            processed_count += 1
            
            # Log first task completion
            if processed_count == 1:
                print(f"{Fore.CYAN}[SCAN_CHECKPOINT] First task completed: {stock_code} ({stock_name}){Style.RESET_ALL}")

            try:
                # Get K-line data with timeout to prevent indefinite waiting
                df = future.result(timeout=15)

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
                    config.box_quality_threshold
                )
                print(f"{Fore.CYAN}[SCAN_CHECKPOINT] ✓ Analysis completed for {stock_code}, is_platform: {analysis_result['is_platform']}{Style.RESET_ALL}")

                success_count += 1

                # If it's a platform stock, add to results
                if analysis_result["is_platform"]:
                    platform_count += 1
                    print(f"{Fore.GREEN}[SCAN_CHECKPOINT] ✓ Platform found: {stock_code} ({stock_name}) - Total platforms: {platform_count}{Style.RESET_ALL}")

                    # Create result object
                    platform_stock = {
                        'code': stock_code,
                        'name': stock_name,
                        'industry': stock.get('industry', 'Unknown'),
                        'platform_windows': analysis_result["platform_windows"],
                        'details': analysis_result["details"],
                        'selection_reasons': analysis_result["selection_reasons"],
                        'kline_data': df.to_dict(orient='records')
                    }

                    # Add mark lines if available
                    if "mark_lines" in analysis_result:
                        platform_stock['mark_lines'] = analysis_result["mark_lines"]
                        print(
                            f"{Fore.GREEN}添加标记线数据到股票 {stock_code}: {analysis_result['mark_lines']}{Style.RESET_ALL}")

                    # Add volume analysis results if available
                    if config.use_volume_analysis and "volume_analysis" in analysis_result:
                        platform_stock['volume_analysis'] = analysis_result["volume_analysis"]

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

        # Close progress bar
        print(f"{Fore.GREEN}[SCAN_CHECKPOINT] Main processing loop completed{Style.RESET_ALL}")
        pbar.close()
        
    print(f"{Fore.GREEN}[SCAN_CHECKPOINT] Final stats - Processed: {processed_count}/{total_stocks}, Success: {success_count}, Empty: {empty_count}, Errors: {error_count}, Platforms: {platform_count}{Style.RESET_ALL}")
    
    # Check if there are incomplete tasks
    incomplete = total_stocks - processed_count
    if incomplete > 0:
        print(f"{Fore.YELLOW}[SCAN_CHECKPOINT] ⚠️ Warning: {incomplete} tasks did not complete, cancelling them...{Style.RESET_ALL}")
        # Cancel remaining futures
        for future in future_to_stock:
            if not future.done():
                try:
                    future.cancel()
                except:
                    pass
    
    print(f"{Fore.GREEN}[SCAN_CHECKPOINT] Data fetching completed: {success_count} success, {empty_count} empty, {error_count} errors{Style.RESET_ALL}")
    print(f"{Fore.GREEN}[SCAN_CHECKPOINT] Found {platform_count} platform stocks, starting filters...{Style.RESET_ALL}")

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
    print(f"{Fore.CYAN}[SCAN_CHECKPOINT] Applying industry diversity filter on {len(fundamental_filtered_stocks)} stocks{Style.RESET_ALL}")
    filtered_stocks = apply_industry_diversity_filter(
        fundamental_filtered_stocks,
        expected_count=config.expected_count
    )
    print(f"{Fore.GREEN}[SCAN_CHECKPOINT] Industry filter complete, selected {len(filtered_stocks)} stocks{Style.RESET_ALL}")

    # Sort by breakthrough & breakthrough precursor signals if enabled
    # Note: This should happen before industry diversity filter to prioritize stocks with breakthrough signals
    # But we apply it after to maintain industry diversity while still sorting within the filtered set
    print(f"{Fore.CYAN}[SCAN_CHECKPOINT] Starting breakthrough sorting (enabled={config.sort_by_breakthrough}){Style.RESET_ALL}")
    if config.sort_by_breakthrough:
        print(f"{Fore.CYAN}Sorting stocks by breakthrough & breakthrough precursor signals...{Style.RESET_ALL}")
        
        def calculate_breakthrough_score(stock: Dict[str, Any]) -> Tuple[int, int]:
            """
            Calculate a score for sorting stocks by breakthrough signals.
            Returns: (has_confirmation, signal_count)
            - has_confirmation: 1 if has breakthrough confirmation, 0 otherwise
            - signal_count: number of breakthrough precursor indicators
            Higher scores (has_confirmation first, then signal_count) should be sorted first.
            """
            has_confirmation = 0
            signal_count = 0
            
            # Check for breakthrough confirmation (highest priority)
            if config.use_breakthrough_confirmation:
                if stock.get('has_breakthrough_confirmation', False):
                    has_confirmation = 1
            
            # Check for breakthrough prediction signals
            if config.use_breakthrough_prediction and 'breakthrough_prediction' in stock:
                breakthrough_pred = stock['breakthrough_prediction']
                if isinstance(breakthrough_pred, dict):
                    signal_count = breakthrough_pred.get('signal_count', 0)
            
            return (has_confirmation, signal_count)
        
        # Sort stocks: first by has_confirmation (descending), then by signal_count (descending)
        filtered_stocks.sort(
            key=lambda stock: calculate_breakthrough_score(stock),
            reverse=True
        )
        
        sorted_count = len(filtered_stocks)
        print(f"{Fore.GREEN}Sorted {sorted_count} stocks by breakthrough signals.{Style.RESET_ALL}")
    else:
        print(f"{Fore.YELLOW}Breakthrough sorting disabled.{Style.RESET_ALL}")
    
    print(f"{Fore.GREEN}[SCAN_CHECKPOINT] Sorting complete, preparing to return results{Style.RESET_ALL}")

    # Print summary
    print(f"{Fore.CYAN}======================================{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Scan completed{Style.RESET_ALL}")
    print(f"{Fore.CYAN}======================================{Style.RESET_ALL}")
    print(
        f"Total stocks processed: {Fore.GREEN}{success_count + empty_count + error_count}{Style.RESET_ALL}")
    print(f"  - Success: {Fore.GREEN}{success_count}{Style.RESET_ALL}")
    print(f"  - Empty data: {Fore.YELLOW}{empty_count}{Style.RESET_ALL}")
    print(f"  - Errors: {Fore.RED}{error_count}{Style.RESET_ALL}")
    print(
        f"Platform stocks found: {Fore.GREEN}{platform_count}{Style.RESET_ALL}")
    if config.use_fundamental_filter:
        print(
            f"Fundamental filtered stocks: {Fore.GREEN}{fundamental_count}{Style.RESET_ALL}")
    print(
        f"Filtered stocks (industry diversity): {Fore.GREEN}{len(filtered_stocks)}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}======================================{Style.RESET_ALL}")

    # Final progress update
    print(f"{Fore.CYAN}[SCAN_CHECKPOINT] Updating final progress{Style.RESET_ALL}")
    if update_progress:
        update_progress(
            progress=100,
            message=f"Scan completed. Found {platform_count} platform stocks, filtered to {len(filtered_stocks)}."
        )
    
    print(f"{Fore.GREEN}[SCAN_CHECKPOINT] ✓ Scan complete! Returning {len(filtered_stocks)} stocks{Style.RESET_ALL}")
    return filtered_stocks
