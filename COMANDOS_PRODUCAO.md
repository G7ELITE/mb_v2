# 🎯 Comandos Práticos - ManyBlack V2 Produção

## 🧑‍💻 Desenvolvimento Local (MESMO DE SEMPRE)

```bash
# Iniciar desenvolvimento (ZERO mudanças!)
./start-dev.sh  # ou ./start.sh

# Configurar ngrok (IGUAL ao que já usa)
./setup_ngrok.sh

# Ativar webhook Telegram
./activate_webhook.sh

# Ver logs
./logs.sh live
```

## 🏭 Produção na VPS

### Configuração Inicial (Uma vez só)
```bash
# 1. Na VPS, clonar repo
git clone https://github.com/SEU_USUARIO/mb-v2.git
cd mb-v2
git checkout main

# 2. Configurar environment
cp env.production.example .env
nano .env  # Configurar chaves reais

# 3. Configurar SSL
sudo certbot certonly --nginx -d www.equipe.manyblack.com
cp /etc/letsencrypt/live/www.equipe.manyblack.com/*.pem nginx/ssl/

# 4. Primeiro deploy
./deploy-prod.sh
```

### Updates Futuros
```bash
# Local: push para main
git push origin main

# VPS: deploy automático
git pull origin main
./deploy-prod.sh
```

### Monitoramento
```bash
# Ver status
docker-compose -f docker-compose.prod.yml ps

# Ver logs
docker-compose -f docker-compose.prod.yml logs -f app
docker-compose -f docker-compose.prod.yml logs -f nginx

# Health check
curl https://www.equipe.manyblack.com/health

# Backup banco
docker-compose -f docker-compose.prod.yml exec postgres pg_dump -U mbuser manyblack_v2 > backup.sql
```

## 🔄 Workflow Diário

### Durante desenvolvimento:
```bash
git checkout -b feature/nova-funcionalidade
# Desenvolve normalmente...
./start-dev.sh
./setup_ngrok.sh
# Testa tudo...
```

### Quando terminar feature:
```bash
git checkout main
git merge feature/nova-funcionalidade
git push origin main
```

### Na VPS (automático):
```bash
git pull origin main
./deploy-prod.sh
```

## 🚨 Troubleshooting

### Se algo der errado na VPS:
```bash
# Ver todos os logs
docker-compose -f docker-compose.prod.yml logs

# Reiniciar stack completa
docker-compose -f docker-compose.prod.yml restart

# Build limpo
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml build --no-cache
docker-compose -f docker-compose.prod.yml up -d
```

### Webhook Telegram após deploy:
```bash
# Atualizar webhook para novo domínio
curl -X POST "https://api.telegram.org/bot{SEU_BOT_TOKEN}/setWebhook" \
     -H "Content-Type: application/json" \
     -d '{"url":"https://www.equipe.manyblack.com/channels/telegram/webhook"}'
```

---

**✅ Pronto! Seu projeto está preparado para produção de forma simples e profissional.**
