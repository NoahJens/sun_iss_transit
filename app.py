import streamlit as st
from skyfield.api import wgs84
from astro_data import earth, sun, load_iss_data
from transit import find_transit 
from utils import decimal_places, trigger_orbit_update

# # Define observation point
# observer = earth + wgs84.latlon(53.788419, 9.569346) # Sommerland 

st.title("Sun - ISS Transit Calculator?")

if "iss" not in st.session_state or "epoch" not in st.session_state:
    print("session test")
    # st.write("session test")
    iss, epoch = load_iss_data(override = False)
    st.session_state.iss = iss
    st.session_state.epoch = epoch

# Use cached values
print("overwrite session values")
iss = st.session_state.iss
epoch = st.session_state.epoch

st.write(f'ISS orbit data from {epoch}')

if st.button("Update ISS orbit data"):
    override = True
    iss, epoch = load_iss_data(override)
    print(f"epoch inside button: {epoch}")
    st.session_state.iss = iss
    st.session_state.epoch = epoch
    
st.text('Apparent diameter of sun approx. 0.5 degrees')
st.subheader('Coordinates')
# Input fields for latitude and longitude
lat_str = st.text_input("Latitude [decimal degrees]", value="53.7985")
lon_str = st.text_input("Longitude [decimal degrees]", value="9.5470")
# Button to update the observer
if st.button("Run"):
    try:
        if decimal_places(lat_str) < 4 or decimal_places(lon_str) < 4:
            raise ValueError("Coordinates must have at least 4 decimal places")
        
        # Now convert to float after checking decimals
        lat = float(lat_str)
        lon = float(lon_str)
        observer = earth + wgs84.latlon(lat, lon)

        # st.success(f"Coordinates updated: {lat} N, {lon} E")
        st.warning('Transit times will only be reliable up to about a day in advance')
        
        status_placeholder = st.empty()
        status_placeholder.markdown(
            "<span style='color:red'>Calculating (near-) transit events for the next 7 days... please wait.</span>",
            unsafe_allow_html=True
        )

        transit = find_transit(observer, sun, iss)
        status_placeholder.empty()

        if transit.empty: 
            st.error("No (near-) transit events found in the upcoming 7 days")
        else:
            st.dataframe(transit)
        
    except ValueError as e:
        st.error(str(e))