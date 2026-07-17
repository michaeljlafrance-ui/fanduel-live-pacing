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
        # Testing the alternative root sports endpoint to check valid paths
        u1 = f"https://{H}/v2/sports"
        res = requests.get(u1, headers=hd)
        
        if res.status_code != 200:
            st.error(f"API Error Code: {res.status_code}")
            st.warning(f"Server Raw Response: {res.text}")
            st.stop()
            
        data = res.json()
        
        # Display the raw active structure so we can see the exact strings
        st.success("Successfully connected to the API root!")
        st.write("Active Sports / Leagues Payload:")
        st.json(data)
            
    except Exception as e:
        st.error(f"Crash: {str(e)}")
