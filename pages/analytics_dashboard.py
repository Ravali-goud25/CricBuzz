import streamlit as st
import pandas as pd
import plotly.express as px
from utils.db_connection import get_connection


st.set_page_config(
    page_title="Analytics Dashboard",
    page_icon="📈",
    layout="wide"
)

st.title("📈 Cricket Analytics Dashboard")
st.markdown("Interactive BI Dashboard powered by CricbuzzDB")

# ==========================================================
# DB
# ==========================================================
conn = get_connection()

# ==========================================================
# SIDEBAR FILTERS
# ==========================================================
st.sidebar.header("🎛 Dashboard Filters")

top_n = st.sidebar.slider(
    "Top N Records",
    min_value=5,
    max_value=25,
    value=10
)

# format filter
formats = pd.read_sql("""
SELECT DISTINCT ISNULL(match_format,'Unknown') AS fmt
FROM matches_completed
ORDER BY fmt
""", conn)["fmt"].tolist()

selected_formats = st.sidebar.multiselect(
    "Match Format",
    formats,
    default=formats
)

# series filter
series = pd.read_sql("""
SELECT DISTINCT series_name
FROM matches_completed
WHERE series_name IS NOT NULL
ORDER BY series_name
""", conn)["series_name"].tolist()

selected_series = st.sidebar.multiselect(
    "Series",
    series,
    default=[]
)

# year filter
years = pd.read_sql("""
SELECT DISTINCT YEAR(match_date) AS yr
FROM matches_completed
WHERE match_date IS NOT NULL
ORDER BY yr DESC
""", conn)["yr"].tolist()

selected_years = st.sidebar.multiselect(
    "Year",
    years,
    default=years
)

completed_only = st.sidebar.checkbox(
    "Completed Matches Only",
    value=True
)

# ==========================================================
# DYNAMIC WHERE CLAUSE
# ==========================================================
where = []

if selected_formats:
    fmt_vals = "','".join(selected_formats)
    where.append(f"ISNULL(match_format,'Unknown') IN ('{fmt_vals}')")

if selected_series:
    ser_vals = "','".join([x.replace("'", "''") for x in selected_series])
    where.append(f"series_name IN ('{ser_vals}')")

if selected_years:
    yr_vals = ",".join([str(x) for x in selected_years])
    where.append(f"YEAR(match_date) IN ({yr_vals})")

if completed_only:
    where.append("winner_team_id IS NOT NULL")

where_sql = "WHERE " + " AND ".join(where) if where else ""

# ==========================================================
# KPI SECTION
# ==========================================================
kpi_sql = f"""
SELECT
COUNT(*) AS total_matches,
COUNT(DISTINCT series_id) AS total_series,
COUNT(DISTINCT venue_id) AS total_venues,
COUNT(DISTINCT team1_id) + COUNT(DISTINCT team2_id) AS team_refs
FROM matches_completed
{where_sql}
"""

kpi = pd.read_sql(kpi_sql, conn).iloc[0]

c1, c2, c3, c4 = st.columns(4)

c1.metric("Matches", int(kpi["total_matches"]))
c2.metric("Series", int(kpi["total_series"]))
c3.metric("Venues", int(kpi["total_venues"]))
c4.metric("Team Refs", int(kpi["team_refs"]))

st.divider()

# ==========================================================
# ROW 1
# ==========================================================
col1, col2 = st.columns(2)

# ----------------------------------------------------------
# Team Wins
# ----------------------------------------------------------
with col1:
    st.subheader("🏆 Top Winning Teams")

    q = f"""
    SELECT TOP {top_n}
        t.team_name,
        COUNT(*) AS wins
    FROM matches_completed m
    JOIN teams t
      ON m.winner_team_id = t.team_id
    {where_sql}
    GROUP BY t.team_name
    ORDER BY wins DESC
    """

    df = pd.read_sql(q, conn)

    fig = px.bar(
        df,
        x="team_name",
        y="wins",
        text="wins",
        color="wins"
    )

    st.plotly_chart(fig, use_container_width=True)

# ----------------------------------------------------------
# Venue Usage
# ----------------------------------------------------------
with col2:
    st.subheader("🏟 Most Used Venues")

    q = f"""
    SELECT TOP {top_n}
        v.venue_name,
        COUNT(*) AS matches_played
    FROM matches_completed m
    JOIN venues v
      ON m.venue_id = v.venue_id
    {where_sql}
    GROUP BY v.venue_name
    ORDER BY matches_played DESC
    """

    df = pd.read_sql(q, conn)

    fig = px.bar(
        df,
        x="venue_name",
        y="matches_played",
        text="matches_played",
        color="matches_played"
    )

    st.plotly_chart(fig, use_container_width=True)

# ==========================================================
# ROW 2
# ==========================================================
col3, col4 = st.columns(2)

# ----------------------------------------------------------
# Top Run Scorers
# ----------------------------------------------------------
with col3:
    st.subheader("🏏 Top Run Scorers")

    q = f"""
    SELECT TOP {top_n}
        p.full_name,
        SUM(b.runs) AS runs
    FROM batting_innings b
    JOIN players p
      ON b.player_id = p.player_id
    JOIN matches_completed m
      ON b.match_id = m.match_id
    {where_sql}
    GROUP BY p.full_name
    ORDER BY runs DESC
    """

    df = pd.read_sql(q, conn)

    fig = px.bar(
        df,
        x="full_name",
        y="runs",
        text="runs",
        color="runs"
    )

    st.plotly_chart(fig, use_container_width=True)

# ----------------------------------------------------------
# Top Wicket Takers
# ----------------------------------------------------------
with col4:
    st.subheader("🎯 Top Wicket Takers")

    q = f"""
    SELECT TOP {top_n}
        p.full_name,
        SUM(bw.wickets) AS wickets
    FROM bowling_innings bw
    JOIN players p
      ON bw.player_id = p.player_id
    JOIN matches_completed m
      ON bw.match_id = m.match_id
    {where_sql}
    GROUP BY p.full_name
    ORDER BY wickets DESC
    """

    df = pd.read_sql(q, conn)

    fig = px.bar(
        df,
        x="full_name",
        y="wickets",
        text="wickets",
        color="wickets"
    )

    st.plotly_chart(fig, use_container_width=True)

# ==========================================================
# ROW 3
# ==========================================================
st.divider()

col5, col6 = st.columns(2)

# ----------------------------------------------------------
# Match Format Split
# ----------------------------------------------------------
with col5:
    st.subheader("📊 Match Format Distribution")

    q = f"""
    SELECT
        ISNULL(match_format,'Unknown') AS format,
        COUNT(*) AS total_matches
    FROM matches_completed
    {where_sql}
    GROUP BY match_format
    ORDER BY total_matches DESC
    """

    df = pd.read_sql(q, conn)

    fig = px.pie(
        df,
        names="format",
        values="total_matches",
        hole=0.45
    )

    st.plotly_chart(fig, use_container_width=True)

# ----------------------------------------------------------
# Win Type Split
# ----------------------------------------------------------
with col6:
    st.subheader("🥇 Win Type Distribution")

    q = f"""
    SELECT
        ISNULL(win_type,'Other') AS result_type,
        COUNT(*) AS total
    FROM matches_completed
    {where_sql}
    GROUP BY win_type
    ORDER BY total DESC
    """

    df = pd.read_sql(q, conn)

    fig = px.pie(
        df,
        names="result_type",
        values="total",
        hole=0.45
    )

    st.plotly_chart(fig, use_container_width=True)

# ==========================================================
# ROW 4
# ==========================================================
st.divider()

st.subheader("📅 Match Timeline")

q = f"""
SELECT
    match_date,
    COUNT(*) AS matches
FROM matches_completed
{where_sql}
GROUP BY match_date
ORDER BY match_date
"""

df = pd.read_sql(q, conn)

fig = px.line(
    df,
    x="match_date",
    y="matches",
    markers=True
)

st.plotly_chart(fig, use_container_width=True)

# ==========================================================
# FOOTER
# ==========================================================
conn.close()

st.caption("Powered by SQL Server + Streamlit + Plotly")