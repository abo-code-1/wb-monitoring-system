"""
Models for WBMonitor dashboard - Complete business intelligence system.
"""
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class WBToken(models.Model):
    """Stores API tokens for Wildberries APIs per user."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wb_tokens')
    content_token = models.CharField(max_length=1000, blank=True, help_text="Content API token")
    stats_token = models.CharField(max_length=1000, blank=True, help_text="Statistics API token")
    prices_token = models.CharField(max_length=1000, blank=True, help_text="Prices API token")
    analytics_token = models.CharField(max_length=1000, blank=True, help_text="Analytics API token (optional)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user']
        verbose_name = "WB Token"
        verbose_name_plural = "WB Tokens"

    def __str__(self):
        return f"Tokens for {self.user.username}"


class Settings(models.Model):
    """User-specific settings for dashboard preferences."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='dashboard_settings')
    low_stock_threshold = models.IntegerField(default=10, help_text="Quantity threshold for 'Low Stock' alert")
    low_rating_threshold = models.FloatField(default=4.0, help_text="Rating threshold for 'Low Rating' alert")
    items_per_page = models.IntegerField(default=50, help_text="Items per page in dashboard")
    default_sort = models.CharField(max_length=50, default='nmId', help_text="Default sort column")
    default_sort_order = models.CharField(max_length=5, default='asc', choices=[('asc', 'Ascending'), ('desc', 'Descending')])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Setting"
        verbose_name_plural = "Settings"

    def __str__(self):
        return f"Settings for {self.user.username}"


class Product(models.Model):
    """Main product table with comprehensive metrics."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='products')
    nm_id = models.BigIntegerField(help_text="Wildberries product ID")
    title = models.CharField(max_length=500, help_text="Product title")
    brand = models.CharField(max_length=255, help_text="Product brand")
    category = models.CharField(max_length=255, help_text="Product category")
    price = models.DecimalField(max_digits=12, decimal_places=2, help_text="Product price in RUB")
    rating = models.DecimalField(max_digits=3, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(5)], help_text="Product rating 0-5")
    feedbacks = models.IntegerField(default=0, help_text="Number of feedbacks/reviews")
    quantity = models.IntegerField(default=0, help_text="Stock quantity")
    sales_7d = models.IntegerField(default=0, help_text="Sales in last 7 days")
    sales_30d = models.IntegerField(default=0, help_text="Sales in last 30 days")
    storage_cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="Storage cost")
    is_active = models.BooleanField(default=True, help_text="Whether product is active")
    is_sample = models.BooleanField(default=False, help_text="Whether this is sample data")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        verbose_name = "Product"
        verbose_name_plural = "Products"
        indexes = [
            models.Index(fields=['user', 'nm_id']),
            models.Index(fields=['category']),
        ]

    def __str__(self):
        return f"{self.brand} - {self.title} ({self.nm_id})"

    @property
    def days_of_stock(self):
        """Calculate days of stock remaining."""
        if self.sales_7d > 0:
            return round(self.quantity / max(1, self.sales_7d / 7), 1)
        return None


class ProductSnapshot(models.Model):
    """Historical snapshot of product metrics for trend analysis."""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='snapshots')
    snapshot_at = models.DateTimeField(help_text="Timestamp of snapshot")
    price = models.DecimalField(max_digits=12, decimal_places=2)
    rating = models.DecimalField(max_digits=3, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(5)])
    quantity = models.IntegerField()
    feedbacks = models.IntegerField()
    sales_7d = models.IntegerField()
    sales_30d = models.IntegerField()
    storage_cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    stock_status = models.CharField(max_length=20, help_text="Stock status at snapshot time")

    class Meta:
        ordering = ['-snapshot_at']
        verbose_name = "Product Snapshot"
        verbose_name_plural = "Product Snapshots"
        indexes = [
            models.Index(fields=['product', '-snapshot_at']),
        ]

    def __str__(self):
        return f"Snapshot {self.product.nm_id} at {self.snapshot_at}"


class BusinessAlert(models.Model):
    """Business intelligence alerts for products."""
    ALERT_TYPE_CHOICES = [
        ('OUT_OF_STOCK', 'Out of Stock'),
        ('LOW_STOCK', 'Low Stock'),
        ('LOW_RATING', 'Low Rating'),
        ('DEAD_STOCK', 'Dead Stock'),
        ('HIGH_VALUE_AT_RISK', 'High Value at Risk'),
    ]
    SEVERITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='business_alerts')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='business_alerts')
    alert_type = models.CharField(max_length=50, choices=ALERT_TYPE_CHOICES)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    message = models.TextField(help_text="Alert message")
    impact_score = models.FloatField(default=0.0, help_text="Impact score 0-100")
    estimated_loss = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True, help_text="Estimated financial loss")
    detected_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-impact_score', '-detected_at']
        verbose_name = "Business Alert"
        verbose_name_plural = "Business Alerts"
        indexes = [
            models.Index(fields=['user', 'is_active', '-impact_score']),
            models.Index(fields=['alert_type', 'severity']),
        ]

    def __str__(self):
        return f"{self.get_alert_type_display()} - {self.product.title} ({self.severity})"


class AIAdvice(models.Model):
    """AI-generated business advice for products."""
    ADVICE_TYPE_CHOICES = [
        ('RESTOCK', 'Restock Product'),
        ('CHANGE_PRICE', 'Change Price'),
        ('FIX_RATING', 'Fix Rating'),
        ('IMPROVE_LISTING', 'Improve Listing'),
        ('PROMOTE', 'Promote Product'),
    ]
    STATUS_CHOICES = [
        ('NEW', 'New'),
        ('SHOWN', 'Shown'),
        ('APPLIED', 'Applied'),
        ('IGNORED', 'Ignored'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ai_advices')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='ai_advices')
    alert = models.ForeignKey(BusinessAlert, on_delete=models.SET_NULL, null=True, blank=True, related_name='ai_advices')
    advice_type = models.CharField(max_length=50, choices=ADVICE_TYPE_CHOICES)
    advice_text = models.TextField(help_text="AI-generated advice")
    priority = models.IntegerField(default=3, help_text="Priority 1-5 (1=highest)")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='NEW')
    created_at = models.DateTimeField(auto_now_add=True)
    applied_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['priority', '-created_at']
        verbose_name = "AI Advice"
        verbose_name_plural = "AI Advices"
        indexes = [
            models.Index(fields=['user', 'status', 'priority']),
        ]

    def __str__(self):
        return f"AI Advice for {self.product.title} ({self.get_advice_type_display()})"


class Competitor(models.Model):
    """Tracks competitor products/sellers."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='competitors')
    url = models.URLField(max_length=500, help_text="Wildberries product URL or seller profile")
    name = models.CharField(max_length=255, help_text="Competitor name or identifier")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Competitor"
        verbose_name_plural = "Competitors"

    def __str__(self):
        return f"{self.name} ({self.user.username})"


class APICallLog(models.Model):
    """Diagnostic log for API calls."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='api_call_logs', null=True, blank=True)
    endpoint = models.CharField(max_length=255)
    status_code = models.IntegerField(null=True, blank=True)
    response_time_ms = models.IntegerField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "API Call Log"
        verbose_name_plural = "API Call Logs"

    def __str__(self):
        return f"{self.endpoint} - {self.status_code or 'Error'} at {self.created_at}"
