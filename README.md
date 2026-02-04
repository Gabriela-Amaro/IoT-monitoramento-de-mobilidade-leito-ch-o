# Monitoramento de Mobilidade Leito-Chão 🛏️

Sistema IoT para monitoramento de presença de pacientes usando sensor ultrassônico HC-SR04 com ESP32, MQTT e dashboard web em tempo real.

## Arquitetura

```
ESP32 + HC-SR04  →  MQTT (local)  →  emissor.py  →  API Flask (AWS)  →  Dashboard Web
```

## Requisitos

- Python 3.8+
- Docker & Docker Compose
- Mosquitto MQTT (para uso local)

## Execução Local

### 1. Backend (API + Dashboard)

```bash
cd subir
docker compose up --build
```

Acesse: **http://localhost:5000**

### 2. Simulador (testes sem hardware)

```bash
# Instalar dependências
pip install -r requirements.txt

# Rodar simulador (envia dados fictícios)
python simulador.py
```

### 3. Ambiente Completo (com MQTT + Hardware)

```bash
# Iniciar broker MQTT
sudo systemctl start mosquitto

# Rodar emissor (recebe MQTT e envia para API)
python emissor.py
```

## Configuração

| Arquivo | Variável | Descrição |
|---------|----------|-----------|
| `emissor.py` | `AWS_URL` | URL da API (alterar para localhost:5000 local) |
| `simulador.py` | `AWS_URL` | URL da API |
| `sensor_ultrassonico.ino` | `mqtt_server` | IP do broker MQTT |

## Endpoints da API

| Rota | Descrição |
|------|-----------|
| `GET /` | Dashboard tempo real |
| `GET /graficos` | Histórico de alertas |
| `POST /api/enviar` | Recebe dados do sensor |
| `GET /api/leituras-hoje` | Leituras do dia |
| `GET /api/alertas-por-hora` | Alertas agrupados por hora |
