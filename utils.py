import pytz

from skyfield.timelib import Time
from datetime import datetime

def convert_t(t):
    """
    Convert a Skyfield Time or datetime object to Berlin (CEST) timezone
    and return a formatted string.
    
    Args:
        t (Time or datetime): Time to convert.
        
    Returns:
        str: Time formatted as 'YYYY-MM-DD HH:MM:SS CEST'.
    """

    if isinstance(t, Time):  # Skyfield Time object
        t_utc = t.utc_datetime()
    elif isinstance(t, datetime):  # Regular datetime object
        t_utc = t
    else:
        raise TypeError("t must be a Skyfield Time or datetime object")

    # Convert to Berlin timezone
    t_berlin = t_utc.astimezone(pytz.timezone('Europe/Berlin'))
    return t_berlin.strftime("%Y-%m-%d %H:%M:%S %Z")

def decimal_places(value):
    """
    Count the number of decimal places in a numeric value.
    
    Args:
        value (float or str): Number to inspect.
        
    Returns:
        int: Number of digits after the decimal point.
    """

    s = str(value)
    if '.' in s:
        return len(s.split('.')[-1])
    else:
        return 0