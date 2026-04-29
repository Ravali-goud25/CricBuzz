import pandas as pd
import pyodbc
import os
from datetime import datetime

# ======================================
# CONFIG
# ======================================
CSV_FILE = r"output\teams_discovered.csv"

# Change SERVER if needed
SERVER = r"RAVALI"
DATABASE = "CricbuzzDB"

LOG_DIR = "output"
LOG_FILE = os.path.join(LOG_DIR, "teams_load_log.txt")

os.makedirs(LOG_DIR, exist_ok=True)

# ======================================
# CONNECTION
# ======================================
CONN_STR = (
    "DRIVER={SQL Server};"
    f"SERVER={SERVER};"
    f"DATABASE={DATABASE};"
    "Trusted_Connection=yes;"
)

# ======================================
# LOGGER
# ======================================
def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line)

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


# ======================================
# MAIN
# ======================================
def main():

    log("===== START teams load =====")

    # -----------------------------
    # Validate CSV
    # -----------------------------
    if not os.path.exists(CSV_FILE):
        log(f"ERROR: CSV not found -> {CSV_FILE}")
        return

    # -----------------------------
    # Read CSV
    # -----------------------------
    df = pd.read_csv(CSV_FILE)

    required_cols = {"team_id", "team_name", "source"}

    if not required_cols.issubset(df.columns):
        log("ERROR: CSV columns invalid.")
        log(f"Found columns: {list(df.columns)}")
        return

    # clean
    df = df.dropna(subset=["team_id", "team_name"])
    df["team_id"] = df["team_id"].astype(int)
    df["team_name"] = df["team_name"].astype(str).str.strip()
    df["source"] = df["source"].astype(str).str.strip()

    # remove duplicate ids
    df = df.drop_duplicates(subset=["team_id"])

    log(f"Rows ready for load: {len(df)}")

    # -----------------------------
    # Connect SQL Server
    # -----------------------------
    try:
        conn = pyodbc.connect(CONN_STR)
        cursor = conn.cursor()
        log("Connected to SQL Server.")
    except Exception as e:
        log(f"ERROR connecting SQL Server: {e}")
        return

    inserted = 0
    skipped = 0
    failed = 0

    # -----------------------------
    # Insert rows safely
    # -----------------------------
    for _, row in df.iterrows():

        try:
            cursor.execute("""
                IF NOT EXISTS (
                    SELECT 1 FROM teams WHERE team_id = ?
                )
                BEGIN
                    INSERT INTO teams (
                        team_id,
                        team_name,
                        source
                    )
                    VALUES (?, ?, ?)
                END
            """,
            row["team_id"],
            row["team_id"],
            row["team_name"],
            row["source"]
            )

            if cursor.rowcount == 1:
                inserted += 1
            else:
                skipped += 1

        except Exception as e:
            failed += 1
            log(f"FAILED team_id={row['team_id']} : {e}")

    conn.commit()
    cursor.close()
    conn.close()

    # -----------------------------
    # Summary
    # -----------------------------
    log("===== LOAD COMPLETE =====")
    log(f"Inserted : {inserted}")
    log(f"Skipped  : {skipped}")
    log(f"Failed   : {failed}")


if __name__ == "__main__":
    main()