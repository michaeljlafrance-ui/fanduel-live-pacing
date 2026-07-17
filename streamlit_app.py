import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="FanDuel Live Tracker", layout="wide")
st.title("🏀 FanDuel Live Quarter Predictive Engine")

RAPIDAPI_KEY = "932206dd22mshf288a41328bab03p12d137jsn9b24ebdfb34c"
RAPIDAPI_HOST = "odds-api-io-real-time-sports-betting-odds-api.p.rapidapi.com"

headers = {
    "X-RapidAPI-Key": RAPIDAPI_KEY,
    "X-RapidAPI-Host": RAPIDAPI_HOST,
    "Content-Type": "application/json"
}

if st.button("🔄 Refresh Live Boards", type="primary"):
    with st.spinner("Polling Odds-API.io..."):
        try:
            # STEP 1: Fetch Live Events
            url = f"https://{RAPIDAPI_HOST}/v2/events"
            res = requests.get(url, headers=headers, params={"status": "live", "sport": "basketball"})
            
            if res.status_code != 200:
                st.error(f"API Error: {res.status_code}")
                st.stop()
                
            data = res.json()
            if not data:
                st.info("No live basketball fixtures trading right now.")
                st.stop()
                
            id_map = {}
            id_list = []
            for ev in data:
                if ev and 'id' in ev:
                    ev_id = str(ev['id'])
                    id_list.append(ev_id)
                    id_map[ev_id] = {
                        "League": ev.get("league", "BASKETBALL").upper(),
                        "Matchup": f"{ev.get('away', 'Away')} @ {ev.get('home', 'Home')}".upper()
                    }
            
            if not id_list:
                st.warning("No active match IDs recovered.")
                st.stop()
                
            # STEP 2: Bulk Retrieve Odds
            odds_url = f"https://{RAPIDAPI_HOST}/v2/odds/multi"
            odds_res = requests.get(odds_url, headers=headers, params={"bookmakers": "FanDuel", "eventIds": ",".join(id_list)})
            
            if odds_res.status_code != 200:
                st.error("Odds pipeline down.")
                st.stop()
                
            odds_data = odds_res.json()
            rows = []
            
            # STEP 3: Single-Line Guard Rails to Avoid Truncation Errors
            for item in odds_data:
                if not item or 'bookmakers' not in item: continue
                m_id = str(item.get('id', item.get('eventId', '')))
                meta = id_map.get(m_id, {"League": "BASKETBALL", "Matchup": "LIVE FIXTURE"})
                
                bm = item['bookmakers']
                fd = bm.get('fanduel') or bm.get('FanDuel') or (bm[0] if isinstance(bm, list) and bm else None)
                if not fd: continue
                
                mkts = fd.get('markets') or fd.get('totals') or []
                mkt = mkts[0] if isinstance(mkts, list) and mkts else mkts
                if not mkt or 'outcomes' not in mkt: continue
                
                for out in mkt['outcomes']:
                    line = float(out.get('point') or out.get('line') or 0.0)
                    choice = out.get('name', 'OVER').upper()
                    q_pace = round(line / 4, 1)
                    alert = "⚠️ EXTENDED PACE: Target Under" if q_pace >= 54.5 else "NORMAL"
                    
                    rows.append(
