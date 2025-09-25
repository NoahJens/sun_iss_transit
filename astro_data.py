from skyfield.api import load, EarthSatellite, Angle, wgs84
from utils import convert_t, trigger_orbit_update
from urllib.error import URLError, HTTPError
import streamlit as st
import json
import requests
from datetime import datetime, timezone
import time

ts = load.timescale()

planets = load('de421.bsp')
earth, sun = planets['earth'], planets['sun']

# Load ISS position data from CelesTrak
max_days = .1    # download again once 7 days old
# name = 'ISS.csv'  # custom filename, not 'gp.php'

import requests
import json
from datetime import datetime, timezone

def load_iss_data(override):
    success = None 
    st.write("override {override}")
    try:
        owner = "NoahJens"
        repo = "sun_iss_transit"
        file_path = "ISS.csv"
        branch = "main"
        workflow_file = "TLE_download.yml"
        headers = {"Authorization": f"token {st.secrets['GITHUB_TOKEN']}"}
        url_runs = f"https://api.github.com/repos/{owner}/{repo}/actions/workflows/{workflow_file}/runs"
        params = {"branch": "main", "per_page": 1}

        # Check last workflow run instead of commit date
        if override:          
            r = requests.get(url_runs, headers=headers, params=params)
            r.raise_for_status()
            st.write("override = True")
            runs = r.json().get("workflow_runs", [])
            
            age_days = None

            success = False 

            if runs:
                last_run = runs[0]
                st.write(f"last run: {last_run['id']}")
                print(f"last run: {last_run['id']}")
                completed_at = last_run.get("updated_at") or last_run.get("created_at")
                completed_dt = datetime.fromisoformat(completed_at.replace("Z", "+00:00"))
                age_days = (datetime.now(timezone.utc) - completed_dt).total_seconds() / 86400
                print(f"age days: {age_days}")
            st.write(f"age_days: {age_days}")

            # Trigger workflow if no run exists or last run is too old
            if not runs or age_days >= max_days:  # 0.1 days ≈ 2.4 hours
                status_placeholder = st.empty()
                status_placeholder.markdown(
                    "<span style='color:red'>Updating ISS orbit data... please wait</span>",
                    unsafe_allow_html=True
                )

                # Trigger GitHub Actions workflow
                print("trigger update")
                repo_state_before = requests.get(f"https://api.github.com/repos/{owner}/{repo}/commits/main", headers=headers).json()["sha"]
                success = trigger_orbit_update(workflow_file)
                repo_state_after = requests.get(f"https://api.github.com/repos/{owner}/{repo}/commits/main", headers=headers).json()["sha"]
                print(f"success: {success}")
                if not success:
                    st.error("⚠️ Could not trigger TLE update workflow or workflow failed")
                    status_placeholder.empty()
                    return 
                status_placeholder.empty()

    except (HTTPError, URLError, OSError) as e:
        print("couldnt update")
        st.error(f"⚠️ Could not update TLE ({e})")
        return 
    
    print("load_iss_data")
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

    if success == False: 
        st.info("Orbit data is up to date")
    elif success == True: 
        if repo_state_before == repo_state_after: 
            st.info("No new orbit data available")
        else:
            st.success(f"Orbit data has been updated (epoch: {epoch})")
    return iss, epoch
