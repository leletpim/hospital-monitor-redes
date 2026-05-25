import sqlite3

DB_PATH = "hospital.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id TEXT NOT NULL,
            type TEXT NOT NULL,
            value REAL NOT NULL,
            unit TEXT NOT NULL,
            timestamp DATETIME NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id TEXT NOT NULL,
            type TEXT NOT NULL,
            value REAL NOT NULL,
            level TEXT NOT NULL,
            message TEXT NOT NULL,
            timestamp DATETIME NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id TEXT UNIQUE NOT NULL,
            token TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()


def insert_alert(patient_id, type, value, message, timestamp, level):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO alerts (patient_id, type, value, message, timestamp, level)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (patient_id, type, value, message, timestamp, level))
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


def insert_reading(patient_id, type, value, unit, timestamp):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO readings (patient_id, type, value, unit, timestamp)
        VALUES (?, ?, ?, ?, ?)
    ''', (patient_id, type, value, unit, timestamp))
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

# insere um novo paciente na tabela patients
def register_patient(patient_id, token):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR IGNORE INTO patients (patient_id, token)
        VALUES (?, ?)
    ''', (patient_id, token))
    conn.commit()
    conn.close()

# busca o patient_id na tabela e verifica se o token bate
def validate_token(patient_id, token):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM patients
        WHERE patient_id = ? AND token = ?
    ''', (patient_id, token))
    patient = cursor.fetchone()
    conn.close()
    return patient is not None