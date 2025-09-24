from skyfield.api import load, EarthSatellite, Angle, wgs84
from utils import convert_t, trigger_orbit_update
from urllib.error import URLError, HTTPError
import streamlit as st
import json
import requests
from datetime import datetime, timezone

ts = load.timescale()

planets = load('de421.bsp')
earth, sun = planets['earth'], planets['sun']

# Load ISS position data from CelesTrak
max_days = .1    # download again once 7 days old
name = 'ISS.csv'  # custom filename, not 'gp.php'

import requests
import json
from datetime import datetime, timezone

def load_iss_data(override):
    try:
        # Check last workflow run instead of commit date
        if override:
            owner = "NoahJens"
            repo = "sun_iss_transit"
            workflow_file = "TLE_download.yml"
            headers = {"Authorization": f"token {st.secrets['GITHUB_TOKEN']}"}
            url_runs = f"https://api.github.com/repos/{owner}/{repo}/actions/workflows/{workflow_file}/runs"
            params = {"branch": "main", "per_page": 1}
            
            r = requests.get(url_runs, headers=headers, params=params)
            r.raise_for_status()
            runs = r.json().get("workflow_runs", [])
            
            age_days = None
            if runs:
                last_run = runs[0]
                completed_at = last_run.get("updated_at") or last_run.get("created_at")
                completed_dt = datetime.fromisoformat(completed_at.replace("Z", "+00:00"))
                age_days = (datetime.now(timezone.utc) - completed_dt).total_seconds() / 86400

            # Trigger workflow if no run exists or last run is too old
            if not runs or age_days >= 0.0001:  # 0.1 days ≈ 2.4 hours
                print("pre download")
                status_placeholder = st.empty()
                status_placeholder.markdown(
                    "<span style='color:red'>Updating ISS orbit data... please wait.</span>",
                    unsafe_allow_html=True
                )

                # Trigger GitHub Actions workflow
                success = trigger_orbit_update(workflow_file)
                print(f"success: {success}")
                if not success:
                    st.error("⚠️ Could not trigger TLE update workflow.")
                    status_placeholder.empty()
                    return False, False
                status_placeholder.empty()
                print("Updated ISS position")

    except (HTTPError, URLError, OSError, requests.RequestException) as e:
        print("couldnt update")
        st.error(f"⚠️ Could not update TLE ({e})")
        return False, False
    
    print("load_iss_data")
    # Load ISS position from online repo
    url = "https://raw.githubusercontent.com/NoahJens/sun_iss_transit/main/ISS.csv"
    r = requests.get(url)
    r.raise_for_status()
    data = json.loads(r.text)

    # Find the ISS row (using NORAD ID is safest)
    iss_row = next(row for row in data if row.get("NORAD_CAT_ID") == 25544)

    # Create the EarthSatellite object
    iss_geo = EarthSatellite.from_omm(ts, iss_row)
    epoch = convert_t(iss_geo.epoch)

    iss = earth + iss_geo
    return iss, epoch