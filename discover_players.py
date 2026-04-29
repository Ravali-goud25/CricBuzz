import os
import json
import time
import requests
import pandas as pd
import pyodbc


API_KEY = "fd0b4ba094msh2df730c6efcc7d6p1fdd65jsne9c47c33d0c8"
API_HOST = "cricbuzz-cricket.p.rapidapi.com"
BASE_URL = "https://cricbuzz-cricket.p.rapidapi.com"

HEADERS = {
    "X-RapidAPI-Key": API_KEY,
    "X-RapidAPI-Host": API_HOST
}

SERVER = r"RAVALI"
DATABASE = "CricbuzzDB"

RAW_DIR = "raw/players"
OUTPUT_DIR = "output"

os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ======================================
# SQL CONNECTION
# ======================================
CONN_STR = (
    "DRIVER={SQL Server};"
    f"SERVER={SERVER};"
    f"DATABASE={DATABASE};"
    "Trusted_Connection=yes;"
)

# ======================================
# HELPERS
# ======================================
def get_team_ids():
    conn = pyodbc.connect(CONN_STR)
    query = "SELECT team_id FROM teams ORDER BY team_id"
    df = pd.read_sql(query, conn)
    conn.close()
    return df["team_id"].tolist()


def fetch_json(endpoint, save_path):
    url = BASE_URL + endpoint
    print(f"Fetching {endpoint}")

    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()

        data = response.json()

        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        time.sleep(1)
        return data

    except Exception as e:
        print(f"FAILED {endpoint} -> {e}")
        return None


players = {}

def add_player(player_id, full_name, team_id, source):
    if not player_id or not full_name:
        return

    try:
        player_id = int(player_id)
    except:
        return

    if player_id not in players:
        players[player_id] = {
            "player_id": player_id,
            "full_name": str(full_name).strip(),
            "team_id": team_id,
            "source": source
        }


def walk_json(obj, team_id, source):

    if isinstance(obj, dict):

        # common pattern
        if "id" in obj and "name" in obj:
            add_player(obj["id"], obj["name"], team_id, source)

        if "playerId" in obj and "name" in obj:
            add_player(obj["playerId"], obj["name"], team_id, source)

        if "playerId" in obj and "fullName" in obj:
            add_player(obj["playerId"], obj["fullName"], team_id, source)

        for v in obj.values():
            walk_json(v, team_id, source)

    elif isinstance(obj, list):
        for item in obj:
            walk_json(item, team_id, source)


# ======================================
# MAIN
# ======================================
def main():

    team_ids = get_team_ids()
    print(f"Teams found in SQL Server: {len(team_ids)}")

    for team_id in team_ids:

        endpoint = f"/teams/v1/{team_id}/players"
        save_path = f"{RAW_DIR}/team_{team_id}.json"

        data = fetch_json(endpoint, save_path)

        if data:
            walk_json(data, team_id, f"team_{team_id}")

    # save csv
    df = pd.DataFrame(list(players.values()))

    if not df.empty:
        df = df.sort_values("full_name")

    output_file = f"{OUTPUT_DIR}/players_discovered.csv"
    df.to_csv(output_file, index=False)

    print("\nDone.")
    print(f"Players discovered: {len(df)}")
    print(f"Saved: {output_file}")


if __name__ == "__main__":
    main()