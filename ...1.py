import sqlite3

con = sqlite3.connect("vecinal.db")
cur = con.cursor()

print("INCIDENCIAS:")
for r in cur.execute("SELECT * FROM incidencias"):
    print(r)

print("\nGEOLOCALIZACION:")
for r in cur.execute("SELECT * FROM geolocalizacion"):
    print(r)

con.close()
