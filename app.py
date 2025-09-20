import streamlit as st
from skyfield.api import wgs84
from astro_data import earth, sun, iss, epoch 
from transit import find_transit 

# Define observation point
observer = earth + wgs84.latlon(53.788419, 9.569346) # Sommerland 

st.title("Sun - ISS Transit Calculator")
st.write('ISS orbit data from:', epoch)
st.write('Calculations for 53.79 N, 9.56 E')
st.write('Apparent diameter of sun approx. 0.5 degree')


status_placeholder = st.empty()
status_placeholder.markdown("<span style='color:red'>Calculating transit... please wait.</span>", unsafe_allow_html=True)

transit = find_transit(observer, sun, iss) 
status_placeholder.empty()

st.dataframe(transit)