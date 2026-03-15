import requests
import logging
from typing import Any, Dict

class VedicAstroAPIClient:
    """Client for the VedicAstro FastAPI service."""

    def __init__(self, base_url: str = "http://127.0.0.1:8088"):
        self.base_url = base_url
        self.logger = logging.getLogger(__name__)

    def get_all_horoscope_data(
        self,
        date: str,
        time: str,
        latitude: float,
        longitude: float,
        timezone: float,
        ayanamsa: str = "Lahiri",
        house_system: str = "Equal"
    ) -> Dict[str, Any]:
        """Fetch all horoscope data from the API."""
        url = f"{self.base_url}/get_all_horoscope_data"
        
        # Parse date and time
        y, m, d = map(int, date.split("-"))
        hr, mn, sc = map(int, time.split(":"))
        
        # Convert float timezone to string (+HH:MM)
        sign = "+" if timezone >= 0 else "-"
        abs_tz = abs(timezone)
        tz_hr = int(abs_tz)
        tz_mn = int((abs_tz - tz_hr) * 60)
        utc_str = f"{sign}{tz_hr:02d}:{tz_mn:02d}"

        payload = {
            "year": y,
            "month": m,
            "day": d,
            "hour": hr,
            "minute": mn,
            "second": sc,
            "utc": utc_str,
            "latitude": latitude,
            "longitude": longitude,
            "ayanamsa": ayanamsa,
            "house_system": house_system
        }

        try:
            self.logger.info(f"Requesting horoscope data from {url}")
            response = requests.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching data from VedicAstro API: {e}")
            raise
