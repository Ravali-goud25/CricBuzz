import os
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

RAW_MATCH = "raw/matches"
RAW_SERIES = "raw/series"
RAW_VENUES = "raw/venues"
OUTPUT_DIR = "output"

os.makedirs(RAW_VENUES, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ==========================================================
# SAFE API SETTINGS
# ==========================================================
REQUEST_GAP = 8          # seconds
MAX_CALLS_PER_RUN = 10   # safe batch
TIMEOUT = 30

venues = {}

# ==========================================================
# HELPERS
# ==========================================================
def read_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return None


def clean_text(v):
    if v is None:
        return None
    s = str(v).strip()
    return s if s else None


def clean_capacity(v):
    if v is None:
        return None

    nums = "".join(c for c in str(v) if c.isdigit())

    if nums == "":
        return None

    try:
        return int(nums)
    except:
        return None


def safe_int(v):
    try:
        return int(v)
    except:
        return None


# ==========================================================
# UPSERT VENUE
# ==========================================================
def add_venue(
    venue_id,
    venue_name,
    city=None,
    country=None,
    capacity=None,
    source="raw"
):

    venue_id = safe_int(venue_id)

    if not venue_id or not venue_name:
        return

    row = {
        "venue_id": venue_id,
        "venue_name": clean_text(venue_name),
        "city": clean_text(city),
        "country": clean_text(country),
        "capacity": clean_capacity(capacity),
        "source": source
    }

    if venue_id not in venues:
        venues[venue_id] = row
        return

    # enrich existing
    old = venues[venue_id]

    for k in ["venue_name", "city", "country", "capacity"]:
        if old.get(k) in [None, "", 0] and row.get(k) not in [None, "", 0]:
            old[k] = row[k]


# ==========================================================
# JSON WALKER
# ==========================================================
def walk(obj, source):

    if isinstance(obj, dict):

        # common match structure
        if "venueInfo" in obj and isinstance(obj["venueInfo"], dict):

            v = obj["venueInfo"]

            add_venue(
                venue_id=v.get("id"),
                venue_name=v.get("ground"),
                city=v.get("city"),
                country=v.get("country"),
                capacity=v.get("capacity"),
                source=source
            )

        # alternate structure
        if "venue" in obj and isinstance(obj["venue"], dict):

            v = obj["venue"]

            add_venue(
                venue_id=v.get("id"),
                venue_name=v.get("name") or v.get("ground"),
                city=v.get("city"),
                country=v.get("country"),
                capacity=v.get("capacity"),
                source=source
            )

        # recurse
        for val in obj.values():
            walk(val, source)

    elif isinstance(obj, list):
        for item in obj:
            walk(item, source)


# ==========================================================
# LOAD EXISTING RAW FILES
# ==========================================================
def load_existing():

    folders = [RAW_MATCH, RAW_SERIES, RAW_VENUES]

    for folder in folders:

        if not os.path.exists(folder):
            continue

        for file in os.listdir(folder):

            if file.endswith(".json"):

                path = os.path.join(folder, file)
                data = read_json(path)

                if data:
                    walk(data, file)


# ==========================================================
# FETCH VENUE DETAIL
# ==========================================================
def fetch_venue(venue_id):

    endpoint = f"/venues/v1/{venue_id}"
    url = BASE_URL + endpoint

    try:
        print("Fetching:", endpoint)

        r = requests.get(
            url,
            headers=HEADERS,
            timeout=TIMEOUT
        )

        if r.status_code == 429:
            print("RATE LIMITED -> stopping batch")
            return False

        if r.status_code == 403:
            print("FORBIDDEN / API KEY ISSUE")
            return False

        r.raise_for_status()

        data = r.json()

        # save raw
        path = os.path.join(RAW_VENUES, f"{venue_id}.json")

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        walk(data, f"{venue_id}.json")

        time.sleep(REQUEST_GAP)

        return True

    except Exception as e:
        print("FAILED:", venue_id, e)
        return False


# ==========================================================
# ENRICH FEW VENUES EACH RUN
# ==========================================================
def enrich():

    count = 0

    ids = sorted(list(venues.keys()))

    for venue_id in ids:

        if count >= MAX_CALLS_PER_RUN:
            break

        raw_file = os.path.join(RAW_VENUES, f"{venue_id}.json")

        # skip already fetched
        if os.path.exists(raw_file):
            continue

        ok = fetch_venue(venue_id)

        if not ok:
            break

        count += 1


# ==========================================================
# SAVE CSV
# ==========================================================
def save_csv():

    rows = list(venues.values())

    df = pd.DataFrame(rows)

    if df.empty:
        print("No venues found.")
        return

    df = df[
        [
            "venue_id",
            "venue_name",
            "city",
            "country",
            "capacity",
            "source"
        ]
    ]

    df = df.sort_values(
        by=["country", "city", "venue_name"],
        na_position="last"
    )

    out = os.path.join(
        OUTPUT_DIR,
        "venues_discovered.csv"
    )

    df.to_csv(out, index=False)

    print("\nDone.")
    print("Venues:", len(df))
    print("Saved:", out)


# ==========================================================
# MAIN
# ==========================================================
def main():

    print("STEP 1 -> Loading raw files")
    load_existing()

    print("Current venues:", len(venues))

    print("STEP 2 -> Safe API enrichment")
    enrich()

    print("STEP 3 -> Saving CSV")
    save_csv()


if __name__ == "__main__":
    main()