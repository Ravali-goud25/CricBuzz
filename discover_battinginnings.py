import os
import json
import time
import glob
import requests
import pandas as pd


API_KEY = "fd0b4ba094msh2df730c6efcc7d6p1fdd65jsne9c47c33d0c8"
API_HOST = "cricbuzz-cricket.p.rapidapi.com"

BASE_URL = "https://cricbuzz-cricket.p.rapidapi.com"

HEADERS = {
    "X-RapidAPI-Key": API_KEY,
    "X-RapidAPI-Host": API_HOST
}

MATCHES_FILE = r"output\matches_completed.csv"

RAW_DIR = r"raw\scorecards"
OUTPUT_FILE = r"output\batting_innings.csv"

os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs("output", exist_ok=True)

# ----------------------------------------------------------
# SAFE API SETTINGS
# ----------------------------------------------------------
REQUEST_GAP = 8          # seconds
MAX_NEW_FETCH = 5        # new files per run
TIMEOUT = 30

rows = []

# ==========================================================
# HELPERS
# ==========================================================
def safe_int(v):
    try:
        return int(v)
    except:
        return None


def safe_float(v):
    try:
        return float(v)
    except:
        return None


def txt(v):
    if v is None:
        return None

    s = str(v).strip()
    return s if s else None


def get_match_id(filepath):
    name = os.path.basename(filepath)
    return int(name.split("_")[0])


# ==========================================================
# FETCH SCORECARD
# ==========================================================
def fetch_scorecard(match_id):

    file_path = os.path.join(
        RAW_DIR,
        f"{match_id}_scard.json"
    )

    # already exists
    if os.path.exists(file_path):
        return True

    endpoint = f"/mcenter/v1/{match_id}/scard"
    url = BASE_URL + endpoint

    try:
        print("Fetching:", endpoint)

        r = requests.get(
            url,
            headers=HEADERS,
            timeout=TIMEOUT
        )

        if r.status_code == 429:
            print("RATE LIMITED (429).")
            return False

        if r.status_code == 403:
            print("FORBIDDEN (403). Check API key.")
            return False

        r.raise_for_status()

        data = r.json()

        with open(
            file_path,
            "w",
            encoding="utf-8"
        ) as f:
            json.dump(data, f, indent=2)

        time.sleep(REQUEST_GAP)

        return True

    except Exception as e:
        print("FAILED:", match_id, e)
        return False


# ==========================================================
# PARSE ONE FILE
# ==========================================================
def parse_file(filepath):

    match_id = get_match_id(filepath)

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

    except:
        return

    # actual Cricbuzz key
    scorecards = data.get("scorecard", [])

    if not isinstance(scorecards, list):
        return

    for innings in scorecards:

        innings_no = safe_int(
            innings.get("inningsid")
        )

        team_name = txt(
            innings.get("batteamname")
        )

        batsmen = innings.get("batsman", [])

        if not isinstance(batsmen, list):
            continue

        position = 1

        for bat in batsmen:

            player_id = safe_int(
                bat.get("id")
            )

            if not player_id:
                continue

            rows.append({

                "match_id": match_id,
                "innings_no": innings_no,

                "batting_team": team_name,
                "bat_position": position,

                "player_id": player_id,
                "player_name": txt(
                    bat.get("name")
                ),

                "runs": safe_int(
                    bat.get("runs")
                ),

                "balls": safe_int(
                    bat.get("balls")
                ),

                "fours": safe_int(
                    bat.get("fours")
                ),

                "sixes": safe_int(
                    bat.get("sixes")
                ),

                "strike_rate": safe_float(
                    bat.get("strkrate")
                ),

                "dismissal": txt(
                    bat.get("outdec")
                ),

                "is_captain": safe_int(
                    bat.get("iscaptain")
                ),

                "is_keeper": safe_int(
                    bat.get("iskeeper")
                ),

                "source": f"{match_id}_scard"
            })

            position += 1


# ==========================================================
# MAIN
# ==========================================================
def main():

    # --------------------------------------
    # STEP 1 Read match ids
    # --------------------------------------
    if not os.path.exists(MATCHES_FILE):
        print("Missing:", MATCHES_FILE)
        return

    dfm = pd.read_csv(MATCHES_FILE)

    if "match_id" not in dfm.columns:
        print("match_id column missing.")
        return

    match_ids = (
        dfm["match_id"]
        .dropna()
        .astype(int)
        .tolist()
    )

    print("Matches found:", len(match_ids))

    # --------------------------------------
    # STEP 2 Fetch limited new files
    # --------------------------------------
    fetched = 0

    for match_id in match_ids:

        if fetched >= MAX_NEW_FETCH:
            break

        path = os.path.join(
            RAW_DIR,
            f"{match_id}_scard.json"
        )

        if os.path.exists(path):
            continue

        ok = fetch_scorecard(match_id)

        if not ok:
            break

        fetched += 1

    # --------------------------------------
    # STEP 3 Parse all local raw files
    # --------------------------------------
    files = glob.glob(
        os.path.join(RAW_DIR, "*.json")
    )

    for file in files:
        print("Parsing:", file)
        parse_file(file)

    # --------------------------------------
    # STEP 4 Save CSV
    # --------------------------------------
    df = pd.DataFrame(rows)

    if df.empty:
        print("\nNo batting rows found.")
        return

    df = df.sort_values(
        by=["match_id", "innings_no",
            "bat_position"]
    )

    df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print("\nDone.")
    print("Rows:", len(df))
    print("Saved:", OUTPUT_FILE)


if __name__ == "__main__":
    main()