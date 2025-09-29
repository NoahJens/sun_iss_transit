import numpy as np 
import pandas as pd

from utils import convert_t, angular_separation
from astro_data import ts 

def find_transit(observer, sun, iss):
    # Start time as Skyfield time
    start_date = ts.now()

    # ---------------------------------------------------------
    # COARSE CHECK
    # ---------------------------------------------------------

    days_to_scan = 7 # Coarse scan 7 days ahead
    coarse_threshold_deg = 10 # Save instances with angular seperation of less than 10 degree
    minutes_per_step = 4 # Check angular seperation in coarse scan every 4 minutes
    
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

    window_minutes = 2 # check two minutes in past and 2 in future from coarse candidate (covers the 4 minutes of the coarse scan)
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

        # append only the time with the minimum separation to the records
        if pairs:
            best_time, min_sep, min_alt = min(pairs, key=lambda x: x[1])
            records.append((convert_t(best_time), min_sep, min_alt))
 
    # write the pair with the smallest angular separation of each candidate to a df (if separation is under 2 degree) 
    df = pd.DataFrame(records, columns=["Time CEST", "Separation [deg]", "Sun altitude [deg]"])
    return df