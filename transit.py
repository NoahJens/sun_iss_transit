import numpy as np 
import pandas as pd

from utils import convert_t
from astro_data import ts 

def angular_separation(t, observer, sun, iss):
    """
    Calculate the angular separation (in degrees) between the Sun and ISS
    as seen by a given observer, along with the Sun's altitude.
    
    Args:
        t (Time): Skyfield Time object representing the observation time.
        observer: Skyfield observer object (Earth location).
        sun: Skyfield Sun object.
        iss: Skyfield EarthSatellite object representing the ISS.
        
    Returns:
        separation_deg (float): Angular separation between Sun and ISS in degrees.
        sun_alt_deg (float): Sun's altitude in degrees.
    """

    sun_vec = observer.at(t).observe(sun).apparent()
    iss_vec = observer.at(t).observe(iss).apparent()

    # Compute Sun altitude in degrees
    sun_alt, _, _ = sun_vec.altaz()
    sun_alt = sun_alt.degrees
    
    # Compute angular separation between Sun and ISS
    return sun_vec.separation_from(iss_vec).degrees, sun_alt

def find_transit(observer, sun, iss):
    """
    Calculate potential Sun-ISS transit events for a given observer over the next 7 days.

    The function performs a two-step search:
    1. Coarse scan every 4 minutes to find candidate times when the ISS passes close to the Sun.
    2. Fine scan at 1-second resolution around each candidate to find the moment of minimum angular separation.

    Args:
        observer: Skyfield observer object representing the observer's location on Earth.
        sun: Skyfield Sun object.
        iss: Skyfield EarthSatellite object representing the ISS.

    Returns:
        pd.DataFrame: A dataframe containing times of potential transits in CEST, 
                      the angular separation between the ISS and Sun in degrees, 
                      and the Sun's altitude in degrees.
    """

    # Start time as Skyfield time
    start_date = ts.now()

    # ---------------------------------------------------------
    # COARSE CHECK
    # ---------------------------------------------------------

    days_to_scan = 7 # Coarse scan 7 days ahead
    coarse_threshold_deg = 15 # Save instances with angular seperation of less than 15 degree
    minutes_per_step = 1 # Check angular seperation in coarse scan every minute
    
    candidate_times = [] 

    for day_offset in range(days_to_scan):
        # Generate times to check angular separation for 
        day = start_date + day_offset   
        y, m, d, h, mi, s = day.utc # UTC components

        hours = np.arange(0, 24)
        minutes = np.arange(0, 60, minutes_per_step)
        hh, mm = np.meshgrid(hours, minutes)
        hh = hh.flatten()
        mm = mm.flatten()

        times = ts.utc(y, m, d, hh, mm) 

        # Vectorized angular separation check
        for t in times: 
            separation, sun_alt = angular_separation(t, observer, sun, iss)

            # Append time to candidates, when separation is less than 10 degrees and the sun is 10 degrees above the horizon
            if separation <= coarse_threshold_deg and sun_alt > 10:
                candidate_times.append(t)
    
    # ---------------------------------------------------------
    # FINE CHECK 
    # ---------------------------------------------------------

    window_minutes = 0.5 # Check half a minutes in past and half a minute in future from coarse candidate (covers the 1 minutes of the coarse scan)
    offset_minutes= window_minutes / (24 * 60)
    fine_threshold_deg = 2 # 2 degrees angular seperation as threshold for fine scan

    records = []

    for cand in candidate_times:
        start_fine = cand - offset_minutes
        fine_seconds = np.arange(0, (2 * window_minutes * 60) + 1, 1)
        fine_offsets = fine_seconds / 86400.0
        times_fine = start_fine + fine_offsets

        pairs = [] # List to store tuples of time, separation and sun altitude

        for t in times_fine:
            separation, sun_alt = angular_separation(t, observer, sun, iss)
            
            # Append candidate to pairs, when separation is under the fine threshold 
            if separation <= fine_threshold_deg:
                pairs.append((t, separation, sun_alt))

        # Append only the time with the minimum separation to the records
        if pairs:
            best_time, min_sep, min_alt = min(pairs, key=lambda x: x[1])
            records.append((best_time, min_sep, min_alt))
    
    # ---------------------------------------------------------
    # REMOVE DUPLICATES 
    # ---------------------------------------------------------
    cleaned_records = []

    records.sort(key=lambda x: x[0])  # sort by Skyfield Time

    for rec in records:
        rec_time = rec[0]  # keep as Skyfield Time for comparison
        rec_sep = rec[1]
        rec_alt = rec[2]

        if not cleaned_records:
            cleaned_records.append((rec_time, rec_sep, rec_alt))
        else:
            last_time = cleaned_records[-1][0]
            # If within 15 seconds, keep the one with smaller separation
            delta_sec = (rec_time.tt - last_time.tt) * 86400  # tt is in days, 86400 sec/day
            if delta_sec < 15:
                if rec_sep < cleaned_records[-1][1]:
                    cleaned_records[-1] = (rec_time, rec_sep, rec_alt)
            else:
                cleaned_records.append((rec_time, rec_sep, rec_alt))

    # Convert times to desired format using convert_t() when creating the DataFrame 
    df = pd.DataFrame(
        [(convert_t(t), sep, alt) for t, sep, alt in cleaned_records],
        columns=["Time CEST", "Separation [deg]", "Sun altitude [deg]"]
    )
    return df