# api/index.py
from colorama import Fore, Style
import colorama  # For colored console output
import traceback
import pandas as pd
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, RootModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse, JSONResponse
import json
import asyncio
import sys
import os
import hashlib

# 添加当前目录到 Python 路径，以便导入模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Import our modular components (using absolute imports)
try:
    from api.config import ScanConfig
    from api.task_manager import task_manager, TaskStatus
    from api.data_fetcher import fetch_stock_basics, fetch_industry_data, BaostockConnectionManager, set_use_local_database_first
    from api.platform_scanner import prepare_stock_list, scan_stocks
    from api.case_api import router as case_router
    from api.json_utils import convert_numpy_types, sanitize_float_for_json
    from api.analyzers.fundamental_analyzer import get_stock_fundamentals
    from api.backtest_history_manager import (
        save_backtest_history, get_backtest_history_list, 
        get_backtest_history, delete_backtest_history, clear_all_backtest_history,
        check_backtest_exists, delete_backtest_history_by_date
    )
    from api.scan_history_manager import (
        get_scan_history_list, get_scan_history,
        delete_scan_history, clear_all_scan_history
    )
    try:
        from api.batch_scan_manager import batch_scan_manager
    except ImportError:
        batch_scan_manager = None
except ImportError:
    # 如果绝对导入失败，尝试相对导入（本地开发环境）
    from .config import ScanConfig
    from .task_manager import task_manager, TaskStatus
    from .data_fetcher import fetch_stock_basics, fetch_industry_data, BaostockConnectionManager, set_use_local_database_first
    from .platform_scanner import prepare_stock_list, scan_stocks
    from .case_api import router as case_router
    from .json_utils import convert_numpy_types, sanitize_float_for_json
    from .analyzers.fundamental_analyzer import get_stock_fundamentals
    from .backtest_history_manager import (
        save_backtest_history, get_backtest_history_list, 
        get_backtest_history, delete_backtest_history, clear_all_backtest_history,
        check_backtest_exists, delete_backtest_history_by_date
    )
    from .scan_history_manager import (
        get_scan_history_list, get_scan_history,
        delete_scan_history, clear_all_scan_history
    )
    try:
        from .batch_scan_manager import batch_scan_manager
    except ImportError:
        batch_scan_manager = None

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
        DEFAULT_USE_BREAKTHROUGH_PREDICTION, DEFAULT_USE_WINDOW_WEIGHTS
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
        DEFAULT_USE_BREAKTHROUGH_PREDICTION, DEFAULT_USE_WINDOW_WEIGHTS
    )


# Define request body model using Pydantic


class ScanConfigRequest(BaseModel):
    """Request model for stock platform scan configuration.
    
    All default values are imported from config.py to ensure consistency
    across the entire codebase.
    """
    # Scan date - 扫描日期，默认为今天
    scan_date: Optional[str] = Field(default=None, description="扫描日期，格式：YYYY-MM-DD，默认为今天")
    
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

    # System settings
    max_workers: int = 5  # Keep concurrency reasonable for serverless
    retry_attempts: int = 2
    retry_delay: int = 1
    expected_count: int = 10  # 期望返回的股票数量，默认为10
    max_stock_count: Optional[int] = None  # 扫描股票数量限制，None或0表示全量扫描
    
    # Cache settings
    use_scan_cache: bool = True  # 是否使用扫描结果缓存，默认为开启
    
    # Data source settings
    use_local_database_first: bool = True  # 优先使用本地数据库数据，默认为开启

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


def generate_scan_cache_key(scan_config: Dict[str, Any], backtest_date: str) -> str:
    """
    Generate a unique cache key for scan results based on scan config and backtest date.
    
    Args:
        scan_config: Scan configuration dictionary (should NOT contain scan_date)
        backtest_date: Backtest date string (YYYY-MM-DD)
    
    Returns:
        MD5 hash string as cache key
    """
    # Ensure scan_date and use_scan_cache are not in config_dict
    # scan_date is passed separately, use_scan_cache doesn't affect cache key
    clean_config = {k: v for k, v in scan_config.items() if k not in ['scan_date', 'use_scan_cache']}
    
    # Sort config keys and convert to JSON string for consistent hashing
    config_str = json.dumps(clean_config, sort_keys=True, ensure_ascii=False)
    # Combine config and backtest_date
    cache_string = f"{config_str}:{backtest_date}"
    # Generate MD5 hash
    cache_key = hashlib.md5(cache_string.encode('utf-8')).hexdigest()
    
    # Debug log (only show first 16 chars to avoid log spam)
    print(f"{Fore.CYAN}[CACHE_KEY] Generated cache key: {cache_key[:16]}... (scan_date={backtest_date}){Style.RESET_ALL}")
    
    return cache_key


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
    
    # 特别强调 scan_date 的值
    if 'scan_date' in config_dict:
        print(f"{Fore.MAGENTA}[DEBUG] scan_date in config_dict: {config_dict['scan_date']}{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}[DEBUG] ⚠️ scan_date NOT in config_dict!{Style.RESET_ALL}")

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
            
            # Set global database-first preference from config
            use_db_first = config_dict.get('use_local_database_first', True)
            set_use_local_database_first(use_db_first)
            
            # Fetch stock basics
            with BaostockConnectionManager():
                stock_basics_df = fetch_stock_basics(use_local_database_first=use_db_first)

                # Update task status
                task_manager.update_task(
                    task_id,
                    progress=10,
                    message="Fetched stock basic information"
                )

                # Fetch industry data
                try:
                    industry_df = fetch_industry_data(use_local_database_first=use_db_first)
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
                
                # 如果设置了最大股票数量限制，则限制股票列表
                original_stock_count = len(stock_list)
                if config_request.max_stock_count and config_request.max_stock_count > 0:
                    stock_list = stock_list[:config_request.max_stock_count]
                    print(f"{Fore.YELLOW}[INDEX] 限制扫描股票数量: {original_stock_count} -> {len(stock_list)} (限制: {config_request.max_stock_count}){Style.RESET_ALL}")
                
                task_manager.update_task(
                    task_id,
                    progress=30,
                    message=f"Prepared list of {len(stock_list)} stocks for scanning"
                )

                # Create scan config
                scan_config = ScanConfig(**config_dict)
                
                # 使用配置中的扫描日期，如果没有则使用当前日期
                scan_date = scan_config.scan_date
                if scan_date is None:
                    scan_date = datetime.now().strftime('%Y-%m-%d')
                    print(f"{Fore.YELLOW}[INDEX] 未提供扫描日期，使用当前日期: {scan_date}{Style.RESET_ALL}")
                else:
                    print(f"{Fore.GREEN}[INDEX] ✓ 使用配置的扫描日期: {scan_date}{Style.RESET_ALL}")
                
                # 生成缓存键：从 config_dict 中移除 scan_date 和 use_scan_cache，避免影响缓存键
                # scan_date 会作为单独参数传入，use_scan_cache 不影响扫描结果
                cache_config_dict = config_dict.copy()
                original_scan_date_in_dict = cache_config_dict.get('scan_date')
                cache_config_dict.pop('scan_date', None)  # 移除 scan_date，避免影响缓存键
                cache_config_dict.pop('use_scan_cache', None)  # 移除 use_scan_cache，避免影响缓存键
                
                # 详细日志：显示缓存键生成过程
                print(f"{Fore.CYAN}[CACHE_DEBUG] 原始 config_dict 中的 scan_date: {original_scan_date_in_dict}{Style.RESET_ALL}")
                print(f"{Fore.CYAN}[CACHE_DEBUG] 实际使用的 scan_date: {scan_date}{Style.RESET_ALL}")
                print(f"{Fore.CYAN}[CACHE_DEBUG] 移除 scan_date 后的 config_dict keys: {list(cache_config_dict.keys())[:5]}...{Style.RESET_ALL}")
                
                cache_key = generate_scan_cache_key(cache_config_dict, scan_date)
                print(f"{Fore.CYAN}[INDEX] 缓存键生成: scan_date={scan_date}, cache_key={cache_key[:16]}...{Style.RESET_ALL}")
                
                # 检查缓存（如果启用了缓存）
                db = get_stock_database()
                cached_result = None
                if config_request.use_scan_cache:
                    cached_result = db.get_scan_cache(cache_key)
                    if cached_result:
                        print(f"{Fore.GREEN}[INDEX] 使用扫描结果缓存（use_scan_cache=True）{Style.RESET_ALL}")
                    else:
                        print(f"{Fore.YELLOW}[INDEX] 缓存未命中，将执行新扫描（use_scan_cache=True）{Style.RESET_ALL}")
                else:
                    print(f"{Fore.CYAN}[INDEX] 跳过缓存检查，直接执行扫描（use_scan_cache=False）{Style.RESET_ALL}")
                
                if cached_result:
                    cached_scan_date = cached_result.get('backtest_date', 'unknown')
                    print(f"{Fore.GREEN}找到缓存结果: 请求日期={scan_date}, 缓存中的日期={cached_scan_date}, 扫描配置已缓存{Style.RESET_ALL}")
                    if cached_scan_date != scan_date:
                        print(f"{Fore.RED}[CACHE_WARNING] ⚠️ 缓存日期不匹配！请求日期={scan_date}, 缓存日期={cached_scan_date}{Style.RESET_ALL}")
                    platform_stocks = cached_result['scanned_stocks']
                    task_manager.update_task(
                        task_id,
                        progress=100,
                        message=f"使用缓存结果，找到 {len(platform_stocks)} 只符合条件的股票"
                    )
                else:
                    # 缓存未命中，执行扫描
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
                        print(f"{Fore.CYAN}[INDEX] Starting scan_stocks with {len(stock_list)} stocks, scan_date={scan_date}{Style.RESET_ALL}")
                        scan_result = scan_stocks(
                            stock_list, scan_config, update_progress, end_date=scan_date, return_stats=True)
                        if isinstance(scan_result, tuple):
                            platform_stocks, scan_stats = scan_result
                            total_scanned = scan_stats.get('total_scanned', len(stock_list))
                            success_count = scan_stats.get('success_count', len(platform_stocks))
                        else:
                            # Backward compatibility: if function doesn't return stats
                            platform_stocks = scan_result
                            total_scanned = len(stock_list)
                            success_count = len(platform_stocks)  # 近似值
                        print(f"{Fore.GREEN}[INDEX] ✓ scan_stocks completed successfully, returned {len(platform_stocks)} stocks{Style.RESET_ALL}")
                        print(f"{Fore.CYAN}[INDEX] First few stocks: {[s.get('code', 'unknown') for s in platform_stocks[:5]]}{Style.RESET_ALL}")
                        
                        # 保存扫描结果到缓存（仅当结果不为空时）
                        if platform_stocks and len(platform_stocks) > 0:
                            try:
                                db.save_scan_cache(cache_key, config_dict, scan_date, platform_stocks,
                                                  total_scanned=total_scanned, success_count=success_count)
                                print(f"{Fore.GREEN}扫描结果已保存到缓存（{len(platform_stocks)}个股票），统计：{success_count}/{total_scanned}{Style.RESET_ALL}")
                            except Exception as cache_error:
                                print(f"{Fore.YELLOW}Warning: Failed to save scan cache: {cache_error}{Style.RESET_ALL}")
                        else:
                            # 即使结果为空，也保存统计信息
                            try:
                                db.save_scan_cache(cache_key, config_dict, scan_date, platform_stocks,
                                                  total_scanned=total_scanned, success_count=success_count)
                                print(f"{Fore.YELLOW}扫描结果为空，但已保存统计信息：{success_count}/{total_scanned}{Style.RESET_ALL}")
                            except Exception as cache_error:
                                print(f"{Fore.YELLOW}Warning: Failed to save scan cache: {cache_error}{Style.RESET_ALL}")
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
    
    # 使用配置中的扫描日期，如果没有则使用当前日期
    scan_date = scan_config.scan_date
    if scan_date is None:
        scan_date = datetime.now().strftime('%Y-%m-%d')
        print(f"{Fore.YELLOW}[INDEX] 未提供扫描日期，使用当前日期: {scan_date}{Style.RESET_ALL}")
    else:
        print(f"{Fore.GREEN}[INDEX] ✓ 使用配置的扫描日期: {scan_date}{Style.RESET_ALL}")
    
    # 生成缓存键：从 config_dict 中移除 scan_date 和 use_scan_cache，避免影响缓存键
    # scan_date 会作为单独参数传入，use_scan_cache 不影响扫描结果
    cache_config_dict = config_dict.copy()
    original_scan_date_in_dict = cache_config_dict.get('scan_date')
    cache_config_dict.pop('scan_date', None)  # 移除 scan_date，避免影响缓存键
    cache_config_dict.pop('use_scan_cache', None)  # 移除 use_scan_cache，避免影响缓存键
    
    # 详细日志：显示缓存键生成过程
    print(f"{Fore.CYAN}[CACHE_DEBUG] 原始 config_dict 中的 scan_date: {original_scan_date_in_dict}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}[CACHE_DEBUG] 实际使用的 scan_date: {scan_date}{Style.RESET_ALL}")
    
    cache_key = generate_scan_cache_key(cache_config_dict, scan_date)
    print(f"{Fore.CYAN}[INDEX] 缓存键生成: scan_date={scan_date}, cache_key={cache_key[:16]}...{Style.RESET_ALL}")
    
    # 检查缓存（如果启用了缓存）
    db = get_stock_database()
    cached_result = None
    if config_request.use_scan_cache:
        cached_result = db.get_scan_cache(cache_key)
        if cached_result:
            print(f"{Fore.GREEN}[INDEX] 使用扫描结果缓存（use_scan_cache=True）{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}[INDEX] 缓存未命中，将执行新扫描（use_scan_cache=True）{Style.RESET_ALL}")
    else:
        print(f"{Fore.CYAN}[INDEX] 跳过缓存检查，直接执行扫描（use_scan_cache=False）{Style.RESET_ALL}")
    
    if cached_result:
        cached_scan_date = cached_result.get('backtest_date', 'unknown')
        print(f"{Fore.GREEN}找到缓存结果: 请求日期={scan_date}, 缓存中的日期={cached_scan_date}, 扫描配置已缓存{Style.RESET_ALL}")
        if cached_scan_date != scan_date:
            print(f"{Fore.RED}[CACHE_WARNING] ⚠️ 缓存日期不匹配！请求日期={scan_date}, 缓存日期={cached_scan_date}{Style.RESET_ALL}")
        platform_stocks = cached_result['scanned_stocks']
    else:
        # 缓存未命中，执行扫描
        # Set global database-first preference from config
        use_db_first = config_request.use_local_database_first if hasattr(config_request, 'use_local_database_first') else True
        set_use_local_database_first(use_db_first)
        
        # Fetch stock basics
        with BaostockConnectionManager():
            stock_basics_df = fetch_stock_basics(use_local_database_first=use_db_first)

            # Fetch industry data
            try:
                industry_df = fetch_industry_data(use_local_database_first=use_db_first)
            except Exception as e:
                print(
                    f"{Fore.YELLOW}Warning: Failed to fetch industry data: {e}{Style.RESET_ALL}")
                industry_df = pd.DataFrame()

            # Prepare stock list
            stock_list = prepare_stock_list(stock_basics_df, industry_df)
            
            # 如果设置了最大股票数量限制，则限制股票列表
            original_stock_count = len(stock_list)
            if config_request.max_stock_count and config_request.max_stock_count > 0:
                stock_list = stock_list[:config_request.max_stock_count]
                print(f"{Fore.YELLOW}[INDEX] 限制扫描股票数量: {original_stock_count} -> {len(stock_list)} (限制: {config_request.max_stock_count}){Style.RESET_ALL}")

            # Run the scan
            scan_result = scan_stocks(stock_list, scan_config, end_date=scan_date, return_stats=True)
            if isinstance(scan_result, tuple):
                platform_stocks, scan_stats = scan_result
                total_scanned = scan_stats.get('total_scanned', len(stock_list))
                success_count = scan_stats.get('success_count', len(platform_stocks))
            else:
                # Backward compatibility: if function doesn't return stats
                platform_stocks = scan_result
                total_scanned = len(stock_list)
                success_count = len(platform_stocks)  # 近似值
            
            # 保存扫描结果到缓存（仅当结果不为空时）
            if platform_stocks and len(platform_stocks) > 0:
                try:
                    db.save_scan_cache(cache_key, config_dict, scan_date, platform_stocks,
                                      total_scanned=total_scanned, success_count=success_count)
                    print(f"{Fore.GREEN}扫描结果已保存到缓存（{len(platform_stocks)}个股票），统计：{success_count}/{total_scanned}{Style.RESET_ALL}")
                except Exception as e:
                    print(f"{Fore.YELLOW}Warning: Failed to save scan cache: {e}{Style.RESET_ALL}")
            else:
                # 即使结果为空，也保存统计信息
                try:
                    db.save_scan_cache(cache_key, config_dict, scan_date, platform_stocks,
                                      total_scanned=total_scanned, success_count=success_count)
                    print(f"{Fore.YELLOW}扫描结果为空，但已保存统计信息：{success_count}/{total_scanned}{Style.RESET_ALL}")
                except Exception as e:
                    print(f"{Fore.YELLOW}Warning: Failed to save scan cache: {e}{Style.RESET_ALL}")

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
    query_date: Optional[str] = Field(None, description="Query date (YYYY-MM-DD), defaults to today")


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
            # Use query_date if provided, otherwise use today
            if request.query_date:
                try:
                    end_date = datetime.strptime(request.query_date, '%Y-%m-%d').strftime('%Y-%m-%d')
                except ValueError:
                    raise HTTPException(
                        status_code=400,
                        detail="Invalid query_date format. Expected format: 'YYYY-MM-DD'"
                    )
            else:
                end_date = datetime.now().strftime('%Y-%m-%d')
            # Calculate start_date based on end_date
            end_datetime = datetime.strptime(end_date, '%Y-%m-%d')
            start_date = (end_datetime - timedelta(days=max_window * 2)).strftime('%Y-%m-%d')
            
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
    selected_stocks: List[Dict[str, Any]]  # 选中的股票列表（从扫描结果传递）


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
    marketReturnRate: Optional[float] = None  # 大盘收益率（同周期内）


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
        progress_callback(5, "开始回测，准备股票数据...")
    
    # 1. 直接使用传入的股票列表（不再执行扫描）
    # 回测功能不进行股票扫描，直接使用前端页面选中的股票列表
    print(f"{Fore.CYAN}开始回测: 回测日={request.backtest_date}, 统计日={request.stat_date}{Style.RESET_ALL}")
    
    # 验证股票列表
    if not request.selected_stocks or len(request.selected_stocks) == 0:
        raise HTTPException(status_code=400, detail="未选择股票，请至少选择一只股票进行回测")
    
    # 过滤掉指数代码和非活跃股票（从选中的股票列表中过滤）
    valid_stocks = []  # 有效的股票列表（过滤后的选中股票）
    filtered_indices = 0
    filtered_inactive = 0
    
    # 获取股票基本信息用于类型检查
    db = get_stock_database()
    stock_basics_df = db.get_stock_basics()
    stock_type_map = {}
    stock_status_map = {}
    
    if stock_basics_df is not None and not stock_basics_df.empty:
        # 数据库返回的列名可能是 'code_name' 而不是 'name'
        for _, row in stock_basics_df.iterrows():
            code = row['code']
            # 尝试多种可能的列名
            stock_type = row.get('type', row.get('stock_type', '1'))
            stock_status = row.get('status', row.get('stock_status', '1'))
            stock_type_map[code] = str(stock_type)  # 确保是字符串类型
            stock_status_map[code] = str(stock_status)  # 确保是字符串类型
    
    for stock in request.selected_stocks:
        code = stock.get('code', '')
        if not code:
            continue
        
        # 优先使用数据库中的类型，如果没有则使用股票对象中的类型，最后默认为'1'（普通股票）
        stock_type = stock_type_map.get(code)
        if stock_type is None:
            stock_type = str(stock.get('type', '1'))
        
        stock_status = stock_status_map.get(code)
        if stock_status is None:
            stock_status = str(stock.get('status', '1'))
        
        # 跳过指数代码（type=2）
        if stock_type == '2' or stock_type == 2:
            filtered_indices += 1
            print(f"{Fore.YELLOW}跳过指数代码: {code} ({stock.get('name', '')}){Style.RESET_ALL}")
            continue
        
        # 跳过非活跃股票（status=0）
        if stock_status == '0' or stock_status == 0:
            filtered_inactive += 1
            print(f"{Fore.YELLOW}跳过非活跃股票: {code} ({stock.get('name', '')}){Style.RESET_ALL}")
            continue
        
        # 添加到有效股票列表
        valid_stocks.append(stock)
    
    if filtered_indices > 0:
        print(f"{Fore.YELLOW}已过滤 {filtered_indices} 个指数代码{Style.RESET_ALL}")
    if filtered_inactive > 0:
        print(f"{Fore.YELLOW}已过滤 {filtered_inactive} 个非活跃股票{Style.RESET_ALL}")
    
    # 如果过滤后没有股票，但原始列表有股票，给出警告但不抛出异常
    # 让后续的K线数据获取来决定是否真的没有可用股票
    if len(valid_stocks) == 0 and len(request.selected_stocks) > 0:
        print(f"{Fore.RED}警告: 所有股票都被过滤掉了！原始股票数: {len(request.selected_stocks)}, 过滤后: {len(valid_stocks)}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}调试信息: 数据库中有 {len(stock_type_map)} 只股票的类型信息{Style.RESET_ALL}")
        # 如果所有股票都被过滤，尝试使用原始列表（可能是数据库信息不完整）
        valid_stocks = request.selected_stocks
        print(f"{Fore.YELLOW}使用原始股票列表继续回测（可能包含指数代码或非活跃股票）{Style.RESET_ALL}")
    
    print(f"{Fore.GREEN}使用选中的股票列表进行回测，共 {len(valid_stocks)} 只有效股票（原始选中: {len(request.selected_stocks)} 只）{Style.RESET_ALL}")
    
    if progress_callback:
        progress_callback(10, f"准备回测 {len(valid_stocks)} 只股票...")
    
    # 2. 对于每只选中的股票，执行买入和卖出逻辑（不进行扫描）
    buy_records = []
    sell_records = []
    stock_details = []
    
    buy_amount_per_stock = 10000  # 每只股票买入1万元
    
    total_stocks = len(valid_stocks)
    for idx, stock in enumerate(valid_stocks):
        code = stock['code']
        name = stock.get('name', code)
        
        if progress_callback:
            progress = 10 + int((idx + 1) / total_stocks * 85)
            progress_callback(progress, f"正在处理股票 {idx + 1}/{total_stocks}: {name} ({code})...")
        
        # 获取从回测日到统计日的历史数据
        start_date = request.backtest_date
        end_date = request.stat_date
        
        with BaostockConnectionManager():
            kline_df = fetch_kline_data(code, start_date, end_date)
        
        if kline_df.empty:
            print(f"{Fore.YELLOW}Warning: {code} ({name}) 在 {start_date} 到 {end_date} 期间无数据，跳过{Style.RESET_ALL}")
            # 记录跳过的股票信息，但不添加到买入记录
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
        # 只提取日期部分，去掉时间
        buy_date_obj = buy_day_data.iloc[0]['date']
        if isinstance(buy_date_obj, pd.Timestamp):
            buy_date_raw = buy_date_obj.strftime('%Y-%m-%d')
        else:
            buy_date_raw = str(buy_date_obj).split()[0]  # 取第一个空格前的部分
        # 买入日期显示为"日期（开盘）"，因为买入价格是开盘价
        buy_date = f"{buy_date_raw}（开盘）"
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
            # 只提取日期部分，去掉时间
            date_obj = day_data['date']
            if isinstance(date_obj, pd.Timestamp):
                current_date = date_obj.strftime('%Y-%m-%d')
            else:
                current_date = str(date_obj).split()[0]  # 取第一个空格前的部分
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
                    # 止损日期显示为"日期（止损）"
                    sell_date = f"{current_date}（止损）"
                    sell_reason = '止损'
                    break
            
            # 检查止盈（使用最高价）
            if request.use_take_profit:
                high_return_rate = ((current_high - buy_price) / buy_price) * 100
                if high_return_rate >= request.take_profit_percent:
                    sell_price = buy_price * (1 + request.take_profit_percent / 100)
                    # 止盈日期显示为"日期（止盈）"
                    sell_date = f"{current_date}（止盈）"
                    sell_reason = '止盈'
                    break
            
            # 如果到了统计日，使用收盘价卖出（确保日期格式一致）
            if current_date == request.stat_date or str(day_data.get('date_str', current_date)) == request.stat_date:
                sell_price = current_close
                # 统计日卖出日期显示为"日期（收盘）"，因为卖出价格是收盘价
                sell_date = f"{current_date}（收盘）"
                sell_reason = '统计日卖出'
                break
        
        # 如果没有卖出（理论上不应该发生，因为统计日一定会卖出）
        if sell_price is None:
            # 使用最后一天的收盘价
            if len(kline_df) > 0:
                last_day = kline_df.iloc[-1]
                sell_price = float(last_day['close'])
                # 只提取日期部分，去掉时间
                last_date_obj = last_day['date']
                if isinstance(last_date_obj, pd.Timestamp):
                    last_date = last_date_obj.strftime('%Y-%m-%d')
                else:
                    last_date = str(last_date_obj).split()[0]  # 取第一个空格前的部分
                # 统计日卖出日期显示为"日期（收盘）"
                sell_date = f"{last_date}（收盘）"
                sell_reason = '统计日卖出'
            else:
                # 如果没有数据，使用买入价（未卖出）
                sell_price = buy_price
                sell_date = f"{buy_date_raw}（未卖出）"
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
    
    # 如果没有成功买入任何股票，给出警告
    if total_stocks == 0:
        print(f"{Fore.RED}警告: 没有成功买入任何股票！可能的原因：{Style.RESET_ALL}")
        print(f"{Fore.RED}  1. 所有股票在指定日期范围内都没有K线数据{Style.RESET_ALL}")
        print(f"{Fore.RED}  2. 回测日期可能是未来日期（当前日期之后）{Style.RESET_ALL}")
        print(f"{Fore.RED}  3. 回测日期可能是非交易日（周末或节假日）{Style.RESET_ALL}")
        print(f"{Fore.RED}  4. 股票可能已退市或停牌{Style.RESET_ALL}")
        print(f"{Fore.CYAN}原始选中股票数: {len(valid_stocks)}, 成功买入: {total_stocks}{Style.RESET_ALL}")
    
    total_investment = sum(record['buyAmount'] for record in buy_records)
    total_profit = sum(detail['profit'] for detail in stock_details)
    total_return_rate = (total_profit / total_investment * 100) if total_investment > 0 else 0
    profitable_stocks = sum(1 for detail in stock_details if detail['profit'] > 0)
    loss_stocks = sum(1 for detail in stock_details if detail['profit'] < 0)
    
    # 4. 计算大盘收益率（使用上证指数 sh.000001）
    market_return_rate = None
    try:
        if progress_callback:
            progress_callback(99, "正在获取大盘指数数据...")
        
        # 获取上证指数数据
        market_index_code = "sh.000001"  # 上证指数
        start_date = request.backtest_date
        end_date = request.stat_date
        
        with BaostockConnectionManager():
            market_df = fetch_kline_data(market_index_code, start_date, end_date)
        
        if not market_df.empty:
            # 确保数据按日期排序
            market_df = market_df.sort_values('date').reset_index(drop=True)
            
            # 找到回测日的数据（买入日）
            market_df['date_str'] = market_df['date'].astype(str)
            buy_day_data = market_df[market_df['date_str'] == request.backtest_date]
            
            # 如果回测日没有数据，使用第一个交易日
            if buy_day_data.empty and len(market_df) > 0:
                buy_day_data = market_df.iloc[[0]]
            
            # 找到统计日的数据（卖出日）
            stat_day_data = market_df[market_df['date_str'] == request.stat_date]
            
            # 如果统计日没有数据，使用最后一个交易日
            if stat_day_data.empty and len(market_df) > 0:
                stat_day_data = market_df.iloc[[-1]]
            
            if not buy_day_data.empty and not stat_day_data.empty:
                buy_price = float(buy_day_data.iloc[0]['close'])
                sell_price = float(stat_day_data.iloc[-1]['close'])
                market_return_rate = ((sell_price - buy_price) / buy_price) * 100
                print(f"{Fore.GREEN}大盘收益率计算成功: {market_return_rate:.2f}%{Style.RESET_ALL}")
            else:
                print(f"{Fore.YELLOW}Warning: 无法找到大盘指数的买入日或统计日数据{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}Warning: 无法获取大盘指数数据{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.YELLOW}Warning: 计算大盘收益率时出错: {e}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()
        # 不阻止回测完成，只是记录警告
    
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
            lossStocks=loss_stocks,
            marketReturnRate=market_return_rate
        ),
        buyRecords=[BuyRecord(**record) for record in buy_records],
        sellRecords=[SellRecord(**record) for record in sell_records],
        stockDetails=[StockDetail(**detail) for detail in stock_details]
    )
    
    print(f"{Fore.GREEN}回测完成: 总股票数={total_stocks}, 总投入={total_investment:.2f}, 总收益={total_profit:.2f}, 总收益率={total_return_rate:.2f}%{Style.RESET_ALL}")
    
    return response


@app.post("/api/backtest")
async def run_backtest(request: BacktestRequest):
    """
    执行回测（同步版本，不支持进度推送）
    """
    try:
        result = run_backtest_with_progress(request, progress_callback=None)
        # 转换为字典并清理无效的浮点值（inf, -inf, nan）以避免 JSON 序列化错误
        result_dict = result.model_dump()
        sanitized_dict = sanitize_float_for_json(result_dict)
        # 直接返回清理后的字典，避免 Pydantic 验证 None 值的问题
        return JSONResponse(content=sanitized_dict)
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
                
                # 清理无效的浮点值（inf, -inf, nan）以避免 JSON 序列化错误
                result_dict = sanitize_float_for_json(result_dict)
                
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
                        'selected_stocks': request.selected_stocks  # 保存选中的股票列表
                    }
                    history_id = save_backtest_history(config_dict, result_dict)
                    result_dict['historyId'] = history_id  # 将历史ID添加到结果中
                    print(f"{Fore.GREEN}回测历史已保存: {history_id}{Style.RESET_ALL}")
                except Exception as e:
                    print(f"{Fore.YELLOW}Warning: Failed to save backtest history: {e}{Style.RESET_ALL}")
                    import traceback
                    traceback.print_exc()
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
async def get_backtest_history_list_endpoint(batch_task_id: Optional[str] = None):
    """
    获取回测历史记录列表
    
    Args:
        batch_task_id: 可选的批量任务ID，用于过滤批量回测数据
    """
    try:
        records = get_backtest_history_list(batch_task_id=batch_task_id)
        # 清理无效的浮点值（inf, -inf, nan）以避免 JSON 序列化错误
        sanitized_records = sanitize_float_for_json(records)
        return {
            "success": True,
            "data": sanitized_records,
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
        # 清理无效的浮点值（inf, -inf, nan）以避免 JSON 序列化错误
        sanitized_record = sanitize_float_for_json(record)
        return {
            "success": True,
            "data": sanitized_record
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


@app.delete("/api/backtest/history/date/{backtest_date}")
async def delete_backtest_history_by_date_endpoint(backtest_date: str):
    """
    删除指定扫描日期的所有回测历史记录
    """
    try:
        # 验证日期格式
        from datetime import datetime
        try:
            datetime.strptime(backtest_date, '%Y-%m-%d')
        except ValueError:
            raise HTTPException(status_code=400, detail="日期格式错误，应为 YYYY-MM-DD")
        
        count = delete_backtest_history_by_date(backtest_date)
        return {
            "success": True,
            "message": f"已删除 {count} 条回测历史记录（扫描日期: {backtest_date}）",
            "count": count
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


class BatchBacktestRequest(BaseModel):
    """批量回测请求模型"""
    backtest_date: str  # 回测日（截止日），格式：YYYY-MM-DD
    stat_date: str  # 统计日，格式：YYYY-MM-DD
    buy_strategy: str = "fixed_amount"  # 买入策略
    selected_stocks: List[Dict[str, Any]]  # 选中的股票列表
    profit_loss_combinations: List[Dict[str, Any]]  # 止盈止损组合列表
    # 每个组合包含: use_stop_loss, use_take_profit, stop_loss_percent, take_profit_percent


class BatchBacktestResult(BaseModel):
    """批量回测结果"""
    total: int  # 总任务数
    completed: int  # 已完成数
    skipped: int  # 跳过数（已存在）
    failed: int  # 失败数
    results: List[Dict[str, Any]]  # 详细结果列表


@app.post("/api/backtest/batch", response_model=BatchBacktestResult)
async def run_batch_backtest(request: BatchBacktestRequest):
    """
    批量回测：根据多个止盈止损组合批量生成回测数据
    如果数据已存在则跳过
    """
    try:
        # 验证日期格式
        from datetime import datetime
        try:
            backtest_date = datetime.strptime(request.backtest_date, '%Y-%m-%d')
            stat_date = datetime.strptime(request.stat_date, '%Y-%m-%d')
        except ValueError:
            raise HTTPException(status_code=400, detail="日期格式错误，应为 YYYY-MM-DD")
        
        if backtest_date >= stat_date:
            raise HTTPException(status_code=400, detail="回测日必须早于统计日")
        
        # 验证股票列表
        if not request.selected_stocks or len(request.selected_stocks) == 0:
            raise HTTPException(status_code=400, detail="未选择股票，请至少选择一只股票进行回测")
        
        # 验证止盈止损组合
        if not request.profit_loss_combinations or len(request.profit_loss_combinations) == 0:
            raise HTTPException(status_code=400, detail="请至少设置一个止盈止损组合")
        
        total = len(request.profit_loss_combinations)
        completed = 0
        skipped = 0
        failed = 0
        results = []
        
        print(f"{Fore.CYAN}开始批量回测: 共 {total} 个组合{Style.RESET_ALL}")
        
        # 遍历每个止盈止损组合
        for idx, combination in enumerate(request.profit_loss_combinations):
            try:
                # 构建回测请求配置
                config_dict = {
                    'backtest_date': request.backtest_date,
                    'stat_date': request.stat_date,
                    'buy_strategy': request.buy_strategy,
                    'use_stop_loss': combination.get('use_stop_loss', False),
                    'use_take_profit': combination.get('use_take_profit', False),
                    'stop_loss_percent': combination.get('stop_loss_percent', -3.0),
                    'take_profit_percent': combination.get('take_profit_percent', 10.0),
                    'selected_stocks': request.selected_stocks
                }
                
                # 检查是否已存在
                existing_id = check_backtest_exists(config_dict)
                if existing_id:
                    print(f"{Fore.YELLOW}[{idx + 1}/{total}] 跳过已存在的回测记录: {existing_id}{Style.RESET_ALL}")
                    skipped += 1
                    results.append({
                        'index': idx + 1,
                        'status': 'skipped',
                        'message': '回测记录已存在',
                        'history_id': existing_id,
                        'config': config_dict
                    })
                    continue
                
                # 创建回测请求
                backtest_request = BacktestRequest(
                    backtest_date=request.backtest_date,
                    stat_date=request.stat_date,
                    buy_strategy=request.buy_strategy,
                    use_stop_loss=combination.get('use_stop_loss', False),
                    use_take_profit=combination.get('use_take_profit', False),
                    stop_loss_percent=combination.get('stop_loss_percent', -3.0),
                    take_profit_percent=combination.get('take_profit_percent', 10.0),
                    selected_stocks=request.selected_stocks
                )
                
                # 执行回测
                print(f"{Fore.CYAN}[{idx + 1}/{total}] 执行回测: 止损={combination.get('stop_loss_percent')}%, 止盈={combination.get('take_profit_percent')}%{Style.RESET_ALL}")
                result = run_backtest_with_progress(backtest_request, progress_callback=None)
                result_dict = result.model_dump()
                
                # 保存回测历史
                history_id = save_backtest_history(config_dict, result_dict)
                print(f"{Fore.GREEN}[{idx + 1}/{total}] 回测完成并保存: {history_id}{Style.RESET_ALL}")
                
                completed += 1
                results.append({
                    'index': idx + 1,
                    'status': 'completed',
                    'message': '回测完成',
                    'history_id': history_id,
                    'config': config_dict,
                    'summary': result_dict.get('summary', {})
                })
                
            except Exception as e:
                print(f"{Fore.RED}[{idx + 1}/{total}] 回测失败: {e}{Style.RESET_ALL}")
                import traceback
                traceback.print_exc()
                failed += 1
                results.append({
                    'index': idx + 1,
                    'status': 'failed',
                    'message': str(e),
                    'config': config_dict if 'config_dict' in locals() else combination
                })
        
        print(f"{Fore.GREEN}批量回测完成: 总计={total}, 完成={completed}, 跳过={skipped}, 失败={failed}{Style.RESET_ALL}")
        
        # 清理无效的浮点值（inf, -inf, nan）以避免 JSON 序列化错误
        sanitized_results = sanitize_float_for_json(results)
        
        return BatchBacktestResult(
            total=total,
            completed=completed,
            skipped=skipped,
            failed=failed,
            results=sanitized_results
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"{Fore.RED}批量回测失败: {e}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"批量回测执行失败: {str(e)}"
        )


# =================================
# Scan History API
# =================================

@app.get("/api/scan/history")
async def get_scan_history_list_endpoint():
    """
    获取扫描历史记录列表
    """
    try:
        records = get_scan_history_list()
        return {
            "success": True,
            "data": records,
            "count": len(records)
        }
    except Exception as e:
        print(f"{Fore.RED}获取扫描历史列表失败: {e}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"获取扫描历史列表失败: {str(e)}"
        )


@app.get("/api/scan/history/{cache_key}")
async def get_scan_history_endpoint(cache_key: str):
    """
    获取单个扫描历史记录详情
    """
    try:
        record = get_scan_history(cache_key)
        if record is None:
            raise HTTPException(
                status_code=404,
                detail=f"扫描历史记录不存在: {cache_key}"
            )
        return {
            "success": True,
            "data": record
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"{Fore.RED}获取扫描历史记录失败: {e}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"获取扫描历史记录失败: {str(e)}"
        )


@app.delete("/api/scan/history/{cache_key}")
async def delete_scan_history_endpoint(cache_key: str):
    """
    删除单个扫描历史记录
    """
    try:
        success = delete_scan_history(cache_key)
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"扫描历史记录不存在: {cache_key}"
            )
        return {
            "success": True,
            "message": "扫描历史记录已删除"
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"{Fore.RED}删除扫描历史记录失败: {e}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"删除扫描历史记录失败: {str(e)}"
        )


@app.delete("/api/scan/history")
async def clear_all_scan_history_endpoint():
    """
    清空所有扫描历史记录
    """
    try:
        count = clear_all_scan_history()
        return {
            "success": True,
            "message": f"已清空 {count} 条扫描历史记录",
            "count": count
        }
    except Exception as e:
        print(f"{Fore.RED}清空扫描历史记录失败: {e}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"清空扫描历史记录失败: {str(e)}"
        )


# =================================
# Batch Scan API
# =================================

class BatchScanRequest(BaseModel):
    """Request model for batch scan"""
    task_name: str = Field(..., description="任务名称")
    start_date: str = Field(..., description="开始日期，格式：YYYY-MM-DD")
    end_date: str = Field(..., description="结束日期，格式：YYYY-MM-DD")
    scan_period_days: int = Field(default=7, description="扫描周期（天数），默认7天")
    # Reuse ScanConfigRequest fields for scan configuration
    windows: List[int] = Field(default_factory=lambda: DEFAULT_WINDOWS.copy())
    box_threshold: float = DEFAULT_BOX_THRESHOLD
    ma_diff_threshold: float = DEFAULT_MA_DIFF_THRESHOLD
    volatility_threshold: float = DEFAULT_VOLATILITY_THRESHOLD
    use_volume_analysis: bool = DEFAULT_USE_VOLUME_ANALYSIS
    volume_change_threshold: float = DEFAULT_VOLUME_CHANGE_THRESHOLD
    volume_stability_threshold: float = DEFAULT_VOLUME_STABILITY_THRESHOLD
    volume_increase_threshold: float = DEFAULT_VOLUME_INCREASE_THRESHOLD
    use_technical_indicators: bool = False
    use_breakthrough_prediction: bool = DEFAULT_USE_BREAKTHROUGH_PREDICTION
    use_low_position: bool = DEFAULT_USE_LOW_POSITION
    high_point_lookback_days: int = DEFAULT_HIGH_POINT_LOOKBACK_DAYS
    decline_period_days: int = DEFAULT_DECLINE_PERIOD_DAYS
    decline_threshold: float = DEFAULT_DECLINE_THRESHOLD
    use_rapid_decline_detection: bool = DEFAULT_USE_RAPID_DECLINE_DETECTION
    rapid_decline_days: int = DEFAULT_RAPID_DECLINE_DAYS
    rapid_decline_threshold: float = DEFAULT_RAPID_DECLINE_THRESHOLD
    use_breakthrough_confirmation: bool = DEFAULT_USE_BREAKTHROUGH_CONFIRMATION
    breakthrough_confirmation_days: int = DEFAULT_BREAKTHROUGH_CONFIRMATION_DAYS
    use_box_detection: bool = DEFAULT_USE_BOX_DETECTION
    box_quality_threshold: float = DEFAULT_BOX_QUALITY_THRESHOLD
    use_fundamental_filter: bool = False
    revenue_growth_percentile: float = 0.3
    profit_growth_percentile: float = 0.3
    roe_percentile: float = 0.3
    liability_percentile: float = 0.3
    pe_percentile: float = 0.7
    pb_percentile: float = 0.7
    fundamental_years_to_check: int = 3
    use_window_weights: bool = False
    window_weights: Dict[int, float] = Field(default_factory=dict)
    max_workers: int = 5
    retry_attempts: int = 2
    retry_delay: int = 1
    expected_count: int = 10
    max_stock_count: Optional[int] = None
    use_scan_cache: bool = True
    use_local_database_first: bool = True


class BatchScanTaskResponse(BaseModel):
    """Response model for batch scan task creation"""
    task_id: str
    message: str


@app.post("/api/batch-scan/start", response_model=BatchScanTaskResponse)
async def start_batch_scan(request: BatchScanRequest):
    """
    创建并启动批量扫描任务
    """
    if batch_scan_manager is None:
        raise HTTPException(status_code=500, detail="批量扫描功能未初始化")
    try:
        # Validate dates
        from datetime import datetime
        try:
            start_date = datetime.strptime(request.start_date, '%Y-%m-%d')
            end_date = datetime.strptime(request.end_date, '%Y-%m-%d')
        except ValueError:
            raise HTTPException(status_code=400, detail="日期格式错误，应为 YYYY-MM-DD")
        
        if start_date > end_date:
            raise HTTPException(status_code=400, detail="开始日期不能晚于结束日期")
        
        if request.scan_period_days <= 0:
            raise HTTPException(status_code=400, detail="扫描周期必须大于0")
        
        # Convert request to scan config dict (exclude batch scan specific fields)
        scan_config_dict = request.model_dump()
        scan_config_dict.pop('task_name', None)
        scan_config_dict.pop('start_date', None)
        scan_config_dict.pop('end_date', None)
        scan_config_dict.pop('scan_period_days', None)
        
        # Create task
        task_id = batch_scan_manager.create_batch_scan_task(
            task_name=request.task_name,
            start_date=request.start_date,
            end_date=request.end_date,
            scan_period_days=request.scan_period_days,
            scan_config=scan_config_dict
        )
        
        # Start task in background
        batch_scan_manager.start_batch_scan_task(task_id)
        
        return BatchScanTaskResponse(
            task_id=task_id,
            message="批量扫描任务已创建并启动"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"{Fore.RED}创建批量扫描任务失败: {e}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"创建批量扫描任务失败: {str(e)}"
        )


@app.get("/api/batch-scan/tasks")
async def get_batch_scan_tasks():
    """
    获取批量扫描任务列表
    """
    try:
        from api.stock_database import get_stock_database
        db = get_stock_database()
        tasks = db.get_batch_scan_task_list()
        return {
            "success": True,
            "data": tasks,
            "count": len(tasks)
        }
    except Exception as e:
        print(f"{Fore.RED}获取批量扫描任务列表失败: {e}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"获取批量扫描任务列表失败: {str(e)}"
        )


@app.get("/api/batch-scan/tasks/{task_id}")
async def get_batch_scan_task(task_id: str):
    """
    获取单个批量扫描任务详情
    """
    try:
        from api.stock_database import get_stock_database
        db = get_stock_database()
        task = db.get_batch_scan_task(task_id)
        if not task:
            raise HTTPException(
                status_code=404,
                detail=f"批量扫描任务不存在: {task_id}"
            )
        return {
            "success": True,
            "data": task
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"{Fore.RED}获取批量扫描任务失败: {e}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"获取批量扫描任务失败: {str(e)}"
        )


@app.post("/api/batch-scan/tasks/{task_id}/cancel")
async def cancel_batch_scan_task(task_id: str):
    """
    取消批量扫描任务
    """
    if batch_scan_manager is None:
        raise HTTPException(status_code=500, detail="批量扫描功能未初始化")
    try:
        success = batch_scan_manager.cancel_batch_scan_task(task_id)
        if not success:
            raise HTTPException(
                status_code=400,
                detail=f"无法取消任务 {task_id}，任务可能不存在或已完成"
            )
        return {
            "success": True,
            "message": "任务已取消"
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"{Fore.RED}取消批量扫描任务失败: {e}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"取消批量扫描任务失败: {str(e)}"
        )


@app.get("/api/batch-scan/tasks/{task_id}/results")
async def get_batch_scan_results(task_id: str):
    """
    获取批量扫描任务的所有扫描结果
    """
    try:
        from api.stock_database import get_stock_database
        db = get_stock_database()
        
        # Check if task exists
        task = db.get_batch_scan_task(task_id)
        if not task:
            raise HTTPException(
                status_code=404,
                detail=f"批量扫描任务不存在: {task_id}"
            )
        
        results = db.get_batch_scan_results(task_id)
        # 清理无效的浮点值（inf, -inf, nan）以避免 JSON 序列化错误
        sanitized_results = sanitize_float_for_json(results)
        return {
            "success": True,
            "data": sanitized_results,
            "count": len(results)
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"{Fore.RED}获取批量扫描结果失败: {e}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"获取批量扫描结果失败: {str(e)}"
        )


@app.get("/api/batch-scan/results/{result_id}")
async def get_batch_scan_result(result_id: str):
    """
    获取单个批量扫描结果详情
    """
    try:
        from api.stock_database import get_stock_database
        db = get_stock_database()
        result = db.get_batch_scan_result(result_id)
        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"批量扫描结果不存在: {result_id}"
            )
        # 清理无效的浮点值（inf, -inf, nan）以避免 JSON 序列化错误
        sanitized_result = sanitize_float_for_json(result)
        return {
            "success": True,
            "data": sanitized_result
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"{Fore.RED}获取批量扫描结果失败: {e}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"获取批量扫描结果失败: {str(e)}"
        )


@app.delete("/api/batch-scan/tasks/{task_id}")
async def delete_batch_scan_task(task_id: str):
    """
    删除批量扫描任务及其所有结果
    """
    try:
        from api.stock_database import get_stock_database
        db = get_stock_database()
        
        # Cancel if running
        batch_scan_manager.cancel_batch_scan_task(task_id)
        
        # Delete task
        success = db.delete_batch_scan_task(task_id)
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"批量扫描任务不存在: {task_id}"
            )
        return {
            "success": True,
            "message": "批量扫描任务已删除"
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"{Fore.RED}删除批量扫描任务失败: {e}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"删除批量扫描任务失败: {str(e)}"
        )


# =================================
# Batch Task Backtest API
# =================================

class BatchTaskBacktestRequest(BaseModel):
    """批量任务回测请求"""
    task_id: str  # 批量扫描任务ID
    period_stat_dates: Dict[str, str]  # 每个周期对应的统计日 { scanDate: statDate }
    buy_strategy: str = "fixed_amount"  # 买入策略
    use_stop_loss: bool = True  # 使用止损
    use_take_profit: bool = True  # 使用止盈
    stop_loss_percent: float = -2.0  # 止损百分比
    take_profit_percent: float = 18.0  # 止盈百分比


class BatchTaskBacktestResult(BaseModel):
    """批量任务回测结果"""
    task_id: str
    total: int  # 总回测数
    completed: int  # 已完成数
    failed: int  # 失败数
    results: List[Dict[str, Any]]  # 详细结果列表


@app.post("/api/batch-scan/tasks/{task_id}/backtest", response_model=BatchTaskBacktestResult)
async def run_batch_task_backtest(task_id: str, request: BatchTaskBacktestRequest):
    """
    为批量扫描任务执行一键回测
    使用每个周期的开始日（scanDate）作为回测日
    """
    try:
        from datetime import datetime
        from api.stock_database import get_stock_database
        
        db = get_stock_database()
        
        # 验证任务是否存在
        task = db.get_batch_scan_task(task_id)
        if not task:
            raise HTTPException(
                status_code=404,
                detail=f"批量扫描任务不存在: {task_id}"
            )
        
        # 验证period_stat_dates
        if not request.period_stat_dates or len(request.period_stat_dates) == 0:
            raise HTTPException(status_code=400, detail="请为所有周期设置统计日")
        
        # 获取该任务的所有扫描结果
        scan_results = db.get_batch_scan_results(task_id)
        if not scan_results or len(scan_results) == 0:
            raise HTTPException(
                status_code=400,
                detail="该批量扫描任务还没有扫描结果，请先完成扫描"
            )
        
        print(f"{Fore.CYAN}开始批量任务回测: 任务ID={task_id}, 扫描结果数={len(scan_results)}{Style.RESET_ALL}")
        
        total = len(scan_results)
        completed = 0
        failed = 0
        results = []
        
        # 为每个扫描结果执行回测
        for idx, scan_result in enumerate(scan_results):
            try:
                scan_date = scan_result.get('scanDate')
                if not scan_date:
                    print(f"{Fore.YELLOW}[{idx + 1}/{total}] 跳过：扫描结果缺少scanDate{Style.RESET_ALL}")
                    failed += 1
                    results.append({
                        'index': idx + 1,
                        'status': 'failed',
                        'message': '扫描结果缺少scanDate',
                        'scanDate': None
                    })
                    continue
                
                # 获取该周期对应的统计日
                stat_date_str = request.period_stat_dates.get(scan_date)
                if not stat_date_str:
                    print(f"{Fore.YELLOW}[{idx + 1}/{total}] 跳过：扫描日期{scan_date}未设置统计日{Style.RESET_ALL}")
                    failed += 1
                    results.append({
                        'index': idx + 1,
                        'status': 'failed',
                        'message': f'扫描日期{scan_date}未设置统计日',
                        'scanDate': scan_date
                    })
                    continue
                
                # 验证统计日格式
                try:
                    stat_date = datetime.strptime(stat_date_str, '%Y-%m-%d')
                except ValueError:
                    print(f"{Fore.YELLOW}[{idx + 1}/{total}] 跳过：统计日格式错误: {stat_date_str}{Style.RESET_ALL}")
                    failed += 1
                    results.append({
                        'index': idx + 1,
                        'status': 'failed',
                        'message': f'统计日格式错误: {stat_date_str}',
                        'scanDate': scan_date
                    })
                    continue
                
                # 验证回测日必须早于统计日
                backtest_date_obj = datetime.strptime(scan_date, '%Y-%m-%d')
                if backtest_date_obj >= stat_date:
                    print(f"{Fore.YELLOW}[{idx + 1}/{total}] 跳过：回测日({scan_date})必须早于统计日({stat_date_str}){Style.RESET_ALL}")
                    failed += 1
                    results.append({
                        'index': idx + 1,
                        'status': 'failed',
                        'message': f'回测日({scan_date})必须早于统计日({stat_date_str})',
                        'scanDate': scan_date
                    })
                    continue
                
                # 获取扫描到的股票列表
                scanned_stocks = scan_result.get('scannedStocks', [])
                if not scanned_stocks or len(scanned_stocks) == 0:
                    print(f"{Fore.YELLOW}[{idx + 1}/{total}] 跳过：扫描日期{scan_date}没有扫描到股票{Style.RESET_ALL}")
                    failed += 1
                    results.append({
                        'index': idx + 1,
                        'status': 'failed',
                        'message': '该扫描日期没有扫描到股票',
                        'scanDate': scan_date
                    })
                    continue
                
                print(f"{Fore.CYAN}[{idx + 1}/{total}] 执行回测: 回测日={scan_date}, 统计日={stat_date_str}, 股票数={len(scanned_stocks)}{Style.RESET_ALL}")
                
                # 构建回测请求
                backtest_request = BacktestRequest(
                    backtest_date=scan_date,
                    stat_date=stat_date_str,
                    buy_strategy=request.buy_strategy,
                    use_stop_loss=request.use_stop_loss,
                    use_take_profit=request.use_take_profit,
                    stop_loss_percent=request.stop_loss_percent,
                    take_profit_percent=request.take_profit_percent,
                    selected_stocks=scanned_stocks
                )
                
                # 执行回测
                result = run_backtest_with_progress(backtest_request, progress_callback=None)
                result_dict = result.model_dump()
                
                # 保存回测历史，标记为批量回测
                config_dict = {
                    'backtest_date': scan_date,
                    'stat_date': stat_date_str,
                    'buy_strategy': request.buy_strategy,
                    'use_stop_loss': request.use_stop_loss,
                    'use_take_profit': request.use_take_profit,
                    'stop_loss_percent': request.stop_loss_percent,
                    'take_profit_percent': request.take_profit_percent,
                    'selected_stocks': scanned_stocks,
                    'batch_task_id': task_id
                }
                history_id = save_backtest_history(config_dict, result_dict, batch_task_id=task_id)
                print(f"{Fore.GREEN}[{idx + 1}/{total}] 回测完成并保存: {history_id}{Style.RESET_ALL}")
                
                completed += 1
                results.append({
                    'index': idx + 1,
                    'status': 'completed',
                    'message': '回测完成',
                    'scanDate': scan_date,
                    'historyId': history_id,
                    'summary': result_dict.get('summary', {})
                })
                
            except Exception as e:
                print(f"{Fore.RED}[{idx + 1}/{total}] 回测失败: {e}{Style.RESET_ALL}")
                import traceback
                traceback.print_exc()
                failed += 1
                results.append({
                    'index': idx + 1,
                    'status': 'failed',
                    'message': str(e),
                    'scanDate': scan_result.get('scanDate')
                })
        
        print(f"{Fore.GREEN}批量任务回测完成: 总计={total}, 完成={completed}, 失败={failed}{Style.RESET_ALL}")
        
        # 清理无效的浮点值（inf, -inf, nan）以避免 JSON 序列化错误
        sanitized_results = sanitize_float_for_json(results)
        
        return BatchTaskBacktestResult(
            task_id=task_id,
            total=total,
            completed=completed,
            failed=failed,
            results=sanitized_results
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"{Fore.RED}批量任务回测失败: {e}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"批量任务回测执行失败: {str(e)}"
        )