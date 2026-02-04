#!/bin/bash
# ===========================================
# Script de Deploy - Monitor IoT Ultrassônico
# ===========================================

set -e

echo "=========================================="
echo "  INSTALAÇÃO - Monitor IoT"
echo "=========================================="

# Verifica se está na pasta certa
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Execute dentro da pasta 'subir'"
    exit 1
fi

# 1. Instala Docker (se não tiver)
echo "[1/3] Verificando Docker..."
if ! command -v docker &> /dev/null; then
    echo "   Instalando Docker..."
    sudo yum install -y docker 2>/dev/null || sudo apt-get install -y docker.io
fi
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER 2>/dev/null || true

# 2. Instala Docker Compose como plugin (comando: docker compose)
echo "[2/3] Verificando Docker Compose Plugin..."
DOCKER_CONFIG=${DOCKER_CONFIG:-/usr/local/lib/docker}
sudo mkdir -p $DOCKER_CONFIG/cli-plugins
sudo curl -SL "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-linux-x86_64" -o $DOCKER_CONFIG/cli-plugins/docker-compose
sudo chmod +x $DOCKER_CONFIG/cli-plugins/docker-compose

# Verifica instalação
docker compose version

# 3. Inicia aplicação
echo "[3/3] Iniciando aplicação..."
sudo docker compose down 2>/dev/null || true
sudo docker compose up -d --build

echo ""
echo "=========================================="
echo "  ✅ DEPLOY CONCLUÍDO!"
echo "=========================================="
IP_PUBLICO=$(curl -s ifconfig.me 2>/dev/null || echo "SEU_IP")
echo ""
echo "Acesse: http://${IP_PUBLICO}:5000"
echo ""
echo "Comandos úteis:"
echo "  sudo docker compose logs -f    # Ver logs"
echo "  sudo docker compose restart    # Reiniciar"
echo "  sudo docker compose down       # Parar"
echo "  sudo docker compose up -d      # Iniciar"
echo "  sudo docker compose up --build # Rebuild"
echo ""
