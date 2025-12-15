"""
JSON utilities for handling special values like NaN and Infinity.
"""
import json
import math
from typing import Any, Dict, List, Union

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


def sanitize_float_for_json(value: Any) -> Any:
    """
    Sanitize float values for JSON serialization.
    Converts NaN, Infinity, and -Infinity to None.

    Args:
        value: The value to sanitize

    Returns:
        The sanitized value
    """
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None
        return value
    elif isinstance(value, dict):
        return {k: sanitize_float_for_json(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [sanitize_float_for_json(item) for item in value]
    return value


def sanitize_kline_data(kline_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Sanitize K-line data for JSON serialization.
    Specifically handles numeric fields that might contain NaN or Infinity.

    Args:
        kline_data: List of K-line data points

    Returns:
        Sanitized K-line data
    """
    if not kline_data:
        return []

    numeric_fields = ['open', 'high', 'low', 'close', 'volume', 'turn',
                      'preclose', 'pctChg', 'peTTM', 'pbMRQ']

    sanitized_data = []
    for point in kline_data:
        sanitized_point = {}
        for key, value in point.items():
            if key in numeric_fields and isinstance(value, float):
                if math.isnan(value) or math.isinf(value):
                    sanitized_point[key] = None
                else:
                    sanitized_point[key] = value
            else:
                sanitized_point[key] = value
        sanitized_data.append(sanitized_point)

    return sanitized_data


def convert_numpy_types(value: Any) -> Any:
    """
    Convert NumPy types to Python native types for JSON serialization.
    
    Args:
        value: The value to convert
        
    Returns:
        The converted value with Python native types
    """
    if not HAS_NUMPY:
        return value
    
    # Convert NumPy bool_ to Python bool
    if isinstance(value, np.bool_):
        return bool(value)
    # Convert NumPy int types to Python int
    # Use np.integer base class and specific types (avoid np.int_ which was removed in NumPy 2.0)
    elif isinstance(value, (np.integer, np.intc, np.intp, np.int8,
                           np.int16, np.int32, np.int64, np.uint8, np.uint16,
                           np.uint32, np.uint64)):
        return int(value)
    # Convert NumPy float types to Python float
    # Use np.floating base class and specific types (avoid np.float_ which was removed in NumPy 2.0)
    elif isinstance(value, (np.floating, np.float16, np.float32, np.float64)):
        if math.isnan(value) or math.isinf(value):
            return None
        return float(value)
    # Convert NumPy arrays to lists
    elif isinstance(value, np.ndarray):
        return value.tolist()
    # Recursively handle dictionaries
    elif isinstance(value, dict):
        return {k: convert_numpy_types(v) for k, v in value.items()}
    # Recursively handle lists
    elif isinstance(value, (list, tuple)):
        return [convert_numpy_types(item) for item in value]
    
    return value


def sanitize_task_result(task_result: Union[List[Dict[str, Any]], None]) -> Union[List[Dict[str, Any]], None]:
    """
    Sanitize task result for JSON serialization.

    Args:
        task_result: The task result to sanitize

    Returns:
        The sanitized task result
    """
    if task_result is None:
        return None

    sanitized_result = []
    for stock in task_result:
        sanitized_stock = sanitize_float_for_json(stock)
        # Also convert NumPy types
        sanitized_stock = convert_numpy_types(sanitized_stock)

        # 特别处理K线数据
        if 'kline_data' in sanitized_stock and sanitized_stock['kline_data']:
            sanitized_stock['kline_data'] = sanitize_kline_data(
                sanitized_stock['kline_data'])

        sanitized_result.append(sanitized_stock)

    return sanitized_result
