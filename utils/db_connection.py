import pyodbc
import streamlit as st
from dotenv import load_dotenv
import os

load_dotenv()  # Load environment variables from .env file


@st.cache_resource
def get_db_connection():
    """Create and return a connection to SQL Server using Windows Authentication"""
    try:
        conn_str = (
            'DRIVER={ODBC Driver 17 for SQL Server};'
            f'SERVER={os.getenv("DB_SERVER")};'
            f'DATABASE={os.getenv("DB_NAME")};'
            'Trusted_Connection=yes;'  # This is the key for Windows Authentication
            'Encrypt=yes;TrustServerCertificate=yes;'
        )

        conn = pyodbc.connect(conn_str)
        return conn
    except Exception as e:
        st.error(f"Database connection failed: {str(e)}")
        st.error("Please check: 1) SQL Server is running, 2) Database exists, 3) ODBC Driver is installed")
        return None


def execute_query(query, params=None, fetch=True):
    """Helper function to execute SQL queries"""
    conn = get_db_connection()
    if not conn:
        return None

    cursor = conn.cursor()
    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)

        if fetch and cursor.description is not None:
            columns = [column[0] for column in cursor.description]
            rows = cursor.fetchall()
            return [dict(zip(columns, row)) for row in rows]
        else:
            conn.commit()
            return {"status": "success", "message": "Query executed successfully"}
    except Exception as e:
        if conn:
            conn.rollback()
        st.error(f"Query execution error: {str(e)}")
        return None
    finally:
        if cursor:
            cursor.close()