import sys
import os

# Add VedicAstro to sys.path
sys.path.append(os.path.join(os.getcwd(), 'VedicAstro'))

from vedicastro.VedicAstro import VedicHoroscopeData

RASHIS = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 'Libra', 
          'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']

def get_navamsa_sign(longitude):
    """
    Calculates the Navamsa (D9) sign index for a given longitude.
    Each Navamsa is 3 degrees 20 minutes (3.3333... degrees).
    """
    # Total navamsas from 0 degrees Aries
    navamsa_index = int(longitude / (30 / 9))
    return RASHIS[navamsa_index % 12]

# Birth details
details = {
    "name": "Devansh Yadav",
    "year": 2003,
    "month": 5,
    "day": 27,
    "hour": 6,
    "minute": 45,
    "second": 0,
    "latitude": 25.4484,
    "longitude": 78.5685,
    "tz": "Asia/Kolkata"
}

# Initialize
vhd = VedicHoroscopeData(
    year=details["year"], 
    month=details["month"], 
    day=details["day"], 
    hour=details["hour"], 
    minute=details["minute"], 
    second=details["second"], 
    latitude=details["latitude"], 
    longitude=details["longitude"], 
    tz=details["tz"],
    ayanamsa="Lahiri",
    house_system="Placidus"
)

# Generate chart
chart = vhd.generate_chart()
planets_data = vhd.get_planets_data_from_chart(chart)

print(f"Navamsa (D9) Chart for {details['name']}\n")
print(f"{'Object':<10} | {'D1 Sign':<15} | {'D9 Sign'}")
print("-" * 40)

for p in planets_data:
    d9_sign = get_navamsa_sign(p.LonDecDeg)
    print(f"{p.Object:<10} | {p.Rasi:<15} | {d9_sign}")
