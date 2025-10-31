"""
Models for WBMonitor dashboard.
"""
from django.db import models
from django.contrib.auth.models import User


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


class SampleProduct(models.Model):
    """Sample product data for testing/development when APIs are unavailable."""
    nmId = models.BigIntegerField(unique=True, help_text="Wildberries product ID")
    title = models.CharField(max_length=500, help_text="Product title")
    brand = models.CharField(max_length=255, help_text="Product brand")
    rating = models.FloatField(null=True, blank=True, help_text="Product rating (0-5)")
    feedbacks = models.IntegerField(default=0, help_text="Number of feedbacks/reviews")
    quantity = models.IntegerField(default=0, help_text="Stock quantity")
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Product price")
    storage_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Storage cost")
    is_active = models.BooleanField(default=True, help_text="Whether this sample product should be used")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['nmId']
        verbose_name = "Sample Product"
        verbose_name_plural = "Sample Products"

    def __str__(self):
        return f"{self.brand} - {self.title} (nmId: {self.nmId})"

