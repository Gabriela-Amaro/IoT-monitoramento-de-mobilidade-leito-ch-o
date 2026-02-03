import paho.mqtt.client as mqtt
import json
import requests
import time
from datetime import datetime

# --- CONFIGURAÇÕES ---
MQTT_BROKER = "localhost"  # Seu Mosquitto Local
MQTT_TOPIC = "lab/03/dht11"

# COLOQUE AQUI O IP PÚBLICO DA SUA EC2 DA AWS
AWS_URL = "http://44.213.60.114:5000/api/enviar"

# Variáveis globais para controle de tempo
ultimo_envio = 0
INTERVALO_ENVIO = 3  # Segundos

def verificar_periodo():
    hora = datetime.now().hour
    if 4 <= hora < 12:
        return "noite"
    elif 12 <= hora < 18:
        return "tarde"
    else:
        return "noite"

def on_connect(client, userdata, flags, rc):
    print("Conectado ao MQTT Local!")
    client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    global ultimo_envio
    
    try:
        # Recebe e Trata Localmente
        payload = msg.payload.decode()
        dados = json.loads(payload)
        temp = dados['temperatura']
        umid = dados['umidade']
        periodo_atual = verificar_periodo()
        
        print(f"Local: {temp}°C | {umid}% | Periodo: {periodo_atual}")
        
        # Verifica se já passou 3 segundos
        agora = time.time()
        if (agora - ultimo_envio) >= INTERVALO_ENVIO:
            
            # Prepara o pacote para a AWS
            json_aws = {
                "temperatura": temp,
                "umidade": umid,
                "periodo": periodo_atual
            }
            
            # Envia para a AWS via HTTP POST
            try:
                resposta = requests.post(AWS_URL, json=json_aws, timeout=2)
                if resposta.status_code == 201:
                    print(">> Enviado para AWS com sucesso!")
                    ultimo_envio = agora
                else:
                    print(f"Erro AWS: {resposta.status_code}")
            except Exception as e:
                print(f"Falha na conexão com AWS: {e}")
                
    except Exception as e:
        print(f"Erro de processamento: {e}")

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect(MQTT_BROKER, 1883, 60)
client.loop_forever()