import streamlit as st
import pandas as pd
from utils.db_connection import get_connection



st.set_page_config(page_title="SQL Queries", page_icon="📊", layout="wide")

st.title("📊 SQL Practice Queries")
st.markdown("Run analytical SQL queries directly on your CricbuzzDB database.")

# ==========================================================
# QUERY DICTIONARY
# ==========================================================
queries = {

    "Question 1 - Players representing India":
    {
        "question": """
Find all players who represent India.
Display full name, playing role, batting style, bowling style.
""",

        "sql": """
SELECT
    p.full_name,
    p.playing_role,
    p.batting_style,
    p.bowling_style
FROM players p
JOIN teams t
    ON p.team_id = t.team_id
WHERE t.team_name = 'India'
ORDER BY p.full_name;
"""
    },

    # ------------------------------------------------------

    "Question 2 - Matches played in last 30 days":
    {
        "question": """
Show matches played in last 30 days with teams and venue.
""",

        "sql": """
SELECT
    m.match_desc,
    t1.team_name AS team1,
    t2.team_name AS team2,
    v.venue_name,
    v.city,
    m.match_date
FROM matches_completed m
LEFT JOIN teams t1
    ON m.team1_id = t1.team_id
LEFT JOIN teams t2
    ON m.team2_id = t2.team_id
LEFT JOIN venues v
    ON m.venue_id = v.venue_id
WHERE m.match_date >= DATEADD(DAY, -30, GETDATE())
ORDER BY m.match_date DESC;
"""
    },

    # ------------------------------------------------------

    "Question 3 - Top 10 run scorers":
    {
        "question": """
Top 10 highest run scorers using batting_innings.
""",

        "sql": """
SELECT TOP 10
    p.full_name,
    SUM(b.runs) AS total_runs,
    ROUND(AVG(CAST(b.runs AS FLOAT)),2) AS avg_runs,
    SUM(CASE WHEN b.runs >= 100 THEN 1 ELSE 0 END) AS centuries
FROM batting_innings b
JOIN players p
    ON b.player_id = p.player_id
GROUP BY p.full_name
ORDER BY total_runs DESC;
"""
    },

    # ------------------------------------------------------

    "Question 4 - Venues capacity > 50000":
    {
        "question": """
Display venues with capacity > 50000.
""",

        "sql": """
SELECT
    venue_name,
    city,
    country,
    capacity
FROM venues
WHERE capacity > 50000
ORDER BY capacity DESC;
"""
    },

    # ------------------------------------------------------

    "Question 5 - Team wins count":
    {
        "question": """
How many matches each team has won.
""",

        "sql": """
SELECT
    t.team_name,
    COUNT(*) AS total_wins
FROM matches_completed m
JOIN teams t
    ON m.winner_team_id = t.team_id
GROUP BY t.team_name
ORDER BY total_wins DESC;
"""
    },

    # ------------------------------------------------------

    "Question 6 - Players by role":
    {
        "question": """
Count players by playing role.
""",

        "sql": """
SELECT
    ISNULL(playing_role,'Unknown') AS playing_role,
    COUNT(*) AS player_count
FROM players
GROUP BY playing_role
ORDER BY player_count DESC;
"""
    },

    # ------------------------------------------------------

    "Question 7 - Highest individual score by format":
    {
        "question": """
Highest batting score in each format.
""",

        "sql": """
SELECT
    m.match_format,
    MAX(b.runs) AS highest_score
FROM batting_innings b
JOIN matches_completed m
    ON b.match_id = m.match_id
GROUP BY m.match_format
ORDER BY highest_score DESC;
"""
    },

    # ------------------------------------------------------

    "Question 8 - Series started in 2024":
    {
        "question": """
Show all series started in year 2024.
""",

        "sql": """
SELECT
    series_name,
    host_country,
    match_format,
    start_date,
    total_matches
FROM series
WHERE YEAR(start_date) = 2024
ORDER BY start_date;
"""
    },

# ------------------------------------------------------

"Question 9 - All rounders with runs and wickets":
{
    "question": """
Players with more than 100 runs and 5 wickets.
""",

    "sql": """
SELECT
    p.full_name,
    SUM(ISNULL(b.runs,0)) AS total_runs,
    SUM(ISNULL(bw.wickets,0)) AS total_wickets
FROM players p
LEFT JOIN batting_innings b
    ON p.player_id = b.player_id
LEFT JOIN bowling_innings bw
    ON p.player_id = bw.player_id
GROUP BY p.full_name
HAVING SUM(ISNULL(b.runs,0)) > 100
   AND SUM(ISNULL(bw.wickets,0)) >= 5
ORDER BY total_runs DESC;
"""
},

# ------------------------------------------------------

"Question 10 - Last 20 completed matches":
{
    "question": """
Show last 20 completed matches with winner.
""",

    "sql": """
SELECT TOP 20
    m.match_desc,
    t1.team_name AS team1,
    t2.team_name AS team2,
    tw.team_name AS winner,
    m.win_margin,
    m.win_type,
    m.match_date
FROM matches_completed m
LEFT JOIN teams t1
    ON m.team1_id = t1.team_id
LEFT JOIN teams t2
    ON m.team2_id = t2.team_id
LEFT JOIN teams tw
    ON m.winner_team_id = tw.team_id
ORDER BY m.match_date DESC;
"""
},

# ------------------------------------------------------

"Question 11 - Player runs across formats":
{
    "question": """
Compare player total runs across formats.
""",

    "sql": """
SELECT
    p.full_name,

SUM(CASE WHEN m.match_format='Test'
THEN b.runs ELSE 0 END) AS Test_Runs,

SUM(CASE WHEN m.match_format='ODI'
THEN b.runs ELSE 0 END) AS ODI_Runs,

SUM(CASE WHEN m.match_format LIKE '%T20%'
THEN b.runs ELSE 0 END) AS T20_Runs,

ROUND(AVG(CAST(b.runs AS FLOAT)),2) avg_runs

FROM batting_innings b
JOIN players p
    ON b.player_id = p.player_id
JOIN matches_completed m
    ON b.match_id = m.match_id
GROUP BY p.full_name
ORDER BY avg_runs DESC;
"""
},

# ------------------------------------------------------

"Question 12 - Home vs Away wins":
{
    "question": """
Wins by teams at venues in same country.
""",

    "sql": """
SELECT
    t.team_name,
    COUNT(*) AS wins
FROM matches_completed m
JOIN teams t
    ON m.winner_team_id = t.team_id
GROUP BY t.team_name
ORDER BY wins DESC;
"""
},

# ------------------------------------------------------

"Question 13 - 100+ batting partnerships":
{
    "question": """
Consecutive batting positions with 100+ combined runs.
""",

    "sql": """
SELECT
    p1.full_name AS batter1,
    p2.full_name AS batter2,
    b1.match_id,
    b1.innings_no,
    (b1.runs + b2.runs) AS partnership_runs
FROM batting_innings b1
JOIN batting_innings b2
    ON b1.match_id = b2.match_id
   AND b1.innings_no = b2.innings_no
   AND b2.batting_position = b1.batting_position + 1
JOIN players p1
    ON b1.player_id = p1.player_id
JOIN players p2
    ON b2.player_id = p2.player_id
WHERE (b1.runs + b2.runs) >= 100
ORDER BY partnership_runs DESC;
"""
},

# ------------------------------------------------------

"Question 14 - Venue bowling performance":
{
    "question": """
Bowler performance by venue.
""",

    "sql": """
SELECT
    p.full_name,
    v.venue_name,
    COUNT(*) matches_played,
    SUM(bw.wickets) wickets,
    ROUND(AVG(bw.economy),2) avg_economy
FROM bowling_innings bw
JOIN players p
    ON bw.player_id = p.player_id
JOIN matches_completed m
    ON bw.match_id = m.match_id
JOIN venues v
    ON m.venue_id = v.venue_id
GROUP BY p.full_name, v.venue_name
HAVING COUNT(*) >= 2
ORDER BY wickets DESC;
"""
},

# ------------------------------------------------------

"Question 15 - Close match batting performers":
{
    "question": """
Players in close matches.
""",

    "sql": """
SELECT
    p.full_name,
    COUNT(*) innings_played,
    ROUND(AVG(CAST(b.runs AS FLOAT)),2) avg_runs
FROM batting_innings b
JOIN players p
    ON b.player_id = p.player_id
JOIN matches_completed m
    ON b.match_id = m.match_id
WHERE m.win_type IN ('runs','wickets')
GROUP BY p.full_name
ORDER BY avg_runs DESC;
"""
},

# ------------------------------------------------------

"Question 16 - Year wise batting performance":
{
    "question": """
Year-wise batting average since 2020.
""",

    "sql": """
SELECT
    YEAR(m.match_date) AS match_year,
    p.full_name,
    COUNT(*) innings,
    ROUND(AVG(CAST(b.runs AS FLOAT)),2) avg_runs,
    ROUND(AVG(b.strike_rate),2) avg_sr
FROM batting_innings b
JOIN players p
    ON b.player_id = p.player_id
JOIN matches_completed m
    ON b.match_id = m.match_id
WHERE YEAR(m.match_date) >= 2020
GROUP BY YEAR(m.match_date), p.full_name
HAVING COUNT(*) >= 2
ORDER BY match_year DESC, avg_runs DESC;
"""
},

# ------------------------------------------------------

"Question 17 - Toss advantage analysis":
{
    "question": """
Percentage of matches won by toss-winning team.
""",

    "sql": """
SELECT
    toss_decision,
    COUNT(*) AS total_matches,
    SUM(CASE
        WHEN toss_winner_team_id = winner_team_id THEN 1
        ELSE 0
    END) AS toss_won_matches,
    ROUND(
        100.0 *
        SUM(CASE
            WHEN toss_winner_team_id = winner_team_id THEN 1
            ELSE 0
        END) / COUNT(*),2
    ) AS win_pct
FROM matches_completed
WHERE toss_winner_team_id IS NOT NULL
GROUP BY toss_decision;
"""
},

# ------------------------------------------------------

"Question 18 - Most economical bowlers":
{
    "question": """
Best bowlers in ODI/T20 by economy.
""",

    "sql": """
SELECT
    p.full_name,
    COUNT(*) matches_bowled,
    SUM(bw.wickets) wickets,
    ROUND(AVG(bw.economy),2) avg_economy
FROM bowling_innings bw
JOIN players p
    ON bw.player_id = p.player_id
JOIN matches_completed m
    ON bw.match_id = m.match_id
WHERE m.match_format IN ('ODI','T20I','T20')
GROUP BY p.full_name
HAVING COUNT(*) >= 2
ORDER BY avg_economy ASC;
"""
},

# ------------------------------------------------------

"Question 19 - Most consistent batsmen":
{
    "question": """
Average runs and standard deviation.
Lower stdev = more consistent.
""",

    "sql": """
SELECT
    p.full_name,
    COUNT(*) innings,
    ROUND(AVG(CAST(b.runs AS FLOAT)),2) avg_runs,
    ROUND(STDEV(CAST(b.runs AS FLOAT)),2) consistency_score
FROM batting_innings b
JOIN players p
    ON b.player_id = p.player_id
GROUP BY p.full_name
HAVING COUNT(*) >= 2
ORDER BY consistency_score ASC;
"""
},

# ------------------------------------------------------

"Question 20 - Matches by format":
{
    "question": """
Matches played by player across formats.
""",

    "sql": """
SELECT
    p.full_name,

SUM(CASE WHEN m.match_format='Test' THEN 1 ELSE 0 END) AS Test_Matches,
SUM(CASE WHEN m.match_format='ODI' THEN 1 ELSE 0 END) AS ODI_Matches,
SUM(CASE WHEN m.match_format LIKE '%T20%' THEN 1 ELSE 0 END) AS T20_Matches,

ROUND(AVG(CAST(b.runs AS FLOAT)),2) avg_runs

FROM batting_innings b
JOIN players p
    ON b.player_id = p.player_id
JOIN matches_completed m
    ON b.match_id = m.match_id
GROUP BY p.full_name
HAVING COUNT(*) >= 2
ORDER BY avg_runs DESC;
"""
},

# ------------------------------------------------------

"Question 21 - Overall player ranking":
{
    "question": """
Combined batting + bowling score.
""",

    "sql": """
SELECT TOP 20
    p.full_name,

    SUM(ISNULL(b.runs,0))*0.01 +
    AVG(ISNULL(b.runs,0))*0.5 +
    AVG(ISNULL(b.strike_rate,0))*0.3 +

    SUM(ISNULL(bw.wickets,0))*2 +
    (6-AVG(ISNULL(bw.economy,6)))*2

    AS total_score

FROM players p
LEFT JOIN batting_innings b
    ON p.player_id = b.player_id
LEFT JOIN bowling_innings bw
    ON p.player_id = bw.player_id

GROUP BY p.full_name
ORDER BY total_score DESC;
"""
},

# ------------------------------------------------------

"Question 22 - Head to head records":
{
    "question": """
Head-to-head between team pairs.
""",

    "sql": """
SELECT
    t1.team_name AS team1,
    t2.team_name AS team2,
    COUNT(*) matches_played,
    SUM(CASE WHEN winner_team_id = team1_id THEN 1 ELSE 0 END) team1_wins,
    SUM(CASE WHEN winner_team_id = team2_id THEN 1 ELSE 0 END) team2_wins
FROM matches_completed m
JOIN teams t1
    ON m.team1_id = t1.team_id
JOIN teams t2
    ON m.team2_id = t2.team_id
GROUP BY t1.team_name, t2.team_name
HAVING COUNT(*) >= 1
ORDER BY matches_played DESC;
"""
},

# ------------------------------------------------------

"Question 23 - Recent player form":
{
    "question": """
Last innings performance trend.
""",

    "sql": """
WITH cte AS
(
SELECT
    p.full_name,
    b.runs,
    ROW_NUMBER() OVER(
        PARTITION BY p.full_name
        ORDER BY b.match_id DESC
    ) rn
FROM batting_innings b
JOIN players p
    ON b.player_id = p.player_id
)

SELECT
    full_name,
    COUNT(*) innings,
    ROUND(AVG(CAST(runs AS FLOAT)),2) avg_recent_runs
FROM cte
WHERE rn <= 5
GROUP BY full_name
HAVING COUNT(*) >= 2
ORDER BY avg_recent_runs DESC;
"""
},

# ------------------------------------------------------

"Question 24 - Best batting partnerships":
{
    "question": """
Most successful consecutive batting pairs.
""",

    "sql": """
SELECT TOP 20
    p1.full_name AS batter1,
    p2.full_name AS batter2,
    COUNT(*) partnerships,
    ROUND(AVG(b1.runs + b2.runs),2) avg_partnership,
    MAX(b1.runs + b2.runs) highest_partnership
FROM batting_innings b1
JOIN batting_innings b2
    ON b1.match_id = b2.match_id
   AND b1.innings_no = b2.innings_no
   AND b2.batting_position = b1.batting_position + 1
JOIN players p1
    ON b1.player_id = p1.player_id
JOIN players p2
    ON b2.player_id = p2.player_id
GROUP BY p1.full_name, p2.full_name
ORDER BY avg_partnership DESC;
"""
},

# ------------------------------------------------------

"Question 25 - Quarterly performance trend":
{
    "question": """
Quarter-wise batting performance.
""",

    "sql": """
SELECT
    YEAR(m.match_date) AS yr,
    DATEPART(QUARTER,m.match_date) AS qtr,
    p.full_name,
    COUNT(*) innings,
    ROUND(AVG(CAST(b.runs AS FLOAT)),2) avg_runs,
    ROUND(AVG(b.strike_rate),2) avg_sr
FROM batting_innings b
JOIN players p
    ON b.player_id = p.player_id
JOIN matches_completed m
    ON b.match_id = m.match_id
GROUP BY
    YEAR(m.match_date),
    DATEPART(QUARTER,m.match_date),
    p.full_name
HAVING COUNT(*) >= 1
ORDER BY yr DESC, qtr DESC, avg_runs DESC;
"""
},

}

# ==========================================================
# UI SELECTOR
# ==========================================================
selected_query = st.selectbox(
    "Choose Query",
    list(queries.keys())
)

query_info = queries[selected_query]

# ==========================================================
# SHOW QUESTION
# ==========================================================
st.subheader("📌 Problem Statement")
st.info(query_info["question"])

# ==========================================================
# SHOW SQL
# ==========================================================
with st.expander("📄 View SQL Query"):
    st.code(query_info["sql"], language="sql")

# ==========================================================
# RUN QUERY
# ==========================================================
if st.button("▶ Run Query"):

    try:
        conn = get_connection()

        df = pd.read_sql(query_info["sql"], conn)

        st.success("Query Executed Successfully")

        st.dataframe(
            df,
            use_container_width=True
        )

        conn.close()

    except Exception as e:
        st.error(f"Error: {e}")