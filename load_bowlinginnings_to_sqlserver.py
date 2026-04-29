import pandas as pd
import pyodbc
import math

# ==========================================================
# CONFIG
# ==========================================================
CSV_FILE = r"output\bowling_innings.csv"

SERVER = r"RAVALI"
DATABASE = "CricbuzzDB"

CONN_STR = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    f"SERVER={SERVER};"
    f"DATABASE={DATABASE};"
    "Trusted_Connection=yes;"
)

# ==========================================================
# HELPERS
# ==========================================================
def is_null(v):

    if v is None:
        return True

    if isinstance(v, float) and math.isnan(v):
        return True

    s = str(v).strip().lower()

    return s in ("", "nan", "none", "null")


def clean_text(v):

    if is_null(v):
        return None

    return str(v).strip()


def clean_int(v):

    if is_null(v):
        return None

    try:
        return int(float(v))
    except:
        return None


def clean_float(v):

    if is_null(v):
        return None

    try:
        return float(v)
    except:
        return None


# ==========================================================
# LOAD CSV
# ==========================================================
df = pd.read_csv(CSV_FILE)

# ==========================================================
# CONNECT SQL SERVER
# ==========================================================
conn = pyodbc.connect(CONN_STR)
cursor = conn.cursor()

# ==========================================================
# VERIFY TABLE EXISTS
# ==========================================================
cursor.execute("""
SELECT COUNT(*)
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_NAME = 'bowling_innings'
""")

exists = cursor.fetchone()[0]

if exists == 0:
    print("Table bowling_innings does not exist.")
    cursor.close()
    conn.close()
    raise SystemExit()

# ==========================================================
# UNIQUE INDEX
# ==========================================================
cursor.execute("""
IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = 'ux_bowling_unique'
)
BEGIN
    CREATE UNIQUE INDEX ux_bowling_unique
    ON dbo.bowling_innings (
        match_id,
        innings_no,
        player_id
    )
END
""")

conn.commit()

# ==========================================================
# INSERT SQL
# ==========================================================
sql = """
IF NOT EXISTS (
    SELECT 1
    FROM dbo.bowling_innings
    WHERE match_id = ?
      AND innings_no = ?
      AND player_id = ?
)
BEGIN
    INSERT INTO dbo.bowling_innings (
        match_id,
        innings_no,
        bowling_team_id,
        player_id,
        overs,
        maidens,
        runs_conceded,
        wickets,
        economy,
        wides,
        no_balls,
        source
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
END
"""

# ==========================================================
# EXECUTE
# ==========================================================
loaded = 0
failed = 0

for _, row in df.iterrows():

    try:

        match_id = clean_int(row["match_id"])
        innings_no = clean_int(row["innings_no"])
        player_id = clean_int(row["player_id"])

        if match_id is None or player_id is None:
            failed += 1
            continue

        cursor.execute(
            sql,

            # check duplicate
            match_id,
            innings_no,
            player_id,

            # insert values
            match_id,
            innings_no,
            None,   # bowling_team_id not mapped yet
            player_id,
            clean_float(row["overs"]),
            clean_int(row["maidens"]),
            clean_int(row["runs_conceded"]),
            clean_int(row["wickets"]),
            clean_float(row["economy"]),
            clean_int(row["wides"]),
            clean_int(row["no_balls"]),
            clean_text(row["source"])
        )

        loaded += 1

    except Exception as e:

        failed += 1
        print(
            f"FAILED player_id={row.get('player_id')} -> {e}"
        )

# ==========================================================
# FINISH
# ==========================================================
conn.commit()
cursor.close()
conn.close()

print("\nDone.")
print("Inserted rows :", loaded)
print("Failed rows   :", failed)