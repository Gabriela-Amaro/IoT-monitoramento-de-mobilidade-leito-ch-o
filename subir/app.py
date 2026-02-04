from flask import Flask, request, jsonify, render_template_string, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit
from datetime import datetime, date, timedelta, timezone
from sqlalchemy import func
import os

# Timezone Brasil (UTC-3)
BRAZIL_TZ = timezone(timedelta(hours=-3))

app = Flask(__name__)
app.config['SECRET_KEY'] = 'monitor-ultrassonico-secret'

# Configuração do Banco
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://user:password@db/monitor_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Modelo da Tabela
class Leitura(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    distancia_cm = db.Column(db.Float)
    alerta = db.Column(db.Boolean, default=False)
    data_hora = db.Column(db.DateTime, default=datetime.utcnow)
    ip_origem = db.Column(db.String(45))  # Suporta IPv4 e IPv6

def get_client_ip():
    """Obtém o IP real do cliente, considerando proxies"""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    return request.remote_addr

# Quando cliente conecta via WebSocket, entra na room do seu IP
@socketio.on('connect')
def handle_connect():
    from flask_socketio import join_room
    ip_cliente = get_client_ip()
    join_room(ip_cliente)

with app.app_context():
    db.create_all()

@app.route('/sensor.jsonld')
def serve_jsonld():
    return send_from_directory(os.getcwd(), 'sensor.jsonld', mimetype='application/ld+json')

@app.route('/api/enviar', methods=['POST'])
def receber_dados():
    dados = request.json
    ip_cliente = get_client_ip()
    
    # Parse data_hora string to datetime
    data_hora_str = dados.get('data_hora')
    if data_hora_str:
        try:
            data_hora = datetime.fromisoformat(data_hora_str)
        except ValueError:
            data_hora = datetime.now()
    else:
        data_hora = datetime.now()
    
    # Aceita tanto 'distancia_cm' quanto 'distancia'
    distancia = dados.get('distancia_cm') or dados.get('distancia')
    
    nova_leitura = Leitura(
        distancia_cm=distancia,
        alerta=dados.get('alerta', False),
        data_hora=data_hora,
        ip_origem=ip_cliente
    )
    db.session.add(nova_leitura)
    db.session.commit()
    
    # Notifica apenas clientes do mesmo IP (room = IP)
    socketio.emit('nova_leitura', {
        'distancia_cm': nova_leitura.distancia_cm,
        'alerta': nova_leitura.alerta,
        'data_hora': nova_leitura.data_hora.strftime("%H:%M:%S")
    }, room=ip_cliente)
    
    return jsonify({"status": "sucesso", "ip_registrado": ip_cliente}), 201

@app.route('/api/leituras-hoje')
def leituras_hoje():
    # Usa timezone do Brasil para determinar "hoje"
    agora_brasil = datetime.now(BRAZIL_TZ)
    hoje = agora_brasil.date()
    ip_visualizador = get_client_ip()
    
    # Filtra apenas leituras do mesmo IP (mesma casa/rede)
    leituras = Leitura.query.filter(
        func.date(Leitura.data_hora) == hoje,
        Leitura.ip_origem == ip_visualizador
    ).order_by(Leitura.data_hora.asc()).all()
    
    return jsonify([{
        'distancia_cm': l.distancia_cm,
        'alerta': l.alerta,
        'data_hora': l.data_hora.strftime("%H:%M:%S")
    } for l in leituras])

@app.route('/api/alertas-por-hora')
def alertas_por_hora():
    data_str = request.args.get('data')
    if data_str:
        data_filtro = datetime.strptime(data_str, '%Y-%m-%d').date()
    else:
        # Usa timezone do Brasil como padrão
        data_filtro = datetime.now(BRAZIL_TZ).date()
    
    ip_visualizador = get_client_ip()
    
    # Agrupa alertas por hora (filtrando por IP)
    resultado = db.session.query(
        func.extract('hour', Leitura.data_hora).label('hora'),
        func.count(Leitura.id).label('total_alertas')
    ).filter(
        func.date(Leitura.data_hora) == data_filtro,
        Leitura.alerta == True,
        Leitura.ip_origem == ip_visualizador
    ).group_by(
        func.extract('hour', Leitura.data_hora)
    ).order_by('hora').all()
    
    # Formata resposta com todas as 24 horas
    alertas_por_hora = {int(r.hora): r.total_alertas for r in resultado}
    dados = [{'hora': h, 'alertas': alertas_por_hora.get(h, 0)} for h in range(24)]
    
    return jsonify({
        'data': data_filtro.strftime('%Y-%m-%d'),
        'dados': dados
    })

@app.route('/api/datas-disponiveis')
def datas_disponiveis():
    ip_visualizador = get_client_ip()
    
    # Retorna apenas datas que têm dados do mesmo IP
    datas = db.session.query(
        func.date(Leitura.data_hora).label('data')
    ).filter(
        Leitura.ip_origem == ip_visualizador
    ).distinct().order_by(func.date(Leitura.data_hora).desc()).all()
    
    return jsonify([d.data.strftime('%Y-%m-%d') for d in datas])

@app.route('/')
def index():
    ultima = Leitura.query.order_by(Leitura.id.desc()).first()
    
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Monitoramento de Mobilidade</title>
        <meta charset="UTF-8">
        <script src="https://cdn.socket.io/4.0.0/socket.io.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: 'Segoe UI', Tahoma, sans-serif; 
                background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                min-height: 100vh;
                color: #fff;
                padding: 20px;
            }
            .container { max-width: 1200px; margin: 0 auto; }
            h1 { 
                text-align: center; 
                margin-bottom: 30px;
                font-size: 2em;
            }
            h1 span { opacity: 0.7; font-weight: normal; }
            
            .status-card {
                background: rgba(255,255,255,0.1);
                backdrop-filter: blur(10px);
                border-radius: 20px;
                padding: 30px;
                margin-bottom: 30px;
                border: 1px solid rgba(255,255,255,0.2);
                display: flex;
                justify-content: space-around;
                align-items: center;
                flex-wrap: wrap;
                gap: 20px;
            }
            
            .status-item { text-align: center; }
            .status-value { 
                font-size: 3em; 
                font-weight: bold;
                display: block;
            }
            .status-label { opacity: 0.7; margin-top: 5px; }
            
            .alert-indicator {
                padding: 15px 40px;
                border-radius: 50px;
                font-size: 1.5em;
                font-weight: bold;
                transition: all 0.3s ease;
            }
            .alert-normal { 
                background: linear-gradient(135deg, #00b894, #00cec9);
                box-shadow: 0 0 30px rgba(0,184,148,0.5);
            }
            .alert-danger { 
                background: linear-gradient(135deg, #e74c3c, #c0392b);
                box-shadow: 0 0 30px rgba(231,76,60,0.5);
                animation: pulse 1s infinite;
            }
            @keyframes pulse {
                0%, 100% { transform: scale(1); }
                50% { transform: scale(1.05); }
            }
            
            .chart-card {
                background: rgba(255,255,255,0.1);
                backdrop-filter: blur(10px);
                border-radius: 20px;
                padding: 30px;
                margin-bottom: 30px;
                border: 1px solid rgba(255,255,255,0.2);
            }
            .chart-title { margin-bottom: 20px; font-size: 1.2em; }
            
            .nav-link {
                display: inline-block;
                background: linear-gradient(135deg, #6c5ce7, #a29bfe);
                color: #fff;
                text-decoration: none;
                padding: 15px 30px;
                border-radius: 50px;
                font-weight: bold;
                transition: transform 0.3s ease;
            }
            .nav-link:hover { transform: translateY(-3px); }
            .text-center { text-align: center; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1><span>Monitoramento de Mobilidade Leito-Chão</span></h1>
            
            <div class="status-card">
                <div class="status-item">
                    <span class="status-value" id="distancia">--</span>
                    <span class="status-label">Distância (cm)</span>
                </div>
                <div class="status-item">
                    <span class="status-value" id="hora">--:--:--</span>
                    <span class="status-label">Última Leitura</span>
                </div>
                <div id="alert-box" class="alert-indicator alert-normal">
                    🟢 Normal
                </div>
            </div>
            
            <div class="chart-card">
                <h3 class="chart-title">Distância ao Longo do Tempo (Hoje)</h3>
                <canvas id="distanciaChart"></canvas>
            </div>
            
            <div class="text-center">
                <a href="/graficos" class="nav-link">Ver Histórico de Alertas</a>
            </div>
        </div>
        
        <script>
            const socket = io();
            let chart;
            const MAX_PONTOS = 100;
            let alertas = []; // Array para armazenar status de alerta de cada ponto
            
            // Inicializa gráfico
            const ctx = document.getElementById('distanciaChart').getContext('2d');
            chart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [
                        {
                            // Linha principal (todas as leituras)
                            label: 'Distância (cm)',
                            data: [],
                            borderColor: '#00cec9',
                            backgroundColor: 'rgba(0,206,201,0.1)',
                            fill: true,
                            tension: 0.4,
                            pointRadius: 3,
                            pointBackgroundColor: [],
                            pointBorderColor: [],
                            pointBorderWidth: 1,
                            borderWidth: 2
                        },
                        {
                            // Linha de alertas (só conecta pontos de alerta)
                            label: 'Alertas',
                            data: [],
                            borderColor: '#e74c3c',
                            backgroundColor: 'transparent',
                            fill: false,
                            tension: 0,
                            pointRadius: 5,
                            pointBackgroundColor: '#e74c3c',
                            pointBorderColor: '#c0392b',
                            pointBorderWidth: 2,
                            borderWidth: 1,
                            spanGaps: true // Conecta pontos mesmo com gaps (null)
                        }
                    ]
                },
                options: {
                    animation: false,
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: true,
                            grid: { color: 'rgba(255,255,255,0.1)' },
                            ticks: { color: '#fff' }
                        },
                        x: {
                            grid: { color: 'rgba(255,255,255,0.1)' },
                            ticks: { color: '#fff', maxTicksLimit: 10 }
                        }
                    },
                    plugins: {
                        legend: { labels: { color: '#fff' } }
                    }
                }
            });
            
            // Carrega dados iniciais (todos do dia)
            fetch('/api/leituras-hoje')
                .then(r => r.json())
                .then(data => {
                    // Carrega todos os dados históricos
                    chart.data.labels = data.map(l => l.data_hora);
                    chart.data.datasets[0].data = data.map(l => l.distancia_cm);
                    alertas = data.map(l => l.alerta);
                    
                    // Linha de alertas: só mostra valor quando tem alerta
                    chart.data.datasets[1].data = data.map(l => l.alerta ? l.distancia_cm : null);
                    
                    // Define cores dos pontos da linha principal
                    chart.data.datasets[0].pointBackgroundColor = alertas.map(a => a ? '#e74c3c' : '#00cec9');
                    chart.data.datasets[0].pointBorderColor = alertas.map(a => a ? '#c0392b' : '#00b894');
                    chart.update('none');
                    
                    if (data.length > 0) {
                        const ultimo = data[data.length - 1];
                        atualizarStatus(ultimo.distancia_cm, ultimo.alerta, ultimo.data_hora);
                    }
                });
            
            
            function addPonto(hora, distancia, alerta) {
                // Limita novos pontos
                if (chart.data.labels.length > MAX_PONTOS) {
                    chart.data.labels.shift();
                    chart.data.datasets[0].data.shift();
                    chart.data.datasets[1].data.shift();
                    chart.data.datasets[0].pointBackgroundColor.shift();
                    chart.data.datasets[0].pointBorderColor.shift();
                    alertas.shift();
                }
                
                chart.data.labels.push(hora);
                chart.data.datasets[0].data.push(distancia);
                chart.data.datasets[1].data.push(alerta ? distancia : null); // Linha de alertas
                alertas.push(alerta);
                
                // Cor do ponto na linha principal
                chart.data.datasets[0].pointBackgroundColor.push(alerta ? '#e74c3c' : '#00cec9');
                chart.data.datasets[0].pointBorderColor.push(alerta ? '#c0392b' : '#00b894');
                
                chart.update('none');
            }
            
            function atualizarStatus(distancia, alerta, hora) {
                document.getElementById('distancia').textContent = distancia.toFixed(1);
                document.getElementById('hora').textContent = hora;
                
                const alertBox = document.getElementById('alert-box');
                if (alerta) {
                    alertBox.className = 'alert-indicator alert-danger';
                    alertBox.innerHTML = '🔴 ALERTA!';
                } else {
                    alertBox.className = 'alert-indicator alert-normal';
                    alertBox.innerHTML = '🟢 Normal';
                }
            }
            
            // Timer para adicionar pontos vazios quando não recebe dados
            let ultimoRecebimento = Date.now();
            const INTERVALO_ESPERADO = 3000; // 3 segundos
            
            // Marca quando recebeu dados
            socket.on('nova_leitura', function(data) {
                ultimoRecebimento = Date.now();
                addPonto(data.data_hora, data.distancia_cm, data.alerta);
                atualizarStatus(data.distancia_cm, data.alerta, data.data_hora);
            });
            
            // Verifica a cada segundo se precisa adicionar ponto vazio
            setInterval(() => {
                const agora = Date.now();
                if (agora - ultimoRecebimento > INTERVALO_ESPERADO) {
                    // Não recebeu dados recentemente, adiciona ponto vazio
                    const horaAtual = new Date().toLocaleTimeString('pt-BR', {hour: '2-digit', minute: '2-digit', second: '2-digit'});
                    addPontoVazio(horaAtual);
                    ultimoRecebimento = agora; // Reseta para não adicionar vários seguidos
                }
            }, 1000);
            
            function addPontoVazio(hora) {
                if (chart.data.labels.length > MAX_PONTOS) {
                    chart.data.labels.shift();
                    chart.data.datasets[0].data.shift();
                    chart.data.datasets[1].data.shift();
                    chart.data.datasets[0].pointBackgroundColor.shift();
                    chart.data.datasets[0].pointBorderColor.shift();
                    alertas.shift();
                }
                
                chart.data.labels.push(hora);
                chart.data.datasets[0].data.push(null); // Ponto vazio
                chart.data.datasets[1].data.push(null);
                alertas.push(false);
                chart.data.datasets[0].pointBackgroundColor.push('transparent');
                chart.data.datasets[0].pointBorderColor.push('transparent');
                
                chart.update('none');
            }
            
            // Fallback: polling a cada 5s caso WebSocket falhe
            setInterval(() => {
                fetch('/api/leituras-hoje')
                    .then(r => r.json())
                    .then(data => {
                        if (data.length > 0) {
                            const ultimo = data[data.length - 1];
                            atualizarStatus(ultimo.distancia_cm, ultimo.alerta, ultimo.data_hora);
                        }
                    });
            }, 5000);
        </script>
    </body>
    </html>
    """
    return render_template_string(html)

@app.route('/graficos')
def graficos():
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Histórico de Alertas - IoT</title>
        <meta charset="UTF-8">
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: 'Segoe UI', Tahoma, sans-serif; 
                background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                min-height: 100vh;
                color: #fff;
                padding: 20px;
            }
            .container { max-width: 1200px; margin: 0 auto; }
            h1 { 
                text-align: center; 
                margin-bottom: 30px;
                font-size: 2em;
            }
            
            .controls {
                background: rgba(255,255,255,0.1);
                backdrop-filter: blur(10px);
                border-radius: 20px;
                padding: 20px;
                margin-bottom: 30px;
                border: 1px solid rgba(255,255,255,0.2);
                display: flex;
                justify-content: center;
                align-items: center;
                gap: 20px;
                flex-wrap: wrap;
            }
            
            select, button {
                padding: 12px 25px;
                border-radius: 50px;
                border: none;
                font-size: 1em;
                cursor: pointer;
            }
            select {
                background: rgba(255,255,255,0.9);
                color: #333;
            }
            button {
                background: linear-gradient(135deg, #6c5ce7, #a29bfe);
                color: #fff;
                font-weight: bold;
                transition: transform 0.3s ease;
            }
            button:hover { transform: translateY(-2px); }
            
            .chart-card {
                background: rgba(255,255,255,0.1);
                backdrop-filter: blur(10px);
                border-radius: 20px;
                padding: 30px;
                margin-bottom: 30px;
                border: 1px solid rgba(255,255,255,0.2);
            }
            .chart-title { margin-bottom: 20px; font-size: 1.2em; text-align: center; }
            
            .nav-link {
                display: inline-block;
                background: linear-gradient(135deg, #00b894, #00cec9);
                color: #fff;
                text-decoration: none;
                padding: 15px 30px;
                border-radius: 50px;
                font-weight: bold;
                transition: transform 0.3s ease;
            }
            .nav-link:hover { transform: translateY(-3px); }
            .text-center { text-align: center; }
            
            .info-text {
                text-align: center;
                opacity: 0.7;
                margin-bottom: 20px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Histórico de Alertas</h1>
            
            <p class="info-text">Visualize a incidência de alertas de presença por hora do dia</p>
            
            <div class="controls">
                <label>Selecione a data:</label>
                <select id="dataSelect" onchange="carregarDados()"></select>
            </div>
            
            <div class="chart-card">
                <h3 class="chart-title" id="chart-title">Alertas por Hora</h3>
                <canvas id="alertasChart"></canvas>
            </div>
            
            <div class="text-center">
                <a href="/" class="nav-link">Voltar ao Monitor</a>
            </div>
        </div>
        
        <script>
            let chart;
            
            // Inicializa gráfico
            const ctx = document.getElementById('alertasChart').getContext('2d');
            chart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: Array.from({length: 24}, (_, i) => i + 'h'),
                    datasets: [{
                        label: 'Quantidade de Alertas',
                        data: Array(24).fill(0),
                        backgroundColor: 'rgba(231,76,60,0.7)',
                        borderColor: '#e74c3c',
                        borderWidth: 2,
                        borderRadius: 5
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: true,
                            grid: { color: 'rgba(255,255,255,0.1)' },
                            ticks: { color: '#fff', stepSize: 1 }
                        },
                        x: {
                            grid: { color: 'rgba(255,255,255,0.1)' },
                            ticks: { color: '#fff' }
                        }
                    },
                    plugins: {
                        legend: { labels: { color: '#fff' } }
                    }
                }
            });
            
            // Carrega datas disponíveis
            fetch('/api/datas-disponiveis')
                .then(r => r.json())
                .then(datas => {
                    const select = document.getElementById('dataSelect');
                    if (datas.length === 0) {
                        const hoje = new Date().toISOString().split('T')[0];
                        datas = [hoje];
                    }
                    datas.forEach(d => {
                        const opt = document.createElement('option');
                        opt.value = d;
                        opt.textContent = formatarData(d);
                        select.appendChild(opt);
                    });
                    carregarDados();
                });
            
            function formatarData(dataStr) {
                const [ano, mes, dia] = dataStr.split('-');
                return dia + '/' + mes + '/' + ano;
            }
            
            function carregarDados() {
                const data = document.getElementById('dataSelect').value;
                fetch('/api/alertas-por-hora?data=' + data)
                    .then(r => r.json())
                    .then(resp => {
                        const alertas = resp.dados.map(d => d.alertas);
                        chart.data.datasets[0].data = alertas;
                        chart.update();
                        
                        document.getElementById('chart-title').textContent = 
                            'Alertas por Hora - ' + formatarData(resp.data);
                    });
            }
        </script>
    </body>
    </html>
    """
    return render_template_string(html)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)