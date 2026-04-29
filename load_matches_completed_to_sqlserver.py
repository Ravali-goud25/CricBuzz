import pandas as pd
import pyodbc
import math
SERVER = "RAVALI"
DATABASE = "CricbuzzDB"

conn = pyodbc.connect(
    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
    f"SERVER={SERVER};"
    f"DATABASE={DATABASE};"
    f"Trusted_Connection=yes;"
)

cursor = conn.cursor()

# ==========================================================
# FILE PATH
# ==========================================================
CSV_FILE = "output/matches_completed.csv"

# ==========================================================
# READ CSV
# ==========================================================
df = pd.read_csv(CSV_FILE)

# ==========================================================
# HELPERS
# ==========================================================
def clean(v):
    if pd.isna(v):
        return None

    if isinstance(v, float) and math.isnan(v):
        return None

    s = str(v).strip()

    if s == "" or s.lower() == "nan":
        return None

    return v


def to_int(v):
    v = clean(v)

    if v is None:
        return None

    try:
        return int(float(v))
    except:
        return None


def to_text(v):
    v = clean(v)

    if v is None:
        return None

    return str(v).strip()


def to_date(v):
    v = clean(v)

    if v is None:
        return None

    try:
        return pd.to_datetime(v).date()
    except:
        return None


def to_datetime(v):
    v = clean(v)

    if v is None:
        return None

    try:
        return pd.to_datetime(v).to_pydatetime()
    except:
        return None

# ==========================================================
# OPTIONAL: CLEAR OLD DATA
# ==========================================================
cursor.execute("DELETE FROM matches_completed")
conn.commit()

# ==========================================================
# INSERT
# ==========================================================
inserted = 0
failed = 0

sql = """
INSERT INTO matches_completed (
    match_id,
    series_id,
    series_name,
    match_desc,
    match_format,
    team1_id,
    team2_id,
    venue_id,
    match_date,
    start_time,
    status,
    winner_team_id,
    win_margin,
    win_type,
    toss_winner_team_id,
    toss_decision,
    source
)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

for _, row in df.iterrows():

    try:
        values = (
            to_int(row.get("match_id")),
            to_int(row.get("series_id")),
            to_text(row.get("series_name")),
            to_text(row.get("match_desc")),
            to_text(row.get("match_format")),
            to_int(row.get("team1_id")),
            to_int(row.get("team2_id")),
            to_int(row.get("venue_id")),
            to_date(row.get("match_date")),
            to_datetime(row.get("start_time")),
            to_text(row.get("status")),
            to_int(row.get("winner_team_id")),
            to_text(row.get("win_margin")),
            to_text(row.get("win_type")),
            to_int(row.get("toss_winner_team_id")),
            to_text(row.get("toss_decision")),
            to_text(row.get("source"))
        )

        cursor.execute(sql, values)
        inserted += 1

    except Exception as e:
        failed += 1
        print("FAILED ROW:", row.get("match_id"), "->", e)

# ==========================================================
# COMMIT
# ==========================================================
conn.commit()

print("\nDone.")
print("Inserted rows :", inserted)
print("Failed rows   :", failed)

cursor.close()
conn.close()