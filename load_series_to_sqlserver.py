import pandas as pd
import pyodbc
import math

# ======================================
# CONFIG
# ======================================
CSV_FILE = r"output\series_discovered.csv"

SERVER = r"RAVALI"
DATABASE = "CricbuzzDB"

CONN_STR = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    f"SERVER={SERVER};"
    f"DATABASE={DATABASE};"
    "Trusted_Connection=yes;"
)

# =====================================================
# HELPERS
# =====================================================
def is_null(v):
    if v is None:
        return True

    if isinstance(v, float) and math.isnan(v):
        return True

    txt = str(v).strip().lower()

    return txt in ("", "nan", "none", "null")


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


def clean_date(v):
    """
    Supports:
    2026-01-27
    1745366400000
    blank/null
    """

    if is_null(v):
        return None

    txt = str(v).strip()

    try:
        # epoch milliseconds
        if txt.isdigit() and len(txt) >= 10:
            dt = pd.to_datetime(
                int(txt),
                unit="ms",
                errors="coerce"
            )

        else:
            dt = pd.to_datetime(
                txt,
                errors="coerce"
            )

        if pd.isna(dt):
            return None

        return dt.date()

    except:
        return None


# =====================================================
# LOAD CSV
# =====================================================
df = pd.read_csv(CSV_FILE)

# =====================================================
# CONNECT SQL SERVER
# =====================================================
conn = pyodbc.connect(CONN_STR)
cursor = conn.cursor()

# =====================================================
# MERGE SQL
# =====================================================
sql = """
MERGE series AS target
USING (
    SELECT
        ? AS series_id,
        ? AS series_name,
        ? AS match_format,
        ? AS category,
        ? AS host_country,
        ? AS start_date,
        ? AS end_date,
        ? AS total_matches,
        ? AS source
) AS src
ON target.series_id = src.series_id

WHEN MATCHED THEN
UPDATE SET
    series_name   = src.series_name,
    match_format  = src.match_format,
    category      = src.category,
    host_country  = src.host_country,
    start_date    = src.start_date,
    end_date      = src.end_date,
    total_matches = src.total_matches,
    source        = src.source

WHEN NOT MATCHED THEN
INSERT (
    series_id,
    series_name,
    match_format,
    category,
    host_country,
    start_date,
    end_date,
    total_matches,
    source
)
VALUES (
    src.series_id,
    src.series_name,
    src.match_format,
    src.category,
    src.host_country,
    src.start_date,
    src.end_date,
    src.total_matches,
    src.source
);
"""

# =====================================================
# EXECUTE
# =====================================================
loaded = 0
failed = 0

for _, row in df.iterrows():

    try:

        series_id = clean_int(row["series_id"])

        if series_id is None:
            failed += 1
            continue

        cursor.execute(
            sql,

            series_id,
            clean_text(row["series_name"]),
            clean_text(row["match_format"]),
            clean_text(row["category"]),
            clean_text(row["host_country"]),
            clean_date(row["start_date"]),
            clean_date(row["end_date"]),
            clean_int(row["total_matches"]),
            clean_text(row["source"])
        )

        loaded += 1

    except Exception as e:

        failed += 1
        print(
            f"FAILED row series_id={row['series_id']} -> {e}"
        )

# =====================================================
# COMMIT
# =====================================================
conn.commit()
cursor.close()
conn.close()

print("\nDone.")
print("Loaded rows :", loaded)
print("Failed rows :", failed)