# 🏏 Cricbuzz LiveStats - Cricket Analytics Dashboard

A comprehensive **cricket analytics web application** that integrates live data from the Cricbuzz API with a SQL Server database. Built as a full-stack learning project featuring real-time updates, interactive SQL analytics, and CRUD operations.

## ✨ Key Features

- ⚡ **Real-time match updates** using Cricbuzz API
- 📊 **Detailed player statistics** and top performer dashboards
- 🔍 **Interactive SQL Query Interface** with 25 practice questions (Beginner to Advanced)
- 🛠️ **Full CRUD Operations** for managing player records
- 📈 **SQL-driven analytics** with proper data preprocessing
- 🗄️ **Database integration** with SQL Server

## 🛠️ Tech Stack

- **Frontend**: Streamlit
- **Backend**: Python 3
- **Database**: Microsoft SQL Server
- **API**: Cricbuzz Cricket API (RapidAPI)
- **Database Connector**: pyodbc
- **Environment Management**: python-dotenv

## 📁 Project Structure

```bash
cricbuzz_livestats/
├── app.py                          # Main Streamlit application
├── requirements.txt
├── README.md
├── .env                            # Database and API credentials
├── pages/
│   ├── home.py                     # Home / Dashboard landing page
│   ├── live_matches.py             # Live & Recent Matches
│   ├── top_stats.py                # Top Player Statistics
│   ├── sql_queries.py              # SQL Practice Questions (25 queries)
│   └── crud_operations.py          # Create, Read, Update, Delete operations
├── utils/
│   └── db_connection.py            # SQL Server connection utility
└── notebooks/                      # Optional Jupyter notebooks
    └── data_fetching.ipynb