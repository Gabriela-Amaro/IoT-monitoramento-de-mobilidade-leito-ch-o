#!/usr/bin/env python3
"""
Simulador do Sensor Ultrassônico para Testes
Envia dados fictícios para a API da AWS em loop
"""

import requests
import random
import time
from datetime import datetime

# URL da API (altere para o IP da AWS em produção)
AWS_URL = "http://98.95.203.92:5000/api/enviar"

# Configurações da simulação
INTERVALO_ENVIO = 3  # segundos entre cada envio
SIMULAR_ALERTAS = True  # se True, simula alertas periodicamente

def gerar_leitura():
    """
    Gera uma leitura simulada do sensor.
    - Distância normal (pessoa na cama): 10-25cm ou 110-200cm
    - Distância de alerta (pessoa levantou): 30-100cm
    """
    if SIMULAR_ALERTAS and random.random() < 0.3:  # 30% chance de alerta
        # Simula pessoa levantando (alerta)
        distancia = random.uniform(30, 100)
        alerta = True
    else:
        # Simula pessoa deitada (normal)
        if random.random() < 0.5:
            distancia = random.uniform(10, 25)  # muito perto
        else:
            distancia = random.uniform(110, 200)  # muito longe
        alerta = False
    
    return round(distancia, 1), alerta

def main():
    print("=" * 50)
    print("🔧 SIMULADOR DO SENSOR ULTRASSÔNICO")
    print(f"📡 Enviando para: {AWS_URL}")
    print(f"⏱️  Intervalo: {INTERVALO_ENVIO}s")
    print("=" * 50)
    print("\nPressione Ctrl+C para parar\n")
    
    contador = 0
    alertas_total = 0
    
    try:
        while True:
            contador += 1
            distancia, alerta = gerar_leitura()
            
            if alerta:
                alertas_total += 1
            
            payload = {
                "distancia_cm": distancia,
                "alerta": alerta,
                "data_hora": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            }
            
            status_icon = "🔴 ALERTA" if alerta else "🟢 Normal"
            print(f"[{contador:04d}] {distancia:6.1f} cm | {status_icon}")
            
            try:
                resposta = requests.post(AWS_URL, json=payload, timeout=5)
                if resposta.status_code == 201:
                    print(f"        ✅ Enviado com sucesso!")
                else:
                    print(f"        ❌ Erro: HTTP {resposta.status_code}")
            except requests.exceptions.ConnectionError:
                print(f"        ⚠️  Sem conexão com {AWS_URL}")
            except Exception as e:
                print(f"        ❌ Erro: {e}")
            
            time.sleep(INTERVALO_ENVIO)
            
    except KeyboardInterrupt:
        print(f"\n\n{'=' * 50}")
        print(f"📊 RESUMO DA SIMULAÇÃO")
        print(f"   Total de leituras: {contador}")
        print(f"   Total de alertas:  {alertas_total}")
        print(f"   Taxa de alertas:   {(alertas_total/contador*100):.1f}%")
        print(f"{'=' * 50}")

if __name__ == "__main__":
    main()
