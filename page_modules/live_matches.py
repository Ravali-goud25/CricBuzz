import streamlit as st
from utils.db_connection import execute_query

def live_matches_page():
    st.title("🏏 Live & Recent Matches")
    st.markdown("### Real-time Match Updates from Cricbuzz")

    query = """
        SELECT 
            m.match_id,
            m.match_description,
            m.match_type,
            CONVERT(VARCHAR(20), m.match_date, 120) AS match_date_str,
            COALESCE(t1.team_name, 'Team ' + CAST(COALESCE(m.team1_id, 0) AS VARCHAR(10))) AS team1_name,
            COALESCE(t2.team_name, 'Team ' + CAST(COALESCE(m.team2_id, 0) AS VARCHAR(10))) AS team2_name,
            COALESCE(v.venue_name, 'Venue ' + CAST(COALESCE(m.venue_id, 0) AS VARCHAR(10))) AS venue_name,
            COALESCE(v.city, '') AS city
        FROM dbo.Matches m
        LEFT JOIN dbo.Teams t1 ON m.team1_id = t1.team_id
        LEFT JOIN dbo.Teams t2 ON m.team2_id = t2.team_id
        LEFT JOIN dbo.Venues v ON m.venue_id = v.venue_id
        ORDER BY ISNULL(m.match_date, '1900-01-01') DESC
    """

    matches = execute_query(query)

    if matches and len(matches) > 0:
        st.success(f"Showing {len(matches)} matches")
        for match in matches:
            with st.expander(f"**{match.get('match_description', 'Match')}** - {match.get('match_type', 'N/A')}"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown(f"**{match['team1_name']} vs {match['team2_name']}**")
                with col2:
                    venue_str = match['venue_name']
                    if match.get('city'):
                        venue_str += f", {match['city']}"
                    st.write(f"📍 {venue_str}")
                with col3:
                    st.write(f"🗓️ {match.get('match_date_str', 'N/A')}")
                st.caption(f"Match ID: {match['match_id']}")
    else:
        st.warning("No matches found. Go to Home → Store Matches first.")

    if st.button("🔄 Refresh Matches"):
        st.rerun()