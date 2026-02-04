#!/bin/bash
# ===========================================
# Script de Deploy - Monitor IoT Ultrassônico
# Execute na instância EC2 dentro da pasta subir
# ===========================================

set -e

echo "=========================================="
echo "  DEPLOY - Monitor IoT Ultrassônico"
echo "=========================================="

# Verifica se está na pasta certa
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Erro: Execute este script dentro da pasta 'subir'"
    exit 1
fi

# 1. Atualiza sistema
echo "[1/5] Atualizando sistema..."
sudo yum update -y 2>/dev/null || sudo apt-get update -y 2>/dev/null || true

# 2. Remove Docker antigo e instala versão atual
echo "[2/5] Instalando Docker..."
sudo yum remove -y docker docker-client docker-latest docker-engine 2>/dev/null || true

# Amazon Linux 2023
if grep -q "Amazon Linux" /etc/os-release 2>/dev/null; then
    sudo yum install -y docker
    sudo systemctl start docker
    sudo systemctl enable docker
# Ubuntu
elif command -v apt-get &> /dev/null; then
    sudo apt-get install -y docker.io docker-compose-plugin
    sudo systemctl start docker
fi

sudo usermod -aG docker $USER 2>/dev/null || true

# 3. Instala Docker Compose V2 (plugin)
echo "[3/5] Configurando Docker Compose..."
sudo mkdir -p /usr/local/lib/docker/cli-plugins
sudo curl -SL "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-linux-x86_64" -o /usr/local/lib/docker/cli-plugins/docker-compose
sudo chmod +x /usr/local/lib/docker/cli-plugins/docker-compose

# 4. Build manual da imagem (evita problema do buildx)
echo "[4/5] Construindo imagem..."
sudo docker build -t monitor-iot-web .

# 5. Inicia com docker compose
echo "[5/5] Iniciando aplicação..."
sudo docker compose down 2>/dev/null || true

# Cria rede se não existir
sudo docker network create subir_default 2>/dev/null || true

# Inicia o banco
sudo docker run -d --name db \
    --network subir_default \
    -e POSTGRES_USER=user \
    -e POSTGRES_PASSWORD=password \
    -e POSTGRES_DB=monitor_db \
    -v pgdata:/var/lib/postgresql/data \
    --restart always \
    postgres:13 2>/dev/null || sudo docker start db

# Aguarda banco iniciar
echo "   Aguardando banco de dados..."
sleep 5

# Inicia a aplicação
sudo docker run -d --name web \
    --network subir_default \
    -p 5000:5000 \
    --restart always \
    monitor-iot-web 2>/dev/null || sudo docker start web

echo ""
echo "=========================================="
echo "  ✅ DEPLOY CONCLUÍDO!"
echo "=========================================="
echo ""
IP_PUBLICO=$(curl -s ifconfig.me 2>/dev/null || echo "SEU_IP")
echo "Acesse: http://${IP_PUBLICO}:5000"
echo ""
echo "Comandos úteis:"
echo "  Ver logs:         sudo docker logs -f web"
echo "  Reiniciar:        sudo docker restart web"
echo "  Parar tudo:       sudo docker stop web db"
echo "  Ver containers:   sudo docker ps"
echo ""
