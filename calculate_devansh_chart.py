import sys
import os

# Add VedicAstro to sys.path so we can import it
sys.path.append(os.path.join(os.getcwd(), 'VedicAstro'))

from vedicastro.VedicAstro import VedicHoroscopeData
from vedicastro.utils import pretty_data_table
import polars as pl
from pprint import pprint

# Devansh Yadav's birth details
year = 2003
month = 5
day = 27
hour = 6
minute = 45
second = 0
latitude = 25.4484
longitude = 78.5685
tz = "Asia/Kolkata"  # Jhansi, Uttar Pradesh, India is UTC+5:30

# Initialize VedicHoroscopeData
# Note: The library seems to expect 'utc' as a string if provided, 
# or it uses TimezoneFinder if 'tz' is None.
# Looking at the code: self.utc,_ = get_utc_offset(self.time_zone, self.chart_time)
# So providing tz="Asia/Kolkata" should work.

vhd = VedicHoroscopeData(
    year=year, 
    month=month, 
    day=day, 
    hour=hour, 
    minute=minute, 
    second=second, 
    latitude=latitude, 
    longitude=longitude, 
    tz=tz,
    ayanamsa="Lahiri",
    house_system="Placidus"
)

# Generate chart
chart = vhd.generate_chart()

# Get planetary and house data
planets_data = vhd.get_planets_data_from_chart(chart)
houses_data = vhd.get_houses_data_from_chart(chart)

# Print planetary data
print("\n--- Planetary Positions ---")
print(pretty_data_table(planets_data))

# Print house data
print("\n--- House Cusps ---")
print(pretty_data_table(houses_data))

# Compute Vimshottari Dasa
print("\n--- Vimshottari Dasa (Overview) ---")
dasa = vhd.compute_vimshottari_dasa(chart)
# Print only major dasas for brevity
for d_name, d_info in dasa.items():
    print(f"{d_name:8}: {d_info['start']} to {d_info['end']}")
