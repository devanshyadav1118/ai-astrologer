import sys
import os

# Add VedicAstro to sys.path
sys.path.append(os.path.join(os.getcwd(), 'VedicAstro'))

from vedicastro.VedicAstro import VedicHoroscopeData
import polars as pl

RASHIS = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 'Libra', 
          'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']

def get_navamsa_sign(longitude):
    """Calculates the Navamsa (D9) sign for a given longitude."""
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
houses_data = vhd.get_houses_data_from_chart(chart)
dasa = vhd.compute_vimshottari_dasa(chart)

# Build Markdown content
md_content = f"# Birth Chart Report - {details['name']}\n\n"
md_content += f"**Birth Details:** {details['day']}-{details['month']}-{details['year']} {details['hour']}:{details['minute']}\n"
md_content += f"**Location:** {details['latitude']}, {details['longitude']} ({details['tz']})\n\n"

# House Positions Table
md_content += "## House Positions\n\n"
md_content += "| House | Rasi | Longitude | Nakshatra | Rasi Lord | Nakshatra Lord | Sub Lord |\n"
md_content += "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n"
for h in houses_data:
    md_content += f"| {h.Object} | {h.Rasi} | {h.SignLonDMS} | {h.Nakshatra} | {h.RasiLord} | {h.NakshatraLord} | {h.SubLord} |\n"
md_content += "\n"

# Planetary Positions Table
md_content += "## Planetary Positions (D1 - Rasi)\n\n"
md_content += "| Planet | Rasi | Longitude | Nakshatra | Rasi Lord | Nakshatra Lord | Sub Lord | House |\n"
md_content += "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n"
for p in planets_data:
    md_content += f"| {p.Object} | {p.Rasi} | {p.SignLonDMS} | {p.Nakshatra} | {p.RasiLord} | {p.NakshatraLord} | {p.SubLord} | {p.HouseNr} |\n"
md_content += "\n"

# Navamsa Chart Table
md_content += "## Navamsa Chart (D9)\n\n"
md_content += "| Planet | D1 Rasi | D9 Sign |\n"
md_content += "| :--- | :--- | :--- |\n"
for p in planets_data:
    d9_sign = get_navamsa_sign(p.LonDecDeg)
    md_content += f"| {p.Object} | {p.Rasi} | {d9_sign} |\n"
md_content += "\n"

# Vimshottari Dashas
md_content += "## Vimshottari Dashas & Bhuktis\n\n"
for m_dasa, m_info in dasa.items():
    md_content += f"### Maha Dasa: {m_dasa} ({m_info['start']} to {m_info['end']})\n\n"
    md_content += "| Bhukti | Start | End |\n"
    md_content += "| :--- | :--- | :--- |\n"
    for b_name, b_info in m_info['bhuktis'].items():
        md_content += f"| {b_name} | {b_info['start']} | {b_info['end']} |\n"
    md_content += "\n"

# Save to file
report_path = "devansh_yadav_report.md"
with open(report_path, "w") as f:
    f.write(md_content)

print(f"Report generated: {report_path}")
