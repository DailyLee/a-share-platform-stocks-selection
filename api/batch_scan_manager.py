"""
Batch Scan Manager module for handling batch scanning tasks.
Manages batch scan tasks and executes scans in the background.
"""
import uuid
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from enum import Enum

try:
    from api.stock_database import get_stock_database
    from api.config import ScanConfig
    from api.data_fetcher import fetch_stock_basics, fetch_industry_data, BaostockConnectionManager, set_use_local_database_first
    from api.platform_scanner import prepare_stock_list, scan_stocks
except ImportError:
    from .stock_database import get_stock_database
    from .config import ScanConfig
    from .data_fetcher import fetch_stock_basics, fetch_industry_data, BaostockConnectionManager, set_use_local_database_first
    from .platform_scanner import prepare_stock_list, scan_stocks

from colorama import Fore, Style
import colorama


class BatchScanStatus(Enum):
    """Batch scan task status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BatchScanManager:
    """Manages batch scan tasks."""
    
    _instance = None
    _lock = threading.Lock()
    _running_tasks: Dict[str, threading.Thread] = {}
    
    def __new__(cls):
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super(BatchScanManager, cls).__new__(cls)
        return cls._instance
    
    def create_batch_scan_task(self, task_name: str, start_date: str, end_date: str,
                               scan_period_days: int, scan_config: Dict[str, Any]) -> str:
        """
        Create a new batch scan task.
        
        Args:
            task_name: User-defined task name
            start_date: Start date in 'YYYY-MM-DD' format
            end_date: End date in 'YYYY-MM-DD' format
            scan_period_days: Number of days between scans
            scan_config: Scan configuration dictionary
            
        Returns:
            Task ID
        """
        task_id = str(uuid.uuid4())
        db = get_stock_database()
        db.save_batch_scan_task(task_id, task_name, start_date, end_date, scan_period_days, scan_config)
        return task_id
    
    def start_batch_scan_task(self, task_id: str) -> bool:
        """
        Start a batch scan task in the background.
        
        Args:
            task_id: Task ID
            
        Returns:
            True if started successfully, False otherwise
        """
        with self._lock:
            if task_id in self._running_tasks:
                return False  # Task already running
            
            # Check if task exists
            db = get_stock_database()
            task = db.get_batch_scan_task(task_id)
            if not task:
                return False
            
            # Start background thread
            thread = threading.Thread(target=self._run_batch_scan_task, args=(task_id,), daemon=True)
            thread.start()
            self._running_tasks[task_id] = thread
            
            return True
    
    def cancel_batch_scan_task(self, task_id: str) -> bool:
        """
        Cancel a running batch scan task.
        
        Args:
            task_id: Task ID
            
        Returns:
            True if cancelled successfully, False otherwise
        """
        db = get_stock_database()
        task = db.get_batch_scan_task(task_id)
        if not task:
            return False
        
        if task['status'] not in ['pending', 'running']:
            return False  # Cannot cancel completed/failed/cancelled tasks
        
        # Update status to cancelled
        db.update_batch_scan_task(task_id, status='cancelled', message='任务已取消')
        
        # Remove from running tasks
        with self._lock:
            self._running_tasks.pop(task_id, None)
        
        return True
    
    def _run_batch_scan_task(self, task_id: str):
        """
        Execute a batch scan task.
        
        Args:
            task_id: Task ID
        """
        colorama.init()
        db = get_stock_database()
        
        try:
            # Get task details
            task = db.get_batch_scan_task(task_id)
            if not task:
                print(f"{Fore.RED}Task {task_id} not found{Style.RESET_ALL}")
                return
            
            # Update status to running
            db.update_batch_scan_task(
                task_id,
                status='running',
                started_at='now',
                message='批量扫描任务已开始'
            )
            
            print(f"{Fore.CYAN}======================================{Style.RESET_ALL}")
            print(f"{Fore.CYAN}Starting batch scan task: {task['taskName']}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}======================================{Style.RESET_ALL}")
            
            # Parse dates
            start_date = datetime.strptime(task['startDate'], '%Y-%m-%d')
            end_date = datetime.strptime(task['endDate'], '%Y-%m-%d')
            scan_period_days = task['scanPeriodDays']
            scan_config_dict = task['scanConfig']
            
            # Generate scan dates
            scan_dates = []
            current_date = start_date
            while current_date <= end_date:
                scan_dates.append(current_date.strftime('%Y-%m-%d'))
                current_date += timedelta(days=scan_period_days)
            
            total_scans = len(scan_dates)
            print(f"{Fore.GREEN}Total scans to perform: {total_scans}{Style.RESET_ALL}")
            print(f"{Fore.GREEN}Scan dates: {scan_dates[:5]}...{scan_dates[-5:] if len(scan_dates) > 5 else scan_dates}{Style.RESET_ALL}")
            
            # Update total scans
            db.update_batch_scan_task(task_id, total_scans=total_scans)
            
            # ===== 性能优化：预加载所有股票的历史数据 =====
            # 计算需要的数据范围（考虑最大窗口期）
            max_window = max(scan_config_dict.get('windows', [30, 60, 90])) if scan_config_dict.get('windows') else 90
            data_start_date = (start_date - timedelta(days=max_window * 2)).strftime('%Y-%m-%d')
            data_end_date = task['endDate']
            
            print(f"{Fore.CYAN}[BATCH_SCAN] 开始预加载历史数据: {data_start_date} 至 {data_end_date}{Style.RESET_ALL}")
            db.update_batch_scan_task(
                task_id,
                message=f'正在预加载历史数据: {data_start_date} 至 {data_end_date}'
            )
            
            # 一次性获取股票基本信息和行业数据
            use_db_first = scan_config_dict.get('use_local_database_first', True)
            set_use_local_database_first(use_db_first)
            
            with BaostockConnectionManager():
                stock_basics_df = fetch_stock_basics(use_local_database_first=use_db_first)
                try:
                    industry_df = fetch_industry_data(use_local_database_first=use_db_first)
                except Exception as e:
                    print(f"{Fore.YELLOW}Warning: Failed to fetch industry data: {e}{Style.RESET_ALL}")
                    industry_df = None
                
                # 准备股票列表
                if industry_df is not None:
                    stock_list = prepare_stock_list(stock_basics_df, industry_df)
                else:
                    import pandas as pd
                    stock_list = prepare_stock_list(stock_basics_df, pd.DataFrame())
                
                # 限制股票数量（如果配置了）
                if scan_config_dict.get('max_stock_count') and scan_config_dict['max_stock_count'] > 0:
                    stock_list = stock_list[:scan_config_dict['max_stock_count']]
                
                print(f"{Fore.GREEN}[BATCH_SCAN] 股票列表准备完成: {len(stock_list)} 只股票{Style.RESET_ALL}")
                
                # 预加载K线数据（确保数据库中有完整数据）
                # 只预加载数据库中缺失的数据，避免重复获取
                self._preload_kline_data(stock_list, data_start_date, data_end_date, task_id, use_db_first)
            
            print(f"{Fore.GREEN}[BATCH_SCAN] 历史数据预加载完成，开始执行批量扫描{Style.RESET_ALL}")
            db.update_batch_scan_task(
                task_id,
                message='历史数据预加载完成，开始执行批量扫描'
            )
            # ===== 预加载完成 =====
            
            # Execute each scan
            completed_scans = 0
            failed_scans = 0
            
            for idx, scan_date in enumerate(scan_dates):
                # Check if task was cancelled
                task = db.get_batch_scan_task(task_id)
                if task and task['status'] == 'cancelled':
                    print(f"{Fore.YELLOW}Task {task_id} was cancelled{Style.RESET_ALL}")
                    break
                
                try:
                    # Update current scan date
                    db.update_batch_scan_task(
                        task_id,
                        current_scan_date=scan_date,
                        message=f'正在扫描: {scan_date} ({idx + 1}/{total_scans})'
                    )
                    
                    print(f"{Fore.CYAN}[{idx + 1}/{total_scans}] Scanning date: {scan_date}{Style.RESET_ALL}")
                    
                    # Execute scan (传入预准备的股票列表以提升性能)
                    scan_result = self._execute_single_scan(scan_date, scan_config_dict, task_id, stock_list)
                    
                    if scan_result:
                        # Save result
                        result_id = str(uuid.uuid4())
                        db.save_batch_scan_result(
                            result_id,
                            task_id,
                            scan_date,
                            scan_config_dict,
                            scan_result['scanned_stocks'],
                            scan_result['total_scanned'],
                            scan_result['success_count']
                        )
                        completed_scans += 1
                        print(f"{Fore.GREEN}[{idx + 1}/{total_scans}] Scan completed: {scan_date}, found {len(scan_result['scanned_stocks'])} stocks{Style.RESET_ALL}")
                    else:
                        failed_scans += 1
                        print(f"{Fore.RED}[{idx + 1}/{total_scans}] Scan failed: {scan_date}{Style.RESET_ALL}")
                    
                    # Update progress
                    progress = int((idx + 1) / total_scans * 100)
                    db.update_batch_scan_task(
                        task_id,
                        completed_scans=completed_scans,
                        failed_scans=failed_scans,
                        progress=progress
                    )
                    
                except Exception as e:
                    failed_scans += 1
                    print(f"{Fore.RED}Error scanning {scan_date}: {e}{Style.RESET_ALL}")
                    import traceback
                    traceback.print_exc()
                    
                    # Update progress
                    progress = int((idx + 1) / total_scans * 100)
                    db.update_batch_scan_task(
                        task_id,
                        completed_scans=completed_scans,
                        failed_scans=failed_scans,
                        progress=progress
                    )
            
            # Mark as completed
            final_status = 'completed' if failed_scans == 0 else 'completed'  # Still completed even with some failures
            db.update_batch_scan_task(
                task_id,
                status=final_status,
                completed_at='now',
                message=f'批量扫描完成: 成功 {completed_scans}/{total_scans}, 失败 {failed_scans}/{total_scans}'
            )
            
            print(f"{Fore.GREEN}Batch scan task {task_id} completed{Style.RESET_ALL}")
            
        except Exception as e:
            print(f"{Fore.RED}Error in batch scan task {task_id}: {e}{Style.RESET_ALL}")
            import traceback
            traceback.print_exc()
            
            db.update_batch_scan_task(
                task_id,
                status='failed',
                error=str(e),
                message=f'批量扫描失败: {str(e)}'
            )
        finally:
            # Remove from running tasks
            with self._lock:
                self._running_tasks.pop(task_id, None)
    
    def _preload_kline_data(self, stock_list: List[Dict[str, Any]], start_date: str, end_date: str, 
                            task_id: str, use_db_first: bool):
        """
        预加载所有股票的K线数据到数据库，避免每次扫描都重新获取。
        
        Args:
            stock_list: 股票列表
            start_date: 开始日期
            end_date: 结束日期
            task_id: 任务ID（用于更新进度）
            use_db_first: 是否优先使用数据库
        """
        import pandas as pd
        from .data_fetcher import fetch_kline_data, _fetch_kline_data_from_api
        from .stock_database import get_stock_database
        
        db = get_stock_database()
        total_stocks = len(stock_list)
        preloaded_count = 0
        skipped_count = 0
        
        print(f"{Fore.CYAN}[BATCH_SCAN] 开始预加载 {total_stocks} 只股票的K线数据...{Style.RESET_ALL}")
        
        for idx, stock in enumerate(stock_list):
            # 检查任务是否被取消
            task = db.get_batch_scan_task(task_id)
            if task and task['status'] == 'cancelled':
                print(f"{Fore.YELLOW}[BATCH_SCAN] 任务已取消，停止预加载{Style.RESET_ALL}")
                break
            
            code = stock['code']
            name = stock['name']
            
            try:
                # 检查数据库中是否已有完整数据
                existing_df = db.get_kline_data(code, start_date, end_date)
                
                if not existing_df.empty:
                    # 检查数据完整性
                    df_dates = pd.to_datetime(existing_df['date'])
                    start_dt = pd.to_datetime(start_date)
                    end_dt = pd.to_datetime(end_date)
                    
                    min_date = df_dates.min()
                    max_date = df_dates.max()
                    
                    # 检查是否需要补充数据
                    need_earlier = (min_date - start_dt).days > 1
                    need_later = (end_dt - max_date).days > 1
                    
                    if not need_earlier and not need_later:
                        # 数据完整，跳过
                        skipped_count += 1
                        if (idx + 1) % 100 == 0:
                            print(f"{Fore.CYAN}[BATCH_SCAN] 预加载进度: {idx + 1}/{total_stocks}, 跳过: {skipped_count}, 已加载: {preloaded_count}{Style.RESET_ALL}")
                        continue
                
                # 需要获取或补充数据
                print(f"{Fore.CYAN}[BATCH_SCAN] 预加载 {code} ({name}) 的数据...{Style.RESET_ALL}")
                df = _fetch_kline_data_from_api(code, start_date, end_date, api_timeout=5.0)
                
                if not df.empty:
                    # 保存到数据库
                    db.save_kline_data(code, df)
                    preloaded_count += 1
                    if (idx + 1) % 50 == 0:
                        print(f"{Fore.GREEN}[BATCH_SCAN] 预加载进度: {idx + 1}/{total_stocks}, 已加载: {preloaded_count}, 跳过: {skipped_count}{Style.RESET_ALL}")
                else:
                    print(f"{Fore.YELLOW}[BATCH_SCAN] {code} ({name}) 无数据{Style.RESET_ALL}")
                    
            except Exception as e:
                print(f"{Fore.RED}[BATCH_SCAN] 预加载 {code} ({name}) 失败: {e}{Style.RESET_ALL}")
                continue
        
        print(f"{Fore.GREEN}[BATCH_SCAN] 预加载完成: 总计 {total_stocks}, 已加载 {preloaded_count}, 跳过 {skipped_count}{Style.RESET_ALL}")
    
    def _execute_single_scan(self, scan_date: str, scan_config_dict: Dict[str, Any], task_id: str, 
                            stock_list: Optional[List[Dict[str, Any]]] = None) -> Optional[Dict[str, Any]]:
        """
        Execute a single scan for a specific date.
        
        Args:
            scan_date: Scan date in 'YYYY-MM-DD' format
            scan_config_dict: Scan configuration dictionary
            task_id: Task ID (for progress updates)
            stock_list: Pre-prepared stock list (optional, for performance optimization)
            
        Returns:
            Scan result dictionary with 'scanned_stocks', 'total_scanned', 'success_count', or None if failed
        """
        try:
            # Create scan config
            scan_config_dict_copy = scan_config_dict.copy()
            scan_config_dict_copy['scan_date'] = scan_date  # Set scan date
            scan_config = ScanConfig(**scan_config_dict_copy)
            
            # Set database preference
            use_db_first = scan_config_dict.get('use_local_database_first', True)
            set_use_local_database_first(use_db_first)
            
            # 如果提供了预准备的股票列表，直接使用；否则重新获取
            if stock_list is None:
                # Fetch stock basics
                with BaostockConnectionManager():
                    stock_basics_df = fetch_stock_basics(use_local_database_first=use_db_first)
                    
                    # Fetch industry data
                    try:
                        industry_df = fetch_industry_data(use_local_database_first=use_db_first)
                    except Exception as e:
                        print(f"{Fore.YELLOW}Warning: Failed to fetch industry data: {e}{Style.RESET_ALL}")
                        industry_df = None
                    
                    # Prepare stock list
                    if industry_df is not None:
                        stock_list = prepare_stock_list(stock_basics_df, industry_df)
                    else:
                        import pandas as pd
                        stock_list = prepare_stock_list(stock_basics_df, pd.DataFrame())
                    
                    # Limit stock count if specified
                    if scan_config_dict.get('max_stock_count') and scan_config_dict['max_stock_count'] > 0:
                        stock_list = stock_list[:scan_config_dict['max_stock_count']]
            else:
                # 使用预准备的股票列表，但可能需要限制数量
                if scan_config_dict.get('max_stock_count') and scan_config_dict['max_stock_count'] > 0:
                    stock_list = stock_list[:scan_config_dict['max_stock_count']]
            
            # Run scan (无论是否使用预准备的股票列表，都需要执行扫描)
            scan_result = scan_stocks(
                stock_list,
                scan_config,
                update_progress=None,  # No progress callback for batch scans
                end_date=scan_date,
                return_stats=True
            )
            
            if isinstance(scan_result, tuple):
                platform_stocks, scan_stats = scan_result
                total_scanned = scan_stats.get('total_scanned', len(stock_list))
                success_count = scan_stats.get('success_count', len(platform_stocks))
            else:
                platform_stocks = scan_result
                total_scanned = len(stock_list)
                success_count = len(platform_stocks)
            
            return {
                'scanned_stocks': platform_stocks,
                'total_scanned': total_scanned,
                'success_count': success_count
            }
                
        except Exception as e:
            print(f"{Fore.RED}Error executing scan for {scan_date}: {e}{Style.RESET_ALL}")
            import traceback
            traceback.print_exc()
            return None


# Create singleton instance
batch_scan_manager = BatchScanManager()

