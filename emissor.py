import paho.mqtt.client as mqtt
import json
import requests
import time
from datetime import datetime

# --- CONFIGURAÇÕES ---
MQTT_BROKER = "localhost"  # Mosquitto Local
MQTT_TOPIC = "lab/03/ultrassonico"

# IP PÚBLICO DA EC2 DA AWS
AWS_URL = "http://44.213.60.114:5000/api/enviar"

# Variáveis globais para controle de tempo
ultimo_envio = 0
INTERVALO_ENVIO = 3  # Segundos

def on_connect(client, userdata, flags, rc):
    print("Conectado ao MQTT Local!")
    client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    global ultimo_envio
    
    try:
        # Recebe dados do ESP32
        payload = msg.payload.decode()
        dados = json.loads(payload)
        
        distancia = dados.get('distancia_cm')
        alerta = dados.get('alerta', False)
        
        print(f"Local: {distancia} cm | Alerta: {'SIM' if alerta else 'NÃO'}")
        
        # Verifica se já passou o intervalo
        agora = time.time()
        if (agora - ultimo_envio) >= INTERVALO_ENVIO:
            
            # Prepara o pacote para a AWS (adiciona timestamp)
            json_aws = {
                "distancia_cm": distancia,
                "alerta": alerta,
                "data_hora": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
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