import streamlit as st
import pandas as pd
from utils.db_connection import get_connection

#===================================================

st.set_page_config(
    page_title="Teams & Players",
    page_icon="🏏",
    layout="wide"
)

st.title("🏏 Teams & Players Explorer")
st.markdown("Browse teams, squads, and player details from CricbuzzDB.")

# ==========================================================
# DB CONNECTION
# ==========================================================
conn = get_connection()

# ==========================================================
# LOAD TEAMS
# ==========================================================
teams_sql = """
SELECT
    team_id,
    team_name
FROM teams
ORDER BY team_name;
"""

teams_df = pd.read_sql(teams_sql, conn)

team_names = teams_df["team_name"].tolist()

# ==========================================================
# SIDEBAR FILTERS
# ==========================================================
st.sidebar.header("Filters")

selected_team = st.sidebar.selectbox(
    "Select Team",
    team_names
)

selected_team_id = int(
    teams_df.loc[
        teams_df["team_name"] == selected_team,
        "team_id"
    ].values[0]
)

role_list = [
    "All",
    "Batsman",
    "Bowler",
    "All-rounder",
    "Wicket-keeper"
]

selected_role = st.sidebar.selectbox(
    "Playing Role",
    role_list
)

search_name = st.sidebar.text_input(
    "Search Player Name"
)

# ==========================================================
# TEAM SUMMARY
# ==========================================================
st.subheader(f"📌 {selected_team}")

summary_sql = f"""
SELECT
    COUNT(*) AS squad_size
FROM players
WHERE team_id = {selected_team_id};
"""

summary_df = pd.read_sql(summary_sql, conn)

col1, col2 = st.columns(2)

col1.metric(
    "Team Name",
    selected_team
)

col2.metric(
    "Squad Size",
    int(summary_df.iloc[0,0])
)

st.divider()

# ==========================================================
# PLAYER QUERY
# ==========================================================
players_sql = f"""
SELECT
    full_name,
    ISNULL(playing_role,'Unknown') AS playing_role,
    ISNULL(batting_style,'-') AS batting_style,
    ISNULL(bowling_style,'-') AS bowling_style
FROM players
WHERE team_id = {selected_team_id}
"""

if selected_role != "All":
    players_sql += f"""
AND playing_role = '{selected_role}'
"""

if search_name.strip():
    players_sql += f"""
AND full_name LIKE '%{search_name.strip()}%'
"""

players_sql += """
ORDER BY full_name;
"""

players_df = pd.read_sql(players_sql, conn)

# ==========================================================
# DISPLAY PLAYERS
# ==========================================================
st.subheader("👥 Squad Players")

st.dataframe(
    players_df,
    use_container_width=True
)

# ==========================================================
# PLAYER STATS SECTION
# ==========================================================
st.divider()

st.subheader("📈 Individual Player Stats")

player_list = players_df["full_name"].tolist()

if len(player_list) > 0:

    selected_player = st.selectbox(
        "Choose Player",
        player_list
    )

    player_stats_sql = f"""
    SELECT
        p.full_name,

        COUNT(DISTINCT b.match_id) AS matches_batted,
        SUM(ISNULL(b.runs,0)) AS total_runs,
        ROUND(AVG(CAST(b.runs AS FLOAT)),2) AS avg_runs,
        MAX(ISNULL(b.runs,0)) AS highest_score,

        SUM(ISNULL(bw.wickets,0)) AS total_wickets,
        ROUND(AVG(CAST(bw.economy AS FLOAT)),2) AS avg_economy

    FROM players p
    LEFT JOIN batting_innings b
        ON p.player_id = b.player_id
    LEFT JOIN bowling_innings bw
        ON p.player_id = bw.player_id

    WHERE p.full_name = '{selected_player}'

    GROUP BY p.full_name;
    """

    stats_df = pd.read_sql(
        player_stats_sql,
        conn
    )

    if not stats_df.empty:

        r = stats_df.iloc[0]

        c1, c2, c3, c4 = st.columns(4)

        c1.metric("Runs", int(r["total_runs"]))
        c2.metric("Avg Runs", r["avg_runs"])
        c3.metric("Wickets", int(r["total_wickets"]))
        c4.metric("Best Score", int(r["highest_score"]))

        st.dataframe(
            stats_df,
            use_container_width=True
        )

else:
    st.warning("No players found for filter.")

# ==========================================================
# CLOSE
# ==========================================================
conn.close()