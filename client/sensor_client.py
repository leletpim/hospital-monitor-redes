import socket
import json
import time
import random
from datetime import datetime

SERVER_HOST = '127.0.0.1'
TCP_PORT = 9000
SENSOR_ID = "sensor_01"
INTERVAL = 3  # segundos entre envios

# monta o JSON, conecta, envia, recebe resposta, calcula e imprime RTT
def send_reading_tcp(type, value, unit):
    reading = {
        "sensor_id": SENSOR_ID,
        "type": type,
        "value": value,
        "unit": unit,
        "timestamp": datetime.now().isoformat(),
        "token": "token123"
    }
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        t_start = time.time()                         
        s.connect((SERVER_HOST, TCP_PORT))
        s.send(json.dumps(reading).encode('utf-8'))
        response = s.recv(1024).decode('utf-8')
        rtt = (time.time() - t_start) * 1000          
        print(f"[{SENSOR_ID}] {type}: {value:.1f}{unit} | RTT: {rtt:.2f}ms")
        print(f"Response: {response}")

def send_reading_udp(type, value, unit):
    reading = {
        "sensor_id": SENSOR_ID,
        "type": type,
        "value": value,
        "unit": unit,
        "timestamp": datetime.now().isoformat(),
        "token": "token123"
    }

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        t_start = time.time()
        s.sendto(json.dumps(reading).encode('utf-8'), (SERVER_HOST, 9001))
        s.settimeout(2)
        try:
            response, _ = s.recvfrom(1024)
            rtt = (time.time() - t_start) * 1000
            print(f"[UDP] {type}: {value:.1f}{unit} | RTT: {rtt:.2f}ms")
        except socket.timeout:
            print(f"[UDP] {type}: sem resposta (timeout)")


# loop infinito alternando entre parâmetros
def run():
    cycle = 0
    while True:
        if cycle % 2 == 0:
            send_reading_tcp("frequência cardíaca", random.uniform(50, 100), "bpm")
            time.sleep(INTERVAL)
            send_reading_tcp("saturação de oxigênio", random.uniform(95, 100), "%")
            time.sleep(INTERVAL)
            send_reading_tcp("pressão arterial sistólica", random.uniform(0, 120), "mmHg")
            time.sleep(INTERVAL)
            send_reading_tcp("pressão arterial diastólica", random.uniform(0, 80), "mmHg")
            time.sleep(INTERVAL)
            send_reading_tcp("temperatura corporal", random.uniform(36.1, 37.2), "°C")
            time.sleep(INTERVAL)
            send_reading_tcp("frequência respiratória", random.uniform(12, 20), "irpm")
        else:
            send_reading_udp("frequência cardíaca", random.uniform(50, 100), "bpm")
            time.sleep(INTERVAL)
            send_reading_udp("saturação de oxigênio", random.uniform(95, 100), "%")
            time.sleep(INTERVAL)
            send_reading_udp("pressão arterial sistólica", random.uniform(0, 120), "mmHg")
            time.sleep(INTERVAL)
            send_reading_udp("pressão arterial diastólica", random.uniform(0, 80), "mmHg")
            time.sleep(INTERVAL)
            send_reading_udp("temperatura corporal", random.uniform(36.1, 37.2), "°C")
            time.sleep(INTERVAL)
            send_reading_udp("frequência respiratória", random.uniform(12, 20), "irpm")
        time.sleep(INTERVAL)
        cycle += 1


if __name__ == "__main__":
    run()
