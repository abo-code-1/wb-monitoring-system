"""
AI Service for generating business advice using Google Gemini 1.5 Pro.
"""
import logging
import google.generativeai as genai
from django.conf import settings
from typing import Optional, Dict, Any
from .models import Product, AIAdvice

logger = logging.getLogger(__name__)

# Configure Gemini API
try:
    GEMINI_API_KEY = getattr(settings, 'GEMINI_API_KEY', None)
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
    else:
        logger.warning("GEMINI_API_KEY not found in settings. AI features will use fallback responses.")
except Exception as e:
    logger.error(f"Error configuring Gemini API: {e}")


def generate_advice_via_gemini(product: Product, alerts: list = None) -> str:
    """
    Generate AI business advice for a product using Google Gemini.
    
    Args:
        product: Product instance
        alerts: List of active alerts for this product (optional)
    
    Returns:
        AI-generated advice text
    """
    # Check if API key is configured
    if not GEMINI_API_KEY:
        return generate_fallback_advice(product, alerts)
    
    try:
        # Build context about the product
        alerts_text = ""
        if alerts:
            alert_types = [alert.get_alert_type_display() for alert in alerts]
            alerts_text = f"\nActive Alerts: {', '.join(alert_types)}"
        
        days_of_stock = product.days_of_stock if hasattr(product, 'days_of_stock') else None
        days_text = f"\nDays of Stock: {days_of_stock}" if days_of_stock else ""
        
        # Construct prompt
        prompt = f"""
You are an experienced Wildberries marketplace consultant with deep expertise in e-commerce optimization.

Analyze this product and provide 1-2 practical, actionable recommendations to improve sales performance, reduce costs, or mitigate risks. Be concise and business-focused.

Product Information:
---
Title: {product.title}
Category: {product.category}
Brand: {product.brand}
Rating: {product.rating}/5.0
Feedbacks: {product.feedbacks}
Price: {product.price} RUB
Stock Quantity: {product.quantity}
Sales (7 days): {product.sales_7d} units
Sales (30 days): {product.sales_30d} units
Storage Cost: {product.storage_cost} RUB{days_text}{alerts_text}
---

Provide your professional recommendation in 1-2 sentences. Be specific and actionable.
Focus on the most critical issue first.
"""
        
        # Generate content using Gemini
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        
        advice_text = response.text.strip()
        logger.info(f"Generated Gemini advice for product {product.nm_id}")
        
        return advice_text
        
    except Exception as e:
        logger.error(f"Error generating Gemini advice: {type(e).__name__}: {e}", exc_info=True)
        return generate_fallback_advice(product, alerts)


def generate_fallback_advice(product: Product, alerts: list = None) -> str:
    """
    Generate fallback advice when Gemini API is unavailable.
    
    Args:
        product: Product instance
        alerts: List of active alerts (optional)
    
    Returns:
        Rule-based advice text
    """
    advice_parts = []
    
    # Check stock level
    if product.quantity == 0:
        advice_parts.append("URGENT: Product is out of stock. Restock immediately to avoid losing sales.")
    elif product.quantity < 10:
        days = product.days_of_stock if hasattr(product, 'days_of_stock') else None
        if days and days < 3:
            advice_parts.append(f"Critical: Low stock ({product.quantity} units, {days} days remaining). Restock to prevent stockouts.")
        else:
            advice_parts.append(f"Low stock alert: {product.quantity} units remaining. Consider restocking.")
    
    # Check rating
    if product.rating < 4.0:
        if product.rating < 3.0:
            advice_parts.append("CRITICAL: Rating is very low ({:.1f}/5.0). Investigate product quality issues and customer complaints immediately.")
        else:
            advice_parts.append("Rating below threshold ({:.1f}/5.0). Review negative feedbacks and improve product quality.")
    
    # Check sales performance
    if product.sales_7d == 0 and product.quantity > 0:
        advice_parts.append("Zero sales in 7 days despite having stock. Consider promotional pricing or listing optimization.")
    elif product.sales_30d > 0 and product.sales_7d < product.sales_30d * 0.6:
        advice_parts.append("Sales declining: 7-day sales down ~40%. Check for pricing, rating, or competition issues.")
    
    # Check storage cost efficiency
    if product.storage_cost and product.price:
        cost_pct = (float(product.storage_cost) / float(product.price)) * 100
        if cost_pct > 5:
            advice_parts.append(f"Storage costs are high ({cost_pct:.1f}% of price). Optimize inventory turnover.")
    
    # Default advice if no issues detected
    if not advice_parts:
        advice_parts.append("Product performing well. Continue monitoring key metrics.")
    
    return " ".join(advice_parts)


def determine_advice_type(product: Product, alerts: list = None) -> str:
    """
    Determine the type of advice based on product status and alerts.
    
    Args:
        product: Product instance
        alerts: List of active alerts (optional)
    
    Returns:
        Advice type string
    """
    if alerts:
        alert_types = [alert.alert_type for alert in alerts]
        
        if 'OUT_OF_STOCK' in alert_types or 'LOW_STOCK' in alert_types:
            return 'RESTOCK'
        elif 'LOW_RATING' in alert_types:
            return 'FIX_RATING'
        elif 'HIGH_VALUE_AT_RISK' in alert_types:
            return 'PROMOTE'
    
    # Analyze product metrics
    if product.quantity == 0:
        return 'RESTOCK'
    elif product.rating < 4.0:
        return 'FIX_RATING'
    elif product.sales_7d < 3:
        return 'PROMOTE'
    else:
        return 'IMPROVE_LISTING'


def determine_priority(product: Product, alerts: list = None) -> int:
    """
    Determine priority score (1-5, 1=highest) for AI advice.
    
    Args:
        product: Product instance
        alerts: List of active alerts (optional)
    
    Returns:
        Priority integer 1-5
    """
    priority = 5  # Default: lowest priority
    
    if alerts:
        for alert in alerts:
            if alert.severity == 'CRITICAL':
                return 1
            elif alert.severity == 'HIGH':
                priority = min(priority, 2)
            elif alert.severity == 'MEDIUM':
                priority = min(priority, 3)
            elif alert.severity == 'LOW':
                priority = min(priority, 4)
    
    # Check critical conditions
    if product.quantity == 0 and product.sales_30d > 0:
        return 1  # Out of stock for popular product
    elif product.rating < 3.0 and product.sales_30d > 10:
        return 2  # Very low rating for popular product
    elif product.quantity < 5 and product.sales_30d > 20:
        return 2  # Very low stock for popular product
    
    return priority

