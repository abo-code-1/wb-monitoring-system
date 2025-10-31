# Quick Start Guide

## Initial Setup (First Time)

1. **Navigate to project directory:**
   ```bash
   cd wbmonitor
   ```

2. **Create and activate virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up PostgreSQL database:**
   - Create database: `CREATE DATABASE wbmonitor;`
   - Create user: `CREATE USER wbmonitor WITH PASSWORD 'wbmonitor';`
   - Grant privileges: `GRANT ALL PRIVILEGES ON DATABASE wbmonitor TO wbmonitor;`
   - Or update `wbmonitor/settings.py` with your database credentials

5. **Run migrations:**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Create superuser:**
   ```bash
   python manage.py createsuperuser
   ```

7. **Run development server:**
   ```bash
   python manage.py runserver
   ```

8. **Access the application:**
   - Dashboard: http://127.0.0.1:8000/dashboard/
   - Admin: http://127.0.0.1:8000/admin/

## Configure API Tokens

1. Log in to the admin panel (http://127.0.0.1:8000/admin/) or use the Settings page
2. Go to Settings page in the dashboard
3. Enter your Wildberries API tokens:
   - **Content API Token** (required)
   - **Statistics API Token** (required)
   - **Prices API Token** (required)
   - **Analytics API Token** (optional)

## Daily Usage

1. **Start the server:**
   ```bash
   cd wbmonitor
   source venv/bin/activate  # If not already activated
   python manage.py runserver
   ```

2. **Access dashboard:**
   - Navigate to http://127.0.0.1:8000/dashboard/
   - Data is automatically cached for 15 minutes
   - Use the "Refresh" button to manually clear cache

3. **Navigate pages:**
   - Dashboard - Main product table with filters
   - Reports - Statistics and charts
   - Alerts - Products requiring attention
   - Competitors - Track competitor products
   - Analysis - Brand statistics and trends
   - Settings - Configure tokens and preferences

## Troubleshooting

### Database Connection Error
- Ensure PostgreSQL is running
- Verify database credentials in `wbmonitor/settings.py`
- Check that database and user exist

### API Token Issues
- Verify tokens are correct in Settings page
- Check Wildberries API documentation for token format
- Some APIs may require additional authentication

### Cache Issues
- Click "Refresh" button on dashboard to clear cache
- Or wait 15 minutes for automatic refresh
- In development, cache uses LocMemCache (in-memory)

### No Data Showing
- Ensure API tokens are configured
- Check that tokens have proper permissions
- Verify APIs are accessible (network/firewall)
- Check Django logs for API errors

