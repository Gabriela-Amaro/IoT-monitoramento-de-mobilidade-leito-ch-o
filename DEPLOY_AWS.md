# 🚀 Guia de Deploy na AWS EC2

## Passo 1: Criar Instância EC2

1. Acesse [AWS Console](https://console.aws.amazon.com/ec2)
2. Clique em **"Launch Instance"**
3. Configure:
   - **Nome**: `monitor-iot`
   - **AMI**: Amazon Linux 2023 (ou Ubuntu 22.04)
   - **Tipo**: `t2.micro` (grátis no free tier)
   - **Par de chaves**: Crie ou selecione uma existente (salve o `.pem`!)
   - **Security Group**: Crie um novo com as regras:
     - SSH (22) - Seu IP
     - HTTP (80) - Anywhere (0.0.0.0/0)
     - Custom TCP (5000) - Anywhere (0.0.0.0/0)
     - Custom TCP (1883) - Anywhere (para MQTT, se usar)
4. Clique **"Launch Instance"**

## Passo 2: Conectar via SSH

```bash
# Dê permissão ao arquivo .pem
chmod 400 sua-chave.pem

# Conecte (substitua pelo IP da sua instância)
ssh -i sua-chave.pem ec2-user@SEU_IP_PUBLICO
# Para Ubuntu: ssh -i sua-chave.pem ubuntu@SEU_IP_PUBLICO
```

## Passo 3: Upload dos Arquivos

**Do seu computador local**, envie a pasta `subir`:

```bash
# Saia da EC2 primeiro (Ctrl+D) e rode localmente:
scp -i sua-chave.pem -r ./subir ec2-user@SEU_IP_PUBLICO:~/
# Para Ubuntu: scp -i sua-chave.pem -r ./subir ubuntu@SEU_IP_PUBLICO:~/
```

## Passo 4: Executar Deploy

Conecte novamente na EC2 e execute:

```bash
ssh -i sua-chave.pem ec2-user@SEU_IP_PUBLICO

cd ~/subir
chmod +x deploy.sh
./deploy.sh
```

## Passo 5: Verificar

Acesse no navegador:
```
http://SEU_IP_PUBLICO:5000
```

## Comandos Úteis (na EC2)

```bash
# Ver logs em tempo real
sudo docker-compose logs -f

# Reiniciar aplicação
sudo docker-compose restart

# Parar tudo
sudo docker-compose down

# Ver containers rodando
sudo docker ps
```

## Atualizar o Emissor Local

No arquivo `emissor.py` local, atualize o IP:

```python
AWS_URL = "http://SEU_IP_PUBLICO:5000/api/enviar"
```

---

## ⚠️ Dicas Importantes

1. **IP Elástico**: Para o IP não mudar ao reiniciar a instância, associe um "Elastic IP" gratuito
2. **Segurança**: Em produção, use HTTPS com certificado SSL
3. **Persistência**: Os dados ficam no volume Docker. Se deletar com `docker-compose down -v`, perde os dados!
