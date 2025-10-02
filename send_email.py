import smtplib
import os
import requests
import base64

from skyfield.api import wgs84, load, EarthSatellite
from transit import find_transit 
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from utils import convert_t
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition


# Email part
def send_email(filename="transits.csv"):
    # Prepare file
    with open(filename, "rb") as f:
        data = f.read()
    encoded_file = base64.b64encode(data).decode()
    email_filename = f"transits_{datetime.now().strftime('%Y%m%d')}.csv"

    # Attachment
    attachment = Attachment(
        FileContent(encoded_file),
        FileName(email_filename),
        FileType("text/csv"),
        Disposition("attachment")
    )

    recipients = [r.strip() for r in os.environ["EMAIL_TO"].split(",")] # EMAIL_TO="first@example.com,second@example.com"

    sg = SendGridAPIClient(os.environ["SENDGRID_API_KEY"])

    for recipient in recipients:
        message = Mail(
            from_email=os.environ["EMAIL_FROM"],
            to_emails=recipient,
            subject="Sun ISS transits",
            html_content="Please find the CSV attached with a 7 day forecast"
        )
        message.attachment = attachment
        try:
            response = sg.send(message)
            print(f"✅ Email sent to {recipient} — Status {response.status_code}")
        except Exception as e:
            print(f"⚠️ Error sending to {recipient}: {e}")


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

if not transit.empty:
    send_email("transits.csv")
else:
    print("No transit events — email not sent")



