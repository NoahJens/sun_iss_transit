import smtplib
import os
import requests

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition
from base64 import b64encode
from datetime import datetime
from skyfield.api import wgs84, load, EarthSatellite
from transit import find_transit 
from datetime import datetime
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

if "GITHUB_TOKEN" in os.environ:
    headers = {"Authorization": f"token {os.environ['GITHUB_TOKEN']}"}
    print('PAT accessed')
else:
    headers = {}

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

# if not transit.empty: 
filename = "transits.csv"
email_filename = f"transits_{datetime.now().strftime('%Y%m%d')}.csv"
subject = "Sun ISS transits"
content_text = "Please find the CSV attached with a 7 day forecast"

# Read file and encode for SendGrid attachment
with open(filename, "rb") as f:
    file_data = f.read()
encoded_file = b64encode(file_data).decode()

attachment = Attachment(
    FileContent(encoded_file),
    FileName(email_filename),
    FileType("application/octet-stream"),
    Disposition("attachment")
)

# Loop over recipients
for recipient in recipients:
    message = Mail(
        from_email=os.environ["EMAIL_FROM"],
        to_emails=recipient,
        subject=subject,
        plain_text_content=content_text
    )
    message.attachment = attachment

    try:
        sg = SendGridAPIClient(os.environ["SENDGRID_API_KEY"])
        response = sg.send(message)
        print(f"Email sent, status code: {response.status_code}")
    except Exception as e:
        print(f"Failed to send email: {e}")
    
    # else:
        # print("No transit events — email not sent")


