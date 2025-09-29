import streamlit as st
from skyfield.api import wgs84
from astro_data import earth, sun, load_iss_data
from transit import find_transit 
from utils import decimal_places


st.title("Sun - ISS Transit Calculator")

# Initial load of ISS data and storage into session state
if "iss" not in st.session_state or "epoch" not in st.session_state:
    st.session_state.iss, st.session_state.epoch = load_iss_data()

st.write(f'ISS orbit data from {st.session_state.epoch}')

# Refreshing orbit data of ISS
if st.button("Update ISS orbit data"):
    st.session_state.iss, st.session_state.epoch = load_iss_data()
    
st.text('Apparent diameter of sun approx. 0.5 degrees')

st.subheader('Coordinates')
# Input fields for latitude and longitude
lat_str = st.text_input("Latitude [decimal degrees]", value="53.7985")
lon_str = st.text_input("Longitude [decimal degrees]", value="9.5470")

# Button to run the transit calculations
if st.button("Run"):
    try:
        # Check, if coordinates have at least four decimal places for accuracy 
        if decimal_places(lat_str) < 4 or decimal_places(lon_str) < 4: 
            raise ValueError("Coordinates must have at least 4 decimal places")
        
        # Now convert to float after checking decimals
        lat = float(lat_str)
        lon = float(lon_str)

        # Update observer with coordinates
        observer = earth + wgs84.latlon(lat, lon)

        st.warning('Transit times will only be reliable up to about a day in advance')
        
        # Display waiting message while df.dataframe of transits is calculated 
        status_placeholder = st.empty()
        status_placeholder.markdown(
            "<span style='color:red'>Calculating (near-) transit events for the next 7 days... please wait</span>",
            unsafe_allow_html=True
        )
        transit = find_transit(observer, sun, st.session_state.iss)
        transit["Epoch"] = st.session_state.epoch # Add epoch to dataframe
    
        status_placeholder.empty()

        # Display transit events or show error message, if none are found in the next 7 days
        if transit.empty: 
            st.error("No (near-) transit events found in the upcoming 7 days")
        else:
            st.dataframe(transit)
        
    except ValueError as e:
        st.error(str(e))