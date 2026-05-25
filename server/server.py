import socket
import threading
import json
from datetime import datetime
from flask import Flask, jsonify
from flask_cors import CORS
from database import init_db, insert_reading, get_readings, insert_alert, get_alerts, register_sensor, validate_token
import time as time_module
import logging

logging.basicConfig(
    filename='server.log',
    level=logging.INFO,
    format='%(asctime)s %(message)s'
)

app = Flask(__name__)
CORS(app)

TCP_PORT = 9000

ALERT_LIMITS = {
    "frequência cardíaca": (50, 100),
    "saturação de oxigênio": (95, 100),
    "pressão arterial sistólica": (0, 120),
    "pressão arterial diastólica": (0, 80), 
    "temperatura corporal": (36.1, 37.2),
    "frequência respiratória": (12, 20) 
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

def check_and_save_alert(reading):
    type = reading['type']
    value = reading['value']
    if type in ALERT_LIMITS and value > ALERT_LIMITS[type]:
        message = f"{type} alta: {value:.1f} (limite: {ALERT_LIMITS[type]})"
        insert_alert(reading['sensor_id'], type, value, message, datetime.now())
        print(f"ALERTA: {message}")
        logging.warning(f"ALERTA | {reading['sensor_id']} | {message}")


# recebe dados, faz parse do JSON, salva, responde
def handle_client(conn, addr):
    with conn: 
        try:
            data = conn.recv(1024).decode('utf-8')
            update_metrics(len(data.encode('utf-8')))
            reading = json.loads(data)

            if not validate_token(reading['sensor_id'], reading.get('token')):
                logging.warning(f"Token inválido | sensor_id: {reading['sensor_id']}")
                response = {"status": "error", "message": "token inválido"}
                conn.send(json.dumps(response).encode('utf-8'))
                return

            insert_reading(
                sensor_id=reading['sensor_id'],
                type=reading['type'],
                value=reading['value'],
                unit=reading['unit'],
                timestamp=datetime.now()
            )
            logging.info(f"TCP | {reading['sensor_id']} | {reading['type']}: {reading['value']}")

            check_and_save_alert(reading)
            response = {"status": "success", "rtt_echo": reading['timestamp']}

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

UDP_PORT = 9001

def handle_udp(s, data, addr):
    try:
        update_metrics(len(data))
        reading = json.loads(data.decode('utf-8'))

        if not validate_token(reading['sensor_id'], reading.get('token')):
                response = {"status": "error", "message": "token inválido"}
                s.sendto(json.dumps(response).encode('utf-8'), addr)
                return
        
        insert_reading(
            sensor_id=reading['sensor_id'],
            type=reading['type'],
            value=reading['value'],
            unit=reading['unit'],
            timestamp=datetime.now()
        )
        logging.info(f"UDP | {reading['sensor_id']} | {reading['type']}: {reading['value']}")

        check_and_save_alert(reading)

        response = {"status": "success", "rtt_echo": reading['timestamp']}

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
            "id": row[0], "sensor_id": row[1], "type": row[2],
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
            "sensor_id": row[1],
            "type": row[2],
            "value": row[3],
            "message": row[4],
            "timestamp": row[5]
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
    app.run(port=8080, debug=False, use_reloader=False)

if __name__ == "__main__":
    init_db()
    register_sensor("sensor_01", "token123")
    threading.Thread(target=start_http_server, daemon=True).start()
    threading.Thread(target=start_udp_server, daemon=True).start()
    start_tcp_server()