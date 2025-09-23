import os
import smtplib
from email.message import EmailMessage

# Example: replace this with your actual candidate checking logic
def check_for_new_candidates():
    # Dummy example
    # Return True if a new candidate is found
    return True, "Candidate XYZ found!"

# Email setup
EMAIL_ADDRESS = os.environ.get("EMAIL_ADDRESS")  # sender email
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")  # app password or SMTP password
TO_ADDRESS = os.environ.get("TO_ADDRESS")  # recipient email

new_found, message = check_for_new_candidates()

if new_found and EMAIL_ADDRESS and EMAIL_PASSWORD and TO_ADDRESS:
    msg = EmailMessage()
    msg['Subject'] = "New Candidate Notification"
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = TO_ADDRESS
    msg.set_content(message)

    # Using Gmail SMTP server; change if using another provider
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)
    print("Email sent successfully")
else:
    print("No new candidates or missing email credentials")