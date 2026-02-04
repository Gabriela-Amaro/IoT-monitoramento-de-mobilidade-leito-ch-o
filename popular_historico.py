#!/usr/bin/env python3
"""
Popular Banco com Dados Históricos
Gera dados fictícios de dias anteriores para testar o histórico de alertas
"""

import requests
import random
from datetime import datetime, timedelta

# URL da API
AWS_URL = "http://98.95.203.92:5000/api/enviar"

# Configurações
DIAS_ANTERIORES = 7  # Quantos dias para trás gerar dados
LEITURAS_POR_DIA = 200  # Quantidade de leituras por dia
CHANCE_ALERTA = 0.25  # 25% de chance de alerta

def gerar_distancia(alerta):
    """Gera distância baseada no status de alerta"""
    if alerta:
        return round(random.uniform(30, 100), 1)  # Alerta: 30-100cm
    else:
        if random.random() < 0.5:
            return round(random.uniform(10, 25), 1)  # Normal: muito perto
        else:
            return round(random.uniform(110, 200), 1)  # Normal: muito longe

def main():
    print("=" * 60)
    print("📊 POPULAR BANCO COM DADOS HISTÓRICOS")
    print(f"   Dias: {DIAS_ANTERIORES} | Leituras/dia: {LEITURAS_POR_DIA}")
    print("=" * 60)
    
    total_enviados = 0
    total_erros = 0
    
    for dias_atras in range(DIAS_ANTERIORES, 0, -1):
        data_base = datetime.now() - timedelta(days=dias_atras)
        data_str = data_base.strftime("%Y-%m-%d")
        
        print(f"\n📅 Gerando dados para {data_str}...")
        
        enviados_dia = 0
        alertas_dia = 0
        
        for i in range(LEITURAS_POR_DIA):
            # Distribui leituras ao longo do dia (6h às 23h)
            hora = 6 + int((i / LEITURAS_POR_DIA) * 17)
            minuto = random.randint(0, 59)
            segundo = random.randint(0, 59)
            
            data_hora = data_base.replace(hour=hora, minute=minuto, second=segundo)
            
            alerta = random.random() < CHANCE_ALERTA
            if alerta:
                alertas_dia += 1
            
            distancia = gerar_distancia(alerta)
            
            payload = {
                "distancia_cm": distancia,
                "alerta": alerta,
                "data_hora": data_hora.strftime("%Y-%m-%dT%H:%M:%S")
            }
            
            try:
                resposta = requests.post(AWS_URL, json=payload, timeout=5)
                if resposta.status_code == 201:
                    enviados_dia += 1
                    total_enviados += 1
                else:
                    total_erros += 1
            except Exception as e:
                total_erros += 1
                if enviados_dia == 0:
                    print(f"   ❌ Erro de conexão: {e}")
                    print("   Verifique se o servidor está rodando!")
                    return
        
        print(f"   ✅ {enviados_dia} leituras | {alertas_dia} alertas ({alertas_dia/LEITURAS_POR_DIA*100:.0f}%)")
    
    print(f"\n{'=' * 60}")
    print(f"📊 RESUMO")
    print(f"   Total enviados: {total_enviados}")
    print(f"   Total erros:    {total_erros}")
    print(f"{'=' * 60}")
    print("\n✅ Pronto! Acesse /graficos para ver o histórico.")

if __name__ == "__main__":
    main()
