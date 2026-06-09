import os
import geoip2.database
import logging

logger = logging.getLogger(__name__)

# Спускаемся на 3 уровня вниз: из app/services/geolocation.py в корень проекта, затем ищем папку data
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "GeoLite2-City.mmdb")

def get_geolocation(ip_address: str):
    if not os.path.exists(DB_PATH):
        logger.warning(f"GeoLite2 database not found at {DB_PATH}")
        return None, None, None, None
    
    try:
        with geoip2.database.Reader(DB_PATH) as reader:
            response = reader.city(ip_address)
            return (
                response.country.name,
                response.city.name,
                response.location.latitude,
                response.location.longitude
            )
    except Exception as e:
        logger.debug(f"Could not resolve geolocation for {ip_address}: {e}")
        return None, None, None, None