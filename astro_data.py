from skyfield.api import load, EarthSatellite, Angle, wgs84
from utils import convert_t
from urllib.error import URLError, HTTPError
import streamlit as st
import json
import os 

ts = load.timescale()

planets = load('de421.bsp')
earth, sun = planets['earth'], planets['sun']

# Load ISS position data from CelesTrak
max_days = .1    # download again once 7 days old
name = 'ISS.csv'  # custom filename, not 'gp.php'
print("test outside") 
base = 'https://celestrak.org/NORAD/elements/gp.php'
url = base + '?GROUP=stations&FORMAT=json'

def load_iss_data(override):
    try:
        if os.path.isfile("/ISS.csv") == False or load.days_old(name) >= max_days: #or override == True and load.days_old(name) >= .1:
            print("pre download")
            status_placeholder = st.empty()
            status_placeholder.markdown(
            "<span style='color:red'>Updating ISS orbit data... please wait.</span>",
            unsafe_allow_html=True
            )
            load.download(url, filename=name)
            status_placeholder.empty()
            print("Updated ISS position")

    except (HTTPError, URLError, OSError) as e:
        print("couldnt update")
        st.error(f"⚠️ Could not update TLE ({e})")
        return False, False
    
    print("load_iss_data")
    # Load ISS position
    with load.open('ISS.csv', mode='r') as f:
        data = json.load(f) 
    print(load.days_old(name))
    # Find the ISS row (using NORAD ID is safest)
    iss_row = next(row for row in data if row.get("NORAD_CAT_ID") == 25544)

    # Create the EarthSatellite object
    iss_geo = EarthSatellite.from_omm(ts, iss_row) # gets the geocentric information on the iss
    epoch = convert_t(iss_geo.epoch)

    iss = earth + iss_geo # converts to solar system related positional information
    return iss, epoch 