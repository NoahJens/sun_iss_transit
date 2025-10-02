import smtplib
import os
import requests

from skyfield.api import wgs84, load, EarthSatellite
from transit import find_transit 
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from utils import convert_t

# Load Skyfield timescale 
ts = load.timescale()

# Load data for earth and sun from Skyfield bsp file 
planets = load('de421.bsp')
earth, sun = planets['earth'], planets['sun']

# Load repo data
owner = "NoahJens"
repo = "sun_iss_transit"
branch = "main"
file_path = "ISS.csv"
headers = {}
if "GITHUB_TOKEN" in os.environ:
    headers = {"Authorization": f"token {os.environ['GITHUB_TOKEN']}"}

# Load last commit of repo (new CSV file was automatically committed by workflow)
url_commit = f"https://api.github.com/repos/{owner}/{repo}/commits?path={file_path}&sha={branch}"
r = requests.get(url_commit, headers=headers)
r.raise_for_status()
latest_commit_sha = r.json()[0]["sha"]

# Fetch CSV at that commit
url_raw_commit = f"https://raw.githubusercontent.com/{owner}/{repo}/{latest_commit_sha}/{file_path}"
r = requests.get(url_raw_commit, headers=headers)
r.raise_for_status()
data = r.json()

# Find the ISS row
iss_row = next(row for row in data if row.get("NORAD_CAT_ID") == 25544)

# Create the EarthSatellite object
iss_geo = EarthSatellite.from_omm(ts, iss_row) # gets the geocentric information on the iss
epoch = convert_t(iss_geo.epoch)

iss = earth + iss_geo

# Calculate transits 
observer = earth + wgs84.latlon(53.7985, 9.5470) # Specific observer
transit = find_transit(observer, sun, iss)
transit["Orbit data timestamp"] = epoch
transit.to_csv("transits.csv", index=False, float_format="%.2f")

# Allow multiple recipients via secrets
recipients = os.environ["EMAIL_TO"].split(",")  # EMAIL_TO="first@example.com,second@example.com"

if not transit.empty: 
    filename = "transits.csv"
    email_filename = f"transits_{datetime.now().strftime('%Y%m%d')}.csv"

    for recipient in recipients:
        msg = MIMEMultipart()
        msg["From"] = os.environ["EMAIL_FROM"]
        msg["To"] = recipient.strip()  # remove spaces
        msg["Subject"] = "Sun ISS transits"

        msg.attach(MIMEText("Please find the CSV attached with a 7 day forecast", "plain"))

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
    print("No transit events — email not sent")



