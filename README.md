# WBMonitor – Wildberries Seller Analytics Dashboard

WBMonitor is a full-stack analytics dashboard built with Python 3.13 and Django, providing a unified control center for Wildberries sellers. It aggregates real data from four different Wildberries APIs (Content, Statistics, Prices, Analytics), merges them into one consistent dataset, and serves actionable insights through an interactive web dashboard.

## Features

- **Unified Data View**: Aggregates data from 4 Wildberries APIs into a single dashboard
- **Real-time Monitoring**: Stock status, ratings, and pricing information
- **Smart Alerts**: Low stock, low rating, and out-of-stock alerts
- **Competitor Tracking**: Track and compare competitor products (coming soon)
- **Performance Analytics**: Brand statistics and sales analysis
- **Caching Layer**: 15-minute cache for fast load times and API rate-limit protection
- **Fault-tolerant**: Graceful fallbacks if APIs fail - shows "N/A" instead of crashes

## System Architecture

### High-Level Architecture

```
Browser (UI) → Nginx (SSL, static) → Gunicorn/Django → Redis (cache 15m) + PostgreSQL → External Wildberries APIs
```

### Main Layers

1. **Frontend (Browser UI)** – Built with HTML5, Tailwind CSS, and JavaScript (ES6)
   - Uses Chart.js for visualizations
   - Litepicker for date ranges
   - Lucide icons for UI polish
   - Pages: dashboard, reports, alerts, competitors, analysis, settings

2. **Backend (Django App)** – Handles API aggregation, caching, and rendering
   - `views.py` - Controllers for all pages
   - `services.py` - WBDataFetcher class for fetching and merging data
   - `models.py` - Tokens, competitors, user settings
   - `utils.py` - Safe defaults, stock-status helpers

3. **Storage Layer**
   - PostgreSQL for users, competitors, and preferences
   - Django LocMemCache or Redis for 15-minute data caching

## Installation

### Prerequisites

- Python 3.13
- PostgreSQL 12+
- Redis (optional, for production caching)

### Setup

1. **Clone or navigate to the project:**
   ```bash
   cd wbmonitor
   ```

2. **Create a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure PostgreSQL database:**
   ```sql
   CREATE DATABASE wbmonitor;
   CREATE USER wbmonitor WITH PASSWORD 'wbmonitor';
   GRANT ALL PRIVILEGES ON DATABASE wbmonitor TO wbmonitor;
   ```

   Or update `wbmonitor/settings.py` with your database credentials.

5. **Run migrations:**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Create a superuser:**
   ```bash
   python manage.py createsuperuser
   ```

7. **Run the development server:**
   ```bash
   python manage.py runserver
   ```

8. **Access the application:**
   - Dashboard: http://127.0.0.1:8000/dashboard/
   - Admin: http://127.0.0.1:8000/admin/

## Configuration

### API Tokens

1. Log in to the admin panel or use the Settings page
2. Navigate to Settings and enter your Wildberries API tokens:
   - **Content API Token** (required) - For product titles, brands, ratings, feedbacks
   - **Statistics API Token** (required) - For real-time stock quantities
   - **Prices API Token** (required) - For product prices and discounts
   - **Analytics API Token** (optional) - For storage costs

### User Settings

Configure dashboard preferences in the Settings page:
- Low Stock Threshold (default: 10)
- Low Rating Threshold (default: 4.0)
- Items Per Page (default: 50)
- Default Sort Column and Order

## Project Structure

```
wbmonitor/
├── wbmonitor/          # Django project settings
│   ├── settings.py     # Project configuration
│   ├── urls.py         # Root URL configuration
│   └── wsgi.py         # WSGI application
├── dashboard/          # Main dashboard app
│   ├── models.py       # WBToken, Competitor, Settings models
│   ├── views.py        # All page views and endpoints
│   ├── services.py     # WBDataFetcher - API fetching and merging
│   ├── utils.py        # Helper functions
│   ├── admin.py        # Django admin configuration
│   ├── urls.py         # Dashboard URL routes
│   └── templates/       # HTML templates
│       ├── base.html
│       └── dashboard/
│           ├── dashboard.html
│           ├── reports.html
│           ├── alerts.html
│           ├── competitors.html
│           ├── analysis.html
│           └── settings.html
├── static/             # Static files (CSS, JS, icons)
├── manage.py           # Django management script
├── requirements.txt    # Python dependencies
└── README.md           # This file
```

## Key Components

### WBDataFetcher (services.py)

Central class that fetches from all four APIs with graceful fallbacks. Each method returns a clean Pandas DataFrame or an empty one if the API fails.

Methods:
- `fetch_content_data()` - Product content (titles, brands, ratings, feedbacks)
- `fetch_statistics_data()` - Real-time stock quantities
- `fetch_prices_data()` - Prices and discounts
- `fetch_analytics_data()` - Storage costs (optional)
- `fetch_and_merge_all()` - Merges all data into unified DataFrame

### Data Merge & Cleaning

All DataFrames are merged on `nmId`, guaranteeing columns:
- `nmId`, `title`, `brand`, `rating`, `feedbacks`
- `quantity`, `price`, `storage_cost`
- `stock_status` (calculated: Out of Stock, Low Stock, In Stock)
- `cost_percentage` (calculated: (storage_cost / price) × 100)
- `alerts` (calculated: low_rating, out_of_stock, low_stock)

### Caching Layer

`get_dashboard_data()` checks cache first. If empty:
1. Calls WBDataFetcher to fetch from all APIs
2. Merges datasets
3. Caches for 15 minutes
4. Returns list of dicts

### Views Layer

Each view uses `get_dashboard_data()`, applies filters, paginates, and renders template:
- `dashboard_view` - Main product table with filters and sorting
- `reports_view` - Aggregated statistics and charts
- `alerts_view` - Products with alerts
- `competitors_view` - Competitor tracking
- `analysis_view` - Brand statistics and trends
- `settings_view` - API tokens and preferences

## Data Flow

1. User opens dashboard (`/dashboard/`)
2. `views.py` calls `get_dashboard_data(user)`
3. If cache hit → render instantly
4. If cache miss → `WBDataFetcher` fetches from four APIs
5. Data merged, cleaned, calculated, cached for 15 min
6. View applies filters, sorts, paginates, renders HTML

**Even if one API fails, UI remains consistent and shows "N/A" instead of false zeroes.**

## Production Deployment

### Recommended Stack

- **Web Server**: Nginx (SSL, static files)
- **Application Server**: Gunicorn
- **Cache**: Redis
- **Database**: PostgreSQL

### Environment Variables

Set these in production:

```bash
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-domain.com
DATABASE_URL=postgresql://user:pass@localhost/wbmonitor
REDIS_URL=redis://localhost:6379/1
```

### Update settings.py for Production

1. Use Redis for caching:
   ```python
   CACHES = {
       'default': {
           'BACKEND': 'django.core.cache.backends.redis.RedisCache',
           'LOCATION': 'redis://127.0.0.1:6379/1',
           'TIMEOUT': 900,  # 15 minutes
       }
   }
   ```

2. Configure static files collection:
   ```bash
   python manage.py collectstatic
   ```

## Future Extensions

- **Competitors Module**: Full competitor data fetching and comparison
- **Sales Analysis**: Historical data aggregation with trend charts
- **Email Notifications**: Alert notifications via email
- **Export**: CSV/Excel export functionality
- **API Endpoints**: REST API for programmatic access

## Why This Architecture Works

✅ **Fault-tolerant**: No API failure can crash the app  
✅ **Unified source**: Single cached dataset powers all pages  
✅ **Scalable**: New pages reuse same service layer  
✅ **Honest UI**: No fake data; missing values show "N/A"  
✅ **Performant**: Cache + Pandas = real-time feel without API overload  

## License

This project is provided as-is for educational and commercial use.

## Support

For issues, questions, or contributions, please refer to the project documentation or contact the development team.

