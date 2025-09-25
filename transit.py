from utils import convert_t, angular_separation
import numpy as np 
from astro_data import ts 
import pandas as pd 

def find_transit(observer, sun, iss):
    # Start time as Skyfield time (not datetime!)
    start_date = ts.now()
    # print("Start date:", convert_t(start_date))

    days_to_scan = 7
    coarse_threshold_deg = 10  # Sun angular diameter ~0.5 deg
    candidate_times = []

    minutes_per_step = 4  # every 5 minutes

    for day_offset in range(days_to_scan):
        day = start_date + day_offset   # Skyfield Time object (not datetime)
        y, m, d, h, mi, s = day.utc     # UTC components

        # Generate times throughout the day
        hours = np.arange(0, 24)
        minutes = np.arange(0, 60, minutes_per_step)
        hh, mm = np.meshgrid(hours, minutes)
        hh = hh.flatten()
        mm = mm.flatten()

        times = ts.utc(y, m, d, hh, mm)  # still Skyfield Time objects

        # Vectorized angular separation check
        for t in times: 
            # print(t.utc_datetime().strftime("%Y-%m-%d %H:%M:%S %Z"))
            separation, sun_alt = angular_separation(t, observer, sun, iss)
            # print(sun_alt)

            if separation <= coarse_threshold_deg and sun_alt > 10:
                # print(f'{t.utc_datetime()}\t{sun_alt:.2f}\t{separation:.2f}')
                candidate_times.append(t)

    window_minutes = 2
    offset_minutes= window_minutes / (24 * 60)
    fine_threshold_deg = 8#2

    records = []

    for cand in candidate_times:
        start_fine = cand - offset_minutes
        fine_seconds = np.arange(0, (2 * window_minutes * 60) + 1, 1)
        fine_offsets = fine_seconds / 86400.0
        times_fine = start_fine + fine_offsets

        pairs = []
        for t in times_fine:
            separation, sun_alt = angular_separation(t, observer, sun, iss)
            if separation <= fine_threshold_deg:
                pairs.append((t, separation, sun_alt))

        if pairs:
            best_time, min_sep, min_alt = min(pairs, key=lambda x: x[1])
            records.append((convert_t(best_time), min_sep, min_alt))
 
    df = pd.DataFrame(records, columns=["Time CEST", "Separation [deg]", "Sun altitude [deg]"])
    return df