
import sqlite3
from datetime import datetime

DB_NAME = "robot_telemetry.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS telemetry (
            timestamp TEXT,
            temperature REAL,
            vibration REAL,
            voltage REAL,
            current REAL,
            energy REAL,
            speed REAL,
            motor_load REAL,
            pitch REAL,
            roll REAL
        )
    """)
    conn.commit()
    conn.close()

def insert_telemetry(data: dict):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        INSERT INTO telemetry (timestamp, temperature, vibration, voltage, current, energy, speed, motor_load, pitch, roll)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().isoformat(),
        data["temperature"],
        data["vibration"],
        data["voltage"],
        data["current"],
        data["energy"],
        data["speed"],
        data["motor_load"],
        data["pitch"],
        data["roll"]
    ))
    conn.commit()
    conn.close()
