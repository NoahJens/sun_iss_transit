from skyfield.api import wgs84
from astro_data import earth, sun, load_iss_data
from transit import find_transit 
from datetime import datetime

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os

# Calculate transits 
iss, epoch = load_iss_data()
observer = earth + wgs84.latlon(53.7985, 9.5470)
transit = find_transit(observer, sun, iss)
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
        server.login(os.environ["EMAIL_USER"], os.environ["EMAIL_PASSWORD"])
        server.send_message(msg)

else:
    print("No transit events — email not sent.")


