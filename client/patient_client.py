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
    # TODO: montar o dicionário JSON com patient_id, metric, value, unit, timestamp, token
    # TODO: conectar via TCP, enviar, receber resposta, calcular e imprimir RTT
    # TODO: verificar se a resposta contém "command" e imprimir se houver
    pass


def send_reading_udp(metric, value, unit):
    # TODO: mesmo que TCP, mas usando socket UDP (SOCK_DGRAM e sendto/recvfrom)
    pass


def run():
    # TODO: loop infinito que alterna entre TCP e UDP a cada ciclo
    # TODO: para cada ciclo, enviar todas as métricas de METRICS
    # TODO: usar random.uniform(min, max) para gerar os valores
    pass


if __name__ == "__main__":
    run()
