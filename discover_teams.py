import os
import json
import time
import requests
import pandas as pd

# ==========================
# CONFIG
# ==========================
API_KEY = "fd0b4ba094msh2df730c6efcc7d6p1fdd65jsne9c47c33d0c8"
API_HOST = "cricbuzz-cricket.p.rapidapi.com"

BASE_URL = "https://cricbuzz-cricket.p.rapidapi.com"

HEADERS = {
    "X-RapidAPI-Key": API_KEY,
    "X-RapidAPI-Host": API_HOST
}

RAW_DIR = "raw"
OUTPUT_DIR = "output"

os.makedirs(f"{RAW_DIR}/teams", exist_ok=True)
os.makedirs(f"{RAW_DIR}/matches", exist_ok=True)
os.makedirs(f"{RAW_DIR}/series", exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ==========================
# REQUEST HELPER
# ==========================
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
        print(f"Failed: {endpoint} -> {e}")
        return None


# ==========================
# TEAM STORAGE
# ==========================
teams = {}


def add_team(team_id, team_name, source):
    if not team_id or not team_name:
        return

    try:
        team_id = int(team_id)
    except:
        return

    team_name = str(team_name).strip()

    if team_id not in teams:
        teams[team_id] = {
            "team_id": team_id,
            "team_name": team_name,
            "source": source
        }


# ==========================
# GENERIC JSON WALKER
# ==========================
def walk_json(obj, source):

    if isinstance(obj, dict):

        # Pattern 1
        if "teamId" in obj and "teamName" in obj:
            add_team(obj["teamId"], obj["teamName"], source)

        # Pattern 2
        if "id" in obj and "teamName" in obj:
            add_team(obj["id"], obj["teamName"], source)

        # Pattern 3
        if "team1" in obj and isinstance(obj["team1"], dict):
            t = obj["team1"]
            add_team(
                t.get("teamId") or t.get("id"),
                t.get("teamName") or t.get("name"),
                source
            )

        # Pattern 4
        if "team2" in obj and isinstance(obj["team2"], dict):
            t = obj["team2"]
            add_team(
                t.get("teamId") or t.get("id"),
                t.get("teamName") or t.get("name"),
                source
            )

        # Pattern 5 (common in series)
        if "team" in obj and isinstance(obj["team"], dict):
            t = obj["team"]
            add_team(
                t.get("teamId") or t.get("id"),
                t.get("teamName") or t.get("name"),
                source
            )

        for v in obj.values():
            walk_json(v, source)

    elif isinstance(obj, list):
        for item in obj:
            walk_json(item, source)


# ==========================
# SERIES HELPERS
# ==========================
def extract_series_ids(data):
    """
    Recursively find numeric ids inside series-like nodes.
    """
    ids = set()

    def recurse(obj):
        if isinstance(obj, dict):

            # Common keys
            if "seriesId" in obj:
                try:
                    ids.add(int(obj["seriesId"]))
                except:
                    pass

            if "id" in obj and (
                "seriesName" in obj
                or "seriesType" in obj
                or "startDt" in obj
            ):
                try:
                    ids.add(int(obj["id"]))
                except:
                    pass

            for v in obj.values():
                recurse(v)

        elif isinstance(obj, list):
            for item in obj:
                recurse(item)

    recurse(data)
    return list(ids)


# ==========================
# MAIN FLOW
# ==========================
def main():

    # --------------------------------
    # 1 International Teams
    # --------------------------------
    data = fetch_json(
        "/teams/v1/international",
        f"{RAW_DIR}/teams/international.json"
    )

    if data:
        walk_json(data, "international")

    # --------------------------------
    # 2 Recent Matches
    # --------------------------------
    data = fetch_json(
        "/matches/v1/recent",
        f"{RAW_DIR}/matches/recent.json"
    )

    if data:
        walk_json(data, "recent_matches")

    # --------------------------------
    # 3 Upcoming Matches
    # --------------------------------
    data = fetch_json(
        "/matches/v1/upcoming",
        f"{RAW_DIR}/matches/upcoming.json"
    )

    if data:
        walk_json(data, "upcoming_matches")

    # --------------------------------
    # 4 Series Archives
    # --------------------------------
    archive_data = fetch_json(
        "/series/v1/archives/international",
        f"{RAW_DIR}/series/archives_international.json"
    )

    series_ids = []

    if archive_data:
        walk_json(archive_data, "series_archive")
        series_ids = extract_series_ids(archive_data)

    # --------------------------------
    # 5 Fetch Individual Series
    # --------------------------------
    # Limit first 20 for safety. Increase later if needed.
    for sid in series_ids[:20]:

        data = fetch_json(
            f"/series/v1/{sid}",
            f"{RAW_DIR}/series/{sid}.json"
        )

        if data:
            walk_json(data, f"series_{sid}")

    # --------------------------------
    # SAVE CSV
    # --------------------------------
    df = pd.DataFrame(list(teams.values()))

    if not df.empty:
        df = df.sort_values("team_name")

    output_file = f"{OUTPUT_DIR}/teams_discovered.csv"
    df.to_csv(output_file, index=False)

    print("\nDone.")
    print(f"Teams discovered: {len(df)}")
    print(f"Saved: {output_file}")


if __name__ == "__main__":
    main()