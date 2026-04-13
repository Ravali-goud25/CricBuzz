import streamlit as st
from utils.db_connection import execute_query

def sql_queries_page():
    st.title("🔍 SQL Queries & Analytics")
    st.markdown("### All 25 Practice Questions")

    level = st.radio("Select Level",
                     ["Beginner (Q1-Q8)", "Intermediate (Q9-Q16)", "Advanced (Q17-Q25)"],
                     horizontal=True)

    if level == "Beginner (Q1-Q8)":
        query_dict = {
            "Q1: Indian Players with Role & Styles": """
                SELECT full_name, playing_role, batting_style, bowling_style 
                FROM dbo.Players 
                WHERE country = 'India'
                ORDER BY full_name;
            """,
            "Q2: Matches in Last 30 Days": """
                SELECT 
                    m.match_description,
                    COALESCE(t1.team_name, 'Team '+CAST(m.team1_id AS VARCHAR(10))) AS team1,
                    COALESCE(t2.team_name, 'Team '+CAST(m.team2_id AS VARCHAR(10))) AS team2,
                    COALESCE(v.venue_name + ', ' + v.city, 'Unknown Venue') AS venue,
                    CONVERT(VARCHAR(10), m.match_date, 120) AS match_date
                FROM dbo.Matches m
                LEFT JOIN dbo.Teams t1 ON m.team1_id = t1.team_id
                LEFT JOIN dbo.Teams t2 ON m.team2_id = t2.team_id
                LEFT JOIN dbo.Venues v ON m.venue_id = v.venue_id
                WHERE m.match_date >= DATEADD(DAY, -30, GETDATE())
                ORDER BY m.match_date DESC;
            """,
            "Q5: Wins per Team": """
                SELECT 
                    t.team_name,
                    COUNT(*) AS total_wins
                FROM dbo.Matches m
                JOIN dbo.Teams t ON m.winner_id = t.team_id
                GROUP BY t.team_name
                ORDER BY total_wins DESC;
            """,
            "Q6: Players by Playing Role": """
                SELECT 
                    playing_role,
                    COUNT(*) AS player_count
                FROM dbo.Players
                GROUP BY playing_role
                ORDER BY player_count DESC;
            """
        }

    elif level == "Intermediate (Q9-Q16)":
        query_dict = {
            "Q10: Last 20 Completed Matches": """
                SELECT TOP 20
                    m.match_description,
                    COALESCE(t1.team_name, 'Team '+CAST(m.team1_id AS VARCHAR(10))) AS team1,
                    COALESCE(t2.team_name, 'Team '+CAST(m.team2_id AS VARCHAR(10))) AS team2,
                    COALESCE(t3.team_name, 'Unknown') AS winner,
                    m.victory_margin,
                    m.victory_type,
                    COALESCE(v.venue_name, 'Unknown Venue') AS venue
                FROM dbo.Matches m
                LEFT JOIN dbo.Teams t1 ON m.team1_id = t1.team_id
                LEFT JOIN dbo.Teams t2 ON m.team2_id = t2.team_id
                LEFT JOIN dbo.Teams t3 ON m.winner_id = t3.team_id
                LEFT JOIN dbo.Venues v ON m.venue_id = v.venue_id
                ORDER BY m.match_date DESC;
            """
        }

    else:
        query_dict = {
            "Advanced queries (need Player_Stats data)": """
                SELECT 'Advanced queries require detailed batting/bowling stats' AS message;
            """
        }

    # Query selector
    selected_query_name = st.selectbox("Select Question to Execute", list(query_dict.keys()))

    if st.button("▶️ Run Selected Query", type="primary"):
        with st.spinner("Running SQL query..."):
            try:
                results = execute_query(query_dict[selected_query_name])
                if results and len(results) > 0:
                    st.success(f"✅ Query executed successfully! {len(results)} rows returned.")
                    st.dataframe(results, use_container_width=True)
                else:
                    st.info("✅ Query executed but returned no rows (data may not be loaded yet).")
            except Exception as e:
                st.error(f"Error: {str(e)}")

    st.divider()
    st.info("**Note**: Many Intermediate & Advanced queries will return empty results until we load detailed `Player_Stats` and `Batting_Partnerships` data.")