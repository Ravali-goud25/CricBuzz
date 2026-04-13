import streamlit as st
from utils.db_connection import execute_query

def crud_operations_page():
    st.title("🛠️ CRUD Operations")
    st.markdown("### Manage Player Records (Create, Read, Update, Delete)")

    tab1, tab2, tab3, tab4 = st.tabs(["Create Player", "View All Players", "Update Player", "Delete Player"])

    # ====================== CREATE ======================
    with tab1:
        st.subheader("Add New Player")
        with st.form("add_player_form"):
            full_name = st.text_input("Full Name")
            playing_role = st.selectbox("Playing Role", ["Batsman", "Bowler", "All-rounder", "Wicket-keeper"])
            batting_style = st.text_input("Batting Style (e.g., Right-hand bat)")
            bowling_style = st.text_input("Bowling Style (e.g., Right-arm offbreak)")
            country = st.text_input("Country", value="India")
            player_id = st.number_input("Player ID (unique)", min_value=1, step=1)

            submitted = st.form_submit_button("Add Player")
            if submitted:
                if full_name and player_id:
                    query = """
                        INSERT INTO dbo.Players (player_id, full_name, playing_role, batting_style, bowling_style, country)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """
                    result = execute_query(query, (player_id, full_name, playing_role, batting_style, bowling_style, country), fetch=False)
                    if result and result.get("status") == "success":
                        st.success(f"✅ Player '{full_name}' added successfully!")
                    else:
                        st.error("Failed to add player.")
                else:
                    st.warning("Full Name and Player ID are required.")

    # ====================== READ ======================
    with tab2:
        st.subheader("All Players in Database")
        if st.button("Refresh Player List"):
            players = execute_query("SELECT * FROM dbo.Players ORDER BY full_name")
            if players:
                st.dataframe(players, use_container_width=True)
            else:
                st.info("No players found.")

    # ====================== UPDATE ======================
    with tab3:
        st.subheader("Update Player")
        player_id_update = st.number_input("Enter Player ID to Update", min_value=1)
        if st.button("Load Player Details"):
            player = execute_query("SELECT * FROM dbo.Players WHERE player_id = ?", (player_id_update,))
            if player:
                st.session_state.player_to_update = player[0]
            else:
                st.error("Player not found.")

        if 'player_to_update' in st.session_state:
            p = st.session_state.player_to_update
            with st.form("update_form"):
                new_name = st.text_input("Full Name", value=p['full_name'])
                new_role = st.selectbox("Role", ["Batsman", "Bowler", "All-rounder", "Wicket-keeper"],
                                      index=["Batsman", "Bowler", "All-rounder", "Wicket-keeper"].index(p['playing_role']) if p['playing_role'] in ["Batsman", "Bowler", "All-rounder", "Wicket-keeper"] else 0)
                new_bat = st.text_input("Batting Style", value=p.get('batting_style', ''))
                new_bowl = st.text_input("Bowling Style", value=p.get('bowling_style', ''))
                new_country = st.text_input("Country", value=p.get('country', 'India'))

                if st.form_submit_button("Update Player"):
                    update_query = """
                        UPDATE dbo.Players 
                        SET full_name=?, playing_role=?, batting_style=?, bowling_style=?, country=?
                        WHERE player_id=?
                    """
                    result = execute_query(update_query, (new_name, new_role, new_bat, new_bowl, new_country, player_id_update), fetch=False)
                    if result and result.get("status") == "success":
                        st.success("✅ Player updated successfully!")
                        del st.session_state.player_to_update
                    else:
                        st.error("Update failed.")

    # ====================== DELETE ======================
    with tab4:
        st.subheader("Delete Player")
        delete_id = st.number_input("Player ID to Delete", min_value=1)
        if st.button("Delete Player", type="primary"):
            if st.checkbox("I confirm I want to delete this player"):
                delete_query = "DELETE FROM dbo.Players WHERE player_id = ?"
                result = execute_query(delete_query, (delete_id,), fetch=False)
                if result and result.get("status") == "success":
                    st.success(f"✅ Player with ID {delete_id} deleted.")
                else:
                    st.error("Delete failed or player not found.")