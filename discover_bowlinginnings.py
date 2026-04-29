import os
import json
import glob
import pandas as pd

RAW_DIR = r"raw\scorecards"
OUTPUT_FILE = r"output\bowling_innings.csv"

os.makedirs("output", exist_ok=True)

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
# PARSE ONE FILE
# ==========================================================
def parse_file(filepath):

    match_id = get_match_id(filepath)

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

    except Exception as e:
        print("Failed to read:", filepath, e)
        return

    scorecards = data.get("scorecard", [])

    if not isinstance(scorecards, list):
        return

    for innings in scorecards:

        innings_no = safe_int(
            innings.get("inningsid")
        )

        bowling_team = txt(
            innings.get("bowlteamname")
        )

        bowlers = innings.get("bowler", [])

        if not isinstance(bowlers, list):
            continue

        for bw in bowlers:

            player_id = safe_int(
                bw.get("id")
            )

            if not player_id:
                continue

            rows.append({

                "match_id": match_id,
                "innings_no": innings_no,

                "bowling_team": bowling_team,

                "player_id": player_id,
                "player_name": txt(
                    bw.get("name")
                ),

                "overs": safe_float(
                    bw.get("overs")
                ),

                "maidens": safe_int(
                    bw.get("maidens")
                ),

                "runs_conceded": safe_int(
                    bw.get("runs")
                ),

                "wickets": safe_int(
                    bw.get("wickets")
                ),

                "economy": safe_float(
                    bw.get("economy")
                ),

                "wides": safe_int(
                    bw.get("wides")
                ),

                "no_balls": safe_int(
                    bw.get("noballs")
                ),

                "source": f"{match_id}_scard"
            })


# ==========================================================
# MAIN
# ==========================================================
def main():

    files = glob.glob(
        os.path.join(RAW_DIR, "*.json")
    )

    if not files:
        print("No scorecard files found in raw/scorecards/")
        return

    print("Scorecard files found:", len(files))

    for file in files:
        print("Parsing:", file)
        parse_file(file)

    df = pd.DataFrame(rows)

    if df.empty:
        print("\nNo bowling rows found.")
        return

    df = df.sort_values(
        by=["match_id", "innings_no", "player_id"]
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