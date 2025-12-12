import pyodbc

try:
    conn = pyodbc.connect(
        "Driver={ODBC Driver 17 for SQL Server};"
        "Server=DESKTOP-VEIPHS8\\SQLEXPRESS;"
        "Database=master;"
        "Trusted_Connection=yes;"
    )
    print("✅ Connection successful to SQL Server!")
    conn.close()
except Exception as e:
    print("❌ Error:", e)
