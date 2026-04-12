import requests
import streamlit as st
import json
from utils.db_connection import execute_query

BASE_URL = "https://cricbuzz-live.vercel.app"


def fetch_teams_raw():
    """Fetch teams and show raw data for preprocessing"""
    st.subheader("Raw Teams Data from API")
    try:
        response = requests.get(f"{BASE_URL}/teams")
        response.raise_for_status()
        data = response.json()

        # Show raw data so you can see the structure
        st.json(data)  # This displays the full JSON nicely
        st.write(f"Total teams received: {len(data) if isinstance(data, list) else len(data.get('data', []))}")

        return data
    except Exception as e:
        st.error(f"Failed to fetch teams: {str(e)}")
        return None


def preprocess_and_store_teams(raw_data):
    """Preprocess raw data before inserting into DB"""
    st.info("Preprocessing teams data...")

    if isinstance(raw_data, list):
        teams = raw_data
    elif isinstance(raw_data, dict):
        teams = raw_data.get('data', raw_data.get('teams', []))
    else:
        teams = []

    inserted = 0
    for team in teams:
        if not team or not team.get('id'):
            continue

        # Preprocessing step - you can add more cleaning here
        cleaned_team = {
            'team_id': int(team.get('id')),
            'team_name': str(team.get('name', '')).strip(),
            'country': str(team.get('country', 'International')).strip(),
            'team_type': str(team.get('type', 'international')).lower()
        }

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
            cleaned_team['team_id'],
            cleaned_team['team_name'],
            cleaned_team['country'],
            cleaned_team['team_type']
        ), fetch=False)
        inserted += 1

    st.success(f"✅ Preprocessed and stored {inserted} teams.")
    return inserted


if __name__ == "__main__":
    st.title("🗄️ Cricbuzz Data Fetcher with Preprocessing")

    if st.button("1. Fetch Raw Teams Data"):
        raw_data = fetch_teams_raw()

    if st.button("2. Preprocess & Store Teams into Database"):
        raw_data = fetch_teams_raw()  # Fetch again or use cached
        if raw_data:
            preprocess_and_store_teams(raw_data)

    st.info("Once you see the raw JSON above, tell me what fields you want to keep/clean. "
            "Then we will move to Series → Players → Matches with proper preprocessing.")