import os
import base64
import requests

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

from datetime import datetime
from skyfield.api import wgs84, load, EarthSatellite
from transit import find_transit 
from datetime import datetime
from utils import convert_t

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

def get_gmail_service():
    import json
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    import base64, os

    SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

    # Decode credentials.json
    creds_bytes = base64.b64decode(os.environ["GMAIL_CREDENTIALS"])
    with open("credentials.json", "wb") as f:
        f.write(creds_bytes)

    # Decode token.json
    token_bytes = base64.b64decode(os.environ["GMAIL_TOKEN"])
    with open("token.json", "wb") as f:
        f.write(token_bytes)

    # Load credentials
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    # Refresh if expired
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open("token.json", "w") as f:
            f.write(creds.to_json())

    service = build("gmail", "v1", credentials=creds)
    return service

def send_email_with_attachment(service, sender, recipient, subject, body_text, attachment_path, attachment_filename):
    """Send an email with an attachment via Gmail API."""
    message = MIMEMultipart()
    message["From"] = sender
    message["To"] = recipient
    message["Subject"] = subject

    # Body text
    message.attach(MIMEText(body_text, "plain"))

    # Attachment
    with open(attachment_path, "rb") as f:
        part = MIMEApplication(f.read(), Name=attachment_filename)
    part['Content-Disposition'] = f'attachment; filename="{attachment_filename}"'
    message.attach(part)

    # Encode and send
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    body = {"raw": raw_message}
    sent = service.users().messages().send(userId="me", body=body).execute()
    print(f"Email sent to {recipient}, Message ID: {sent['id']}")

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
service = get_gmail_service()
recipients = os.environ["EMAIL_TO"].split(",")
sender = os.environ["EMAIL_FROM"]
subject = "Sun ISS transits"
body_text = "Please find the CSV attached with a 7 day forecast"

# File created by your previous code
filename = "transits.csv"
attachment_filename = f"transits_{datetime.now().strftime('%Y%m%d')}.csv"

for recipient in recipients:
    send_email_with_attachment(service, sender, recipient, subject, body_text, filename, attachment_filename)
    # else:
        # print("No transit events — email not sent")


