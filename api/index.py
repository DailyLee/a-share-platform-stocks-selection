# api/index.py
from colorama import Fore, Style
import colorama  # For colored console output
import traceback
import pandas as pd
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, RootModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
import json
import asyncio
import sys
import os

# 添加当前目录到 Python 路径，以便导入模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Import our modular components (using absolute imports)
try:
    from api.config import ScanConfig
    from api.task_manager import task_manager, TaskStatus
    from api.data_fetcher import fetch_stock_basics, fetch_industry_data, BaostockConnectionManager
    from api.platform_scanner import prepare_stock_list, scan_stocks
    from api.case_api import router as case_router
    from api.json_utils import convert_numpy_types
    from api.analyzers.fundamental_analyzer import get_stock_fundamentals
    from api.backtest_history_manager import (
        save_backtest_history, get_backtest_history_list, 
        get_backtest_history, delete_backtest_history, clear_all_backtest_history
    )
except ImportError:
    # 如果绝对导入失败，尝试相对导入（本地开发环境）
    from .config import ScanConfig
    from .task_manager import task_manager, TaskStatus
    from .data_fetcher import fetch_stock_basics, fetch_industry_data, BaostockConnectionManager
    from .platform_scanner import prepare_stock_list, scan_stocks
    from .case_api import router as case_router
    from .json_utils import convert_numpy_types
    from .analyzers.fundamental_analyzer import get_stock_fundamentals
    from .backtest_history_manager import (
        save_backtest_history, get_backtest_history_list, 
        get_backtest_history, delete_backtest_history, clear_all_backtest_history
    )

# Import default values from config to ensure consistency
try:
    from api.config import (
        DEFAULT_WINDOWS, DEFAULT_BOX_THRESHOLD, DEFAULT_MA_DIFF_THRESHOLD,
        DEFAULT_VOLATILITY_THRESHOLD, DEFAULT_VOLUME_CHANGE_THRESHOLD,
        DEFAULT_VOLUME_STABILITY_THRESHOLD, DEFAULT_VOLUME_INCREASE_THRESHOLD,
        DEFAULT_BOX_QUALITY_THRESHOLD, DEFAULT_USE_VOLUME_ANALYSIS,
        DEFAULT_USE_BOX_DETECTION, DEFAULT_USE_LOW_POSITION,
        DEFAULT_HIGH_POINT_LOOKBACK_DAYS, DEFAULT_DECLINE_PERIOD_DAYS,
        DEFAULT_DECLINE_THRESHOLD, DEFAULT_USE_RAPID_DECLINE_DETECTION,
        DEFAULT_RAPID_DECLINE_DAYS, DEFAULT_RAPID_DECLINE_THRESHOLD,
        DEFAULT_USE_BREAKTHROUGH_CONFIRMATION, DEFAULT_BREAKTHROUGH_CONFIRMATION_DAYS,
        DEFAULT_USE_BREAKTHROUGH_PREDICTION, DEFAULT_USE_WINDOW_WEIGHTS,
        DEFAULT_SORT_BY_BREAKTHROUGH
    )
except ImportError:
    # 如果绝对导入失败，尝试相对导入（本地开发环境）
    from .config import (
        DEFAULT_WINDOWS, DEFAULT_BOX_THRESHOLD, DEFAULT_MA_DIFF_THRESHOLD,
        DEFAULT_VOLATILITY_THRESHOLD, DEFAULT_VOLUME_CHANGE_THRESHOLD,
        DEFAULT_VOLUME_STABILITY_THRESHOLD, DEFAULT_VOLUME_INCREASE_THRESHOLD,
        DEFAULT_BOX_QUALITY_THRESHOLD, DEFAULT_USE_VOLUME_ANALYSIS,
        DEFAULT_USE_BOX_DETECTION, DEFAULT_USE_LOW_POSITION,
        DEFAULT_HIGH_POINT_LOOKBACK_DAYS, DEFAULT_DECLINE_PERIOD_DAYS,
        DEFAULT_DECLINE_THRESHOLD, DEFAULT_USE_RAPID_DECLINE_DETECTION,
        DEFAULT_RAPID_DECLINE_DAYS, DEFAULT_RAPID_DECLINE_THRESHOLD,
        DEFAULT_USE_BREAKTHROUGH_CONFIRMATION, DEFAULT_BREAKTHROUGH_CONFIRMATION_DAYS,
        DEFAULT_USE_BREAKTHROUGH_PREDICTION, DEFAULT_USE_WINDOW_WEIGHTS,
        DEFAULT_SORT_BY_BREAKTHROUGH
    )


# Define request body model using Pydantic


class ScanConfigRequest(BaseModel):
    """Request model for stock platform scan configuration.
    
    All default values are imported from config.py to ensure consistency
    across the entire codebase.
    """
    # Window settings - 基于平台期分析的最佳参数组合
    windows: List[int] = Field(default_factory=lambda: DEFAULT_WINDOWS.copy())

    # Price pattern thresholds - 适合识别安记食品类型的平台期
    box_threshold: float = DEFAULT_BOX_THRESHOLD
    ma_diff_threshold: float = DEFAULT_MA_DIFF_THRESHOLD
    volatility_threshold: float = DEFAULT_VOLATILITY_THRESHOLD

    # Volume analysis settings - 适合平台期
    use_volume_analysis: bool = DEFAULT_USE_VOLUME_ANALYSIS
    # Maximum volume change ratio for consolidation
    volume_change_threshold: float = DEFAULT_VOLUME_CHANGE_THRESHOLD
    # Maximum volume stability for consolidation
    volume_stability_threshold: float = DEFAULT_VOLUME_STABILITY_THRESHOLD
    # Minimum volume increase ratio for breakthrough
    volume_increase_threshold: float = DEFAULT_VOLUME_INCREASE_THRESHOLD

    # Technical indicators
    use_technical_indicators: bool = False  # Whether to use technical indicators
    # Whether to use breakthrough prediction
    use_breakthrough_prediction: bool = DEFAULT_USE_BREAKTHROUGH_PREDICTION

    # Position analysis settings
    use_low_position: bool = DEFAULT_USE_LOW_POSITION  # Whether to use low position analysis
    # Number of days to look back for finding the high point
    high_point_lookback_days: int = DEFAULT_HIGH_POINT_LOOKBACK_DAYS
    # Number of days within which the decline should have occurred
    decline_period_days: int = DEFAULT_DECLINE_PERIOD_DAYS
    # Minimum decline percentage from high to be considered at low position
    decline_threshold: float = DEFAULT_DECLINE_THRESHOLD

    # Rapid decline detection settings
    # Whether to use rapid decline detection
    use_rapid_decline_detection: bool = DEFAULT_USE_RAPID_DECLINE_DETECTION
    rapid_decline_days: int = DEFAULT_RAPID_DECLINE_DAYS  # Number of days to define a rapid decline period
    # Minimum decline percentage within rapid_decline_days to be considered rapid
    rapid_decline_threshold: float = DEFAULT_RAPID_DECLINE_THRESHOLD

    # Breakthrough confirmation settings
    # Whether to use breakthrough confirmation
    use_breakthrough_confirmation: bool = DEFAULT_USE_BREAKTHROUGH_CONFIRMATION
    # Number of days to look for confirmation
    breakthrough_confirmation_days: int = DEFAULT_BREAKTHROUGH_CONFIRMATION_DAYS

    # Box pattern detection settings
    use_box_detection: bool = DEFAULT_USE_BOX_DETECTION  # Whether to use box pattern detection
    # Minimum quality score for a valid box pattern
    box_quality_threshold: float = DEFAULT_BOX_QUALITY_THRESHOLD

    # Fundamental analysis settings
    use_fundamental_filter: bool = False  # 是否启用基本面筛选
    # 营收增长率行业百分位要求（值越小要求越严格，如0.3表示要求位于行业前30%）
    revenue_growth_percentile: float = 0.3
    # 净利润增长率行业百分位要求（值越小要求越严格，如0.3表示要求位于行业前30%）
    profit_growth_percentile: float = 0.3
    # ROE行业百分位要求（值越小要求越严格，如0.3表示要求位于行业前30%）
    roe_percentile: float = 0.3
    # 资产负债率行业百分位要求（值越大要求越严格，如0.3表示要求位于行业后30%）
    liability_percentile: float = 0.3
    # PE行业百分位要求（值越大要求越宽松，如0.7表示要求不在行业前30%最高估值）
    pe_percentile: float = 0.7
    # PB行业百分位要求（值越大要求越宽松，如0.7表示要求不在行业前30%最高估值）
    pb_percentile: float = 0.7
    # 检查连续增长的年数
    fundamental_years_to_check: int = 3

    # Window weights
    use_window_weights: bool = False  # Whether to use window weights
    window_weights: Dict[int, float] = Field(
        default_factory=dict)  # Weights for different windows

    # Sorting settings
    # Whether to sort by breakthrough & breakthrough precursor signals
    sort_by_breakthrough: bool = DEFAULT_SORT_BY_BREAKTHROUGH  # Default enabled

    # System settings
    max_workers: int = 5  # Keep concurrency reasonable for serverless
    retry_attempts: int = 2
    retry_delay: int = 1
    expected_count: int = 10  # 期望返回的股票数量，默认为10

# --- Define response models ---


class SelectionReasons(RootModel[Dict[int, str]]):
    """Maps window sizes to selection reasons (descriptive text)"""
    pass


class KlineDataPoint(BaseModel):
    """Model for a single K-line data point."""
    date: str
    open: float | None = None  # Allow None for robustness
    high: float | None = None
    low: float | None = None
    close: float | None = None
    volume: float | None = None
    turn: float | None = None
    preclose: float | None = None
    pctChg: float | None = None
    peTTM: float | None = None
    pbMRQ: float | None = None


class MarkLine(BaseModel):
    """Model for a marking line on a chart."""
    date: Optional[str] = None
    text: str
    color: str
    type: Optional[str] = None
    value: Optional[float] = None


class StockScanResult(BaseModel):
    """Model for a stock that meets platform criteria."""
    code: str
    name: str
    industry: str | None = "未知行业"
    selection_reasons: Dict[int, str]
    kline_data: List[KlineDataPoint]
    mark_lines: Optional[List[MarkLine]] = None

# --- Task-related models ---


class TaskCreationResponse(BaseModel):
    """Response model for task creation."""
    task_id: str
    message: str


class TaskStatusResponse(BaseModel):
    """Response model for task status."""
    task_id: str
    status: str
    progress: int
    message: str
    result: Optional[List[StockScanResult]] = None
    error: Optional[str] = None
    created_at: float
    updated_at: float
    completed_at: Optional[float] = None


# Initialize FastAPI app
app = FastAPI(
    title="Stock Platform Scanner API",
    description="API for scanning stocks for platform consolidation patterns",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include case management router
app.include_router(case_router, prefix="/api")

# Import for platform check endpoint
try:
    from api.data_fetcher import fetch_kline_data, build_historical_data
    from api.analyzers.combined_analyzer import analyze_stock
    from api.stock_database import get_stock_database
except ImportError:
    from .data_fetcher import fetch_kline_data, build_historical_data
    from .analyzers.combined_analyzer import analyze_stock
    from .stock_database import get_stock_database

from datetime import datetime, timedelta

# --- API Endpoints ---


@app.get("/")
async def root():
    """
    Root endpoint for health check.
    """
    return {
        "status": "ok",
        "message": "Stock Platform Scanner API is running",
        "version": "1.0.0"
    }


@app.get("/api/database/stats")
async def get_database_stats():
    """
    Get database statistics.
    """
    db = get_stock_database()
    stats = db.get_stats()
    return stats


@app.post("/api/scan/start", response_model=TaskCreationResponse)
async def start_scan(config_request: ScanConfigRequest, background_tasks: BackgroundTasks):
    """
    Start a stock platform scan as a background task.
    Returns a task ID that can be used to check the status of the scan.
    """
    # Initialize colorama for colored console output
    colorama.init()

    print(f"{Fore.CYAN}======================================{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Starting stock platform scan task{Style.RESET_ALL}")
    print(f"{Fore.CYAN}======================================{Style.RESET_ALL}")

    # Create a new task
    task_id = task_manager.create_task()

    # Convert request to config dictionary
    config_dict = config_request.model_dump()
    print(f"{Fore.YELLOW}Scan configuration:{Style.RESET_ALL}")
    for key, value in config_dict.items():
        print(f"  - {key}: {Fore.GREEN}{value}{Style.RESET_ALL}")

    # Start the scan in the background
    def run_scan_task():
        try:
            # Check if database is empty and build historical data if needed
            db = get_stock_database()
            if db.is_empty():
                task_manager.update_task(
                    task_id,
                    progress=5,
                    message="Database is empty, building historical data (this may take a while)..."
                )
                # Build historical data in background (non-blocking for first access)
                # For now, we'll just fetch stock basics and let individual queries build data
                print(f"{Fore.YELLOW}Database is empty, will build data on first access{Style.RESET_ALL}")
            
            # Fetch stock basics
            with BaostockConnectionManager():
                stock_basics_df = fetch_stock_basics()

                # Update task status
                task_manager.update_task(
                    task_id,
                    progress=10,
                    message="Fetched stock basic information"
                )

                # Fetch industry data
                try:
                    industry_df = fetch_industry_data()
                    task_manager.update_task(
                        task_id,
                        progress=20,
                        message="Fetched industry classification data"
                    )
                except Exception as e:
                    print(
                        f"{Fore.YELLOW}Warning: Failed to fetch industry data: {e}{Style.RESET_ALL}")
                    industry_df = pd.DataFrame()
                    task_manager.update_task(
                        task_id,
                        progress=20,
                        message="Warning: Failed to fetch industry data, continuing without it"
                    )

                # Prepare stock list
                stock_list = prepare_stock_list(stock_basics_df, industry_df)
                task_manager.update_task(
                    task_id,
                    progress=30,
                    message=f"Prepared list of {len(stock_list)} stocks for scanning"
                )

                # Create scan config
                scan_config = ScanConfig(**config_dict)

                # Define progress update callback
                def update_progress(progress=None, message=None):
                    if progress is not None and message is not None:
                        # Scale progress to 30-100 range (30% for preparation, 70% for scanning)
                        # When progress=100 from scan_stocks, scale to 100 (not 90)
                        if progress >= 100:
                            scaled_progress = 100  # Full completion
                            # NOTE: Don't mark as COMPLETED here - wait until result is processed
                            # This prevents result from being None when status is COMPLETED
                            task_manager.update_task(
                                task_id, 
                                progress=scaled_progress, 
                                message=message
                            )
                        else:
                            scaled_progress = 30 + int(progress * 0.7)  # Scale 0-100 to 30-100
                            task_manager.update_task(
                                task_id, progress=scaled_progress, message=message)

                # Run the scan
                try:
                    print(f"{Fore.CYAN}[INDEX] Starting scan_stocks with {len(stock_list)} stocks{Style.RESET_ALL}")
                    platform_stocks = scan_stocks(
                        stock_list, scan_config, update_progress)
                    print(f"{Fore.GREEN}[INDEX] ✓ scan_stocks completed successfully, returned {len(platform_stocks)} stocks{Style.RESET_ALL}")
                    print(f"{Fore.CYAN}[INDEX] First few stocks: {[s.get('code', 'unknown') for s in platform_stocks[:5]]}{Style.RESET_ALL}")
                except Exception as scan_error:
                    # Even if scan had errors, try to return partial results
                    print(f"{Fore.RED}[INDEX] ✗ Scan encountered error: {scan_error}{Style.RESET_ALL}")
                    import traceback
                    traceback.print_exc()
                    # Set empty list if scan completely failed
                    platform_stocks = []
                    print(f"{Fore.YELLOW}[INDEX] Continuing with empty platform_stocks list{Style.RESET_ALL}")

                # CRITICAL FIX: Process results first, then mark as COMPLETED with result
                # This ensures result is never null when status is COMPLETED
                print(f"{Fore.CYAN}[INDEX] Starting to process {len(platform_stocks)} stocks into result format{Style.RESET_ALL}")
                result_stocks = []
                result_processing_error = None
                processed_count = 0
                failed_count = 0
                
                try:
                    # Process results for API response
                    for idx, stock in enumerate(platform_stocks):
                        processed_count += 1
                        stock_code = stock.get('code', 'unknown')
                        stock_name = stock.get('name', 'unknown')
                        
                        # Convert kline_data to KlineDataPoint objects
                        kline_data = []
                        kline_data_points = stock.get('kline_data', [])
                        
                        if not kline_data_points:
                            print(f"{Fore.YELLOW}[INDEX] Warning: Stock {stock_code} ({stock_name}) has no kline_data, skipping{Style.RESET_ALL}")
                            failed_count += 1
                            continue
                        
                        for point in kline_data_points:
                            try:
                                kline_point = {
                                    'date': str(point.get('date')),
                                    'open': float(point['open']) if point.get('open') is not None else None,
                                    'high': float(point['high']) if point.get('high') is not None else None,
                                    'low': float(point['low']) if point.get('low') is not None else None,
                                    'close': float(point['close']) if point.get('close') is not None else None,
                                    'volume': float(point['volume']) if point.get('volume') is not None else None,
                                    'turn': float(point['turn']) if point.get('turn') is not None else None,
                                    'preclose': float(point['preclose']) if point.get('preclose') is not None else None,
                                    'pctChg': float(point['pctChg']) if point.get('pctChg') is not None else None,
                                    'peTTM': float(point['peTTM']) if point.get('peTTM') is not None else None,
                                    'pbMRQ': float(point['pbMRQ']) if point.get('pbMRQ') is not None else None,
                                }
                                kline_data.append(KlineDataPoint(**kline_point))
                            except Exception as e:
                                print(
                                    f"{Fore.YELLOW}[INDEX] Warning: Failed to process K-line data point for {stock_code}: {e}{Style.RESET_ALL}")
                                continue

                        # Create StockScanResult object
                        try:
                            # 处理标记线数据
                            mark_lines = []
                            if 'mark_lines' in stock:
                                for mark in stock['mark_lines']:
                                    try:
                                        mark_lines.append(MarkLine(**mark))
                                    except Exception as e:
                                        print(
                                            f"{Fore.YELLOW}[INDEX] Warning: Failed to process mark line for {stock_code}: {e}{Style.RESET_ALL}")
                                        continue

                            result_stock = StockScanResult(
                                code=stock['code'],
                                name=stock['name'],
                                industry=stock.get('industry', '未知行业'),
                                selection_reasons=stock.get(
                                    'selection_reasons', {}),
                                kline_data=kline_data,
                                mark_lines=mark_lines
                            )
                            result_stocks.append(result_stock)
                            
                            # Log progress every 10 stocks
                            if len(result_stocks) % 10 == 0:
                                print(f"{Fore.CYAN}[INDEX] Processed {len(result_stocks)}/{len(platform_stocks)} stocks successfully{Style.RESET_ALL}")
                        except Exception as e:
                            failed_count += 1
                            print(
                                f"{Fore.RED}[INDEX] Error creating StockScanResult for {stock_code} ({stock_name}): {e}{Style.RESET_ALL}")
                            import traceback
                            traceback.print_exc()
                            continue
                    
                    print(f"{Fore.GREEN}[INDEX] Result processing complete: {len(result_stocks)} successful, {failed_count} failed out of {len(platform_stocks)} total{Style.RESET_ALL}")
                except Exception as e:
                    # If result processing fails, log error but continue with empty result
                    result_processing_error = str(e)
                    print(f"{Fore.RED}Error processing results: {e}{Style.RESET_ALL}")
                    import traceback
                    traceback.print_exc()
                    # result_stocks remains empty list, which is acceptable

                # Get the current task to preserve the detailed message from scan_stocks
                current_task = task_manager.get_task(task_id)
                if current_task and current_task.message and "Processed" in current_task.message:
                    # Use the detailed message from scan_stocks (contains processed count, errors, etc.)
                    # But update it with actual result count
                    base_message = current_task.message
                    if len(result_stocks) != len(platform_stocks):
                        completion_message = f"{base_message} (Filtered to {len(result_stocks)} stocks for display)"
                    else:
                        completion_message = base_message
                else:
                    # Fallback to basic message if detailed message not available
                    if len(result_stocks) == 0 and len(platform_stocks) == 0:
                        completion_message = "Scan completed but no platform stocks found. Some stocks may have been skipped due to timeout."
                    else:
                        completion_message = f"Scan completed. Found {len(platform_stocks)} platform stocks, returning {len(result_stocks)} stocks."
                
                # Add error info to message if result processing had errors
                if result_processing_error:
                    completion_message += f" (Warning: Some results may be incomplete due to processing error: {result_processing_error})"
                
                # Mark as COMPLETED with result (never null - at least empty list)
                # This ensures status=COMPLETED always has a valid result
                result_data = [stock.model_dump() for stock in result_stocks]  # Always a list, never None
                print(f"{Fore.CYAN}[INDEX] Preparing to update task with {len(result_data)} results (type: {type(result_data)}){Style.RESET_ALL}")
                task_manager.update_task(
                    task_id,
                    status=TaskStatus.COMPLETED,
                    progress=100,
                    message=completion_message,
                    result=result_data  # Always a list, never None
                )
                # Verify the result was set correctly
                verify_task = task_manager.get_task(task_id)
                if verify_task:
                    print(f"{Fore.GREEN}Task {task_id} marked as COMPLETED with {len(result_data)} results. Verified: result is {type(verify_task.result)} (None: {verify_task.result is None}, length: {len(verify_task.result) if verify_task.result else 'N/A'}){Style.RESET_ALL}")
                else:
                    print(f"{Fore.RED}ERROR: Task {task_id} not found after update!{Style.RESET_ALL}")

        except Exception as e:
            print(f"{Fore.RED}Error in scan task: {e}{Style.RESET_ALL}")
            traceback.print_exc()
            task_manager.update_task(
                task_id,
                status=TaskStatus.FAILED,
                error=f"Scan failed: {str(e)}\n{traceback.format_exc()}"
            )

    # Start the task in the background
    background_tasks.add_task(run_scan_task)

    # Return task ID
    return TaskCreationResponse(
        task_id=task_id,
        message="Scan started successfully. Use the task ID to check status."
    )


@app.get("/api/scan/status/{task_id}", response_model=TaskStatusResponse)
async def get_scan_status(task_id: str):
    """
    Get the status of a scan task.
    """
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(
            status_code=404, detail=f"Task with ID {task_id} not found")

    return task.to_dict()

# Legacy endpoint for backward compatibility


@app.post("/api/scan", response_model=List[StockScanResult])
async def run_scan(config_request: ScanConfigRequest):
    """
    Legacy API endpoint for backward compatibility.
    This endpoint starts a scan and waits for it to complete.
    For long-running scans, use the /api/scan/start endpoint instead.
    """
    # Initialize colorama for colored console output
    colorama.init()

    print(f"{Fore.CYAN}======================================{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Legacy scan endpoint called{Style.RESET_ALL}")
    print(f"{Fore.CYAN}======================================{Style.RESET_ALL}")

    # Convert request to config dictionary
    config_dict = config_request.model_dump()

    # Create scan config
    scan_config = ScanConfig(**config_dict)

    # Fetch stock basics
    with BaostockConnectionManager():
        stock_basics_df = fetch_stock_basics()

        # Fetch industry data
        try:
            industry_df = fetch_industry_data()
        except Exception as e:
            print(
                f"{Fore.YELLOW}Warning: Failed to fetch industry data: {e}{Style.RESET_ALL}")
            industry_df = pd.DataFrame()

        # Prepare stock list
        stock_list = prepare_stock_list(stock_basics_df, industry_df)

        # Run the scan
        platform_stocks = scan_stocks(stock_list, scan_config)

    # Process results for API response
    result_stocks = []
    for stock in platform_stocks:
        # Convert kline_data to KlineDataPoint objects
        kline_data = []
        for point in stock.get('kline_data', []):
            try:
                kline_point = {
                    'date': str(point.get('date')),
                    'open': float(point['open']) if point.get('open') is not None else None,
                    'high': float(point['high']) if point.get('high') is not None else None,
                    'low': float(point['low']) if point.get('low') is not None else None,
                    'close': float(point['close']) if point.get('close') is not None else None,
                    'volume': float(point['volume']) if point.get('volume') is not None else None,
                    'turn': float(point['turn']) if point.get('turn') is not None else None,
                    'preclose': float(point['preclose']) if point.get('preclose') is not None else None,
                    'pctChg': float(point['pctChg']) if point.get('pctChg') is not None else None,
                    'peTTM': float(point['peTTM']) if point.get('peTTM') is not None else None,
                    'pbMRQ': float(point['pbMRQ']) if point.get('pbMRQ') is not None else None,
                }
                kline_data.append(KlineDataPoint(**kline_point))
            except Exception as e:
                print(
                    f"{Fore.YELLOW}Warning: Failed to process K-line data point: {e}{Style.RESET_ALL}")
                continue

        # Create StockScanResult object
        try:
            # 处理标记线数据
            mark_lines = []
            if 'mark_lines' in stock:
                for mark in stock['mark_lines']:
                    try:
                        mark_lines.append(MarkLine(**mark))
                    except Exception as e:
                        print(
                            f"{Fore.YELLOW}Warning: Failed to process mark line: {e}{Style.RESET_ALL}")
                        continue

            result_stock = StockScanResult(
                code=stock['code'],
                name=stock['name'],
                industry=stock.get('industry', '未知行业'),
                selection_reasons=stock.get('selection_reasons', {}),
                kline_data=kline_data,
                mark_lines=mark_lines
            )
            result_stocks.append(result_stock)
        except Exception as e:
            print(f"{Fore.RED}Error creating StockScanResult: {e}{Style.RESET_ALL}")
            continue

    return result_stocks

# 添加测试API端点


@app.post("/api/scan/test", response_model=List[StockScanResult])
async def test_scan(config_request: ScanConfigRequest):
    """
    Test API endpoint that returns sample data with marking lines.
    This is useful for testing the frontend without running a full scan.
    """
    # 创建一个模拟的股票数据
    from datetime import datetime, timedelta
    import numpy as np

    # 生成日期序列
    end_date = datetime.now()
    dates = [(end_date - timedelta(days=i)).strftime('%Y-%m-%d')
             for i in range(200)]
    dates.reverse()  # 按时间顺序排列

    # 生成价格数据
    high_price = 30.0
    prices = []

    # 上涨阶段
    for i in range(50):
        prices.append(20 + i * 0.2)

    # 高点和下跌阶段
    for i in range(30):
        prices.append(high_price - i * 0.3)

    # 平台期
    platform_price = 20.0
    for i in range(100):
        # 在平台价格附近波动
        prices.append(platform_price + np.random.normal(0, 0.5))

    # 突破
    for i in range(20):
        prices.append(platform_price + 2 + i * 0.1)

    # 创建K线数据
    kline_data = []
    for i, date in enumerate(dates):
        if i < len(prices):
            price = prices[i]
            kline_point = {
                'date': date,
                'open': price - 0.2,
                'high': price + 0.5,
                'low': price - 0.5,
                'close': price + 0.2,
                'volume': 10000 + np.random.randint(0, 5000),
                'turn': 1.5,
                'preclose': price if i == 0 else prices[i-1],
                'pctChg': 0.5,
                'peTTM': 15.0,
                'pbMRQ': 2.0
            }
            kline_data.append(KlineDataPoint(**kline_point))

    # 创建标记线数据
    mark_lines = [
        MarkLine(date=dates[49], text="高点", color="#ec0000"),
        MarkLine(date=dates[50], text="开始下跌", color="#ec0000"),
        MarkLine(date=dates[80], text="平台期开始", color="#3b82f6"),
        MarkLine(date=dates[180], text="突破", color="#10b981")
    ]

    # 创建支撑位和阻力位
    support_level = platform_price - 0.5
    resistance_level = platform_price + 0.5

    mark_lines.append(MarkLine(type="horizontal",
                      value=support_level, text="支撑位", color="#10b981"))
    mark_lines.append(MarkLine(type="horizontal",
                      value=resistance_level, text="阻力位", color="#ec0000"))

    # 创建结果对象
    result_stock = StockScanResult(
        code="sh.000001",
        name="测试股票",
        industry="测试行业",
        selection_reasons={60: "60天窗口期内价格波动小于50%，均线高度粘合，波动率低，成交量稳定"},
        kline_data=kline_data,
        mark_lines=mark_lines
    )

    return [result_stock]

# Platform check endpoint
class PlatformCheckRequest(BaseModel):
    """Request model for single stock platform check."""
    code: str = Field(..., description="Stock code (e.g., 'sh.600000')")


class PlatformCheckResponse(BaseModel):
    """Response model for platform check."""
    code: str
    name: str
    is_platform: bool
    has_breakthrough_signal: bool
    has_breakthrough_confirmation: bool
    platform_windows: List[int]
    explanation: Dict[str, Any]
    kline_data: List[KlineDataPoint]
    mark_lines: Optional[List[MarkLine]] = None
    fundamental_analysis: Optional[Dict[str, Any]] = None


@app.post("/api/platform/check", response_model=PlatformCheckResponse)
async def check_platform(request: PlatformCheckRequest):
    """
    Check if a single stock is in a platform period, has breakthrough signals, and confirmed breakthrough.
    Returns detailed analysis with explanations.
    """
    try:
        code = request.code.strip()
        
        # Validate stock code format
        if not code or '.' not in code:
            raise HTTPException(
                status_code=400,
                detail="Invalid stock code format. Expected format: 'sh.600000' or 'sz.000001'"
            )
        
        # Fetch stock basic information to get name
        with BaostockConnectionManager():
            stock_basics_df = fetch_stock_basics()
            stock_info = stock_basics_df[stock_basics_df['code'] == code]
            
            if stock_info.empty:
                raise HTTPException(
                    status_code=404,
                    detail=f"Stock code {code} not found"
                )
            
            # Support both 'code_name' (from API) and 'name' (from database)
            stock_name = stock_info.iloc[0].get('code_name') or stock_info.iloc[0].get('name', '')
            
            # Calculate date range (use comprehensive windows for single stock check)
            # Include common windows: 30, 60, 90, 80, 100, 120 to match scan results
            comprehensive_windows = sorted(list(set([30, 60, 90, 80, 100, 120])))
            max_window = max(comprehensive_windows)
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=max_window * 2)).strftime('%Y-%m-%d')
            
            # Fetch K-line data
            df = fetch_kline_data(code, start_date, end_date)
            
            if df.empty:
                raise HTTPException(
                    status_code=404,
                    detail=f"No K-line data available for {code}"
                )
            
            # Prepare analysis config (use comprehensive windows for single stock check)
            analysis_config = {
                'windows': comprehensive_windows,
                'box_threshold': DEFAULT_BOX_THRESHOLD,
                'ma_diff_threshold': DEFAULT_MA_DIFF_THRESHOLD,
                'volatility_threshold': DEFAULT_VOLATILITY_THRESHOLD,
                'volume_change_threshold': DEFAULT_VOLUME_CHANGE_THRESHOLD,
                'volume_stability_threshold': DEFAULT_VOLUME_STABILITY_THRESHOLD,
                'volume_increase_threshold': DEFAULT_VOLUME_INCREASE_THRESHOLD,
                'use_volume_analysis': DEFAULT_USE_VOLUME_ANALYSIS,
                'use_breakthrough_prediction': True,  # Always enable for single stock check
                'use_breakthrough_confirmation': True,  # Always enable for single stock check
                'breakthrough_confirmation_days': DEFAULT_BREAKTHROUGH_CONFIRMATION_DAYS,
                'use_low_position': DEFAULT_USE_LOW_POSITION,
                'high_point_lookback_days': DEFAULT_HIGH_POINT_LOOKBACK_DAYS,
                'decline_period_days': DEFAULT_DECLINE_PERIOD_DAYS,
                'decline_threshold': DEFAULT_DECLINE_THRESHOLD,
                'use_rapid_decline_detection': DEFAULT_USE_RAPID_DECLINE_DETECTION,
                'rapid_decline_days': DEFAULT_RAPID_DECLINE_DAYS,
                'rapid_decline_threshold': DEFAULT_RAPID_DECLINE_THRESHOLD,
                'use_box_detection': DEFAULT_USE_BOX_DETECTION,
                'box_quality_threshold': DEFAULT_BOX_QUALITY_THRESHOLD,
                'use_window_weights': False,  # Not needed for single stock check
            }
            
            # Perform comprehensive analysis
            analysis_result = analyze_stock(df, **analysis_config)
            
            # Extract results and convert NumPy types to Python native types
            is_platform = convert_numpy_types(analysis_result.get('is_platform', False))
            platform_windows = convert_numpy_types(analysis_result.get('platform_windows', []))
            
            # Check for breakthrough signals
            breakthrough_prediction = convert_numpy_types(analysis_result.get('breakthrough_prediction', {}))
            has_breakthrough_signal = convert_numpy_types(breakthrough_prediction.get('has_breakthrough_signal', False))
            
            # Check for breakthrough confirmation
            has_breakthrough_confirmation = convert_numpy_types(analysis_result.get('has_breakthrough_confirmation', False))
            has_breakthrough = convert_numpy_types(analysis_result.get('has_breakthrough', False))
            
            # Build explanation (convert NumPy types in nested structures)
            explanation = convert_numpy_types({
                'platform_status': '是平台期' if is_platform else '不是平台期',
                'platform_windows': platform_windows,
                'breakthrough_signal': {
                    'has_signal': has_breakthrough_signal,
                    'signal_count': breakthrough_prediction.get('signal_count', 0),
                    'signals': breakthrough_prediction.get('signals', {}),
                    'details': breakthrough_prediction.get('details', {})
                },
                'breakthrough_confirmation': {
                    'has_breakthrough': has_breakthrough,
                    'has_confirmation': has_breakthrough_confirmation,
                    'details': analysis_result.get('breakthrough_confirmation_details', {})
                },
                'analysis_details': {
                    'windows_checked': analysis_result.get('windows_checked', []),
                    'details': analysis_result.get('details', {}),
                    'selection_reasons': analysis_result.get('selection_reasons', {})
                }
            })
            
            # Convert K-line data to response format
            kline_data = []
            for _, row in df.iterrows():
                kline_point = {
                    'date': str(row.get('date', '')),
                    'open': float(row['open']) if pd.notna(row.get('open')) else None,
                    'high': float(row['high']) if pd.notna(row.get('high')) else None,
                    'low': float(row['low']) if pd.notna(row.get('low')) else None,
                    'close': float(row['close']) if pd.notna(row.get('close')) else None,
                    'volume': float(row['volume']) if pd.notna(row.get('volume')) else None,
                    'turn': float(row['turn']) if pd.notna(row.get('turn')) else None,
                    'preclose': float(row['preclose']) if pd.notna(row.get('preclose')) else None,
                    'pctChg': float(row['pctChg']) if pd.notna(row.get('pctChg')) else None,
                    'peTTM': float(row['peTTM']) if pd.notna(row.get('peTTM')) else None,
                    'pbMRQ': float(row['pbMRQ']) if pd.notna(row.get('pbMRQ')) else None,
                }
                kline_data.append(KlineDataPoint(**kline_point))
            
            # Get mark lines from analysis result
            mark_lines = []
            if 'mark_lines' in analysis_result:
                for mark in analysis_result['mark_lines']:
                    try:
                        mark_lines.append(MarkLine(**mark))
                    except Exception as e:
                        print(f"Warning: Failed to process mark line: {e}")
                        continue
            
            # Get fundamental analysis data
            fundamental_analysis = None
            try:
                fundamental_data = get_stock_fundamentals(code, years_to_check=3)
                if fundamental_data:
                    # Convert NumPy types and format the data
                    fundamental_analysis = convert_numpy_types({
                        'avg_revenue_growth': fundamental_data.get('avg_revenue_growth'),
                        'revenue_growth_consistent': fundamental_data.get('revenue_growth_consistent', False),
                        'avg_profit_growth': fundamental_data.get('avg_profit_growth'),
                        'profit_growth_consistent': fundamental_data.get('profit_growth_consistent', False),
                        'avg_roe': fundamental_data.get('avg_roe'),
                        'roe_consistent': fundamental_data.get('roe_consistent', False),
                        'avg_liability_ratio': fundamental_data.get('avg_liability_ratio'),
                        'liability_ratio_consistent': fundamental_data.get('liability_ratio_consistent', False),
                        'pe_ttm': fundamental_data.get('pe_ttm'),
                        'pb_mrq': fundamental_data.get('pb_mrq')
                    })
            except Exception as e:
                print(f"Warning: Failed to get fundamental analysis for {code}: {e}")
                fundamental_analysis = None
            
            return PlatformCheckResponse(
                code=code,
                name=stock_name,
                is_platform=is_platform,
                has_breakthrough_signal=has_breakthrough_signal,
                has_breakthrough_confirmation=has_breakthrough_confirmation,
                platform_windows=platform_windows,
                explanation=explanation,
                kline_data=kline_data,
                mark_lines=mark_lines if mark_lines else None,
                fundamental_analysis=fundamental_analysis
            )
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error checking platform for {request.code}: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing stock: {str(e)}"
        )

# 注意：我们已经有了根端点 (/), 不需要额外的 /api 端点

# =================================
# Backtest API
# =================================

class BacktestRequest(BaseModel):
    """Request model for backtest"""
    backtest_date: str  # 回测日（截止日），格式：YYYY-MM-DD
    stat_date: str  # 统计日，格式：YYYY-MM-DD
    buy_strategy: str = "fixed_amount"  # 买入策略
    use_stop_loss: bool = True  # 使用止损
    use_take_profit: bool = True  # 使用止盈
    stop_loss_percent: float = -3.0  # 止损百分比
    take_profit_percent: float = 10.0  # 止盈百分比
    scan_config: Dict[str, Any]  # 扫描配置


class BuyRecord(BaseModel):
    """买入记录"""
    code: str
    name: str
    buyDate: str
    buyPrice: float
    quantity: int
    buyAmount: float
    selection_reasons: Optional[Dict[int, str]] = None  # 筛选理由


class SellRecord(BaseModel):
    """卖出记录"""
    code: str
    name: str
    buyDate: str
    sellDate: str
    buyPrice: float
    sellPrice: float
    returnRate: float
    profit: float
    sellReason: str  # 止损、止盈、统计日卖出


class StockDetail(BaseModel):
    """每只股票详细数据"""
    code: str
    name: str
    buyAmount: float
    sellAmount: float
    profit: float
    returnRate: float
    status: str  # 已卖出、未卖出


class BacktestSummary(BaseModel):
    """回测摘要"""
    totalStocks: int
    totalInvestment: float
    totalProfit: float
    totalReturnRate: float
    profitableStocks: int
    lossStocks: int


class BacktestResponse(BaseModel):
    """回测响应"""
    summary: BacktestSummary
    buyRecords: List[BuyRecord]
    sellRecords: List[SellRecord]
    stockDetails: List[StockDetail]


def run_backtest_with_progress(request: BacktestRequest, progress_callback=None):
    """
    执行回测的内部函数，支持进度回调
    """
    from datetime import datetime, timedelta
    import time
    
    # 验证日期格式
    try:
        backtest_date = datetime.strptime(request.backtest_date, '%Y-%m-%d')
        stat_date = datetime.strptime(request.stat_date, '%Y-%m-%d')
    except ValueError:
        raise HTTPException(status_code=400, detail="日期格式错误，应为 YYYY-MM-DD")
    
    if backtest_date >= stat_date:
        raise HTTPException(status_code=400, detail="回测日必须早于统计日")
    
    if progress_callback:
        progress_callback(5, "开始回测，准备扫描配置...")
    
    # 1. 使用扫描配置执行扫描（以回测日为截止日）
    print(f"{Fore.CYAN}开始回测: 回测日={request.backtest_date}, 统计日={request.stat_date}{Style.RESET_ALL}")
    
    # 准备扫描配置
    scan_config_dict = request.scan_config.copy()
    
    # 创建ScanConfig对象
    scan_config = ScanConfig(**scan_config_dict)
    
    if progress_callback:
        progress_callback(10, "正在获取股票基本信息...")
    
    # 执行扫描（使用回测日作为截止日）
    with BaostockConnectionManager():
        # 获取股票基本信息
        stock_basics_df = fetch_stock_basics()
        
        if progress_callback:
            progress_callback(15, "正在获取行业数据...")
        
        # 获取行业数据
        try:
            industry_df = fetch_industry_data()
        except Exception as e:
            print(f"{Fore.YELLOW}Warning: Failed to fetch industry data: {e}{Style.RESET_ALL}")
            industry_df = pd.DataFrame()
        
        if progress_callback:
            progress_callback(20, "正在准备股票列表...")
        
        # 准备股票列表
        stock_list = prepare_stock_list(stock_basics_df, industry_df)
        
        if progress_callback:
            progress_callback(25, f"开始扫描 {len(stock_list)} 只股票，查找符合条件的平台期股票...")
        
        # 执行扫描（使用回测日作为截止日）
        end_date = backtest_date.strftime('%Y-%m-%d')
        
        # 定义进度更新回调
        def scan_progress_update(progress, message):
            if progress_callback:
                # 扫描阶段占30-60%
                scaled_progress = 30 + int(progress * 0.3)
                progress_callback(scaled_progress, message)
        
        scanned_stocks = scan_stocks(stock_list, scan_config, update_progress=scan_progress_update, end_date=end_date)
        
        print(f"{Fore.GREEN}扫描完成，找到 {len(scanned_stocks)} 只符合条件的股票{Style.RESET_ALL}")
    
    if progress_callback:
        progress_callback(60, f"扫描完成，找到 {len(scanned_stocks)} 只符合条件的股票，开始执行回测...")
    
    # 2. 对于每只股票，执行买入和卖出逻辑
    buy_records = []
    sell_records = []
    stock_details = []
    
    buy_amount_per_stock = 10000  # 每只股票买入1万元
    
    total_stocks = len(scanned_stocks)
    for idx, stock in enumerate(scanned_stocks):
        code = stock['code']
        name = stock.get('name', code)
        
        if progress_callback:
            progress = 60 + int((idx + 1) / total_stocks * 35)
            progress_callback(progress, f"正在处理股票 {idx + 1}/{total_stocks}: {name} ({code})...")
        
        # 获取从回测日到统计日的历史数据
        start_date = request.backtest_date
        end_date = request.stat_date
        
        with BaostockConnectionManager():
            kline_df = fetch_kline_data(code, start_date, end_date)
        
        if kline_df.empty:
            print(f"{Fore.YELLOW}Warning: {code} 在 {start_date} 到 {end_date} 期间无数据，跳过{Style.RESET_ALL}")
            continue
        
        # 确保数据按日期排序
        kline_df = kline_df.sort_values('date')
        kline_df = kline_df.reset_index(drop=True)
        
        # 找到回测日的数据（买入日）
        # 确保日期格式一致（转换为字符串进行比较）
        kline_df['date_str'] = kline_df['date'].astype(str)
        buy_day_data = kline_df[kline_df['date_str'] == request.backtest_date]
        if buy_day_data.empty:
            # 如果回测日没有数据，使用第一个交易日
            if len(kline_df) > 0:
                buy_day_data = kline_df.iloc[[0]]
            else:
                continue
        
        buy_price = float(buy_day_data.iloc[0]['open'])
        buy_date = str(buy_day_data.iloc[0]['date'])
        quantity = int(buy_amount_per_stock / buy_price / 100) * 100  # 按手（100股）买入
        actual_buy_amount = quantity * buy_price
        
        # 记录买入
        buy_records.append({
            'code': code,
            'name': name,
            'buyDate': buy_date,
            'buyPrice': buy_price,
            'quantity': quantity,
            'buyAmount': actual_buy_amount,
            'selection_reasons': stock.get('selection_reasons', {})  # 包含筛选理由
        })
        
        # 从买入日的下一天开始检查卖出条件
        buy_day_index = buy_day_data.index[0]
        sell_price = None
        sell_date = None
        sell_reason = None
        
        # 检查从买入日到统计日的数据
        for i in range(buy_day_index + 1, len(kline_df)):
            day_data = kline_df.iloc[i]
            current_date = str(day_data['date'])
            current_close = float(day_data['close'])
            current_low = float(day_data['low'])
            current_high = float(day_data['high'])
            
            # 计算收益率
            return_rate = ((current_close - buy_price) / buy_price) * 100
            
            # 检查止损（使用最低价）
            if request.use_stop_loss:
                low_return_rate = ((current_low - buy_price) / buy_price) * 100
                if low_return_rate <= request.stop_loss_percent:
                    sell_price = buy_price * (1 + request.stop_loss_percent / 100)
                    sell_date = current_date
                    sell_reason = '止损'
                    break
            
            # 检查止盈（使用最高价）
            if request.use_take_profit:
                high_return_rate = ((current_high - buy_price) / buy_price) * 100
                if high_return_rate >= request.take_profit_percent:
                    sell_price = buy_price * (1 + request.take_profit_percent / 100)
                    sell_date = current_date
                    sell_reason = '止盈'
                    break
            
            # 如果到了统计日，使用收盘价卖出（确保日期格式一致）
            if current_date == request.stat_date or str(day_data.get('date_str', current_date)) == request.stat_date:
                sell_price = current_close
                sell_date = current_date
                sell_reason = '统计日卖出'
                break
        
        # 如果没有卖出（理论上不应该发生，因为统计日一定会卖出）
        if sell_price is None:
            # 使用最后一天的收盘价
            if len(kline_df) > 0:
                last_day = kline_df.iloc[-1]
                sell_price = float(last_day['close'])
                sell_date = str(last_day['date'])
                sell_reason = '统计日卖出'
            else:
                # 如果没有数据，使用买入价（未卖出）
                sell_price = buy_price
                sell_date = buy_date
                sell_reason = '未卖出'
        
        # 计算盈亏
        sell_amount = quantity * sell_price
        profit = sell_amount - actual_buy_amount
        final_return_rate = ((sell_price - buy_price) / buy_price) * 100
        
        # 记录卖出
        sell_records.append({
            'code': code,
            'name': name,
            'buyDate': buy_date,
            'sellDate': sell_date,
            'buyPrice': buy_price,
            'sellPrice': sell_price,
            'returnRate': final_return_rate,
            'profit': profit,
            'sellReason': sell_reason
        })
        
        # 记录股票详情
        stock_details.append({
            'code': code,
            'name': name,
            'buyAmount': actual_buy_amount,
            'sellAmount': sell_amount,
            'profit': profit,
            'returnRate': final_return_rate,
            'status': '已卖出' if sell_reason != '未卖出' else '未卖出'
        })
    
    if progress_callback:
        progress_callback(98, "正在计算回测结果...")
    
    # 3. 计算总摘要
    total_stocks = len(buy_records)
    total_investment = sum(record['buyAmount'] for record in buy_records)
    total_profit = sum(detail['profit'] for detail in stock_details)
    total_return_rate = (total_profit / total_investment * 100) if total_investment > 0 else 0
    profitable_stocks = sum(1 for detail in stock_details if detail['profit'] > 0)
    loss_stocks = sum(1 for detail in stock_details if detail['profit'] < 0)
    
    if progress_callback:
        progress_callback(100, "回测完成！")
    
    # 构建响应
    response = BacktestResponse(
        summary=BacktestSummary(
            totalStocks=total_stocks,
            totalInvestment=total_investment,
            totalProfit=total_profit,
            totalReturnRate=total_return_rate,
            profitableStocks=profitable_stocks,
            lossStocks=loss_stocks
        ),
        buyRecords=[BuyRecord(**record) for record in buy_records],
        sellRecords=[SellRecord(**record) for record in sell_records],
        stockDetails=[StockDetail(**detail) for detail in stock_details]
    )
    
    print(f"{Fore.GREEN}回测完成: 总股票数={total_stocks}, 总投入={total_investment:.2f}, 总收益={total_profit:.2f}, 总收益率={total_return_rate:.2f}%{Style.RESET_ALL}")
    
    return response


@app.post("/api/backtest", response_model=BacktestResponse)
async def run_backtest(request: BacktestRequest):
    """
    执行回测（同步版本，不支持进度推送）
    """
    try:
        return run_backtest_with_progress(request, progress_callback=None)
    except HTTPException:
        raise
    except Exception as e:
        print(f"{Fore.RED}回测失败: {e}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"回测执行失败: {str(e)}"
        )


@app.post("/api/backtest/stream")
async def run_backtest_stream(request: BacktestRequest):
    """
    执行回测（流式版本，支持进度推送）
    使用 Server-Sent Events (SSE) 推送进度更新
    """
    import queue
    import concurrent.futures
    
    # 使用队列来传递进度更新
    progress_queue = queue.Queue()
    result_container = {'result': None, 'error': None}
    
    def progress_callback(progress, message):
        # 将进度更新放入队列
        progress_queue.put({
            'type': 'progress',
            'progress': progress,
            'message': message
        })
    
    def run_backtest_task():
        try:
            result = run_backtest_with_progress(request, progress_callback=progress_callback)
            result_container['result'] = result
            progress_queue.put({'type': 'done'})  # 标记完成
        except Exception as e:
            result_container['error'] = str(e)
            progress_queue.put({'type': 'done'})  # 标记完成
    
    async def generate():
        try:
            # 在线程池中启动回测任务
            loop = asyncio.get_event_loop()
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(run_backtest_task)
                
                # 持续发送进度更新
                while True:
                    try:
                        # 从队列获取进度更新（非阻塞）
                        try:
                            update = progress_queue.get_nowait()
                            if update['type'] == 'done':
                                break
                            
                            # 发送进度更新
                            yield f"data: {json.dumps(update, ensure_ascii=False)}\n\n"
                        except queue.Empty:
                            # 队列为空，检查任务是否完成
                            if future.done():
                                break
                            await asyncio.sleep(0.1)
                    except Exception as e:
                        print(f"Error in progress loop: {e}")
                        break
                
                # 等待任务完成
                future.result()
            
            # 发送最终结果
            if result_container['error']:
                error_data = {
                    'type': 'error',
                    'message': result_container['error']
                }
                yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
            else:
                result = result_container['result']
                result_dict = result.model_dump()
                
                # 自动保存回测历史
                try:
                    config_dict = {
                        'backtest_date': request.backtest_date,
                        'stat_date': request.stat_date,
                        'buy_strategy': request.buy_strategy,
                        'use_stop_loss': request.use_stop_loss,
                        'use_take_profit': request.use_take_profit,
                        'stop_loss_percent': request.stop_loss_percent,
                        'take_profit_percent': request.take_profit_percent,
                        'scan_config': request.scan_config
                    }
                    history_id = save_backtest_history(config_dict, result_dict)
                    result_dict['historyId'] = history_id  # 将历史ID添加到结果中
                except Exception as e:
                    print(f"Warning: Failed to save backtest history: {e}")
                    # 不阻止返回结果，只是记录警告
                
                result_data = {
                    'type': 'result',
                    'data': result_dict
                }
                yield f"data: {json.dumps(result_data, ensure_ascii=False, default=str)}\n\n"
                
        except Exception as e:
            error_data = {
                'type': 'error',
                'message': str(e)
            }
            yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


# =================================
# Backtest History API
# =================================

@app.get("/api/backtest/history")
async def get_backtest_history_list_endpoint():
    """
    获取回测历史记录列表
    """
    try:
        records = get_backtest_history_list()
        return {
            "success": True,
            "data": records,
            "count": len(records)
        }
    except Exception as e:
        print(f"{Fore.RED}获取回测历史列表失败: {e}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"获取回测历史列表失败: {str(e)}"
        )


@app.get("/api/backtest/history/{history_id}")
async def get_backtest_history_endpoint(history_id: str):
    """
    获取单个回测历史记录详情
    """
    try:
        record = get_backtest_history(history_id)
        if record is None:
            raise HTTPException(
                status_code=404,
                detail=f"回测历史记录不存在: {history_id}"
            )
        return {
            "success": True,
            "data": record
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"{Fore.RED}获取回测历史记录失败: {e}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"获取回测历史记录失败: {str(e)}"
        )


@app.delete("/api/backtest/history/{history_id}")
async def delete_backtest_history_endpoint(history_id: str):
    """
    删除单个回测历史记录
    """
    try:
        success = delete_backtest_history(history_id)
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"回测历史记录不存在: {history_id}"
            )
        return {
            "success": True,
            "message": "回测历史记录已删除"
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"{Fore.RED}删除回测历史记录失败: {e}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"删除回测历史记录失败: {str(e)}"
        )


@app.delete("/api/backtest/history")
async def clear_all_backtest_history_endpoint():
    """
    清空所有回测历史记录
    """
    try:
        count = clear_all_backtest_history()
        return {
            "success": True,
            "message": f"已清空 {count} 条回测历史记录",
            "count": count
        }
    except Exception as e:
        print(f"{Fore.RED}清空回测历史记录失败: {e}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"清空回测历史记录失败: {str(e)}"
        )
