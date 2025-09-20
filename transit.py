from utils import convert_t, angular_separation
import numpy as np 
from astro_data import ts 


def find_transit(observer, iss, sun, times):
    # Start time as Skyfield time (not datetime!)
    start_date = ts.now()
    print("Start date:", convert_t(start_date))

    days_to_scan = 10
    threshold_deg = 10  # Sun angular diameter ~0.5 deg
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
            separation, sun_alt = angular_separation(t)
            # print(sun_alt)

            if separation <= threshold_deg and sun_alt > 10:
                print(f'{t.utc_datetime()}\t{sun_alt:.2f}\t{separation:.2f}')
                candidate_times.append(t)


    print(f"ISS EPOCH: {convert_t(iss_geo.epoch)}\n")
    print(f"{'TIME':<25} {'SEPARATION [deg]':<18} {'SUN ALT [deg]':<10}")

    fine_candidates = []

    window_minutes = 2
    offset_minutes= window_minutes / (24 * 60)

    for cand in candidate_times:  # cand is a Skyfield Time object
        start_fine = cand - offset_minutes
        end_fine   = cand + offset_minutes

        fine_seconds = np.arange(0, (2 * window_minutes * 60) + 1, 1)
        fine_offsets = fine_seconds / 86400.0  # seconds -> days
        times_fine = start_fine + fine_offsets  # Skyfield Time array

        separations = []
        for t in times_fine:
            separation, sun_alt = angular_separation(t)
            if separation <= 2:
                separations.append(separation)

        if len(separations) > 0:
            min_idx = np.argmin(separations)
            best_time = times_fine[min_idx]
            min_sep   = separations[min_idx]
            print(f"{best_time.utc_iso():<25} {min_sep:<18.4f} {sun_alt:<10.4f}")
    return 