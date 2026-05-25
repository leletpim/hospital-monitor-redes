import socket
import threading
import json
from datetime import datetime
from flask import Flask, jsonify
from flask_cors import CORS
from database import init_db, insert_reading, get_readings, insert_alert, get_alerts, register_patient, validate_token
import time as time_module
import logging

logging.basicConfig(
    filename='server.log',
    level=logging.INFO,
    format='%(asctime)s %(message)s'
)

app = Flask(__name__)
CORS(app)

TCP_PORT = 9100

ALERT_LIMITS = {
    "heart_rate": [
        ("WARNING",   lambda v: v > 100 or v < 55),
        ("CRITICAL",  lambda v: v > 120 or v < 45),
        ("EMERGENCY", lambda v: v > 150 or v < 30)
    ],

    "spo2": [
        ("WARNING",   lambda v: v < 94),
        ("CRITICAL",  lambda v: v < 90),
        ("EMERGENCY", lambda v: v < 85)
    ],

    "systolic_bp": [
        ("WARNING",   lambda v: v > 140 or v < 90),
        ("CRITICAL",  lambda v: v > 180 or v < 80),
        ("EMERGENCY", lambda v: v > 200 or v < 60)
    ],

    "temperature": [
        ("WARNING",   lambda v: v > 37.8 or v < 36),
        ("CRITICAL",  lambda v: v > 39.5 or v < 35.5),
        ("EMERGENCY", lambda v: v >= 41 or v < 34)
    ],

    "respiratory_rate": [
        ("WARNING",   lambda v: v > 20 or v < 12),
        ("CRITICAL",  lambda v: v > 28 or v < 8),
        ("EMERGENCY", lambda v: v > 35 or v < 6)
    ],
}

metrics = {
    "bytes_received": 0,
    "messages_received": 0,
    "start_time": time_module.time()
}
metrics_lock = threading.Lock()


def update_metrics(num_bytes):
    with metrics_lock:
        metrics["bytes_received"] += num_bytes
        metrics["messages_received"] += 1

COMMANDS = {
    "WARNING":   {"action": "INCREASE_RATE", "interval_s": 3},
    "CRITICAL":  {"action": "INCREASE_RATE", "interval_s": 1},
    "EMERGENCY": {"action": "INCREASE_RATE", "interval_s": 1},
}

def check_and_save_alert(reading):
    metric = reading['type']
    value = reading['value']

    if metric not in ALERT_LIMITS:
        return None

    # verifica do mais grave para o menos grave
    detected_level = None
    for level, condition in reversed(ALERT_LIMITS[metric]):
        if condition(value):
            detected_level = level
            break

    if detected_level is None:
        return None

    message = f"{metric} fora do limite ({detected_level}): {value}"
    insert_alert(reading['patient_id'], metric, value, message, datetime.now(), detected_level)
    print(f"ALERTA {detected_level}: {message}")
    logging.warning(f"ALERTA {detected_level} | {reading['patient_id']} | {message}")

    return COMMANDS[detected_level]


# recebe dados, faz parse do JSON, salva, responde
def handle_client(conn, addr):
    with conn: 
        try:
            data = conn.recv(1024).decode('utf-8')
            update_metrics(len(data.encode('utf-8')))
            reading = json.loads(data)

            if not validate_token(reading['patient_id'], reading.get('token')):
                logging.warning(f"Token inválido | patient_id: {reading['patient_id']}")
                response = {"status": "error", "message": "token inválido"}
                conn.send(json.dumps(response).encode('utf-8'))
                return

            insert_reading(
                patient_id=reading['patient_id'],
                type=reading['type'],
                value=reading['value'],
                unit=reading['unit'],
                timestamp=datetime.now()
            )
            logging.info(f"TCP | {reading['patient_id']} | {reading['type']}: {reading['value']}")

            command = check_and_save_alert(reading)
            response = {"status": "success", "rtt_echo": reading['timestamp'], "command": command}

        except (json.JSONDecodeError, KeyError) as e:
            response = {"status": "error", "message": str(e)}

        conn.send(json.dumps(response).encode('utf-8'))

# cria socket, bind, listen, loop de accept + thread por cliente
def start_tcp_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', TCP_PORT))
        s.listen()
        print(f"TCP server listening on port {TCP_PORT}")
        while True:
            conn, addr = s.accept()
            print(f"Connection from {addr}")
            threading.Thread(target=handle_client, args=(conn, addr)).start()
    pass

UDP_PORT = 9101

def handle_udp(s, data, addr):
    try:
        update_metrics(len(data))
        reading = json.loads(data.decode('utf-8'))

        if not validate_token(reading['patient_id'], reading.get('token')):
                response = {"status": "error", "message": "token inválido"}
                s.sendto(json.dumps(response).encode('utf-8'), addr)
                return
        
        insert_reading( 
            patient_id=reading['patient_id'],
            type=reading['type'],
            value=reading['value'],
            unit=reading['unit'],
            timestamp=datetime.now()
        )
        logging.info(f"UDP | {reading['patient_id']} | {reading['type']}: {reading['value']}")

        command = check_and_save_alert(reading)
        response = {"status": "success", "rtt_echo": reading['timestamp'], "command": command}

    except (json.JSONDecodeError, KeyError) as e:
        response = {"status": "error", "message": str(e)}
    s.sendto(json.dumps(response).encode('utf-8'), addr)

def start_udp_server():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.bind(('', UDP_PORT))
        print(f"UDP server listening on port {UDP_PORT}")
        while True:
            data, addr = s.recvfrom(4096)
            print(f"UDP packet from {addr}")
            threading.Thread(target=handle_udp, args=(s, data, addr)).start()

@app.route('/readings')
def readings():
    rows = get_readings()
    result = []
    for row in rows:
        result.append({
            "id": row[0], "patient_id": row[1], "type": row[2],
            "value": row[3], "unit": row[4], "timestamp": row[5]
        })
    return jsonify(result)

@app.route('/alerts')
def alerts():
    rows = get_alerts()
    result = []
    for row in rows:
        result.append({
            "id": row[0],
            "patient_id": row[1],
            "type": row[2],
            "value": row[3],
            "level": row[4],
            "message": row[5],
            "timestamp": row[6]
        })
    return jsonify(result)

@app.route('/metrics')
def get_metrics():
    elapsed = time_module.time() - metrics["start_time"]
    return jsonify({
        "bytes_received": metrics["bytes_received"],
        "messages_received": metrics["messages_received"],
        "throughput_bps": round(metrics["bytes_received"] / elapsed, 2),
        "uptime_seconds": round(elapsed, 1)
    })

def start_http_server():
    app.run(port=8081, debug=False, use_reloader=False)

if __name__ == "__main__":
    init_db()
    register_patient("patient_01", "token123")
    threading.Thread(target=start_http_server, daemon=True).start()
    threading.Thread(target=start_udp_server, daemon=True).start()
    start_tcp_server()