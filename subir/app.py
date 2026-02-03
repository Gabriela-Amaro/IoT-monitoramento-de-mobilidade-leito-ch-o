from flask import Flask, request, jsonify, render_template_string, send_from_directory, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)

# Configuração do Banco
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://user:password@db/monitor_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Modelo da Tabela (ATUALIZADO COM COLUNA alerta)
class Leitura(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    distancia = db.Column(db.Float)
    alerta = db.Column(db.String(20)) # Nova coluna
    data_hora = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()

@app.route('/sensor.jsonld')
def serve_jsonld():
    # Envia o arquivo que está na mesma pasta do app.py
    return send_from_directory(os.getcwd(), 'sensor.jsonld', mimetype='application/ld+json')

@app.route('/api/enviar', methods=['POST'])
def receber_dados():
    dados = request.json
    nova_leitura = Leitura(
        distancia=dados.get('distancia'),
        alerta=dados.get('alerta'),
        data_hora=dados.get('data_hora')
    )
    db.session.add(nova_leitura)
    db.session.commit()
    return jsonify({"status": "sucesso"}), 201

@app.route('/')
def index():
    ultima = Leitura.query.order_by(Leitura.id.desc()).first()
    
    # Valores padrão para não quebrar se o banco estiver vazio
    dados_view = {
        "dist": "--", "alert": "--", "hora": "Aguardando...",
        "bg_color": "#62ee38", "text_color": "#333", 
    }

    if ultima:
        dados_view["dist"] = ultima.distancia
        dados_view["alert"] = ultima.umidade
        dados_view["hora"] = ultima.data_hora.strftime("%H:%M:%S")
        
        # LÓGICA VISUAL BASEADA NO alerta
        # MUDAR A LOGICA
        p = ultima.alerta
        if p == 'noite':
            dados_view["bg_color"] = "#2c3e50" # Azul Escuro
            dados_view["text_color"] = "#ecf0f1" # Branco
            dados_view["icone"] = "🌙" # Lua
        elif p == 'tarde':
            dados_view["bg_color"] = "#f39c12" # Laranja Forte
            dados_view["text_color"] = "#fff"
            dados_view["icone"] = "☀️" # Sol Forte
        else: # dia (manhã)
            dados_view["bg_color"] = "#87CEEB" # Azul Céu
            dados_view["text_color"] = "#333"
            dados_view["icone"] = "🌅" # Sol Nascendo

    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Monitor IoT</title>
        <meta http-equiv="refresh" content="3">

        <script type="application/ld+json" src="{{ url_for('serve_jsonld') }}"></script>

        <style>
            body { 
                font-family: 'Verdana', sans-serif; 
                text-align: center; 
                padding: 50px; 
                background-color: {{ dados.bg_color }}; 
                color: {{ dados.text_color }};
                transition: background-color 0.5s ease;
            }
            .card { 
                background: rgba(255, 255, 255, 0.2); 
                backdrop-filter: blur(10px);
                padding: 30px; 
                border-radius: 20px; 
                display: inline-block; 
                box-shadow: 0 4px 15px rgba(0,0,0,0.2);
                border: 1px solid rgba(255,255,255,0.3);
            }
            .icone-grande { font-size: 80px; margin-bottom: 10px; }
            .valor { font-size: 50px; font-weight: bold; }
            .label { font-size: 18px; opacity: 0.8; }
        </style>
    </head>
    <body>
        <div class="card">
            <div class="icone-grande">{{ dados.icone }}</div>
            <h1>Monitoramento {{ dados.alerta }}</h1>
            
            <div>
                <span class="valor">{{ dados.temp }}°C</span>
                <p class="label">distancia</p>
            </div>
            <br>
            <div>
                <span class="valor">{{ dados.umid }}%</span>
                <p class="label">Umidade</p>
            </div>
            <hr style="border-color: rgba(255,255,255,0.3)">
            <small>Atualizado em: {{ dados.hora }}</small>
        </div>
    </body>
    </html>
    """
    return render_template_string(html, dados=dados_view)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)