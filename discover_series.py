import os
import json
import pandas as pd

RAW_SERIES = "raw/series"
RAW_MATCHES = "raw/matches"
OUTPUT = "output"

os.makedirs(OUTPUT, exist_ok=True)

series_data = {}

# =====================================
# HELPERS
# =====================================
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


def add_series(
    series_id,
    series_name,
    match_format=None,
    category=None,
    host_country=None,
    start_date=None,
    end_date=None,
    total_matches=None,
    source="unknown"
):

    if not series_name:
        return

    sid = safe_int(series_id)

    # if no id available, use negative hash
    if sid is None:
        sid = abs(hash(series_name)) % 100000000
        sid = sid * -1

    if sid not in series_data:

        series_data[sid] = {
            "series_id": sid,
            "series_name": txt(series_name),
            "match_format": txt(match_format),
            "category": txt(category),
            "host_country": txt(host_country),
            "start_date": txt(start_date),
            "end_date": txt(end_date),
            "total_matches": safe_int(total_matches),
            "source": source
        }


# =====================================
# JSON READER
# =====================================
def read_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return None


# =====================================
# WALK SERIES FILES
# =====================================
def walk(obj, source):

    if isinstance(obj, dict):

        # direct series patterns
        if "seriesId" in obj and "seriesName" in obj:
            add_series(
                obj.get("seriesId"),
                obj.get("seriesName"),
                obj.get("seriesType"),
                obj.get("category"),
                obj.get("country"),
                obj.get("startDt"),
                obj.get("endDt"),
                obj.get("totalMatches"),
                source
            )

        if "seriesName" in obj and "matchDesc" in obj:
            add_series(
                obj.get("seriesId"),
                obj.get("seriesName"),
                source=source
            )

        if "seriesAdWrapper" in obj:
            pass

        for val in obj.values():
            walk(val, source)

    elif isinstance(obj, list):
        for item in obj:
            walk(item, source)


# =====================================
# MAIN
# =====================================
def main():

    # -------- parse raw series files ------
    for file in os.listdir(RAW_SERIES):

        if file.endswith(".json"):

            data = read_json(os.path.join(RAW_SERIES, file))

            if data:
                walk(data, file)

    # -------- parse match files ----------
    for file in os.listdir(RAW_MATCHES):

        if file.endswith(".json"):

            data = read_json(os.path.join(RAW_MATCHES, file))

            if data:
                walk(data, file)

    df = pd.DataFrame(list(series_data.values()))

    df = df.sort_values("series_name")

    out = os.path.join(OUTPUT, "series_discovered.csv")
    df.to_csv(out, index=False)

    print("Done.")
    print("Series discovered:", len(df))
    print("Saved:", out)


if __name__ == "__main__":
    main()