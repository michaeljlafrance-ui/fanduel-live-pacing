import streamlit as st
import requests
import pandas as pd

# App Configuration
st.set_page_config(page_title="FanDuel Live Basketball Tracker", layout="wide")
st.title("🏀 FanDuel Live Quarter Predictive Engine")
st.write("Real-time basketball market monitoring and automated pacing analysis.")

# Secret Credentials (Configured via Streamlit Dashboard or hardcoded)
RAPIDAPI_KEY = "932206dd22mshf288a41328bab03p12d137jsn9b24ebdfb34c"
RAPIDAPI_HOST = "odds-api-io-real-time-sports-betting-odds-api.p.rapidapi.com"

# Setup Request Headers
headers = {
    "X-RapidAPI-Key": RAPIDAPI_KEY,
    "X-RapidAPI-Host": RAPIDAPI_HOST,
    "Content-Type": "application/json"
}

# Manual Refresh Button
if st.button("🔄 Refresh Live Boards", type="primary"):
    with st.spinner("Fetching live games from Odds-API.io..."):
        try:
            # STEP 1: Fetch Active Live Events
            events_url = f"https://{RAPIDAPI_HOST}/v2/events"
            events_params = {"status": "live", "sport": "basketball"}
            
            events_res = requests.get(events_url, headers=headers, params=events_params)
            
            if events_res.status_code != 200:
                st.error(f"Events Index Error: {events_res.status_code} - {events_res.text}")
                st.stop()
                
            events_data = events_res.json()
            
            if not events_data:
                st.info("No live basketball fixtures actively trading right now.")
                st.stop()
                
            # Process Live Game IDs and Metadata Map
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
            odds_params = {"bookmakers": "FanDuel", "eventIds": encoded_ids}
            
            odds_res = requests.get(oddsUrl, headers=headers, params=odds_params)
            
            if odds_res.status_code != 200:
                st.error(f"Multi-Odds Retrieval Error: {odds_res.status_code}")
                st.stop()
                
            odds_data = odds_res.json()
            rows = []
            
            # STEP 3: Parse FanDuel Totals and Run Analytics Engine
            for item in odds_data:
                if not item or 'bookmakers' not in item:
                    continue
                    
                m_id = str(item.get('id', item.get('eventId', '')))
                meta = id_map.get(m_id, {"League": "BASKETBALL", "Matchup": "LIVE FIXTURE"})
                
                # Extract FanDuel Node
                bookmakers = item['bookmakers']
                fd_book = bookmakers.get('fanduel') or bookmakers.get('FanDuel')
                
                if not fd_book and isinstance(bookmakers, list) and len(bookmakers) > 0:
                    fd_book = bookmakers[0]
                    
                if not fd_book:
                    continue
                    
                # Extract Markets Array
                markets = fd_book.get('markets') or fd_book.get('totals') or []
                target_mkt = markets[0] if isinstance(markets, list) and len(markets) > 0 else markets
                
                if not target_mkt or 'outcomes' not in target_mkt:
                    continue
                    
                for out in target_mkt['outcomes']:
                    line_val = out.get('point') or out.get('line') or 0.0
                    choice = out.get('name', 'OVER').upper()
                    
                    # Pacing Projections (Replicating sheet formulas in Python)
                    implied_match_pace = float(line_val)
                    implied_quarter_pace = round(implied_match_pace / 4, 1)
                    
                    # Target Alert Generator
                    alert_flag = "NORMAL PACE"
                    if implied_quarter_pace >= 54.5:
                        alert_flag = "⚠️ EXTENDED PACE: Target Quarter Under Spot"
                        
                    rows.append({
                        "Event ID": m_id,
                        "League": meta["League"],
                        "Matchup": meta["Matchup"],
                        "Market Option": f"TOTAL ({choice})",
                        "FanDuel Line": implied_match_pace,
                        "Implied Match Pace": implied_match_pace,
                        "Implied Quarter Pace": implied_quarter_pace,
                        "Alert Flag": alert_flag
                    })
                    
            # STEP 4: Render Interactive Matrix Display
            if rows:
                df = pd.DataFrame(rows)
                
                # Highlight alerts or high priority rows styled visually
                def highlight_alerts(val):
                    color = 'background-color: #ffcccc; color: #cc0000; font-weight: bold;' if 'EXTENDED' in str(val) else ''
                    return color
                
                styled_df = df.style.map(highlight_alerts, subset=['Alert Flag'])
                
                st.subheader(f"⚡ Active Live Grid ({len(df)} lines monitored)")
                st.dataframe(styled_df, use_container_width=True, hide_index=True)
                
            else:
                st.info("No live basketball Totals open on FanDuel at this time.")
                
        except Exception as e:
            st.error(f"Python Pipeline Crash: {str(e)}")
else:
    st.write("Click the refresh button above to poll the live API endpoints.")
