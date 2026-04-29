import streamlit as st
import requests
import pandas as pd
from datetime import datetime



st.set_page_config(
    page_title="Live Scoreboard",
    page_icon="📺",
    layout="wide"
)

# ==========================================================
# API CONFIG
# ==========================================================
API_KEY = "fd0b4ba094msh2df730c6efcc7d6p1fdd65jsne9c47c33d0c8"
API_HOST = "cricbuzz-cricket.p.rapidapi.com"
BASE_URL = "https://cricbuzz-cricket.p.rapidapi.com"

HEADERS = {
    "X-RapidAPI-Key": API_KEY,
    "X-RapidAPI-Host": API_HOST
}

# ==========================================================
# CSS
# ==========================================================
st.markdown("""
<style>

.main{
background:#f7f8fc;
}

.block-container{
max-width:1450px;
padding-top:1rem;
padding-bottom:2rem;
}

h1,h2,h3{
font-family:Arial;
}

.hero{
background:linear-gradient(135deg,#25115c,#ef476f);
padding:34px;
border-radius:22px;
color:white;
box-shadow:0 12px 24px rgba(0,0,0,.10);
text-align:center;
}

.card{
background:white;
padding:20px;
border-radius:18px;
box-shadow:0 6px 16px rgba(0,0,0,.06);
border:1px solid #eceff5;
}

.metric-title{
font-size:14px;
color:#6b7280;
font-weight:600;
}

.metric-value{
font-size:40px;
font-weight:800;
color:#0f2ea8;
}

.metric-small{
font-size:18px;
font-weight:700;
color:#111827;
}

.section{
background:white;
padding:18px;
border-radius:18px;
box-shadow:0 6px 16px rgba(0,0,0,.06);
border:1px solid #eceff5;
}

.blue{
color:#2563eb;
font-weight:800;
font-size:28px;
}

.purple{
color:#4338ca;
font-weight:800;
font-size:28px;
}

.red{
color:#ef4444;
font-weight:800;
font-size:28px;
}

.footer{
background:white;
padding:14px 18px;
border-radius:14px;
border:1px solid #eceff5;
box-shadow:0 6px 16px rgba(0,0,0,.05);
font-size:14px;
color:#6b7280;
}

.smallbox{
background:#f5f3ff;
padding:14px;
border-radius:12px;
text-align:center;
font-weight:700;
color:#4338ca;
margin-bottom:10px;
}

</style>
""", unsafe_allow_html=True)

# ==========================================================
# FETCH
# ==========================================================
@st.cache_data(ttl=20)
def fetch(endpoint):
    try:
        r = requests.get(
            BASE_URL + endpoint,
            headers=HEADERS,
            timeout=20
        )
        return r.json()
    except:
        return {}

# ==========================================================
# LIVE MATCHES
# ==========================================================
def get_live_matches():

    data = fetch("/matches/v1/live")
    rows = []

    for tm in data.get("typeMatches", []):
        for sm in tm.get("seriesMatches", []):

            wrap = sm.get("seriesAdWrapper")
            if not wrap:
                continue

            for m in wrap.get("matches", []):

                info = m.get("matchInfo", {})
                score = m.get("matchScore", {})

                rows.append({
                    "match_id": info.get("matchId"),
                    "display":
                    f"{info.get('team1',{}).get('teamName')} vs "
                    f"{info.get('team2',{}).get('teamName')} | "
                    f"{info.get('matchDesc')}",

                    "team1": info.get("team1", {}).get("teamName"),
                    "team2": info.get("team2", {}).get("teamName"),
                    "status": info.get("status"),
                    "series": info.get("seriesName"),
                    "score": score
                })

    return rows

# ==========================================================
# SCORE PARSER
# ==========================================================
def parse_score(obj):

    if not obj:
        return "-", "-", "-"

    inns = obj.get("inngs1", {})

    return (
        inns.get("runs", "-"),
        inns.get("wickets", "-"),
        inns.get("overs", "-")
    )

def runrate(runs, overs):
    try:
        runs = float(runs)
        overs = float(overs)
        if overs == 0:
            return "-"
        return round(runs / overs, 2)
    except:
        return "-"

# ==========================================================
# PAGE
# ==========================================================
st.title("📺 Live Scoreboard")

if st.button("🔄 Refresh"):
    st.cache_data.clear()

matches = get_live_matches()

if not matches:
    st.warning("No live matches.")
    st.stop()

selected = st.selectbox(
    "Choose Match",
    [x["display"] for x in matches]
)

row = [x for x in matches if x["display"] == selected][0]

match_id = row["match_id"]

# ==========================================================
# SCORECARD API
# ==========================================================
scard = fetch(f"/mcenter/v1/{match_id}/scard")

cards = scard.get("scoreCard", [])
if not cards:
    cards = scard.get("scorecard", [])

# ==========================================================
# SCORES
# ==========================================================
r1,w1,o1 = parse_score(row["score"].get("team1Score", {}))
r2,w2,o2 = parse_score(row["score"].get("team2Score", {}))

rr1 = runrate(r1,o1)
rr2 = runrate(r2,o2)

# ==========================================================
# HERO
# ==========================================================
st.markdown(f"""
<div class='hero'>
<h1 style='margin:0;font-size:58px;'>LIVE SCOREBOARD</h1>
<h2 style='margin-top:18px;'>{selected}</h2>
<h2 style='margin-top:10px;color:#ffd166;'>Live</h2>
</div>
""", unsafe_allow_html=True)

st.write("")

# ==========================================================
# KPI ROW
# ==========================================================
c1,c2,c3,c4 = st.columns(4)

with c1:
    st.markdown(f"""
    <div class='card'>
    <div class='metric-title'>{row['team1']}</div>
    <div class='metric-value'>{r1}/{w1}</div>
    <div class='metric-small'>{o1} ov</div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class='card'>
    <div class='metric-title'>Run Rate</div>
    <div class='metric-value'>{rr1}</div>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div class='card'>
    <div class='metric-title'>{row['team2']}</div>
    <div class='metric-value'>{r2}/{w2}</div>
    <div class='metric-small'>{o2} ov</div>
    </div>
    """, unsafe_allow_html=True)

with c4:
    st.markdown(f"""
    <div class='card'>
    <div class='metric-title'>Run Rate</div>
    <div class='metric-value'>{rr2}</div>
    </div>
    """, unsafe_allow_html=True)

st.write("")

# ==========================================================
# BATTING + ANALYTICS
# ==========================================================
left,right = st.columns([3,1.5])

bats = []
bowls = []

if cards:
    bats = cards[0].get("batsman", [])
    bowls = cards[0].get("bowler", [])

# ----------------------------------------------------------
# BATTING TABLE
# ----------------------------------------------------------
with left:

    st.markdown("<div class='section'><div class='blue'>🎯 Batting</div></div>", unsafe_allow_html=True)

    rows = []

    for b in bats[:8]:
        rows.append({
            "Player": b.get("name"),
            "R": b.get("runs"),
            "B": b.get("balls"),
            "4s": b.get("fours"),
            "6s": b.get("sixes"),
            "SR": b.get("strkrate")
        })

    if rows:
        st.dataframe(
            pd.DataFrame(rows),
            use_container_width=True,
            height=340
        )

# ----------------------------------------------------------
# PLAYER ANALYTICS
# ----------------------------------------------------------
with right:

    st.markdown("<div class='section'><div class='purple'>⭐ Player Analytics</div></div>", unsafe_allow_html=True)

    if bats:

        p = bats[0]

        st.markdown(f"<div class='smallbox'>Top Player<br>{p.get('name')}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='smallbox'>Runs<br>{p.get('runs')}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='smallbox'>Balls<br>{p.get('balls')}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='smallbox'>Strike Rate<br>{p.get('strkrate')}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='smallbox'>Fours<br>{p.get('fours')}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='smallbox'>Sixes<br>{p.get('sixes')}</div>", unsafe_allow_html=True)

st.write("")

# ==========================================================
# BOWLING
# ==========================================================
st.markdown("<div class='section'><div class='red'>🎯 Bowling</div></div>", unsafe_allow_html=True)

rows = []

for b in bowls[:8]:
    rows.append({
        "Bowler": b.get("name"),
        "O": b.get("overs"),
        "R": b.get("runs"),
        "W": b.get("wickets"),
        "Eco": b.get("economy")
    })

if rows:
    st.dataframe(
        pd.DataFrame(rows),
        use_container_width=True,
        height=280
    )

st.write("")

# ==========================================================
# FOOTER
# ==========================================================
now = datetime.now().strftime("%I:%M:%S %p")

l,r = st.columns([4,1])

with l:
    st.markdown(
        f"<div class='footer'>🕒 Last Updated: {now}</div>",
        unsafe_allow_html=True
    )

with r:
    st.markdown(
        "<div class='footer'>🟢 Live Data</div>",
        unsafe_allow_html=True
    )