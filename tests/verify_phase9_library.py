"""Day 1: Ayanamsa Verification for VedicAstro library."""

import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from vedicastro.VedicAstro import VedicHoroscopeData
from chart.vedicastro_calculator import VedicAstroCalculator
import json

def verify_ayanamsa():
    # 1. Setup test data
    birth_date = "2000-01-01"
    birth_time = "12:00:00"
    lat = 28.6
    lon = 77.2
    tz = 5.5
    
    # 2. Get positions from our trusted Calculator (Uses direct Swiss Eph)
    calc = VedicAstroCalculator()
    our_data = calc.calculate_chart(birth_date, birth_time, lat, lon, tz)
    our_moon = next(p for p in our_data["planets"] if p["name"] == "MOON")
    
    # 3. Get positions from VedicAstro library
    try:
        # Split date/time for VA constructor
        y, m, d = map(int, birth_date.split("-"))
        hr, mn, sc = map(int, birth_time.split(":"))
        
        va = VedicHoroscopeData(y, m, d, hr, mn, sc, "+05:30", lat, lon, ayanamsa="Lahiri")
        chart = va.generate_chart()
        va_planets = va.get_planets_data_from_chart(chart)
        
        # va_planets is a list of namedtuples
        va_moon_lon = next(p.LonDecDeg for p in va_planets if p.Object == 'Moon')
    except Exception as e:
        print(f"VedicAstro Error: {e}")
        import traceback
        traceback.print_exc()
        return False

    print(f"Our Moon Longitude: {our_moon['longitude']:.4f}")
    print(f"VA Moon Longitude:  {va_moon_lon:.4f}")
    
    diff = abs(our_moon["longitude"] - va_moon_lon)
    if diff > 180: diff = 360 - diff
    
    print(f"Difference: {diff:.4f} degrees")
    
    if diff < 0.5:
        print("✅ VERIFICATION PASSED: Ayanamsa is correctly aligned.")
        return True
    else:
        print("❌ VERIFICATION FAILED: Ayanamsa mismatch detected.")
        return False

if __name__ == "__main__":
    verify_ayanamsa()
