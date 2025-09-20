import streamlit as st
from skyfield.api import wgs84
from astro_data import earth, sun, iss, epoch 
from transit import find_transit 

# Define observation point
observer = earth + wgs84.latlon(53.788419, 9.569346) # Sommerland 

st.title("Sun and ISS Transit Calculator")

st.write(epoch)
transit = find_transit(observer, sun, iss) 
st.dataframe(transit)