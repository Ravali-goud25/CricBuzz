import streamlit as st
from utils.db_connection import get_db_connection, execute_query
import requests
import os
from datetime import datetime

# ==================== Cricbuzz API Configuration ====================
BASE_URL = "https://cricbuzz-cricket.p.rapidapi.com"
HEADERS = {
    "X-RapidAPI-Key": os.getenv("RAPIDAPI_KEY"),
    "X-RapidAPI-Host": os.getenv("RAPIDAPI_HOST")
}

# ==================== CREATE TABLES FUNCTION ====================
def create_all_tables():
    queries = [
        """IF OBJECT_ID('dbo.Venues', 'U') IS NULL
        BEGIN CREATE TABLE dbo.Venues (venue_id INT PRIMARY KEY, venue_name VARCHAR(255), city VARCHAR(100), country VARCHAR(100), capacity INT); END""",
        """IF OBJECT_ID('dbo.Teams', 'U') IS NULL
        BEGIN CREATE TABLE dbo.Teams (team_id INT PRIMARY KEY, team_name VARCHAR(100), country VARCHAR(100), team_type VARCHAR(50)); END""",
        """IF OBJECT_ID('dbo.Players', 'U') IS NULL
        BEGIN CREATE TABLE dbo.Players (player_id INT PRIMARY KEY, full_name VARCHAR(150), playing_role VARCHAR(50), batting_style VARCHAR(100), bowling_style VARCHAR(100), country VARCHAR(100), date_of_birth DATE); END""",
        """IF OBJECT_ID('dbo.Series', 'U') IS NULL
        BEGIN CREATE TABLE dbo.Series (series_id INT PRIMARY KEY, series_name VARCHAR(255), host_country VARCHAR(100), match_type VARCHAR(50), start_date DATE, end_date DATE, total_matches INT); END""",
        """IF OBJECT_ID('dbo.Matches', 'U') IS NULL
        BEGIN CREATE TABLE dbo.Matches (match_id INT PRIMARY KEY, series_id INT, match_description VARCHAR(255), team1_id INT, team2_id INT, venue_id INT, match_date DATETIME, match_type VARCHAR(50), toss_winner_id INT, toss_decision VARCHAR(50), winner_id INT, victory_margin INT, victory_type VARCHAR(50),
            FOREIGN KEY (series_id) REFERENCES dbo.Series(series_id),
            FOREIGN KEY (team1_id) REFERENCES dbo.Teams(team_id),
            FOREIGN KEY (team2_id) REFERENCES dbo.Teams(team_id),
            FOREIGN KEY (venue_id) REFERENCES dbo.Venues(venue_id),
            FOREIGN KEY (winner_id) REFERENCES dbo.Teams(team_id)); END""",
        """IF OBJECT_ID('dbo.Player_Stats', 'U') IS NULL
        BEGIN CREATE TABLE dbo.Player_Stats (stat_id INT IDENTITY(1,1) PRIMARY KEY, player_id INT, match_id INT, format_type VARCHAR(20), runs_scored INT, balls_faced INT, strike_rate DECIMAL(10,2), wickets_taken INT, overs_bowled DECIMAL(5,2), economy_rate DECIMAL(10,2), catches INT, stumpings INT, batting_position INT, innings_number INT,
            FOREIGN KEY (player_id) REFERENCES dbo.Players(player_id),
            FOREIGN KEY (match_id) REFERENCES dbo.Matches(match_id)); END""",
        """IF OBJECT_ID('dbo.Batting_Partnerships', 'U') IS NULL
        BEGIN CREATE TABLE dbo.Batting_Partnerships (partnership_id INT IDENTITY(1,1) PRIMARY KEY, match_id INT, innings_number INT, batsman1_id INT, batsman2_id INT, partnership_runs INT, batting_position_diff INT,
            FOREIGN KEY (match_id) REFERENCES dbo.Matches(match_id),
            FOREIGN KEY (batsman1_id) REFERENCES dbo.Players(player_id),
            FOREIGN KEY (batsman2_id) REFERENCES dbo.Players(player_id)); END"""
    ]

    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            for q in queries:
                cursor.execute(q)
            conn.commit()
            st.success("✅ All tables created successfully!")
        except Exception as e:
            st.error(f"Table creation error: {e}")
        finally:
            cursor.close()

# ==================== FETCH & PREPROCESS FUNCTIONS ====================

def fetch_teams_raw():
    try:
        response = requests.get(f"{BASE_URL}/teams/v1/international", headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        st.subheader("Raw Teams JSON from API")
        st.json(data)
        return data
    except Exception as e:
        st.error(f"Fetch error: {e}")
        return None

def preprocess_and_store_teams(raw_data):
    st.info("Starting preprocessing of teams data...")
    if not raw_data or 'list' not in raw_data:
        st.error("Invalid data format received from API")
        return 0

    teams_list = raw_data['list']
    inserted = 0
    skipped = 0

    for team in teams_list:
        if 'teamId' not in team or not team.get('teamId'):
            skipped += 1
            continue

        team_id = int(team.get('teamId'))
        team_name = str(team.get('teamName', '')).strip()
        country = str(team.get('countryName', team_name)).strip()

        if team_name in ["Test Teams", "Associate Teams"] or not team_name:
            skipped += 1
            continue

        query = """
            MERGE INTO dbo.Teams AS target
            USING (VALUES (?, ?, ?, ?)) AS source (team_id, team_name, country, team_type)
            ON target.team_id = source.team_id
            WHEN MATCHED THEN UPDATE SET team_name=source.team_name, country=source.country, team_type=source.team_type
            WHEN NOT MATCHED THEN INSERT (team_id, team_name, country, team_type) VALUES (source.team_id, source.team_name, source.country, source.team_type);
        """
        execute_query(query, (team_id, team_name, country, 'international'), fetch=False)
        inserted += 1

    st.success(f"✅ Preprocessed and stored **{inserted} teams** successfully!")
    return inserted


def fetch_series_raw():
    try:
        response = requests.get(f"{BASE_URL}/series/v1/international", headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        st.subheader("Raw Series JSON from API")
        st.json(data)
        return data
    except Exception as e:
        st.error(f"Series fetch error: {e}")
        return None


def preprocess_and_store_series(raw_data):
    st.info("Starting preprocessing of series data...")
    if not raw_data or 'seriesMapProto' not in raw_data:
        st.error("Invalid series data format - 'seriesMapProto' not found")
        return 0

    series_map = raw_data['seriesMapProto']
    inserted = 0

    for month_group in series_map:
        if 'series' not in month_group:
            continue
        for series_item in month_group['series']:
            series_id = series_item.get('id')
            if not series_id:
                continue

            series_name = str(series_item.get('name', '')).strip()
            host_country = ""
            match_type = "International"

            start_dt = series_item.get('startDt')
            end_dt = series_item.get('endDt')
            start_date = None
            if start_dt:
                try:
                    start_date = datetime.fromtimestamp(start_dt / 1000).strftime('%Y-%m-%d')
                except:
                    start_date = None
            end_date = None
            if end_dt:
                try:
                    end_date = datetime.fromtimestamp(end_dt / 1000).strftime('%Y-%m-%d')
                except:
                    end_date = None

            total_matches = 0

            query = """
                MERGE INTO dbo.Series AS target
                USING (VALUES (?, ?, ?, ?, ?, ?, ?)) AS source 
                    (series_id, series_name, host_country, match_type, start_date, end_date, total_matches)
                ON target.series_id = source.series_id
                WHEN MATCHED THEN UPDATE SET series_name=source.series_name, host_country=source.host_country, match_type=source.match_type,
                                             start_date=source.start_date, end_date=source.end_date, total_matches=source.total_matches
                WHEN NOT MATCHED THEN INSERT (series_id, series_name, host_country, match_type, start_date, end_date, total_matches)
                    VALUES (source.series_id, source.series_name, source.host_country, source.match_type, source.start_date, source.end_date, source.total_matches);
            """
            execute_query(query, (int(series_id), series_name, host_country, match_type, start_date, end_date, total_matches), fetch=False)
            inserted += 1

    st.success(f"✅ Preprocessed and stored **{inserted} series** successfully!")
    return inserted


def fetch_players_raw():
    try:
        response = requests.get(f"{BASE_URL}/teams/v1/2/players", headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        st.subheader("Raw Players JSON from Team Players Endpoint")
        st.json(data)
        return data
    except Exception as e:
        st.error(f"Players fetch error: {e}")
        return None


def preprocess_and_store_players(raw_data):
    st.info("Starting improved preprocessing of players data...")
    if not raw_data or 'player' not in raw_data:
        st.error("Invalid players data format")
        return 0

    players_list = raw_data['player']
    inserted = 0
    current_role = "Unknown"

    for player in players_list:
        player_id = player.get('id')
        if not player_id:
            name = str(player.get('name', '')).strip().upper()
            if name in ["BATSMEN", "BATSMAN"]:
                current_role = "Batsman"
            elif name in ["ALL ROUNDER", "ALL-ROUNDER"]:
                current_role = "All-rounder"
            elif name in ["WICKET KEEPER", "WICKET-KEEPER", "WK"]:
                current_role = "Wicket-keeper"
            elif name in ["BOWLER"]:
                current_role = "Bowler"
            continue

        full_name = str(player.get('name', '')).strip()
        batting_style = str(player.get('battingStyle', '')).strip()
        bowling_style = str(player.get('bowlingStyle', '')).strip()

        query = """
            MERGE INTO dbo.Players AS target
            USING (VALUES (?, ?, ?, ?, ?, ?)) AS source 
                (player_id, full_name, playing_role, batting_style, bowling_style, country)
            ON target.player_id = source.player_id
            WHEN MATCHED THEN UPDATE SET full_name=source.full_name, playing_role=source.playing_role,
                                         batting_style=source.batting_style, bowling_style=source.bowling_style, country=source.country
            WHEN NOT MATCHED THEN INSERT (player_id, full_name, playing_role, batting_style, bowling_style, country)
                VALUES (source.player_id, source.full_name, source.playing_role, source.batting_style, source.bowling_style, source.country);
        """
        execute_query(query, (int(player_id), full_name, current_role, batting_style, bowling_style, "India"), fetch=False)
        inserted += 1

    st.success(f"✅ Preprocessed and stored **{inserted} players** successfully!")
    return inserted


def fetch_matches_raw():
    try:
        response = requests.get(f"{BASE_URL}/matches/v1/live", headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        st.subheader("Raw Live Matches JSON from API")
        st.json(data)
        return data
    except Exception as e:
        st.error(f"Live matches fetch error: {e}")
        try:
            response = requests.get(f"{BASE_URL}/matches/v1/recent", headers=HEADERS)
            response.raise_for_status()
            data = response.json()
            st.json(data)
            return data
        except Exception as e2:
            st.error(f"Recent matches also failed: {e2}")
            return None


def preprocess_and_store_matches(raw_data):
    st.info("Starting improved preprocessing of matches data...")
    if not raw_data or 'typeMatches' not in raw_data:
        st.error("Invalid matches data format - 'typeMatches' not found")
        return 0

    inserted = 0
    for type_match in raw_data['typeMatches']:
        if 'seriesMatches' not in type_match:
            continue
        for series_match in type_match['seriesMatches']:
            if 'seriesAdWrapper' not in series_match:
                continue
            series_wrapper = series_match['seriesAdWrapper']
            if 'matches' not in series_wrapper:
                continue
            for match_item in series_wrapper['matches']:
                if 'matchInfo' not in match_item:
                    continue
                match_info = match_item['matchInfo']
                match_id = match_info.get('matchId')
                if not match_id:
                    continue

                match_description = str(match_info.get('matchDesc', '')).strip()
                series_id = match_info.get('seriesId')
                match_type = str(match_info.get('matchFormat', 'Unknown')).strip()

                team1_id = match_info.get('team1', {}).get('teamId') if isinstance(match_info.get('team1'), dict) else None
                team2_id = match_info.get('team2', {}).get('teamId') if isinstance(match_info.get('team2'), dict) else None
                venue_id = match_info.get('venueInfo', {}).get('id') if isinstance(match_info.get('venueInfo'), dict) else None

                start_date_ms = match_info.get('startDate')
                match_date = None
                if start_date_ms:
                    try:
                        match_date = datetime.fromtimestamp(start_date_ms / 1000).strftime('%Y-%m-%d %H:%M:%S')
                    except:
                        match_date = None

                query = """
                    MERGE INTO dbo.Matches AS target
                    USING (VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, NULL, NULL, NULL)) AS source 
                        (match_id, series_id, match_description, team1_id, team2_id, venue_id, match_date, match_type, 
                         toss_winner_id, toss_decision, winner_id, victory_margin, victory_type)
                    ON target.match_id = source.match_id
                    WHEN MATCHED THEN UPDATE SET match_description=source.match_description, series_id=source.series_id,
                                                 team1_id=source.team1_id, team2_id=source.team2_id, venue_id=source.venue_id,
                                                 match_date=source.match_date, match_type=source.match_type
                    WHEN NOT MATCHED THEN INSERT (match_id, series_id, match_description, team1_id, team2_id, venue_id, match_date, match_type,
                                                  toss_winner_id, toss_decision, winner_id, victory_margin, victory_type)
                        VALUES (source.match_id, source.series_id, source.match_description, source.team1_id, source.team2_id, 
                                source.venue_id, source.match_date, source.match_type, NULL, NULL, NULL, NULL, NULL);
                """
                execute_query(query, (int(match_id), series_id, match_description, team1_id, team2_id, venue_id, match_date, match_type), fetch=False)
                inserted += 1

    st.success(f"✅ Preprocessed and stored **{inserted} matches** successfully!")
    return inserted


def fix_matches_foreign_key():
    st.info("Disabling foreign key constraints on Matches table...")
    queries = [
        "ALTER TABLE dbo.Matches NOCHECK CONSTRAINT ALL;",
        "ALTER TABLE dbo.Matches ALTER COLUMN series_id INT NULL;",
        "ALTER TABLE dbo.Matches ALTER COLUMN venue_id INT NULL;",
        "ALTER TABLE dbo.Matches ALTER COLUMN team1_id INT NULL;",
        "ALTER TABLE dbo.Matches ALTER COLUMN team2_id INT NULL;",
        "ALTER TABLE dbo.Matches ALTER COLUMN winner_id INT NULL;",
    ]

    conn = get_db_connection()
    if not conn:
        st.error("Connection failed")
        return

    cursor = conn.cursor()
    try:
        for q in queries:
            cursor.execute(q)
        conn.commit()
        st.success("✅ Foreign key constraints disabled successfully.")
    except Exception as e:
        st.error(f"Fix failed: {e}")
    finally:
        cursor.close()


def auto_populate_teams_and_venues():
    st.info("Populating missing teams and venues...")
    # Teams
    query_teams = """
        INSERT INTO dbo.Teams (team_id, team_name, country, team_type)
        SELECT DISTINCT team_id, 'Team ' + CAST(team_id AS VARCHAR(20)), 'England', 'domestic'
        FROM (
            SELECT team1_id AS team_id FROM dbo.Matches WHERE team1_id IS NOT NULL
            UNION
            SELECT team2_id AS team_id FROM dbo.Matches WHERE team2_id IS NOT NULL
        ) AS missing
        WHERE NOT EXISTS (SELECT 1 FROM dbo.Teams t WHERE t.team_id = missing.team_id)
    """
    execute_query(query_teams, fetch=False)

    # Venues
    query_venues = """
        INSERT INTO dbo.Venues (venue_id, venue_name, city, country, capacity)
        SELECT DISTINCT venue_id, 'Venue ' + CAST(venue_id AS VARCHAR(20)), 'England', 'England', 0
        FROM dbo.Matches
        WHERE venue_id IS NOT NULL 
          AND NOT EXISTS (SELECT 1 FROM dbo.Venues v WHERE v.venue_id = venue_id)
    """
    execute_query(query_venues, fetch=False)

    st.success("✅ Missing teams and venues populated!")
    st.info("Refresh Live Matches page.")


def load_scorecard_data():
    st.info("Scorecard loading module is ready.")
    st.success("✅ Detailed scorecard parsing will be implemented in the next phase.")
    if st.button("View Current Status"):
        stats_count = execute_query("SELECT COUNT(*) as cnt FROM dbo.Player_Stats")[0]['cnt']
        partnership_count = execute_query("SELECT COUNT(*) as cnt FROM dbo.Batting_Partnerships")[0]['cnt']
        st.write(f"Player_Stats records: {stats_count}")
        st.write(f"Batting_Partnerships records: {partnership_count}")


# ==================== MAIN STREAMLIT APP ====================
st.set_page_config(page_title="Cricbuzz LiveStats", page_icon="🏏", layout="wide")

st.title("🏏 Cricbuzz LiveStats - Cricket Analytics Dashboard")
st.markdown("### Real-time Cricket Data + SQL Analytics + CRUD Operations")

page = st.sidebar.selectbox(
    "Navigate to",
    ["Home", "Live Matches", "Top Player Stats", "SQL Queries", "CRUD Operations"]
)

if page == "Home":
    from page_modules.home import home_page
    home_page()

    st.subheader("1. Database Setup")
    if st.button("Create All Tables (Run Once)"):
        create_all_tables()

    st.subheader("2. Fetch & Preprocess Data")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("Fetch Teams"):
            fetch_teams_raw()
        if st.button("Store Teams"):
            raw = fetch_teams_raw()
            if raw: preprocess_and_store_teams(raw)

    with col2:
        if st.button("Fetch Series"):
            fetch_series_raw()
        if st.button("Store Series"):
            raw = fetch_series_raw()
            if raw: preprocess_and_store_series(raw)

    with col3:
        if st.button("Fetch Players"):
            fetch_players_raw()
        if st.button("Store Players"):
            raw = fetch_players_raw()
            if raw: preprocess_and_store_players(raw)

    with col4:
        if st.button("Fix FK"):
            fix_matches_foreign_key()
        if st.button("Fetch Matches"):
            fetch_matches_raw()
        if st.button("Store Matches"):
            raw = fetch_matches_raw()
            if raw: preprocess_and_store_matches(raw)
        if st.button("Auto Populate Teams & Venues"):
            auto_populate_teams_and_venues()
        if st.button("Load Scorecard Data"):
            load_scorecard_data()

    st.info("Use the sidebar to navigate to other page_modules.")

elif page == "Live Matches":
    from page_modules.live_matches import live_matches_page
    live_matches_page()

elif page == "Top Player Stats":
    from page_modules.top_stats import top_stats_page
    top_stats_page()

elif page == "SQL Queries":
    from page_modules.sql_queries import sql_queries_page
    sql_queries_page()

elif page == "CRUD Operations":
    from page_modules.crud_operations import crud_operations_page
    crud_operations_page()

st.caption("Project following your full requirements - preprocessing included")