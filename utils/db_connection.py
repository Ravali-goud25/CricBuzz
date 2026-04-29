import pyodbc

def get_connection():
    conn = pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=RAVALI;"
        "DATABASE=CricbuzzDB;"
        "Trusted_Connection=yes;"
    )
    return conn