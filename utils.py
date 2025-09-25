from skyfield.api import load, Topos, EarthSatellite, Angle, wgs84
import pytz
from skyfield.timelib import Time
from datetime import datetime
import requests
import streamlit as st
import time

def angular_separation(t, observer, sun, iss):
    """Angular separation (degrees) between Sun and ISS as seen by observer"""
    sun_vec = observer.at(t).observe(sun).apparent()
    iss_vec = observer.at(t).observe(iss).apparent()

    sun_alt, sun_az, sun_dist = sun_vec.altaz()
    sun_alt = sun_alt.degrees
    
    return sun_vec.separation_from(iss_vec).degrees, sun_alt

def convert_t(t):
    """
    Convert a Skyfield Time or a datetime object to Berlin time and format as string.
    """
    if isinstance(t, Time):  # Skyfield Time object
        t_utc = t.utc_datetime()
    elif isinstance(t, datetime):  # regular datetime
        t_utc = t
    else:
        raise TypeError("t must be a Skyfield Time or datetime object")

    t_berlin = t_utc.astimezone(pytz.timezone('Europe/Berlin'))
    return t_berlin.strftime("%Y-%m-%d %H:%M:%S %Z")

# Check number of decimal places
def decimal_places(value):
    s = str(value)
    if '.' in s:
        return len(s.split('.')[-1])
    else:
        return 0

def trigger_orbit_update(workflow: str, branch: str = "main") -> bool:
    token = st.secrets["GITHUB_TOKEN"]
    owner = "NoahJens"
    repo = "sun_iss_transit"

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json"
    }
    
    # 1️⃣ Trigger workflow
    url_dispatch = f"https://api.github.com/repos/{owner}/{repo}/actions/workflows/{workflow}/dispatches"
    r = requests.post(url_dispatch, headers=headers, json={"ref": branch})
    if r.status_code != 204:
        st.error(f"Failed to trigger workflow: {r.status_code} {r.text}")
        return False

    # 2️⃣ Wait for a new run to appear
    url_runs = f"https://api.github.com/repos/{owner}/{repo}/actions/workflows/{workflow}/runs"
    params = {"branch": branch, "per_page": 1}

    new_run_id = None
    while new_run_id is None:
        r = requests.get(url_runs, headers=headers, params=params)
        runs = r.json()["workflow_runs"]
        # print(f"runs: {runs}")

        if runs:
            run = runs[0]
            if run["status"] in ["queued", "in_progress"]:
                new_run_id = run["id"]
        time.sleep(3)
        print(f"run ID: {new_run_id}")

    # 3️⃣ Poll that specific run until completed
    url_run = f"https://api.github.com/repos/{owner}/{repo}/actions/runs/{new_run_id}"
    while True:
        r = requests.get(url_run, headers=headers)
        run = r.json()
        print(f"run status: {run["status"]}")
        if run["status"] == "completed":
            print(f"run conclusion: {run["conclusion"]}")
            if run["conclusion"] == "success":
                time.sleep(5) # wait for csv file to update
                return True
            else:
                # st.error(f"Workflow failed")
                return False
        time.sleep(5)