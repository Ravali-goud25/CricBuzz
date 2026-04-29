import pandas as pd
import pyodbc
import math

# ==========================================================
# CONFIG
# ==========================================================
SERVER = "RAVALI"
DATABASE = "CricbuzzDB"
CSV_FILE = "output/venues_discovered.csv"

# ==========================================================
# CONNECT SQL SERVER
# ==========================================================
conn = pyodbc.connect(
    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
    f"SERVER={SERVER};"
    f"DATABASE={DATABASE};"
    f"Trusted_Connection=yes;"
)

cursor = conn.cursor()

# ==========================================================
# READ CSV
# ==========================================================
df = pd.read_csv(CSV_FILE)

# ==========================================================
# HELPERS
# ==========================================================
def is_null(v):
    if v is None:
        return True

    try:
        if pd.isna(v):
            return True
    except:
        pass

    s = str(v).strip().lower()

    return s in ["", "nan", "none", "null"]


def clean_text(v):
    if is_null(v):
        return None
    return str(v).strip()


def clean_int(v):
    if is_null(v):
        return None

    try:
        if isinstance(v, str):
            v = v.replace(",", "").strip()

        return int(float(v))
    except:
        return None


# ==========================================================
# CLEAR OLD TABLE DATA
# ==========================================================
cursor.execute("DELETE FROM venues")
conn.commit()

# ==========================================================
# INSERT SQL
# ==========================================================
sql = """
INSERT INTO venues (
    venue_id,
    venue_name,
    city,
    country,
    capacity,
    source
)
VALUES (?, ?, ?, ?, ?, ?)
"""

inserted = 0
failed = 0

# ==========================================================
# LOAD ROWS
# ==========================================================
for _, row in df.iterrows():

    try:
        values = (
            clean_int(row.get("venue_id")),
            clean_text(row.get("venue_name")),
            clean_text(row.get("city")),
            clean_text(row.get("country")),
            clean_int(row.get("capacity")),
            clean_text(row.get("source"))
        )

        cursor.execute(sql, values)
        inserted += 1

    except Exception as e:
        failed += 1
        print("FAILED ROW:", row.get("venue_id"), "->", e)

# ==========================================================
# COMMIT
# ==========================================================
conn.commit()

print("\nDone.")
print("Inserted rows :", inserted)
print("Failed rows   :", failed)

cursor.close()
conn.close()