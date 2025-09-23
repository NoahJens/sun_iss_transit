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
# max_days = .1    # download again once 7 days old
# name = 'ISS.csv'  # custom filename, not 'gp.php'
print("test outside") 
# base = 'https://celestrak.org/NORAD/elements/gp.php'
# url = base + '?GROUP=stations&FORMAT=json'

def load_iss_data():
    with load.open('ISS.csv', mode='r') as f:
        data = json.load(f) 

    # Find the ISS row (using NORAD ID is safest)
    iss_row = next(row for row in data if row.get("NORAD_CAT_ID") == 25544)

    # Create the EarthSatellite object
    iss_geo = EarthSatellite.from_omm(ts, iss_row) # gets the geocentric information on the iss
    epoch = convert_t(iss_geo.epoch)

    iss = earth + iss_geo # converts to solar system related positional information
    return iss, epoch 