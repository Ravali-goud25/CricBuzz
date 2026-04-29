import pandas as pd
import pyodbc
import math

# ==========================================================
# CONFIG
# ==========================================================
CSV_FILE = r"output\batting_innings.csv"

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
# CONNECT
# ==========================================================
conn = pyodbc.connect(CONN_STR)
cursor = conn.cursor()

# ==========================================================
# VERIFY TABLE EXISTS
# ==========================================================
cursor.execute("""
SELECT COUNT(*)
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_NAME = 'batting_innings'
""")

exists = cursor.fetchone()[0]

if exists == 0:
    print("Table batting_innings does not exist in CricbuzzDB.")
    cursor.close()
    conn.close()
    raise SystemExit()

# ==========================================================
# CREATE UNIQUE INDEX (SAFE)
# ==========================================================
cursor.execute("""
IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = 'ux_batting_unique'
)
BEGIN
    CREATE UNIQUE INDEX ux_batting_unique
    ON dbo.batting_innings (
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
    FROM dbo.batting_innings
    WHERE match_id = ?
      AND innings_no = ?
      AND player_id = ?
)
BEGIN
    INSERT INTO dbo.batting_innings (
        match_id,
        innings_no,
        team_id,
        player_id,
        batting_position,
        runs,
        balls,
        fours,
        sixes,
        strike_rate,
        dismissal_text,
        not_out,
        source
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
END
"""

# ==========================================================
# LOAD DATA
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

        dismissal = clean_text(row["dismissal"])

        not_out = 1

        if dismissal:
            if "not out" not in dismissal.lower():
                not_out = 0

        cursor.execute(
            sql,

            # check
            match_id,
            innings_no,
            player_id,

            # insert
            match_id,
            innings_no,
            None,
            player_id,
            clean_int(row["bat_position"]),
            clean_int(row["runs"]),
            clean_int(row["balls"]),
            clean_int(row["fours"]),
            clean_int(row["sixes"]),
            clean_float(row["strike_rate"]),
            dismissal,
            not_out,
            clean_text(row["source"])
        )

        loaded += 1

    except Exception as e:
        failed += 1
        print(
            f"FAILED player={row.get('player_id')} -> {e}"
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