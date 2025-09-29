import streamlit as st
import requests
from skyfield.api import load, EarthSatellite
from utils import convert_t, trigger_orbit_update
from urllib.error import URLError, HTTPError
from datetime import datetime, timezone

# Load timescale for Skyfield 
ts = load.timescale()

# Load data for earth and sun from Skyfield bsp file 
planets = load('de421.bsp')
earth, sun = planets['earth'], planets['sun']

# Allow new download of ISS orbit data from Celestrak every max_days  
max_days = .1  

def load_iss_data(override):
    success = None # Variable for determining, if workflow successfully finished

    try:
        # Define data for fetching ISS orbit data CSV file from repo 
        owner = "NoahJens"
        repo = "sun_iss_transit"
        branch = "main"
        file_path = "ISS.csv"

        # Define data to check workflow execution
        workflow_file = "TLE_download.yml"
        headers = {"Authorization": f"token {st.secrets['GITHUB_TOKEN']}"}
        url_runs = f"https://api.github.com/repos/{owner}/{repo}/actions/workflows/{workflow_file}/runs"
        params = {"branch": "main", "per_page": 1}

        # Check time of last workflow run, when override is engaged 
        if override:          
            r = requests.get(url_runs, headers=headers, params=params)
            r.raise_for_status()
            runs = r.json().get("workflow_runs", [])
            
            age_days = None # Variable to store how long last workflow is in the past
            success = False 

            # Calculate elapsed time since last workflow and store in age_days
            if runs:
                last_run = runs[0]
                completed_at = last_run.get("updated_at") or last_run.get("created_at")
                completed_dt = datetime.fromisoformat(completed_at.replace("Z", "+00:00"))
                age_days = (datetime.now(timezone.utc) - completed_dt).total_seconds() / 86400

            # Trigger workflow if no run exists or last run is too old
            if not runs or age_days >= max_days:
                status_placeholder = st.empty()
                status_placeholder.markdown(
                    "<span style='color:red'>Updating ISS orbit data... please wait</span>",
                    unsafe_allow_html=True
                )
                repo_state_before = requests.get(f"https://api.github.com/repos/{owner}/{repo}/commits/main", 
                                                 headers=headers).json()["sha"]
                
                success = trigger_orbit_update(workflow_file) # trigger workflow for updating ISS orbit data

                repo_state_after = requests.get(f"https://api.github.com/repos/{owner}/{repo}/commits/main", 
                                                headers=headers).json()["sha"]
                
                if not success:
                    st.error("⚠️ Could not trigger ISS orbit data update workflow or workflow failed")
                    status_placeholder.empty()
                    return 
                
                status_placeholder.empty()

    except (HTTPError, URLError, OSError) as e:
        st.error(f"⚠️ Could not update ISS orbit data ({e})")
        return 
    
    url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{file_path}"
    r = requests.get(url)
    r.raise_for_status()
    data = r.json() 

    # # Load last commit of repo (new CSV file was automatically committed by workflow)
    # url_commit = f"https://api.github.com/repos/{owner}/{repo}/commits?path={file_path}&sha={branch}"
    # r = requests.get(url_commit)
    # r.raise_for_status()
    # latest_commit_sha = r.json()[0]["sha"]

    # # Fetch CSV at that commit
    # url_raw_commit = f"https://raw.githubusercontent.com/{owner}/{repo}/{latest_commit_sha}/{file_path}"
    # r = requests.get(url_raw_commit)
    # r.raise_for_status()
    # data = r.json()

    # Find the ISS row 
    iss_row = next(row for row in data if row.get("NORAD_CAT_ID") == 25544)

    # Create the EarthSatellite object
    iss_geo = EarthSatellite.from_omm(ts, iss_row) # gets the geocentric information on the ISS
    epoch = convert_t(iss_geo.epoch) # Convert epoch to CEST time 

    iss = earth + iss_geo

    # Print info messages, if ISS orbit data has been updated 
    if success == False: 
        st.info("Orbit data is up to date")
    elif success == True: 
        if repo_state_before == repo_state_after: 
            st.info("No new orbit data available")
        else:
            st.success(f"Orbit data has been updated (epoch: {epoch})")
    return iss, epoch
