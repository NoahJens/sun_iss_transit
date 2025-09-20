import streamlit as st
from skyfield.api import load, EarthSatellite, Angle, wgs84
from astro_data import earth
from iss import iss, epoch

# Define observation point
observer = earth + wgs84.latlon(53.788419, 9.569346) # Sommerland 


st.title("Sun and ISS Transit Calculator")

st.write("test")