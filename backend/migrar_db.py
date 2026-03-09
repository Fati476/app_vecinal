import sqlite3
import psycopg2

# SQLite (tu base local)
sqlite_conn = sqlite3.connect("backend/vecinal.db")
sqlite_cursor = sqlite_conn.cursor()

# PostgreSQL (Render)
pg_conn = psycopg2.connect(
    "postgresql://vecinal_user:ZE9kfkLjb0fHceALt0ZOqy2EDEMsbF9H@dpg-d6mv0qlm5p6s73837ge0-a.oregon-postgres.render.com/vecinal",
    sslmode="require"
)
pg_cursor = pg_conn.cursor()

# Obtener tablas de SQLite
sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = sqlite_cursor.fetchall()

for table in tables:
    table_name = table[0]

    if table_name.startswith("sqlite_"):
     continue

    print(f"Migrando tabla: {table_name}")

    sqlite_cursor.execute(f"SELECT * FROM {table_name}")
    rows = sqlite_cursor.fetchall()

    if not rows:
        continue

    placeholders = ",".join(["%s"] * len(rows[0]))

    for row in rows:
        pg_cursor.execute(
            f"INSERT INTO {table_name} VALUES ({placeholders})",
            row
        )

pg_conn.commit()

print("Migración completada")

sqlite_conn.close()
pg_conn.close()