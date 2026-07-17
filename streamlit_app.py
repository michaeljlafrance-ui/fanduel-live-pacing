import streamlit as st
import requests
import pandas as pd

# App Configuration
st.set_page_config(page_title="FanDuel Live Basketball Tracker", layout="wide")
st.title("🏀 FanDuel Live Quarter Predictive Engine")
st.write("Real-time basketball market monitoring and automated pacing analysis.")

# Secret Credentials
RAPIDAPI_KEY = "932206dd22mshf288a41328bab03p12d137jsn9b24ebdfb34c"
RAPIDAPI_HOST = "odds-api-io-real-time-sports-betting-odds-api.p.rapidapi.com"

headers = {
    "X-RapidAPI-Key": RAPIDAPI_KEY,
    "X-RapidAPI-Host": RAPIDAPI_HOST,
    "Content-Type": "application/json"
}

if st.button("🔄 Refresh Live Boards", type="primary"):
    with st.spinner("Fetching live games from Odds-API.io..."):
        try:
            # STEP 1: Fetch Active Live Events matching explicit dashboard filters
            events_url = f"https://{RAPIDAPI_HOST}/v2/events"
            events_params = {
                "status": "live",
                "sport": "basketball"
            }
            
            events_res = requests.get(events_url, headers=headers, params=events_params)
            
            # Direct diagnostics: show raw payload on 404 to see routing demands
            if events_res.status_code != 200:
                st.error(f"Events Index Error: {events_res.status_code}")
                st.warning(f"Server Routing Response: {events_res.text}")
                st.info("If the response reads '404 page not found', the endpoint needs custom league constraints.")
                st.stop()
                
            events_data = events_res.json()
            
            if not events_data:
                st.info("No live basketball fixtures actively trading right now.")
                st.stop()
                
            id_map = {}
            id_list = []
            
            for ev in events_data:
                if not ev or 'id' not in ev:
                    continue
                ev_id = str(ev['id'])
                id_list.append(ev_id)
                id_map[ev_id] = {
                    "League": ev.get("league", "BASKETBALL").upper(),
                    "Matchup": f"{ev.get('away', 'Away')} @ {ev.get('home', 'Home')}".upper()
                }
                
            if not id_list:
                st.warning("Found live fixtures, but they are missing structural API keys.")
                st.stop()
                
            # STEP 2: Bulk Retrieve Odds via Multi Endpoint
            encoded_ids = ",".join(id_list)
            odds_url = f"https://{RAPIDAPI_HOST}/v2/odds/multi"
