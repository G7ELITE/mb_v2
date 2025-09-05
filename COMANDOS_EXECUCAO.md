# 🚀 Comandos para Execução na VPS - ManyBlack V2

Execute estes comandos **NA ORDEM** na VPS de produção:

## 1️⃣ **Reiniciar Containers Docker**
```bash
cd /opt/manyblackv2
export APP_ENV=production
newgrp docker
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d --build
```

## 2️⃣ **Aguardar Inicialização**
```bash
sleep 30
docker ps
```

## 3️⃣ **Verificar Logs da Aplicação**
```bash
docker compose -f docker-compose.prod.yml logs --tail=20 app
docker compose -f docker-compose.prod.yml logs --tail=10 nginx
```

## 4️⃣ **Testar Aplicação Localmente**
```bash
curl -I http://localhost/health
curl -I http://localhost:8000/health
```

## 5️⃣ **Testar via Domínio HTTPS**
```bash
curl -I https://equipe.manyblack.com/health
curl -I https://equipe.manyblack.com/
```

## 6️⃣ **Configurar Webhook do Telegram**
```bash
# Obter token do bot
TELEGRAM_BOT_TOKEN=$(grep TELEGRAM_BOT_TOKEN .env | cut -d'=' -f2)

# Configurar webhook
curl -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/setWebhook" \
     -H "Content-Type: application/json" \
     -d '{"url":"https://equipe.manyblack.com/channels/telegram/webhook"}'
```

## 7️⃣ **Verificar Webhook Configurado**
```bash
curl "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getWebhookInfo"
```

## 8️⃣ **Configurar Renovação Automática SSL**
```bash
# Adicionar cronjob para renovação automática
echo "0 12 * * * /usr/bin/certbot renew --quiet && docker compose -f /opt/manyblackv2/docker-compose.prod.yml restart nginx" | sudo crontab -
```

## 9️⃣ **Verificação Final**
```bash
# Status dos containers
docker compose -f docker-compose.prod.yml ps

# Verificar se tudo está funcionando
curl https://equipe.manyblack.com/health
```

---

## 🔧 **Solução de Problemas**

### Se aplicação não responder:
```bash
docker compose -f docker-compose.prod.yml logs app
```

### Se nginx der erro:
```bash
docker compose -f docker-compose.prod.yml logs nginx
docker compose -f docker-compose.prod.yml restart nginx
```

### Se PostgreSQL não conectar:
```bash
docker compose -f docker-compose.prod.yml logs postgres
```

---

## ✅ **Resultado Esperado**
- ✅ Aplicação respondendo em https://equipe.manyblack.com
- ✅ Health check funcionando
- ✅ Webhook do Telegram configurado
- ✅ SSL funcionando e renovação automática configurada
