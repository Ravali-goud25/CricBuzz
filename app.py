import streamlit as st
from utils.db_connection import get_db_connection, execute_query
import requests

# ==================== Cricbuzz API Configuration ====================
BASE_URL = "https://cricbuzz-cricket.p.rapidapi.com"
HEADERS = {
    "X-RapidAPI-Key": "dc8ef5f8bfmsh456bd292170f639p183b8cjsn527c7a817046",   # ← Replace with your actual key
    "X-RapidAPI-Host": "cricbuzz-cricket.p.rapidapi.com"
}

# Rest of your existing code (create_all_tables, fetch functions, etc.) remains the same

# ==================== CREATE TABLES FUNCTION (already working) ====================
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


# ==================== TEAMS FETCH + PREPROCESS ====================
def fetch_teams_raw():
    try:
        # Correct endpoint based on your screenshots and list
        response = requests.get(f"{BASE_URL}/teams/v1/international", headers=HEADERS)
        response.raise_for_status()
        data = response.json()

        st.subheader("Raw Teams JSON from API")
        st.json(data)  # This will show the full structure for preprocessing

        return data
    except Exception as e:
        st.error(f"Fetch error: {e}")
        st.info(
            "Tip: Make sure your RapidAPI key has access to the 'Cricbuzz Cricket' API and you have not exceeded free tier limits.")
        return None

def preprocess_and_store_teams(raw_data):
    """Improved preprocessing based on actual API response"""
    st.info("Starting preprocessing of teams data...")

    if not raw_data or 'list' not in raw_data:
        st.error("Invalid data format received from API")
        return 0

    teams_list = raw_data['list']
    inserted = 0
    skipped = 0

    for team in teams_list:
        # Skip header entries like "Test Teams", "Associate Teams"
        if 'teamId' not in team or not team.get('teamId'):
            skipped += 1
            continue

        # Preprocessing & Cleaning
        team_id = int(team.get('teamId'))
        team_name = str(team.get('teamName', '')).strip()
        short_name = str(team.get('teamSName', '')).strip()
        country = str(team.get('countryName', team_name)).strip()  # fallback to teamName if no country

        # Skip dummy entries
        if team_name in ["Test Teams", "Associate Teams"] or not team_name:
            skipped += 1
            continue

        query = """
            MERGE INTO dbo.Teams AS target
            USING (VALUES (?, ?, ?, ?)) AS source (team_id, team_name, country, team_type)
            ON target.team_id = source.team_id
            WHEN MATCHED THEN 
                UPDATE SET team_name = source.team_name, 
                           country = source.country,
                           team_type = source.team_type
            WHEN NOT MATCHED THEN
                INSERT (team_id, team_name, country, team_type)
                VALUES (source.team_id, source.team_name, source.country, source.team_type);
        """

        execute_query(query, (
            team_id,
            team_name,
            country,
            'international'   # Most are international; we can refine later
        ), fetch=False)

        inserted += 1

    st.success(f"✅ Preprocessed and stored **{inserted} teams** successfully!")
    st.info(f"Skipped {skipped} header/dummy entries.")
    return inserted


# ==================== SERIES FETCH + PREPROCESS ====================
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
    """Preprocess series data based on actual API response (seriesMapProto)"""
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

            # Preprocessing
            series_name = str(series_item.get('name', '')).strip()
            # Host country is often not directly available - we'll leave as empty for now
            host_country = ""
            match_type = "International"  # Most in this endpoint are international

            # Convert millisecond timestamp to proper date (SQL Server accepts string)
            start_dt = series_item.get('startDt')
            end_dt = series_item.get('endDt')

            start_date = None
            if start_dt:
                try:
                    # Convert milliseconds to YYYY-MM-DD format
                    from datetime import datetime
                    start_date = datetime.fromtimestamp(start_dt / 1000).strftime('%Y-%m-%d')
                except:
                    start_date = None

            end_date = None
            if end_dt:
                try:
                    end_date = datetime.fromtimestamp(end_dt / 1000).strftime('%Y-%m-%d')
                except:
                    end_date = None

            total_matches = 0  # Not available in this endpoint

            query = """
                MERGE INTO dbo.Series AS target
                USING (VALUES (?, ?, ?, ?, ?, ?, ?)) AS source 
                    (series_id, series_name, host_country, match_type, start_date, end_date, total_matches)
                ON target.series_id = source.series_id
                WHEN MATCHED THEN 
                    UPDATE SET series_name = source.series_name,
                               host_country = source.host_country,
                               match_type = source.match_type,
                               start_date = source.start_date,
                               end_date = source.end_date,
                               total_matches = source.total_matches
                WHEN NOT MATCHED THEN
                    INSERT (series_id, series_name, host_country, match_type, start_date, end_date, total_matches)
                    VALUES (source.series_id, source.series_name, source.host_country, 
                            source.match_type, source.start_date, source.end_date, source.total_matches);
            """

            execute_query(query, (
                int(series_id),
                series_name,
                host_country,
                match_type,
                start_date,
                end_date,
                total_matches
            ), fetch=False)

            inserted += 1

    st.success(f"✅ Preprocessed and stored **{inserted} series** successfully!")
    return inserted


# ==================== PLAYERS FETCH + PREPROCESS ====================
def fetch_players_raw():
    try:
        # Try a better endpoint for more players - using international teams players
        # First, we'll use one example team (India - teamId 2) to get players
        # You can later loop over multiple teams
        response = requests.get(f"{BASE_URL}/teams/v1/2/players", headers=HEADERS)
        response.raise_for_status()
        data = response.json()

        st.subheader("Raw Players JSON from Team Players Endpoint")
        st.json(data)
        return data
    except Exception as e:
        st.error(f"Players fetch error: {e}")
        st.info("Trying alternative player endpoint...")
        # Fallback to trending
        try:
            response = requests.get(f"{BASE_URL}/stats/v1/player/trending", headers=HEADERS)
            response.raise_for_status()
            data = response.json()
            st.json(data)
            return data
        except Exception as e2:
            st.error(f"Fallback also failed: {e2}")
            return None


def preprocess_and_store_players(raw_data):
    """Improved preprocessing for players - handles sections (BATSMEN, ALL ROUNDER, etc.)"""
    st.info("Starting improved preprocessing of players data...")

    if not raw_data or 'player' not in raw_data:
        st.error("Invalid players data format")
        return 0

    players_list = raw_data['player']
    inserted = 0
    current_role = "Unknown"

    for player in players_list:
        player_id = player.get('id')

        # Handle section headers (BATSMEN, ALL ROUNDER, etc.)
        if not player_id:
            name = str(player.get('name', '')).strip().upper()
            if name in ["BATSMEN", "BATS MAN", "BATSMAN"]:
                current_role = "Batsman"
            elif name in ["ALL ROUNDER", "ALL-ROUNDER", "ALLROUNDER"]:
                current_role = "All-rounder"
            elif name in ["WICKET KEEPER", "WICKET-KEEPER", "WK"]:
                current_role = "Wicket-keeper"
            elif name in ["BOWLER"]:
                current_role = "Bowler"
            continue

        # Real player - preprocess data
        full_name = str(player.get('name', '')).strip()
        batting_style = str(player.get('battingStyle', '')).strip()
        bowling_style = str(player.get('bowlingStyle', '')).strip()

        # Map role based on current section
        playing_role = current_role

        query = """
            MERGE INTO dbo.Players AS target
            USING (VALUES (?, ?, ?, ?, ?, ?)) AS source 
                (player_id, full_name, playing_role, batting_style, bowling_style, country)
            ON target.player_id = source.player_id
            WHEN MATCHED THEN 
                UPDATE SET full_name = source.full_name,
                           playing_role = source.playing_role,
                           batting_style = source.batting_style,
                           bowling_style = source.bowling_style,
                           country = source.country
            WHEN NOT MATCHED THEN
                INSERT (player_id, full_name, playing_role, batting_style, bowling_style, country)
                VALUES (source.player_id, source.full_name, source.playing_role, 
                        source.batting_style, source.bowling_style, source.country);
        """

        execute_query(query, (
            int(player_id),
            full_name,
            playing_role,
            batting_style,
            bowling_style,
            "India"   # Since we fetched from India team (teamId=2)
        ), fetch=False)

        inserted += 1

    st.success(f"✅ Preprocessed and stored **{inserted} players** successfully!")
    st.info("Note: Currently fetching only India squad. We can expand to other teams later.")
    return inserted


# ==================== MAIN STREAMLIT APP ====================
st.set_page_config(page_title="Cricbuzz LiveStats", page_icon="🏏", layout="wide")
st.title("🏏 Cricbuzz LiveStats - Cricket Analytics Dashboard")
st.markdown("### Real-time Cricket Data + SQL Analytics + CRUD Operations")

page = st.sidebar.selectbox("Navigate to",
                            ["Home", "Live Matches", "Top Player Stats", "SQL Queries", "CRUD Operations"])

if page == "Home":
    st.header("Welcome to the Project!")

    st.subheader("🛠️ 1. Create Database Tables")
    if st.button("Create All Tables (Run Once)"):
        create_all_tables()

    st.subheader("📥 2. Fetch & Preprocess Data")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("Fetch Raw Teams Data"):
            fetch_teams_raw()
        if st.button("Preprocess & Store Teams"):
            raw_data = fetch_teams_raw()
            if raw_data:
                preprocess_and_store_teams(raw_data)

    with col2:
        if st.button("Fetch Raw Series Data"):
            fetch_series_raw()
        if st.button("Preprocess & Store Series"):
            raw_series = fetch_series_raw()
            if raw_series:
                preprocess_and_store_series(raw_series)

    with col3:
        if st.button("Fetch Raw Players Data"):
            fetch_players_raw()
        if st.button("Preprocess & Store Players"):
            raw_players = fetch_players_raw()
            if raw_players:
                preprocess_and_store_players(raw_players)

    st.info("After seeing the raw JSON, you can tell me what extra cleaning you want before storing.")

else:
    st.write(f"**{page}** page is under development.")

st.caption("Project following your full requirements - preprocessing included")