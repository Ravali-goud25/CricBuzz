import streamlit as st
import pandas as pd
import requests
import time

from utils.db_connection import get_connection


st.set_page_config(
    page_title="Top Stats",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Top Stats Dashboard")
st.markdown("Hybrid analytics using SQL Server + Live Cricbuzz API")

# ==========================================================
# CONFIG
# ==========================================================
API_KEY = "fd0b4ba094msh2df730c6efcc7d6p1fdd65jsne9c47c33d0c8"
API_HOST = "cricbuzz-cricket.p.rapidapi.com"

BASE_URL = "https://cricbuzz-cricket.p.rapidapi.com"

HEADERS = {
    "X-RapidAPI-Key": API_KEY,
    "X-RapidAPI-Host": API_HOST
}

# ==========================================================
# SAFE API FETCHER
# ==========================================================
@st.cache_data(ttl=1800)
def fetch_api(endpoint):
    """
    Cached for 30 mins
    Prevent excessive API hits
    """

    url = BASE_URL + endpoint

    try:
        time.sleep(1.5)   # polite delay

        r = requests.get(
            url,
            headers=HEADERS,
            timeout=20
        )

        if r.status_code == 429:
            return {"error": "Rate Limited"}

        if r.status_code != 200:
            return {"error": f"HTTP {r.status_code}"}

        return r.json()

    except Exception as e:
        return {"error": str(e)}

# ==========================================================
# SQL CONNECTION
# ==========================================================
conn = get_connection()

# ==========================================================
# TABS
# ==========================================================
tab1, tab2, tab3 = st.tabs([
    "🏏 SQL Top Stats",
    "🌐 Live API Stats",
    "🏆 ICC Rankings"
])

# ==========================================================
# TAB 1 SQL TOP STATS
# ==========================================================
with tab1:

    st.subheader("Top Batters")

    q1 = """
    SELECT TOP 10
        p.full_name,
        SUM(b.runs) AS total_runs,
        COUNT(*) AS innings,
        ROUND(AVG(CAST(b.runs AS FLOAT)),2) AS avg_runs
    FROM batting_innings b
    JOIN players p ON b.player_id = p.player_id
    GROUP BY p.full_name
    ORDER BY total_runs DESC;
    """

    df1 = pd.read_sql(q1, conn)
    st.dataframe(df1, use_container_width=True)

    st.subheader("Top Bowlers")

    q2 = """
    SELECT TOP 10
        p.full_name,
        SUM(wickets) AS wickets,
        COUNT(*) AS innings,
        ROUND(AVG(CAST(economy AS FLOAT)),2) AS economy
    FROM bowling_innings bw
    JOIN players p ON bw.player_id = p.player_id
    GROUP BY p.full_name
    ORDER BY wickets DESC;
    """

    df2 = pd.read_sql(q2, conn)
    st.dataframe(df2, use_container_width=True)

    st.subheader("Most Successful Teams")

    q3 = """
    SELECT TOP 10
        t.team_name,
        COUNT(*) AS wins
    FROM matches_completed m
    JOIN teams t
        ON m.winner_team_id = t.team_id
    GROUP BY t.team_name
    ORDER BY wins DESC;
    """

    df3 = pd.read_sql(q3, conn)
    st.dataframe(df3, use_container_width=True)

# ==========================================================
# TAB 2 LIVE API STATS
# ==========================================================
with tab2:

    st.subheader("Live Cricbuzz Top Stats")

    stat_type = st.selectbox(
        "Choose Stat",
        ["mostRuns", "mostWickets", "highestScore"]
    )

    endpoint = f"/stats/v1/topstats/0?statsType={stat_type}"

    data = fetch_api(endpoint)

    if "error" in data:
        st.error(data["error"])

    else:
        rows = []

        raw_rows = data.get("values", [])

        for item in raw_rows[:15]:

            vals = item.get("values", [])

            player = vals[0] if len(vals) > 0 else None
            team   = vals[1] if len(vals) > 1 else None
            value  = vals[-1] if len(vals) > 0 else None

            rows.append({
                "Player": player,
                "Team": team,
                "Value": value
            })

        if rows:
            st.dataframe(
                pd.DataFrame(rows),
                use_container_width=True
            )
        else:
            st.warning("No stats returned.")

# ==========================================================
# TAB 3 ICC RANKINGS
# ==========================================================
with tab3:

    st.subheader("ICC Player Rankings")

    role = st.selectbox(
        "Role",
        [
            "batsmen",
            "bowlers",
            "allrounders"
        ]
    )

    format_type = st.selectbox(
        "Format",
        [
            "test",
            "odi",
            "t20"
        ]
    )

    endpoint = f"/stats/v1/rankings/{role}?formatType={format_type}"

    data = fetch_api(endpoint)

    if "error" in data:
        st.error(data["error"])

    else:
        rows = []

        for item in data.get("rank", [])[:15]:

            rows.append({
                "Rank": item.get("rank"),
                "Player": item.get("name"),
                "Country": item.get("country"),
                "Rating": item.get("rating")
            })

        if rows:
            st.dataframe(
                pd.DataFrame(rows),
                use_container_width=True
            )
        else:
            st.info("No ranking data available.")

# ==========================================================
# FOOTER
# ==========================================================
conn.close()

st.caption("SQL data = historical warehouse | API data = fresh Cricbuzz feed")