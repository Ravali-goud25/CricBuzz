import streamlit as st
import pandas as pd
import pyodbc

# ==========================================================
# DB CONNECTION
# ==========================================================
def get_connection():
    conn = pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=RAVALI;"
        "DATABASE=CricbuzzDB;"
        "Trusted_Connection=yes;"
    )
    return conn


# ==========================================================
# PAGE CONFIG
# ==========================================================
st.set_page_config(
    page_title="Player CRUD",
    page_icon="👤",
    layout="wide"
)

st.title("👤 Player Analytics CRUD Page")
st.markdown("Create | Read | Update | Delete Players")

conn = get_connection()
cursor = conn.cursor()

# ==========================================================
# SIDEBAR MENU
# ==========================================================
menu = st.sidebar.radio(
    "Choose Operation",
    ["Create", "Read", "Update", "Delete"]
)

# ==========================================================
# CREATE
# ==========================================================
if menu == "Create":

    st.subheader("➕ Add New Player")

    col1, col2 = st.columns(2)

    with col1:
        player_id = st.number_input("Player ID", step=1)
        full_name = st.text_input("Full Name")
        short_name = st.text_input("Short Name")
        team_id = st.number_input("Team ID", step=1)

    with col2:
        country = st.text_input("Country")
        role = st.text_input("Playing Role")
        batting = st.text_input("Batting Style")
        bowling = st.text_input("Bowling Style")

    if st.button("Insert Player"):

        try:
            cursor.execute("""
                INSERT INTO players
                (
                    player_id,
                    full_name,
                    short_name,
                    team_id,
                    country,
                    playing_role,
                    batting_style,
                    bowling_style,
                    source
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            player_id,
            full_name,
            short_name,
            team_id,
            country,
            role,
            batting,
            bowling,
            "streamlit")

            conn.commit()
            st.success("Player inserted successfully.")

        except Exception as e:
            st.error(str(e))


# ==========================================================
# READ
# ==========================================================
elif menu == "Read":

    st.subheader("📄 View Players")

    q = """
    SELECT
        player_id,
        full_name,
        short_name,
        country,
        playing_role,
        batting_style,
        bowling_style
    FROM players
    ORDER BY full_name
    """

    df = pd.read_sql(q, conn)
    st.dataframe(df, use_container_width=True)


# ==========================================================
# UPDATE
# ==========================================================
elif menu == "Update":

    st.subheader("✏️ Update Player")

    ids = pd.read_sql(
        "SELECT player_id, full_name FROM players ORDER BY full_name",
        conn
    )

    selected = st.selectbox(
        "Select Player",
        ids["full_name"]
    )

    row = ids[ids["full_name"] == selected].iloc[0]
    pid = int(row["player_id"])

    country = st.text_input("New Country")
    role = st.text_input("New Role")
    batting = st.text_input("New Batting Style")
    bowling = st.text_input("New Bowling Style")

    if st.button("Update Player"):

        try:
            cursor.execute("""
                UPDATE players
                SET country = ?,
                    playing_role = ?,
                    batting_style = ?,
                    bowling_style = ?
                WHERE player_id = ?
            """,
            country,
            role,
            batting,
            bowling,
            pid)

            conn.commit()
            st.success("Player updated successfully.")

        except Exception as e:
            st.error(str(e))


# ==========================================================
# DELETE
# ==========================================================
elif menu == "Delete":

    st.subheader("🗑 Delete Player")

    ids = pd.read_sql(
        "SELECT player_id, full_name FROM players ORDER BY full_name",
        conn
    )

    selected = st.selectbox(
        "Select Player to Delete",
        ids["full_name"]
    )

    row = ids[ids["full_name"] == selected].iloc[0]
    pid = int(row["player_id"])

    if st.button("Delete Player"):

        try:
            cursor.execute(
                "DELETE FROM players WHERE player_id = ?",
                pid
            )

            conn.commit()
            st.success("Player deleted successfully.")

        except Exception as e:
            st.error(str(e))

# ==========================================================
# CLOSE
# ==========================================================
conn.close()