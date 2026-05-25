# Protocolo de Aplicação — Monitor Hospitalar

## Visão Geral

O protocolo define a comunicação entre sensores hospitalares simulados e um servidor central de monitoramento. Os sensores enviam leituras de frequência cardíaca (bpm), saturação de oxigênio (%), pressão arterial sistólica (mmHg), temperatura corporal (°C) e frequência respiratória (irpm) ao servidor, que valida, persiste e responde com confirmação. O servidor também expõe uma API HTTP para consulta dos dados por um painel web.

## Arquitetura

- **Modelo:** cliente-servidor
- **Clientes:** monitores de paciente simulados (`sensor_client.py`)
- **Servidor:** servidor central (`server.py`)
- **Banco de dados:** SQLite (`hospital.db`)
- **Interface web:** painel HTML (`dashboard/index.html`)

### Portas utilizadas

| Porta | Protocolo |                         Função                          |
|-------|-----------|---------------------------------------------------------|
| 9100  | TCP       |          Recebimento de leituras dos sensores           |
| 9101  | UDP       | Recebimento de leituras dos sensores (modo alternativo) |
| 8081  | HTTP/TCP  |               API REST para o painel web                |

## Formato das Mensagens

### Requisição — sensor para servidor (TCP e UDP)

Mensagem em JSON, codificada em UTF-8.

```json
{
  "patient_id": "patient_01",
  "type": "heart_rate",
  "value": 82.0,
  "unit": "bpm",
  "timestamp": "2026-05-25T10:00:00.000000",
  "token": "token123"
}
```

| Campo      | Tipo   | Descricao                                        |
|------------|--------|--------------------------------------------------|
| patient_id | string | Identificador unico do paciente                  |
| type       | string | Tipo de sinal vital (ver tabela de metricas)     |
| value      | float  | Valor numerico da leitura                        |
| unit       | string | Unidade da medicao                               |
| timestamp  | string | Data e hora do envio (formato ISO 8601)          |
| token      | string | Token de autenticacao do paciente                |

#### Métricas suportadas

| type                  | Unidade | Faixa normal     |
|-----------------------|---------|------------------|
| heart_rate            | bpm     | 60 – 100         |
| spo2                  | %       | 95 – 100         |
| systolic_bp           | mmHg    | 90 – 120         |
| temperature           | °C      | 36.1 – 37.2      |
| respiratory_rate      | irpm    | 12 – 20          |

### Resposta — sucesso sem alerta (servidor para sensor)

```json
{
  "status": "success",
  "rtt_echo": "2026-05-25T10:00:00.000000",
  "command": null
}
```

### Resposta — sucesso com alerta e comando (servidor para sensor)

Quando um valor ultrapassa um limite, o servidor inclui um alerta e pode enviar um comando ao cliente:

```json
{
  "status": "success",
  "rtt_echo": "2026-05-25T10:00:00.000000",
  "alert": {
    "level": "CRITICAL",
    "message": "Frequência cardíaca crítica: 130 bpm"
  },
  "command": {
    "action": "INCREASE_RATE",
    "interval_s": 2
  }
}
```

| Campo    | Tipo          | Descricao                                               |
|----------|---------------|---------------------------------------------------------|
| status   | string        | "success" indica que a leitura foi aceita e salva       |
| rtt_echo | string        | Timestamp original enviado pelo sensor (para RTT)       |
| alert    | objeto ou null| Presente quando um limite foi ultrapassado              |
| command  | objeto ou null| Comando do servidor para o cliente (pode ser null)      |

#### Comandos possíveis

| action        | Descrição                                              |
|---------------|--------------------------------------------------------|
| INCREASE_RATE | Reduzir o intervalo de envio (parâmetro: interval_s)   |
| NORMAL_RATE   | Voltar ao intervalo padrão de envio                    |

### Resposta — erro de autenticacao (servidor para sensor)

```json
{
  "status": "error",
  "message": "token invalido"
}
```

### Resposta — erro de formato (servidor para sensor)

```json
{
  "status": "error",
  "message": "Expecting value: line 1 column 1 (char 0)"
}
```

## Fluxo de Comunicacao

### TCP

```
Sensor                          Servidor
  |                                |
  |--- TCP SYN ------------------->|
  |<-- TCP SYN-ACK ----------------|
  |--- TCP ACK ------------------->|  (handshake 3-way)
  |                                |
  |--- JSON (leitura + token) ---->|
  |                                |--- valida token
  |                                |--- salva no SQLite
  |                                |--- verifica limites de alerta
  |                                |--- gera comando se necessário
  |<-- JSON (status + alerta + comando) ---|
  |                                |
  |--- TCP FIN ------------------->|
  |<-- TCP FIN-ACK ----------------|  (encerramento)
```

### UDP

```
Sensor                          Servidor
  |                                |
  |--- JSON (leitura + token) ---->|  (sem conexao previa)
  |                                |--- valida token
  |                                |--- salva no SQLite
  |                                |--- verifica limites de alerta
  |                                |--- gera comando se necessário
  |<-- JSON (status + alerta + comando) ---|
```

### HTTP (painel web para servidor)

```
Dashboard                       Servidor
  |                                |
  |--- GET /readings HTTP/1.1 ---->|
  |<-- 200 OK + JSON array --------|
  |                                |
  |--- GET /alerts HTTP/1.1 ------>|
  |<-- 200 OK + JSON array --------|
```

## Endpoints HTTP

### GET /readings

Retorna as ultimas 50 leituras salvas, ordenadas por timestamp decrescente.

Resposta:
```json
[
  {
    "id": 1,
    "patient_id": "patient_01",
    "type": "heart_rate",
    "value": 82.0,
    "unit": "bpm",
    "timestamp": "2026-05-25 10:00:00.000000"
  }
]
```

### GET /alerts

Retorna os ultimos 20 alertas gerados, ordenados por timestamp decrescente.

Resposta:
```json
[
  {
    "id": 1,
    "patient_id": "patient_01",
    "type": "heart_rate",
    "value": 130.0,
    "level": "CRITICAL",
    "message": "Frequência cardíaca crítica: 130 bpm",
    "timestamp": "2026-05-25 10:00:00.000000"
  }
]
```

## Autenticacao

Cada paciente possui um token fixo registrado no servidor. A cada mensagem recebida (TCP ou UDP), o servidor consulta a tabela `patients` no SQLite e verifica se o par (patient_id, token) existe. Se o token for invalido ou ausente, o servidor responde com "status": "error" e descarta a leitura.

O registro de pacientes e feito na inicializacao do servidor via `register_patient(patient_id, token)`.

## Alertas Automaticos

O servidor classifica os alertas em tres niveis de gravidade:

| Metrica           | WARNING           | CRITICAL          | EMERGENCY       |
|-------------------|-------------------|-------------------|-----------------|
| heart_rate        | > 100 ou < 55 bpm | > 120 ou < 45 bpm | > 150 ou < 30   |
| spo2              | < 94%             | < 90%             | < 85%           |
| systolic_bp       | > 140 ou < 90     | > 180 ou < 80     | > 200 ou < 60   |
| temperature       | > 37.8 ou < 36.0  | > 39.5 ou < 35.5  | >= 41.0 ou < 34 |
| respiratory_rate  | > 20 ou < 12      | > 28 ou < 8       | > 35 ou < 6     |

Quando um limite e ultrapassado, o servidor persiste o alerta na tabela `alerts`, registra no log e inclui um comando na resposta ao cliente.

## Medicao de RTT

O cliente registra o tempo imediatamente antes de iniciar a conexao (TCP) ou o envio (UDP), e calcula o RTT apos receber a resposta:

```python
t_start = time.time()
# envia mensagem e aguarda resposta
rtt = (time.time() - t_start) * 1000  # em milissegundos
```

O campo `rtt_echo` na resposta contem o timestamp original enviado pelo sensor, permitindo correlacionar o instante de envio com a resposta do servidor.

## Comparacao TCP vs UDP

| Caracteristica     | TCP (porta 9100)          | UDP (porta 9101)          |
|--------------------|---------------------------|---------------------------|
| Conexao            | Orientado a conexao       | Sem conexao               |
| Confiabilidade     | Garantida (retransmissao) | Nao garantida             |
| Ordenacao          | Garantida                 | Nao garantida             |
| Handshake          | 3-way handshake           | Nenhum                    |
| RTT tipico (local) | 8-13 ms                   | 5-9 ms                    |
| Overhead           | Maior                     | Menor                     |
