import sqlite3

DB_NAME = "robot_telemetry.db"

def read_last_entries(n=10):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM telemetry ORDER BY timestamp DESC LIMIT ?", (n,))
    rows = c.fetchall()
    conn.close()

    print(f"Последние {n} записей из базы данных:")
    for row in rows:
        print(row)

if __name__ == "__main__":
    read_last_entries()
