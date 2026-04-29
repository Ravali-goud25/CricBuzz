import streamlit as st
import pandas as pd
import requests
import time

st.set_page_config(page_title="Live Matches", page_icon="🏏", layout="wide")

st.title("🏏 Live Matches")
st.caption("Simple live match browser")

API_KEY = "fd0b4ba094msh2df730c6efcc7d6p1fdd65jsne9c47c33d0c8"
API_HOST = "cricbuzz-cricket.p.rapidapi.com"

BASE = "https://cricbuzz-cricket.p.rapidapi.com"
HEADERS = {
    "X-RapidAPI-Key": API_KEY,
    "X-RapidAPI-Host": API_HOST
}

@st.cache_data(ttl=60)
def fetch_live():
    try:
        r = requests.get(
            BASE + "/matches/v1/live",
            headers=HEADERS,
            timeout=20
        )
        return r.json()
    except:
        return {}

def parse_live(data):
    rows = []

    for tm in data.get("typeMatches", []):
        for sm in tm.get("seriesMatches", []):
            wrap = sm.get("seriesAdWrapper")
            if not wrap:
                continue

            for m in wrap.get("matches", []):

                info = m.get("matchInfo", {})
                score = m.get("matchScore", {})

                t1 = info.get("team1", {}).get("teamName")
                t2 = info.get("team2", {}).get("teamName")

                s1 = score.get("team1Score", {}).get("inngs1", {})
                s2 = score.get("team2Score", {}).get("inngs1", {})

                rows.append({
                    "Match ID": info.get("matchId"),
                    "Series": info.get("seriesName"),
                    "Match": f"{t1} vs {t2}",
                    "Score 1": f"{s1.get('runs','')}/{s1.get('wickets','')}",
                    "Score 2": f"{s2.get('runs','')}/{s2.get('wickets','')}",
                    "Status": info.get("status")
                })

    return pd.DataFrame(rows)

if st.button("Refresh"):
    st.cache_data.clear()

data = fetch_live()
df = parse_live(data)

if df.empty:
    st.info("No live matches currently.")
else:
    st.dataframe(df, use_container_width=True, height=600)