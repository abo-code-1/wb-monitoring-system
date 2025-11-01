"""
Service layer for business intelligence and alerts.
"""
import logging
from typing import Optional, List, Dict, Any
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import models
from .models import Product, BusinessAlert, Settings, AIAdvice
from .ai_service import generate_advice_via_gemini, determine_advice_type, determine_priority

logger = logging.getLogger(__name__)


def generate_business_alerts(user: User) -> int:
    """
    Generate business alerts for all user's products.
    
    Args:
        user: Django User instance
    
    Returns:
        Number of alerts generated
    """
    try:
        settings = Settings.objects.get(user=user)
    except Settings.DoesNotExist:
        settings = Settings.objects.create(user=user)
    
    products = Product.objects.filter(user=user, is_active=True)
    alerts_generated = 0
    
    # Calculate max values for impact score calculation
    max_price = 0
    if products.exists():
        max_price_result = products.aggregate(max_price=models.Max('price'))
        max_price = float(max_price_result['max_price'] or 0)
    
    for product in products:
        alerts_created = []
        
        # OUT OF STOCK Alert
        if product.quantity == 0:
            impact_score = calculate_impact_score(product, max_price, severity_multiplier=1.5)
            estimated_loss = calculate_estimated_loss(product)
            
            alert = BusinessAlert.objects.update_or_create(
                user=user,
                product=product,
                alert_type='OUT_OF_STOCK',
                defaults={
                    'severity': determine_severity(product),
                    'message': f'Product "{product.title}" is out of stock. Potential loss: {estimated_loss:.0f} RUB',
                    'impact_score': impact_score,
                    'estimated_loss': estimated_loss,
                    'is_active': True,
                    'resolved_at': None,
                }
            )[0]
            alerts_created.append(alert)
        
        # LOW STOCK Alert
        elif product.quantity < settings.low_stock_threshold:
            days_of_stock = product.days_of_stock
            impact_score = calculate_impact_score(product, max_price)
            estimated_loss = calculate_estimated_loss(product)
            
            alert = BusinessAlert.objects.update_or_create(
                user=user,
                product=product,
                alert_type='LOW_STOCK',
                defaults={
                    'severity': determine_severity(product),
                    'message': f'Low stock: {product.quantity} units remaining (~{days_of_stock} days)',
                    'impact_score': impact_score,
                    'estimated_loss': estimated_loss,
                    'is_active': True,
                    'resolved_at': None,
                }
            )[0]
            alerts_created.append(alert)
        
        # LOW RATING Alert
        if float(product.rating) < settings.low_rating_threshold:
            impact_score = calculate_impact_score(product, max_price)
            estimated_loss = calculate_estimated_loss(product, rating_penalty=True)
            
            alert = BusinessAlert.objects.update_or_create(
                user=user,
                product=product,
                alert_type='LOW_RATING',
                defaults={
                    'severity': determine_severity(product),
                    'message': f'Low rating: {product.rating:.1f}/5.0 (threshold: {settings.low_rating_threshold:.1f})',
                    'impact_score': impact_score,
                    'estimated_loss': estimated_loss,
                    'is_active': True,
                    'resolved_at': None,
                }
            )[0]
            alerts_created.append(alert)
        
        # DEAD STOCK Alert
        if product.sales_30d == 0 and product.quantity > 0:
            impact_score = product.quantity * 5  # Arbitrary scoring
            estimated_loss = float(product.price) * product.quantity * 0.1  # 10% of inventory value
            
            alert = BusinessAlert.objects.update_or_create(
                user=user,
                product=product,
                alert_type='DEAD_STOCK',
                defaults={
                    'severity': 'MEDIUM',
                    'message': f'Dead stock: Zero sales in 30 days with {product.quantity} units in inventory',
                    'impact_score': impact_score,
                    'estimated_loss': estimated_loss,
                    'is_active': True,
                    'resolved_at': None,
                }
            )[0]
            alerts_created.append(alert)
        
        # Deactivate alerts that are no longer relevant
        active_alerts = BusinessAlert.objects.filter(
            user=user,
            product=product,
            is_active=True
        )
        
        for existing_alert in active_alerts:
            if existing_alert not in alerts_created:
                # Check if condition still exists
                if existing_alert.alert_type == 'OUT_OF_STOCK' and product.quantity > 0:
                    existing_alert.is_active = False
                    existing_alert.resolved_at = timezone.now()
                    existing_alert.save()
                elif existing_alert.alert_type == 'LOW_STOCK' and product.quantity >= settings.low_stock_threshold:
                    existing_alert.is_active = False
                    existing_alert.resolved_at = timezone.now()
                    existing_alert.save()
                elif existing_alert.alert_type == 'LOW_RATING' and product.rating >= settings.low_rating_threshold:
                    existing_alert.is_active = False
                    existing_alert.resolved_at = timezone.now()
                    existing_alert.save()
        
        alerts_generated += len(alerts_created)
    
    logger.info(f"Generated {alerts_generated} business alerts for user {user.username}")
    return alerts_generated


def calculate_impact_score(product: Product, max_price: float, severity_multiplier: float = 1.0) -> float:
    """
    Calculate impact score for a product based on sales, rating, and price.
    
    Args:
        product: Product instance
        max_price: Maximum price across all products
        severity_multiplier: Multiplier for severity adjustment
    
    Returns:
        Impact score (0-100)
    """
    from django.db import models
    
    sales_factor = min(float(product.sales_30d) / 200.0, 1.0)  # Normalize to 0-1
    rating_factor = float(product.rating) / 5.0  # Normalize to 0-1
    price_factor = float(product.price) / max(1, max_price)  # Normalize to 0-1
    
    score = (sales_factor * 50 + rating_factor * 30 + price_factor * 20) * severity_multiplier
    return round(score, 2)


def calculate_estimated_loss(product: Product, rating_penalty: bool = False) -> float:
    """
    Calculate estimated financial loss for a product.
    
    Args:
        product: Product instance
        rating_penalty: Whether to include rating-based penalty
    
    Returns:
        Estimated loss in RUB
    """
    avg_daily_sales = product.sales_7d / 7.0 if product.sales_7d > 0 else 0
    
    if product.quantity == 0 and avg_daily_sales > 0:
        # Estimate loss based on lost sales days
        missing_days = 7  # Assume 7 days of missed sales
        lost_revenue = avg_daily_sales * float(product.price) * missing_days
        return round(lost_revenue, 2)
    
    elif rating_penalty and float(product.rating) < 4.0:
        # Estimate loss from low rating
        penalty_factor = (4.0 - float(product.rating)) / 1.0  # 0-1 penalty
        estimated_loss = float(product.sales_30d) * float(product.price) * penalty_factor * 0.1
        return round(estimated_loss, 2)
    
    return 0.0


def determine_severity(product: Product) -> str:
    """
    Determine alert severity based on product metrics.
    
    Args:
        product: Product instance
    
    Returns:
        Severity level string
    """
    # Critical: Out of stock with high sales
    if product.quantity == 0 and product.sales_30d > 50:
        return 'CRITICAL'
    
    # High: Low stock with high sales
    if product.quantity < 5 and product.sales_30d > 30:
        return 'HIGH'
    
    # High: Very low rating with good sales
    if float(product.rating) < 3.0 and product.sales_30d > 20:
        return 'HIGH'
    
    # Medium: Low stock or low rating with moderate sales
    if (product.quantity < 10 or float(product.rating) < 4.0) and product.sales_30d > 10:
        return 'MEDIUM'
    
    # Low: Low stock or low rating but minimal sales
    return 'LOW'


def diagnose_sales_drop(product: Product) -> Optional[str]:
    """
    Diagnose the cause of sales drop by comparing snapshots.
    
    Args:
        product: Product instance
    
    Returns:
        Diagnosis text or None
    """
    from django.utils import timezone
    from .models import ProductSnapshot
    
    # Get last 2 snapshots
    snapshots = ProductSnapshot.objects.filter(
        product=product
    ).order_by('-snapshot_at')[:2]
    
    if len(snapshots) < 2:
        return None
    
    latest = snapshots[0]
    previous = snapshots[1]
    
    # Check if sales dropped significantly
    if latest.sales_7d < previous.sales_7d * 0.6:
        # Find the cause
        if latest.quantity < previous.quantity:
            return "Stock levels decreased significantly"
        elif latest.rating < previous.rating - 0.2:
            return "Bad reviews causing rating decline"
        elif latest.price > previous.price * 1.05:
            return "Price increase made product less competitive"
        else:
            return "Sales declining due to unknown factors"
    
    return None


def generate_ai_advice(user: User) -> int:
    """
    Generate AI advice for top priority alerts.
    
    Args:
        user: Django User instance
    
    Returns:
        Number of AI advice entries generated
    """
    # Get top 20 highest priority active alerts
    top_alerts = BusinessAlert.objects.filter(
        user=user,
        is_active=True
    ).order_by('-impact_score', '-severity')[:20]
    
    advice_generated = 0
    
    for alert in top_alerts:
        try:
            # Check if advice already exists for this alert
            existing = AIAdvice.objects.filter(
                user=user,
                alert=alert,
                status__in=['NEW', 'SHOWN']
            ).first()
            
            if existing:
                continue  # Skip if advice already exists
            
            # Generate advice via Gemini
            advice_text = generate_advice_via_gemini(alert.product, [alert])
            advice_type = determine_advice_type(alert.product, [alert])
            priority = determine_priority(alert.product, [alert])
            
            # Create AI advice entry
            AIAdvice.objects.create(
                user=user,
                product=alert.product,
                alert=alert,
                advice_type=advice_type,
                advice_text=advice_text,
                priority=priority,
                status='NEW',
            )
            
            advice_generated += 1
            
        except Exception as e:
            logger.error(f"Error generating AI advice for alert {alert.id}: {e}")
            continue
    
    logger.info(f"Generated {advice_generated} AI advice entries for user {user.username}")
    return advice_generated


def get_products_data(user: User) -> List[Dict[str, Any]]:
    """
    Get all products data for dashboard display.
    
    Args:
        user: Django User instance
    
    Returns:
        List of product dictionaries
    """
    from .utils import calculate_stock_status, generate_alerts
    
    products = Product.objects.filter(user=user, is_active=True)
    
    # Get user settings for calculations
    try:
        settings = Settings.objects.get(user=user)
        low_stock_threshold = settings.low_stock_threshold
        low_rating_threshold = settings.low_rating_threshold
    except Settings.DoesNotExist:
        low_stock_threshold = 10
        low_rating_threshold = 4.0
    
    data = []
    for product in products:
        stock_status = calculate_stock_status(product.quantity, low_stock_threshold)
        alerts = generate_alerts(
            float(product.rating),
            product.quantity,
            low_rating_threshold,
            low_stock_threshold
        )
        
        data.append({
            'nm_id': product.nm_id,
            'nmId': product.nm_id,  # Also include for backward compatibility
            'title': product.title,
            'brand': product.brand,
            'category': product.category,
            'price': float(product.price),
            'rating': float(product.rating),
            'feedbacks': product.feedbacks,
            'quantity': product.quantity,
            'sales_7d': product.sales_7d,
            'sales_30d': product.sales_30d,
            'storage_cost': float(product.storage_cost) if product.storage_cost else None,
            'days_of_stock': product.days_of_stock,
            'is_sample': product.is_sample,
            'stock_status': stock_status,
            'alerts': alerts,
        })
    
    return data


def get_dashboard_data(user: User) -> List[Dict[str, Any]]:
    """
    Get dashboard data (alias for get_products_data for backward compatibility).
    
    Args:
        user: Django User instance
    
    Returns:
        List of product dictionaries
    """
    return get_products_data(user)
