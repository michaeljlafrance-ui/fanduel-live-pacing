import streamlit as st
import requests
import pandas as pd

st.set_page_config(layout="wide")
st.title("🏀 FanDuel Live Pacing Engine")

K = "932206dd22mshf288a41328bab03p12d137jsn9b24ebdfb34c"
H = "odds-api-io-real-time-sports-betting-odds-api.p.rapidapi.com"

hd = {
    "X-RapidAPI-Key": K,
    "X-RapidAPI-Host": H,
    "Content-Type": "application/json"
}

if st.button("🔄 Refresh Live Boards", type="primary"):
    try:
        # STEP 1: Fetch Live Events using specific league routing rules
        u1 = f"https://{H}/v2/events"
        p1 = {
            "status": "pending,live",
            "sport": "basketball",
            "league": "usa-nba"  # Aligned to match dashboard structure requirements
        }
        res = requests.get(u1, headers=hd, params=p1)
        
        if res.status_code != 200:
            st.error(f"API Error Code: {res.status_code}")
            st.warning(f"Server Raw Response: {res.text}")
            st.stop()
            
        data = res.json()
        if not data:
            st.info("No active games found trading under this league right now.")
            st.stop()
            
        id_map = {}
        id_list = []
        for ev in data:
            if ev and 'id' in ev:
                eid = str(ev['id'])
                id_list.append(eid)
                id_map[eid] = {
                    "L": ev.get("league", "BASKETBALL"),
                    "M": f"{ev.get('away')} @ {ev.get('home')}"
                }
        
        # STEP 2: Bulk Retrieve Odds
        u2 = f"https://{H}/v2/odds/multi"
        p2 = {"bookmakers": "FanDuel", "eventIds": ",".join(id_list)}
        ores = requests.get(u2, headers=hd, params=p2)
        
        if ores.status_code != 200:
            st.error("Odds pipeline down.")
            st.stop()
            
        odata = ores.json()
        rows = []
        
        # STEP 3: Parse Data
        for item in odata:
            if not item or 'bookmakers' not in item:
                continue
            mid = str(item.get('id', item.get('eventId', '')))
            meta = id_map.get(mid, {"L": "NBA", "M": "LIVE MATCH"})
            
            bm = item['bookmakers']
            fd = bm.get('fanduel') or bm.get('FanDuel')
            if not fd:
                continue
            
            mkts = fd.get('markets') or fd.get('totals') or []
            mkt = mkts[0] if isinstance(mkts, list) else mkts
            if not mkt or 'outcomes' not in mkt:
                continue
            
            for out in mkt['outcomes']:
                line = float(out.get('point') or 0.0)
                lbl = out.get('name', 'OVER').upper()
                qp = round(line / 4, 1)
                alt = "⚠️ EXTENDED" if qp >= 54.5 else "NORMAL"
                
                r = []
                r.append(mid)
                r.append(meta["L"].upper())
                r.append(meta["M"].upper())
                r.append(f"TOTAL ({lbl})")
                r.append(line)
                r.append(qp)
                r.append(alt)
                rows.append(r)
                
        if rows:
            cols = ["ID", "League", "Matchup", "Market", "Line", "Q Pace", "Alert"]
            df = pd.DataFrame(rows, columns=cols)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No active lines open on FanDuel.")
            
    except Exception as e:
        st.error(f"Crash: {str(e)}")
