import streamlit as st
from skyfield.api import wgs84
from astro_data import earth, sun, iss, epoch 
from transit import find_transit 
from utils import decimal_places

# # Define observation point
# observer = earth + wgs84.latlon(53.788419, 9.569346) # Sommerland 

st.title("Sun - ISS Transit Calculator")
        
st.write('ISS orbit data from:', epoch)
st.write('Apparent diameter of sun approx. 0.5 degree')

# Input fields for latitude and longitude
lat_str = st.text_input("Latitude (decimal degrees)", value="53.7985")
lon_str = st.text_input("Longitude (decimal degrees)", value="9.5470")

# Button to update the observer
if st.button("Run"):
    try:
        if decimal_places(lat_str) < 4 or decimal_places(lon_str) < 4:
            raise ValueError("Coordinates must have at least 4 decimal places")
        
        # Now convert to float after checking decimals
        lat = float(lat_str)
        lon = float(lon_str)
        observer = earth + wgs84.latlon(lat, lon)

        st.success(f"Coordinates updated: {lat} N, {lon} E")
        st.warning('Transit times will only be reliable up to a couple of days in advance')
        
        status_placeholder = st.empty()
        status_placeholder.markdown(
            "<span style='color:red'>Calculating (near-)transit events for the next 30 days... please wait.</span>",
            unsafe_allow_html=True
        )

        transit = find_transit(observer, sun, iss)
        
        status_placeholder.empty()
        st.dataframe(transit)
        
    except ValueError as e:
        st.error(str(e))