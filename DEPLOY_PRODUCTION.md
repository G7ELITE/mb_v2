# 🚀 ManyBlack V2 - Deploy para Produção na VPS

Este guia mostra como preparar e deployar o ManyBlack V2 para produção na VPS com o domínio `www.equipe.manyblack.com`.

## 📋 Pré-requisitos na VPS

1. **Docker & Docker Compose** instalados
2. **Certificado SSL** (Let's Encrypt recomendado)
3. **Domínio** apontando para o IP da VPS
4. **Git** instalado

## 🔧 Configuração Inicial na VPS

### 1. Clonar o Repositório
```bash
# Na VPS
git clone https://github.com/SEU_USUARIO/mb-v2.git
cd mb-v2
git checkout main
```

### 2. Configurar Ambiente de Produção
```bash
# Copiar template de produção
cp env.production.example .env

# Editar com valores reais
nano .env
```

**Configurações importantes no .env:**
```bash
APP_ENV=production
DB_PASSWORD=SUA_SENHA_SUPER_SEGURA
OPENAI_API_KEY=sk-proj-SEU_TOKEN_REAL
TELEGRAM_BOT_TOKEN=SEU_BOT_TOKEN_REAL
TELEGRAM_WEBHOOK_SECRET=SEU_SECRET_SEGURO
JWT_SECRET=UMA_FRASE_LONGA_E_ALEATORIA_DIFERENTES_DO_DEV
FRONTEND_URL=https://www.equipe.manyblack.com
BACKEND_URL=https://www.equipe.manyblack.com
DOMAIN=www.equipe.manyblack.com
```

### 3. Configurar SSL
```bash
# Criar diretório para certificados
mkdir -p nginx/ssl

# Usar certbot (Let's Encrypt) - exemplo
sudo certbot certonly --nginx -d www.equipe.manyblack.com -d equipe.manyblack.com

# Copiar certificados para o projeto
sudo cp /etc/letsencrypt/live/www.equipe.manyblack.com/fullchain.pem nginx/ssl/
sudo cp /etc/letsencrypt/live/www.equipe.manyblack.com/privkey.pem nginx/ssl/
sudo chmod 644 nginx/ssl/*.pem
```

### 4. Deploy Inicial
```bash
# Fazer o primeiro deploy
./deploy-prod.sh
```

## 🔄 Workflow de Desenvolvimento → Produção

### Desenvolvimento Local
```bash
# Branch de desenvolvimento (qualquer branch != main)
git checkout -b feature/nova-funcionalidade

# Desenvolver normalmente com ngrok
./start-dev.sh  # ou ./start.sh (comportamento atual mantido)
./setup_ngrok.sh
```

### Deploy para Produção
```bash
# 1. Merge da feature para main (localmente ou via PR)
git checkout main
git merge feature/nova-funcionalidade
git push origin main

# 2. Na VPS
git pull origin main
./deploy-prod.sh
```

## 📊 Monitoramento

### Ver Logs
```bash
# Logs da aplicação
docker-compose -f docker-compose.prod.yml logs -f app

# Logs do nginx
docker-compose -f docker-compose.prod.yml logs -f nginx

# Logs do postgres
docker-compose -f docker-compose.prod.yml logs -f postgres
```

### Status dos Serviços
```bash
docker-compose -f docker-compose.prod.yml ps
```

### Health Check
```bash
curl https://www.equipe.manyblack.com/health
```

## 🛠️ Manutenção

### Backup do Banco
```bash
docker-compose -f docker-compose.prod.yml exec postgres pg_dump -U mbuser manyblack_v2 > backup_$(date +%Y%m%d_%H%M%S).sql
```

### Restore do Banco
```bash
docker-compose -f docker-compose.prod.yml exec -T postgres psql -U mbuser manyblack_v2 < backup.sql
```

### Atualizar SSL
```bash
# Renovar certificado
sudo certbot renew

# Copiar novos certificados
sudo cp /etc/letsencrypt/live/www.equipe.manyblack.com/fullchain.pem nginx/ssl/
sudo cp /etc/letsencrypt/live/www.equipe.manyblack.com/privkey.pem nginx/ssl/

# Reiniciar nginx
docker-compose -f docker-compose.prod.yml restart nginx
```

## 🔍 Troubleshooting

### Problema: Aplicação não inicia
```bash
# Verificar logs
docker-compose -f docker-compose.prod.yml logs app

# Verificar variáveis de ambiente
docker-compose -f docker-compose.prod.yml exec app env | grep APP_
```

### Problema: SSL não funciona
```bash
# Verificar certificados
ls -la nginx/ssl/

# Testar nginx config
docker-compose -f docker-compose.prod.yml exec nginx nginx -t
```

### Problema: Banco não conecta
```bash
# Verificar se postgres está rodando
docker-compose -f docker-compose.prod.yml ps postgres

# Testar conexão
docker-compose -f docker-compose.prod.yml exec app psql "postgresql://mbuser:PASSWORD@postgres:5432/manyblack_v2" -c "SELECT 1;"
```

## 🚨 IMPORTANTE

1. **NUNCA commite arquivos .env** no git
2. **Use senhas fortes** em produção
3. **Configure backup automático** do banco
4. **Monitor os logs** regularmente
5. **Teste sempre em dev** antes de fazer deploy

## 📱 Configuração do Telegram

Após o deploy, atualize a URL do webhook:
```bash
# Através da interface web ou API
curl -X POST "https://api.telegram.org/bot{BOT_TOKEN}/setWebhook" \
     -H "Content-Type: application/json" \
     -d '{"url":"https://www.equipe.manyblack.com/channels/telegram/webhook"}'
```

---

✅ **Projeto preparado para produção!**
🌐 **Desenvolvimento**: ngrok (qualquer branch != main)  
🚀 **Produção**: VPS + domínio (branch main)
