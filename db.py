# AutoRE_Project/db.py
import pyodbc

def get_connection():
    """
    Returns a connection to SQL Server database.
    Update SERVER and DATABASE names as per your setup.
    """
    conn = pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=localhost\\SQLEXPRESS;"  # agar named instance use karte ho to: localhost\SQLEXPRESS
        "DATABASE=AutoRE_DB;"            # apne actual DB name se replace karo
        "Trusted_Connection=yes;"
    )
    return conn
