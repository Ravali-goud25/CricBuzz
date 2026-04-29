import streamlit as st
import pandas as pd
from utils.db_connection import get_connection

st.title("🏠 Home Dashboard")

conn = get_connection()

queries = {
    "Teams": "SELECT COUNT(*) cnt FROM teams",
    "Players": "SELECT COUNT(*) cnt FROM players",
    "Series": "SELECT COUNT(*) cnt FROM series",
    "Matches": "SELECT COUNT(*) cnt FROM matches_completed",
    "Batting Rows": "SELECT COUNT(*) cnt FROM batting_innings",
    "Bowling Rows": "SELECT COUNT(*) cnt FROM bowling_innings"
}

col1, col2, col3 = st.columns(3)

cards = []

for name, sql in queries.items():
    df = pd.read_sql(sql, conn)
    cards.append((name, int(df.iloc[0,0])))

for i, (name, val) in enumerate(cards):

    if i % 3 == 0:
        col = col1
    elif i % 3 == 1:
        col = col2
    else:
        col = col3

    col.metric(name, val)

st.divider()

st.subheader("Recent Matches")

sql = """
SELECT TOP 10
match_desc,
match_date
FROM matches_completed
ORDER BY match_date DESC
"""

df = pd.read_sql(sql, conn)

st.dataframe(df, use_container_width=True)

conn.close()