import requests
from django.core.cache import cache
from decimal import Decimal

def get_exchange_rate():
    """Get USD to KES exchange rate from API with caching"""
    # Check if rate is cached
    cached_rate = cache.get('usd_to_kes_rate')
    if cached_rate:
        return cached_rate

    try:
        # Using exchangerate-api.com (you'll need to sign up for a free API key)
        API_KEY = 'your_api_key_here'  # Add this to your settings.py
        response = requests.get(f'https://v6.exchangerate-api.com/v6/{API_KEY}/pair/USD/KES')
        data = response.json()
        
        if response.status_code == 200:
            rate = Decimal(str(data['conversion_rate']))
            # Cache the rate for 6 hours
            cache.set('usd_to_kes_rate', rate, 60 * 60 * 6)
            return rate
    except Exception as e:
        print(f"Error fetching exchange rate: {e}")
    
    # Fallback rate if API fails
    return Decimal('130.0')

def convert_to_kes(usd_amount):
    """Convert USD to KES using real-time exchange rate"""
    if not usd_amount:
        return Decimal('0.00')
    rate = get_exchange_rate()
    return round(Decimal(str(usd_amount)) * rate, 2)
