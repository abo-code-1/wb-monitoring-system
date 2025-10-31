"""
Service layer for fetching and merging Wildberries API data.
"""
import logging
import requests
import pandas as pd
from typing import Optional, List, Dict, Any
from django.core.cache import cache
from django.contrib.auth.models import User
from dashboard.models import WBToken, Settings, SampleProduct
from dashboard.utils import (
    safe_float, safe_int, safe_str,
    calculate_stock_status, calculate_cost_percentage, generate_alerts
)

logger = logging.getLogger(__name__)


class WBDataFetcher:
    """
    Central class for fetching data from all four Wildberries APIs.
    Each method returns a clean Pandas DataFrame or empty DataFrame if API fails.
    """
    
    def __init__(self, user: User):
        """
        Initialize fetcher with user's API tokens.
        
        Args:
            user: Django User instance
        """
        self.user = user
        try:
            self.tokens = WBToken.objects.get(user=user)
        except WBToken.DoesNotExist:
            self.tokens = None
        
        # Base URLs for Wildberries APIs
        self.content_base_url = "https://content-api.wildberries.ru/content/v2"
        self.stats_base_url = "https://statistics-api.wildberries.ru/api/v1"
        self.prices_base_url = "https://common-api.wildberries.ru/api/v1"
        self.analytics_base_url = "https://seller-analytics-api.wildberries.ru/api/v1"
    
    def _get_headers(self, token: Optional[str]) -> Dict[str, str]:
        """Get headers for API requests."""
        if not token:
            return {}
        return {
            "Authorization": token,
            "Content-Type": "application/json"
        }
    
    def fetch_content_data(self) -> pd.DataFrame:
        """
        Fetch product content data (titles, brands, ratings, feedbacks).
        Returns DataFrame with columns: ['nmId', 'title', 'brand', 'rating', 'feedbacks']
        """
        if not self.tokens or not self.tokens.content_token:
            return pd.DataFrame()
        
        try:
            # Example endpoint - adjust based on actual WB Content API
            url = f"{self.content_base_url}/get/cards/list"
            headers = self._get_headers(self.tokens.content_token)
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if not data or 'cards' not in data:
                return pd.DataFrame()
            
            # Transform API response to DataFrame
            rows = []
            for item in data.get('cards', []):
                # Extract nmId from various possible fields
                nm_id = item.get('nmID') or item.get('nmId') or item.get('nm_id')
                if not nm_id:
                    continue
                
                rows.append({
                    'nmId': int(nm_id),
                    'title': safe_str(item.get('title'), 'N/A'),
                    'brand': safe_str(item.get('brand'), 'N/A'),
                    'rating': safe_float(item.get('rating'), None),
                    'feedbacks': safe_int(item.get('feedbacksCount') or item.get('feedbacks'), 0),
                })
            
            if not rows:
                return pd.DataFrame()
            
            return pd.DataFrame(rows)
        
        except requests.exceptions.RequestException as e:
            logger.warning(f"Failed to fetch content data: {type(e).__name__}: {e}")
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Unexpected error fetching content data: {type(e).__name__}: {e}", exc_info=True)
            return pd.DataFrame()
    
    def fetch_statistics_data(self) -> pd.DataFrame:
        """
        Fetch real-time stock statistics.
        Returns DataFrame with columns: ['nmId', 'quantity']
        """
        if not self.tokens or not self.tokens.stats_token:
            return pd.DataFrame()
        
        try:
            # Example endpoint - adjust based on actual WB Statistics API
            url = f"{self.stats_base_url}/supplier/stocks"
            headers = self._get_headers(self.tokens.stats_token)
            
            from datetime import datetime
            params = {
                'dateFrom': datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if not data or not isinstance(data, list):
                return pd.DataFrame()
            
            # Transform API response to DataFrame
            rows = []
            for item in data:
                nm_id = item.get('nmID') or item.get('nmId') or item.get('nm_id')
                if not nm_id:
                    continue
                
                rows.append({
                    'nmId': int(nm_id),
                    'quantity': safe_int(item.get('quantity') or item.get('qty'), 0),
                })
            
            if not rows:
                return pd.DataFrame()
            
            return pd.DataFrame(rows)
        
        except requests.exceptions.RequestException as e:
            logger.warning(f"Failed to fetch statistics data: {type(e).__name__}: {e}")
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Unexpected error fetching statistics data: {type(e).__name__}: {e}", exc_info=True)
            return pd.DataFrame()
    
    def fetch_prices_data(self) -> pd.DataFrame:
        """
        Fetch prices and discounts.
        Returns DataFrame with columns: ['nmId', 'price']
        """
        if not self.tokens or not self.tokens.prices_token:
            return pd.DataFrame()
        
        try:
            # Example endpoint - adjust based on actual WB Prices API
            url = f"{self.prices_base_url}/info"
            headers = self._get_headers(self.tokens.prices_token)
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if not data or not isinstance(data, list):
                return pd.DataFrame()
            
            # Transform API response to DataFrame
            rows = []
            for item in data:
                nm_id = item.get('nmID') or item.get('nmId') or item.get('nm_id')
                if not nm_id:
                    continue
                
                # Extract price from various possible fields
                price = item.get('price') or item.get('salePrice') or item.get('sale_price')
                
                rows.append({
                    'nmId': int(nm_id),
                    'price': safe_float(price, None),
                })
            
            if not rows:
                return pd.DataFrame()
            
            return pd.DataFrame(rows)
        
        except requests.exceptions.RequestException as e:
            logger.warning(f"Failed to fetch prices data: {type(e).__name__}: {e}")
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Unexpected error fetching prices data: {type(e).__name__}: {e}", exc_info=True)
            return pd.DataFrame()
    
    def fetch_analytics_data(self) -> pd.DataFrame:
        """
        Fetch storage costs from Analytics API (optional).
        Returns DataFrame with columns: ['nmId', 'storage_cost']
        """
        if not self.tokens or not self.tokens.analytics_token:
            return pd.DataFrame()
        
        try:
            # Example endpoint - adjust based on actual WB Analytics API
            url = f"{self.analytics_base_url}/paid_storage"
            headers = self._get_headers(self.tokens.analytics_token)
            
            from datetime import datetime, timedelta
            date_to = datetime.now()
            date_from = date_to - timedelta(days=7)
            
            params = {
                'dateFrom': date_from.strftime('%Y-%m-%d'),
                'dateTo': date_to.strftime('%Y-%m-%d'),
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if not data or not isinstance(data, list):
                return pd.DataFrame()
            
            # Transform API response to DataFrame
            rows = []
            for item in data:
                nm_id = item.get('nmID') or item.get('nmId') or item.get('nm_id')
                if not nm_id:
                    continue
                
                storage_cost = item.get('storageCost') or item.get('storage_cost') or item.get('cost') or item.get('total')
                
                rows.append({
                    'nmId': int(nm_id),
                    'storage_cost': safe_float(storage_cost, None),
                })
            
            if not rows:
                return pd.DataFrame()
            
            return pd.DataFrame(rows)
        
        except requests.exceptions.RequestException as e:
            logger.warning(f"Failed to fetch analytics data: {type(e).__name__}: {e}")
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Unexpected error fetching analytics data: {type(e).__name__}: {e}", exc_info=True)
            return pd.DataFrame()
    
    def fetch_and_merge_all(self) -> pd.DataFrame:
        """
        Fetch from all four APIs and merge into one unified DataFrame.
        Returns DataFrame with columns: ['nmId', 'title', 'brand', 'rating', 'feedbacks',
                                         'quantity', 'price', 'storage_cost', 'stock_status',
                                         'cost_percentage', 'alerts']
        """
        # Fetch from all APIs in parallel (or sequentially)
        content_df = self.fetch_content_data()
        stats_df = self.fetch_statistics_data()
        prices_df = self.fetch_prices_data()
        analytics_df = self.fetch_analytics_data()
        
        # Start with content data as base (or stats if content is empty)
        if not content_df.empty:
            merged_df = content_df.copy()
        elif not stats_df.empty:
            merged_df = stats_df[['nmId']].copy()
            merged_df['title'] = 'N/A'
            merged_df['brand'] = 'N/A'
            merged_df['rating'] = None
            merged_df['feedbacks'] = 0
        elif not prices_df.empty:
            merged_df = prices_df[['nmId']].copy()
            merged_df['title'] = 'N/A'
            merged_df['brand'] = 'N/A'
            merged_df['rating'] = None
            merged_df['feedbacks'] = 0
        else:
            # No data from any API
            return pd.DataFrame(columns=['nmId', 'title', 'brand', 'rating', 'feedbacks',
                                        'quantity', 'price', 'storage_cost', 'stock_status',
                                        'cost_percentage', 'alerts'])
        
        # Merge statistics (quantity)
        if not stats_df.empty:
            merged_df = merged_df.merge(stats_df[['nmId', 'quantity']], on='nmId', how='left')
        else:
            merged_df['quantity'] = None
        
        # Merge prices
        if not prices_df.empty:
            merged_df = merged_df.merge(prices_df[['nmId', 'price']], on='nmId', how='left')
        else:
            merged_df['price'] = None
        
        # Merge analytics (storage_cost)
        if not analytics_df.empty:
            merged_df = merged_df.merge(analytics_df[['nmId', 'storage_cost']], on='nmId', how='left')
        else:
            merged_df['storage_cost'] = None
        
        # Fill missing values with defaults
        if 'quantity' in merged_df.columns:
            merged_df['quantity'] = merged_df['quantity'].fillna(0)
            merged_df['quantity'] = pd.to_numeric(merged_df['quantity'], errors='coerce').fillna(0).astype(int)
        
        if 'price' in merged_df.columns:
            merged_df['price'] = merged_df['price'].fillna(0)
        
        if 'storage_cost' in merged_df.columns:
            merged_df['storage_cost'] = merged_df['storage_cost'].fillna(0)
        
        if 'title' in merged_df.columns:
            merged_df['title'] = merged_df['title'].fillna('N/A')
        
        if 'brand' in merged_df.columns:
            merged_df['brand'] = merged_df['brand'].fillna('N/A')
        
        if 'rating' in merged_df.columns:
            merged_df['rating'] = merged_df['rating'].fillna(0)
        
        if 'feedbacks' in merged_df.columns:
            merged_df['feedbacks'] = merged_df['feedbacks'].fillna(0)
            merged_df['feedbacks'] = pd.to_numeric(merged_df['feedbacks'], errors='coerce').fillna(0).astype(int)
        
        # Get user settings for thresholds
        try:
            settings = Settings.objects.get(user=self.user)
            low_stock_threshold = settings.low_stock_threshold
            low_rating_threshold = settings.low_rating_threshold
        except Settings.DoesNotExist:
            low_stock_threshold = 10
            low_rating_threshold = 4.0
        
        # Calculate derived fields
        merged_df['stock_status'] = merged_df['quantity'].apply(
            lambda q: calculate_stock_status(q, low_stock_threshold)
        )
        
        merged_df['cost_percentage'] = merged_df.apply(
            lambda row: calculate_cost_percentage(row.get('price'), row.get('storage_cost')),
            axis=1
        )
        
        merged_df['alerts'] = merged_df.apply(
            lambda row: generate_alerts(
                row.get('rating'),
                row.get('quantity'),
                low_rating_threshold,
                low_stock_threshold
            ),
            axis=1
        )
        
        return merged_df

    def get_sample_data(self) -> pd.DataFrame:
        """
        Get sample data from database as fallback when APIs are unavailable.
        Returns DataFrame with same structure as fetch_and_merge_all().
        """
        try:
            sample_products = SampleProduct.objects.filter(is_active=True)
            
            if not sample_products.exists():
                logger.info("No sample products found in database. Use 'python manage.py populate_sample_data' to create sample data.")
                return pd.DataFrame()
            
            rows = []
            for product in sample_products:
                rows.append({
                    'nmId': product.nmId,
                    'title': product.title,
                    'brand': product.brand,
                    'rating': float(product.rating) if product.rating is not None else None,
                    'feedbacks': product.feedbacks,
                    'quantity': product.quantity,
                    'price': float(product.price) if product.price is not None else None,
                    'storage_cost': float(product.storage_cost) if product.storage_cost is not None else None,
                })
            
            if not rows:
                return pd.DataFrame()
            
            df = pd.DataFrame(rows)
            
            # Get user settings for thresholds
            try:
                settings = Settings.objects.get(user=self.user)
                low_stock_threshold = settings.low_stock_threshold
                low_rating_threshold = settings.low_rating_threshold
            except Settings.DoesNotExist:
                low_stock_threshold = 10
                low_rating_threshold = 4.0
            
            # Calculate derived fields (same as in fetch_and_merge_all)
            df['stock_status'] = df['quantity'].apply(
                lambda q: calculate_stock_status(q, low_stock_threshold)
            )
            
            df['cost_percentage'] = df.apply(
                lambda row: calculate_cost_percentage(row.get('price'), row.get('storage_cost')),
                axis=1
            )
            
            df['alerts'] = df.apply(
                lambda row: generate_alerts(
                    row.get('rating'),
                    row.get('quantity'),
                    low_rating_threshold,
                    low_stock_threshold
                ),
                axis=1
            )
            
            logger.info(f"Using {len(df)} sample products from database (APIs unavailable or returned empty data)")
            return df
        
        except Exception as e:
            logger.error(f"Error getting sample data: {type(e).__name__}: {e}", exc_info=True)
            return pd.DataFrame()


def get_dashboard_data(user: User) -> List[Dict[str, Any]]:
    """
    Get dashboard data with caching (15-minute TTL).
    Checks cache first, if empty calls WBDataFetcher, merges datasets,
    caches for 15 minutes, and returns list of dicts.
    
    Args:
        user: Django User instance
    
    Returns:
        List of dictionaries, each representing a product
    """
    cache_key = f"dashboard_data_{user.id}"
    
    # Try to get from cache
    cached_data = cache.get(cache_key)
    if cached_data is not None:
        return cached_data
    
    # Cache miss - fetch fresh data
    fetcher = WBDataFetcher(user)
    merged_df = fetcher.fetch_and_merge_all()
    
    # If API calls failed or returned empty data, use sample data as fallback
    if merged_df.empty:
        logger.info("API data is empty, attempting to use sample data as fallback")
        merged_df = fetcher.get_sample_data()
    
    if merged_df.empty:
        return []
    
    # Convert DataFrame to list of dicts
    data_list = merged_df.to_dict('records')
    
    # Cache for 15 minutes (900 seconds)
    cache.set(cache_key, data_list, 900)
    
    return data_list