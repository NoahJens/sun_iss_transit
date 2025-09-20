from skyfield.api import load, Topos, EarthSatellite, Angle, wgs84
import pytz
from skyfield.timelib import Time
from datetime import datetime

def angular_separation(t, observer, sun, iss):
    """Angular separation (degrees) between Sun and ISS as seen by observer"""
    sun_vec = observer.at(t).observe(sun).apparent()
    iss_vec = observer.at(t).observe(iss).apparent()

    sun_alt, sun_az, sun_dist = sun_vec.altaz()
    sun_alt = sun_alt.degrees
    
    return sun_vec.separation_from(iss_vec).degrees, sun_alt

def convert_t(t):
    """
    Convert a Skyfield Time or a datetime object to Berlin time and format as string.
    """
    if isinstance(t, Time):  # Skyfield Time object
        t_utc = t.utc_datetime()
    elif isinstance(t, datetime):  # regular datetime
        t_utc = t
    else:
        raise TypeError("t must be a Skyfield Time or datetime object")

    t_berlin = t_utc.astimezone(pytz.timezone('Europe/Berlin'))
    return t_berlin.strftime("%Y-%m-%d %H:%M:%S %Z")

# Check number of decimal places
def decimal_places(value):
    s = str(value)
    if '.' in s:
        return len(s.split('.')[-1])
    else:
        return 0
