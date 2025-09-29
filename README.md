# Sun–ISS Transit Calculator

Calculate and get notified when the International Space Station (ISS) will transit near the Sun from your location

---

## About

This project provides:

1. **A Streamlit app** to calculate potential Sun–ISS transits over the next 7 days  
2. **An automated email workflow** that fetches the latest ISS orbit data and sends a CSV with upcoming transits for a specific location  

The app uses Skyfield for precise orbital calculations and automatically keeps ISS TLE data up to date using GitHub workflows.

**Try the app online:** [http://sun-iss-transit.streamlit.app](http://sun-iss-transit.streamlit.app)

---

## Features

### Interactive App
- Enter latitude and longitude to see upcoming transits
- Two-step search:
  - Coarse scan (minutes) to find candidate times
  - Fine scan (seconds) for precise transit timing
- Displays:
  - Transit time in CEST
  - Angular separation between ISS and Sun
  - Sun altitude
- Option to manually update ISS orbit data

### Automated Email Notifications
- Calculates transits for a specific location
- Generates a CSV with upcoming transits
- Sends the CSV via email automatically every 3 days or on manual trigger
- Uses GitHub Actions and GitHub Secrets for email credentials
- Keeps ISS TLE data updated from Celestrak automatically

- For the Email notifications, Github secrets have to be set up: 
    EMAIL_FROM = "your_email@example.com"
    EMAIL_PASSWORD = "your_app_specific_password"
    EMAIL_TO = "recipient_email@example.com"