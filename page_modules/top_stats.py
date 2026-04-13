import streamlit as st
from utils.db_connection import execute_query

def top_stats_page():
    st.title("🏆 Top Player Stats")
    st.markdown("### Popular Cricket Statistics from Database")

    tab1, tab2, tab3 = st.tabs(["Top Run Scorers", "Top Wicket Takers", "Player Roles"])

    with tab1:
        st.subheader("Top 10 Run Scorers (All Formats)")
        query_runs = """
            SELECT TOP 10 
                p.full_name,
                p.playing_role,
                SUM(ps.runs_scored) AS total_runs,
                AVG(ps.strike_rate) AS avg_strike_rate
            FROM dbo.Player_Stats ps
            JOIN dbo.Players p ON ps.player_id = p.player_id
            GROUP BY p.full_name, p.playing_role
            ORDER BY total_runs DESC;
        """
        runs_data = execute_query(query_runs)
        if runs_data and len(runs_data) > 0:
            st.dataframe(runs_data, use_container_width=True)
        else:
            st.info("No batting stats available yet. Load detailed player stats next.")

    with tab2:
        st.subheader("Top 10 Wicket Takers")
        query_wickets = """
            SELECT TOP 10 
                p.full_name,
                p.playing_role,
                SUM(ps.wickets_taken) AS total_wickets,
                AVG(ps.economy_rate) AS avg_economy
            FROM dbo.Player_Stats ps
            JOIN dbo.Players p ON ps.player_id = p.player_id
            GROUP BY p.full_name, p.playing_role
            ORDER BY total_wickets DESC;
        """
        wickets_data = execute_query(query_wickets)
        if wickets_data and len(wickets_data) > 0:
            st.dataframe(wickets_data, use_container_width=True)
        else:
            st.info("No bowling stats available yet.")

    with tab3:
        st.subheader("Player Distribution by Role")
        query_roles = """
            SELECT 
                playing_role,
                COUNT(*) AS count
            FROM dbo.Players
            GROUP BY playing_role
            ORDER BY count DESC;
        """
        roles_data = execute_query(query_roles)
        if roles_data:
            st.dataframe(roles_data, use_container_width=True)
        else:
            st.info("No player data found.")

    st.caption("Note: Top stats will become more meaningful once we load detailed Player_Stats data.")
