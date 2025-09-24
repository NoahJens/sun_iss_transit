from skyfield.api import load, EarthSatellite, Angle, wgs84
from utils import convert_t, trigger_orbit_update
from urllib.error import URLError, HTTPError
import streamlit as st
import json
import requests
from datetime import datetime, timezone
import os

ts = load.timescale()

planets = load('de421.bsp')
earth, sun = planets['earth'], planets['sun']

# Load ISS position data from CelesTrak
max_days = .1    # download again once 7 days old
name = 'ISS.csv'  # custom filename, not 'gp.php'

def load_iss_data(override):
    try:    
        # check if ISS.csv is missing or override is True
        if not os.path.isfile("ISS.csv") or (override and load.days_old(name) >= 0.0001):
            print("pre download")
            status_placeholder = st.empty()
            status_placeholder.markdown(
                "<span style='color:red'>Updating ISS orbit data... please wait.</span>",
                unsafe_allow_html=True
            )
            
            # Trigger GitHub Actions workflow
            success = trigger_orbit_update("TLE_download.yml")  # workflow_dispatch
            print(f"success: {success}")
            if success == False:
                st.error("⚠️ Could not trigger TLE update workflow.")
                status_placeholder.empty()
                return False, False
            status_placeholder.empty()
            print("Updated ISS position")

    except (HTTPError, URLError, OSError) as e:
        print("couldnt update")
        st.error(f"⚠️ Could not update TLE ({e})")
        return False, False
    
    print("load_iss_data")
    # Load ISS position

    url = "https://raw.githubusercontent.com/NoahJens/sun_iss_transit/main/ISS.csv"
    r = requests.get(url)
    data = json.loads(r.text)  # data now contains the latest ISS info

    print(load.days_old(name))
    # with load.open('ISS.csv', mode='r') as f:
    #     data = json.load(f) 

    # Find the ISS row (using NORAD ID is safest)
    iss_row = next(row for row in data if row.get("NORAD_CAT_ID") == 25544)

    # Create the EarthSatellite object
    iss_geo = EarthSatellite.from_omm(ts, iss_row) # gets the geocentric information on the iss
    epoch = convert_t(iss_geo.epoch)

    iss = earth + iss_geo # converts to solar system related positional information
    return iss, epoch 