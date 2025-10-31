"""
Utility functions for WBMonitor dashboard.
"""
from typing import Any, Dict, Optional


def safe_get(data: Dict, key: str, default: Any = None) -> Any:
    """Safely get a value from a dictionary with a default."""
    return data.get(key, default)


def safe_float(value: Any, default: float = 0.0) -> float:
    """Safely convert a value to float, returning default if conversion fails."""
    try:
        return float(value) if value is not None and value != '' else default
    except (ValueError, TypeError):
        return default


def safe_int(value: Any, default: int = 0) -> int:
    """Safely convert a value to int, returning default if conversion fails."""
    try:
        return int(value) if value is not None and value != '' else default
    except (ValueError, TypeError):
        return default


def safe_str(value: Any, default: str = "N/A") -> str:
    """Safely convert a value to string, returning default if conversion fails."""
    if value is None or value == '':
        return default
    return str(value)


def calculate_stock_status(quantity: Optional[int], low_stock_threshold: int = 10) -> str:
    """
    Calculate stock status based on quantity.
    
    Args:
        quantity: Product quantity
        low_stock_threshold: Threshold for 'Low Stock' status
    
    Returns:
        'Out of Stock', 'Low Stock', or 'In Stock'
    """
    if quantity is None:
        return "N/A"
    
    qty = safe_int(quantity, 0)
    if qty == 0:
        return "Out of Stock"
    elif qty < low_stock_threshold:
        return "Low Stock"
    else:
        return "In Stock"


def calculate_cost_percentage(price: Optional[float], storage_cost: Optional[float]) -> Optional[float]:
    """
    Calculate storage cost as percentage of price.
    
    Args:
        price: Product price
        storage_cost: Storage cost
    
    Returns:
        Percentage or None if calculation not possible
    """
    price_val = safe_float(price)
    cost_val = safe_float(storage_cost)
    
    if price_val == 0 or price_val is None:
        return None
    
    return (cost_val / price_val) * 100 if cost_val is not None else None


def generate_alerts(
    rating: Optional[float],
    quantity: Optional[int],
    low_rating_threshold: float = 4.0,
    low_stock_threshold: int = 10
) -> list:
    """
    Generate list of alerts for a product.
    
    Args:
        rating: Product rating
        quantity: Product quantity
        low_rating_threshold: Threshold for low rating alert
        low_stock_threshold: Threshold for low stock alert
    
    Returns:
        List of alert strings
    """
    alerts = []
    
    rating_val = safe_float(rating)
    qty = safe_int(quantity, 0)
    
    if rating_val and rating_val < low_rating_threshold:
        alerts.append("low_rating")
    
    if qty == 0:
        alerts.append("out_of_stock")
    elif qty < low_stock_threshold:
        alerts.append("low_stock")
    
    return alerts


def format_price(price: Optional[float]) -> str:
    """Format price for display."""
    if price is None:
        return "N/A"
    return f"{safe_float(price):,.2f} ₽"


def format_percentage(value: Optional[float], decimals: int = 2) -> str:
    """Format percentage for display."""
    if value is None:
        return "N/A"
    return f"{safe_float(value):.{decimals}f}%"

