from skyfield.api import load, EarthSatellite, Angle, wgs84
from utils import convert_t
import json

ts = load.timescale()

planets = load('de421.bsp')
earth, sun = planets['earth'], planets['sun']

# Load ISS position data from CelesTrak
max_days = 3    # download again once 3 days old
name = 'ISS.csv'  # custom filename, not 'gp.php'

base = 'https://celestrak.org/NORAD/elements/gp.php'
url = base + '?GROUP=stations&FORMAT=json'

if not load.exists(name) or load.days_old(name) >= max_days:
    print("Updated ISS position")
    load.download(url, filename=name)

# Load ISS position
with load.open('ISS.csv', mode='r') as f:
    data = json.load(f) 

# Find the ISS row (using NORAD ID is safest)
iss_row = next(row for row in data if row.get("NORAD_CAT_ID") == 25544)

# Create the EarthSatellite object
iss_geo = EarthSatellite.from_omm(ts, iss_row) # gets the geocentric information on the iss
epoch = convert_t(iss_geo.epoch)

iss = earth + iss_geo # converts to solar system related positional information