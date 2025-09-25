from skyfield.api import wgs84, load, EarthSatellite
from transit import find_transit 
from datetime import datetime

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
import requests
from utils import convert_t, angular_separation
import numpy as np 
import pandas as pd 

ts = load.timescale()

planets = load('de421.bsp')
earth, sun = planets['earth'], planets['sun']

owner = "NoahJens"
repo = "sun_iss_transit"
file_path = "ISS.csv"
branch = "main"

# Calculate iss data 
url_commit = f"https://api.github.com/repos/{owner}/{repo}/commits?path={file_path}&sha={branch}"
r = requests.get(url_commit)
r.raise_for_status()
latest_commit_sha = r.json()[0]["sha"]

# Fetch CSV at that commit
url_raw_commit = f"https://raw.githubusercontent.com/{owner}/{repo}/{latest_commit_sha}/{file_path}"
r = requests.get(url_raw_commit)
r.raise_for_status()
data = r.json()

# Find the ISS row (using NORAD ID is safest)
iss_row = next(row for row in data if row.get("NORAD_CAT_ID") == 25544)

# Create the EarthSatellite object
iss_geo = EarthSatellite.from_omm(ts, iss_row) # gets the geocentric information on the iss
epoch = convert_t(iss_geo.epoch)

iss = earth + iss_geo


# Calculate transits 
observer = earth + wgs84.latlon(53.7985, 9.5470)

######################################################
# calc transit 
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
fine_threshold_deg = 2

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

transit = pd.DataFrame(records, columns=["Time CEST", "Separation [deg]", "Sun altitude [deg]"])
#############################################################
transit["Epoch"] = epoch
transit.to_csv("transits.csv", index=False)

if not transit.empty:

    # File to send
    filename = "transits.csv"
    email_filename = f"transits_{datetime.now().strftime('%Y%m%d')}.csv"

    # Email setup
    msg = MIMEMultipart()
    msg["From"] = os.environ["EMAIL_FROM"]
    msg["To"] = os.environ["EMAIL_TO"]
    msg["Subject"] = "Sun ISS transits"

    # Body
    msg.attach(MIMEText("Please find the CSV attached with a 7 day forecast", "plain"))

    # Attach CSV
    with open(filename, "rb") as f:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(f.read())
    encoders.encode_base64(part)
    part.add_header("Content-Disposition", f"attachment; filename={email_filename}")
    msg.attach(part)

    # Send
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(os.environ["EMAIL_FROM"], os.environ["EMAIL_PASSWORD"])
        server.send_message(msg)

else:
    print("No transit events — email not sent.")


