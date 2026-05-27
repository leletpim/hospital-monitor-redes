import socket
import json
import time
import random
from datetime import datetime

SERVER_HOST = '127.0.0.1'
TCP_PORT = 9100
UDP_PORT = 9101
PATIENT_ID = "patient_01"
TOKEN = "token123"
INTERVAL = 5  # segundos entre envios

# Métricas e suas faixas normais para simulação
METRICS = {
    "heart_rate":       {"unit": "bpm",  "min": 60,   "max": 100},
    "spo2":             {"unit": "%",    "min": 95,   "max": 100},
    "systolic_bp":      {"unit": "mmHg", "min": 90,   "max": 120},
    "temperature":      {"unit": "°C",   "min": 36.1, "max": 37.2},
    "respiratory_rate": {"unit": "irpm", "min": 12,   "max": 20},
}


def send_reading_tcp(metric, value, unit):
    data = {
        "patient_id": PATIENT_ID,
        "type": metric,
        "value": value,
        "unit": unit,
        "timestamp": datetime.now().isoformat(),
        "token": TOKEN
    }

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        client.connect((SERVER_HOST, TCP_PORT))

        start_time = time.time()

        client.sendall(json.dumps(data).encode())

        response = client.recv(1024)

        end_time = time.time()

        rtt = (end_time - start_time) * 1000

        response_data = json.loads(response.decode())

        print(f"[TCP] {metric}: {value:.2f} {unit} | RTT: {rtt:.2f} ms")

        if "command" in response_data:
            print("Comando recebido:", response_data["command"])

    except Exception as e:
        print("Erro TCP:", e)

    finally:
        client.close()

def send_reading_udp(metric, value, unit):
    data = {
        "patient_id": PATIENT_ID,
        "type": metric,
        "value": value,
        "unit": unit,
        "timestamp": datetime.now().isoformat(),
        "token": TOKEN
    }

    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        start_time = time.time()

        client.sendto(
            json.dumps(data).encode(),
            (SERVER_HOST, UDP_PORT)
        )

        response, _ = client.recvfrom(1024)

        end_time = time.time()

        rtt = (end_time - start_time) * 1000

        response_data = json.loads(response.decode())

        print(f"[UDP] {metric}: {value:.2f} {unit} | RTT: {rtt:.2f} ms")

        if "command" in response_data:
            print("Comando recebido:", response_data["command"])

    except Exception as e:
        print("Erro UDP:", e)

    finally:
        client.close()

def run():
    use_tcp = True

    while True:
        for metric, info in METRICS.items():

            value = random.uniform(info["min"], info["max"])

            if use_tcp:
                send_reading_tcp(
                    metric,
                    value,
                    info["unit"]
                )
            else:
                send_reading_udp(
                    metric,
                    value,
                    info["unit"]
                )

        use_tcp = not use_tcp

        time.sleep(INTERVAL)


if __name__ == "__main__":
    run()
