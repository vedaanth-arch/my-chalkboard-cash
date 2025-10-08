"""
AIPS - AI-Driven Penny Stock Validation System
Utility functions and helpers
"""

import os
import logging
import yaml
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import pandas as pd
import numpy as np


def setup_logging(log_level: str = "INFO", log_file: str = None):
    """Setup logging configuration"""
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    handlers = [logging.StreamHandler()]
    
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        handlers=handlers
    )
    
    return logging.getLogger("AIPS")


def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """Load configuration from YAML file"""
    try:
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
        return config
    except Exception as e:
        logging.error(f"Error loading config: {e}")
        return {}


def ensure_directories():
    """Create necessary directories if they don't exist"""
    directories = ['reports', 'logs', 'data', 'cache']
    for directory in directories:
        os.makedirs(directory, exist_ok=True)


def format_indian_currency(amount: float) -> str:
    """Format amount in Indian numbering system (Lakhs/Crores)"""
    if pd.isna(amount) or amount == 0:
        return "₹0"
    
    if abs(amount) >= 10000000:  # Crores
        return f"₹{amount/10000000:.2f} Cr"
    elif abs(amount) >= 100000:  # Lakhs
        return f"₹{amount/100000:.2f} L"
    elif abs(amount) >= 1000:  # Thousands
        return f"₹{amount/1000:.2f} K"
    else:
        return f"₹{amount:.2f}"


def calculate_percentage_change(old_value: float, new_value: float) -> float:
    """Calculate percentage change between two values"""
    if pd.isna(old_value) or pd.isna(new_value) or old_value == 0:
        return np.nan
    return ((new_value - old_value) / abs(old_value)) * 100


def get_indian_stock_symbol(symbol: str, exchange: str = "NSE") -> str:
    """Convert stock symbol to Yahoo Finance format for Indian stocks"""
    symbol = symbol.upper().strip()
    
    # Remove existing suffix if any
    symbol = symbol.replace('.NS', '').replace('.BO', '')
    
    # Add appropriate suffix
    if exchange.upper() == "NSE":
        return f"{symbol}.NS"
    elif exchange.upper() == "BSE":
        return f"{symbol}.BO"
    else:
        return f"{symbol}.NS"  # Default to NSE


def safe_divide(numerator: float, denominator: float, default: float = np.nan) -> float:
    """Safely divide two numbers, returning default if denominator is zero"""
    try:
        if pd.isna(numerator) or pd.isna(denominator) or denominator == 0:
            return default
        return numerator / denominator
    except:
        return default


def calculate_cagr(start_value: float, end_value: float, years: float) -> float:
    """Calculate Compound Annual Growth Rate"""
    try:
        if start_value <= 0 or end_value <= 0 or years <= 0:
            return np.nan
        return (pow(end_value / start_value, 1 / years) - 1) * 100
    except:
        return np.nan


def get_date_range(period_days: int):
    """Get start and end dates for a period"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=period_days)
    return start_date, end_date


def clean_numeric_value(value: Any) -> float:
    """Clean and convert value to float"""
    try:
        if pd.isna(value):
            return np.nan
        if isinstance(value, str):
            # Remove common symbols and convert
            value = value.replace(',', '').replace('₹', '').replace('%', '').strip()
        return float(value)
    except:
        return np.nan


def generate_timestamp() -> str:
    """Generate timestamp string for filenames"""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


class ProgressTracker:
    """Track progress of stock validation"""
    
    def __init__(self, total: int):
        self.total = total
        self.current = 0
        self.success = 0
        self.failed = 0
        self.start_time = datetime.now()
    
    def update(self, success: bool = True):
        """Update progress"""
        self.current += 1
        if success:
            self.success += 1
        else:
            self.failed += 1
    
    def get_status(self) -> str:
        """Get current status string"""
        elapsed = (datetime.now() - self.start_time).total_seconds()
        percent = (self.current / self.total) * 100 if self.total > 0 else 0
        
        return (f"Progress: {self.current}/{self.total} ({percent:.1f}%) | "
                f"Success: {self.success} | Failed: {self.failed} | "
                f"Time: {elapsed:.1f}s")


def validate_stock_symbol(symbol: str) -> bool:
    """Basic validation of stock symbol format"""
    if not symbol or not isinstance(symbol, str):
        return False
    
    # Remove suffix for validation
    symbol = symbol.replace('.NS', '').replace('.BO', '').strip()
    
    # Check if alphanumeric and reasonable length
    return symbol.isalnum() and 1 <= len(symbol) <= 20


def categorize_market_cap(market_cap: float) -> str:
    """Categorize company by market capitalization (Indian standards)"""
    if pd.isna(market_cap):
        return "Unknown"
    
    # Convert to crores
    market_cap_cr = market_cap / 10000000
    
    if market_cap_cr >= 20000:
        return "Large Cap"
    elif market_cap_cr >= 5000:
        return "Mid Cap"
    elif market_cap_cr >= 500:
        return "Small Cap"
    else:
        return "Micro Cap"
