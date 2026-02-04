#!/bin/bash
# ===========================================
# Script de Limpeza Geral - Docker
# Remove containers, volumes, imagens e redes
# ===========================================

echo "=========================================="
echo "  🧹 LIMPEZA GERAL - Docker"
echo "=========================================="
echo ""
echo "⚠️  ATENÇÃO: Isso vai remover TUDO do Docker!"
echo "   - Todos os containers"
echo "   - Todos os volumes (DADOS SERÃO PERDIDOS!)"
echo "   - Todas as imagens"
echo "   - Todas as redes não padrão"
echo ""
read -p "Tem certeza? (digite 'sim' para confirmar): " confirmacao

if [ "$confirmacao" != "sim" ]; then
    echo "❌ Cancelado."
    exit 0
fi

echo ""
echo "[1/5] Parando todos os containers..."
sudo docker stop $(sudo docker ps -aq) 2>/dev/null || echo "   Nenhum container rodando"

echo "[2/5] Removendo todos os containers..."
sudo docker rm $(sudo docker ps -aq) 2>/dev/null || echo "   Nenhum container para remover"

echo "[3/5] Removendo todos os volumes..."
sudo docker volume rm $(sudo docker volume ls -q) 2>/dev/null || echo "   Nenhum volume para remover"

echo "[4/5] Removendo todas as imagens..."
sudo docker rmi $(sudo docker images -q) -f 2>/dev/null || echo "   Nenhuma imagem para remover"

echo "[5/5] Removendo redes não utilizadas..."
sudo docker network prune -f

echo ""
echo "=========================================="
echo "  ✅ LIMPEZA CONCLUÍDA!"
echo "=========================================="
echo ""
sudo docker system df
echo ""
