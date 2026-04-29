import streamlit as st

st.set_page_config(
    page_title="Cricbuzz LiveStats",
    page_icon="🏏",
    layout="wide"
)

st.title("🏏 Cricbuzz LiveStats Dashboard")

st.markdown("""
Welcome to the Cricket Analytics Project.

Use the sidebar to navigate pages.

### Modules:
- Home
- SQL Queries
- Teams & Players
- Top Stats
- Live Matches
- Analytics Dashboard
""")