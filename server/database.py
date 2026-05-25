import sqlite3

DB_PATH = "sensor_data.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sensor_id TEXT NOT NULL,
            type TEXT NOT NULL,
            value REAL NOT NULL,
            unit TEXT NOT NULL,
            timestamp DATETIME NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sensor_id TEXT NOT NULL,
            type TEXT NOT NULL,
            value REAL NOT NULL,
            message TEXT NOT NULL,
            timestamp DATETIME NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sensor_id TEXT UNIQUE NOT NULL,
            token TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()


def insert_alert(sensor_id, type, value, message, timestamp):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO alerts (sensor_id, type, value, message, timestamp)
        VALUES (?, ?, ?, ?, ?)
    ''', (sensor_id, type, value, message, timestamp))
    conn.commit()
    conn.close()

def get_alerts(limit=20):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM alerts
        ORDER BY timestamp DESC
        LIMIT ?
    ''', (limit,))
    alerts = cursor.fetchall()
    conn.close()
    return alerts


def insert_reading(sensor_id, type, value, unit, timestamp):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO readings (sensor_id, type, value, unit, timestamp)
        VALUES (?, ?, ?, ?, ?)
    ''', (sensor_id, type, value, unit, timestamp))
    conn.commit()
    conn.close()

def get_readings(limit=50):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM readings
        ORDER BY timestamp DESC
        LIMIT ?
    ''', (limit,))
    readings = cursor.fetchall()
    conn.close()
    return readings

# insere um novo sensor na tabela users
def register_sensor(sensor_id, token):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR IGNORE INTO users (sensor_id, token)
        VALUES (?, ?)
    ''', (sensor_id, token))
    conn.commit()
    conn.close()

# busca o sensor_id na tabela e verifica se o token bate
def validate_token(sensor_id, token):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM users
        WHERE sensor_id = ? AND token = ?
    ''', (sensor_id, token))
    user = cursor.fetchone()
    conn.close()
    return user is not None