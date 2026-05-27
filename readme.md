# Hospital Monitor Redes

Projeto de monitoramento hospitalar utilizando TCP e UDP.

## Dependências

Instale as bibliotecas necessárias:

```bash
pip install flask flask-cors
```

## Como executar o servidor

```bash
cd server
python server.py
```

O servidor ficará disponível em:

- TCP: porta 9100
- UDP: porta 9101
- API Dashboard: http://localhost:8081

## Como executar o cliente

Abra outro terminal:

```bash
cd client
python patient_client.py
```

O cliente enviará métricas simuladas do paciente alternando entre TCP e UDP.

## Dashboard

Abra o arquivo:

```plaintext
dashboard/index.html
```

O dashboard exibe:

- Leituras dos pacientes
- Alertas
- Métricas do servidor

Atualização automática a cada 5 segundos.