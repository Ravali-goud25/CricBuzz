import os
import re
import json
import time
import requests
import pandas as pd

API_KEY = "fd0b4ba094msh2df730c6efcc7d6p1fdd65jsne9c47c33d0c8"
API_HOST = "cricbuzz-cricket.p.rapidapi.com"
BASE_URL = "https://cricbuzz-cricket.p.rapidapi.com"

HEADERS = {
    "X-RapidAPI-Key": API_KEY,
    "X-RapidAPI-Host": API_HOST
}

RAW_DIR = "raw/matches"
OUT_DIR = "output"

os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(OUT_DIR, exist_ok=True)

matches = {}

# ==========================================================
# HELPERS
# ==========================================================
def safe_int(v):
    try:
        return int(v)
    except:
        return None


def txt(v):
    if v is None:
        return None
    s = str(v).strip()
    return s if s else None


def to_date(ms):
    try:
        return pd.to_datetime(int(ms), unit="ms").date()
    except:
        return None


def to_datetime(ms):
    try:
        return pd.to_datetime(int(ms), unit="ms")
    except:
        return None


# ==========================================================
# API FETCH
# ==========================================================
def fetch_json(endpoint, file_name):
    url = BASE_URL + endpoint
    path = os.path.join(RAW_DIR, file_name)

    try:
        print("Fetching:", endpoint)

        r = requests.get(
            url,
            headers=HEADERS,
            timeout=30
        )

        if r.status_code == 429:
            print("RATE LIMITED. Sleeping...")
            time.sleep(10)
            return None

        r.raise_for_status()

        data = r.json()

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        time.sleep(1)
        return data

    except Exception as e:
        print("FAILED:", endpoint, e)
        return None


# ==========================================================
# WINNER PARSER
# ==========================================================
def normalize(s):
    if not s:
        return ""
    return re.sub(r"[^a-z0-9 ]", "", s.lower()).strip()


def detect_winner(status, team1_name, team2_name, team1_id, team2_id):
    """
    Example:
    Bangladesh won by 55 runs
    Mumbai Indians won by 99 runs
    Match drawn
    Tie
    """

    if not status:
        return None, None, None

    st = status.lower()

    # no result cases
    if "drawn" in st:
        return None, "drawn", "draw"

    if "tie" in st:
        return None, "tie", "tie"

    if "abandoned" in st or "no result" in st:
        return None, None, None

    if "won by" not in st:
        return None, None, None

    t1 = normalize(team1_name)
    t2 = normalize(team2_name)
    raw = normalize(status)

    winner_id = None

    if t1 and t1 in raw:
        winner_id = team1_id
    elif t2 and t2 in raw:
        winner_id = team2_id

    # margin
    margin = None
    m = re.search(r"won by (.+)", status, re.I)
    if m:
        margin = m.group(1).strip()

    # type
    win_type = None
    if margin:
        low = margin.lower()

        if "run" in low:
            win_type = "runs"
        elif "wkt" in low or "wicket" in low:
            win_type = "wickets"

    return winner_id, margin, win_type


# ==========================================================
# ADD MATCH
# ==========================================================
def add_match(row):
    match_id = row["match_id"]

    if not match_id:
        return

    matches[match_id] = row


# ==========================================================
# WALK JSON
# ==========================================================
def walk_json(obj, source):

    if isinstance(obj, dict):

        if "matchInfo" in obj:

            m = obj["matchInfo"]

            team1 = m.get("team1", {})
            team2 = m.get("team2", {})
            venue = m.get("venueInfo", {})

            status = txt(m.get("status"))

            team1_name = txt(team1.get("teamName"))
            team2_name = txt(team2.get("teamName"))

            team1_id = safe_int(team1.get("teamId"))
            team2_id = safe_int(team2.get("teamId"))

            winner_id, margin, win_type = detect_winner(
                status,
                team1_name,
                team2_name,
                team1_id,
                team2_id
            )

            row = {
                "match_id": safe_int(m.get("matchId")),
                "series_id": safe_int(m.get("seriesId")),
                "series_name": txt(m.get("seriesName")),
                "match_desc": txt(m.get("matchDesc")),
                "match_format": txt(m.get("matchFormat")),
                "team1_id": team1_id,
                "team2_id": team2_id,
                "venue_id": safe_int(venue.get("id")),
                "match_date": to_date(m.get("startDate")),
                "start_time": to_datetime(m.get("startDate")),
                "status": status,
                "winner_team_id": winner_id,
                "win_margin": margin,
                "win_type": win_type,
                "toss_winner_team_id": None,
                "toss_decision": None,
                "source": source
            }

            add_match(row)

        for v in obj.values():
            walk_json(v, source)

    elif isinstance(obj, list):
        for x in obj:
            walk_json(x, source)


# ==========================================================
# MAIN
# ==========================================================
def main():

    files = {
        "recent.json": "/matches/v1/recent",
        "live.json": "/matches/v1/live",
        "upcoming.json": "/matches/v1/upcoming"
    }

    # fetch latest
    for file_name, ep in files.items():
        data = fetch_json(ep, file_name)
        if data:
            walk_json(data, file_name)

    # also parse any existing files
    for file in os.listdir(RAW_DIR):
        if file.endswith(".json"):
            path = os.path.join(RAW_DIR, file)

            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                walk_json(data, file)

            except:
                pass

    # save csv
    df = pd.DataFrame(list(matches.values()))

    if not df.empty:
        df = df.sort_values(
            by=["match_date", "match_id"],
            ascending=[False, False]
        )

    out = os.path.join(OUT_DIR, "matches_completed.csv")
    df.to_csv(out, index=False)

    print("\nDone.")
    print("Matches discovered:", len(df))
    print("Saved:", out)


if __name__ == "__main__":
    main()