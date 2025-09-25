from skyfield.api import EarthSatellite, wgs84, load

from astro_data import earth, sun, ts
from transit import find_transit 
from datetime import datetime

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
import requests 
from utils import convert_t
import time

time.sleep(10)

# planets = load('de421.bsp')
# earth, sun = planets['earth'], planets['sun']
observer = earth + wgs84.latlon(53.7985, 9.5470)

owner = "NoahJens"
repo = "sun_iss_transit"
file_path = "ISS.csv"
branch = "main"
workflow_file = "TLE_download.yml"
url_runs = f"https://api.github.com/repos/{owner}/{repo}/actions/workflows/{workflow_file}/runs"
params = {"branch": "main", "per_page": 1}

# Load ISS position from online repo
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
transit = find_transit(observer, sun, iss)
transit["Epoch"] = epoch
transit.to_csv("transits.csv", index=False)

if not transit.empty:

    # File to send
    filename = "transits.csv"
    email_filename = f"transits_{datetime.now().strftime("%Y%m%d")}.csv"

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


