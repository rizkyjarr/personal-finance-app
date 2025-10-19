from os import getenv
from dotenv import load_dotenv
from mssql_python import connect

load_dotenv()

with connect(getenv("SQL_CONNECTION_STRING")) as conn:
    with conn.cursor() as cursor:
        cursor.execute("SELECT TOP 3 name, collation_name FROM sys.databases")
        rows = cursor.fetchall()
        for row in rows:
            print(row.name, row.collation_name)