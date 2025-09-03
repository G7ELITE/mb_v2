# 🎯 ManyBlack V2 — STACK STATUS (PRONTO PARA USO)

## ✅ **SISTEMA 100% OPERACIONAL**

### 🖥️ **Serviços Ativos**
- **Backend**: ✅ `http://localhost:8000` (PID: 16034)
- **Frontend**: ✅ `http://localhost:5173` (PID: 16069/16070)
- **Ngrok**: ✅ `https://acabf2ebc154.ngrok-free.app` (PID: 16407)
- **Redis**: ✅ Conectado (modo real)
- **PostgreSQL**: ✅ Database manyblack_v2 (user: mbuser)

### 🌐 **URLs Públicas**
- **🏠 Interface**: `https://acabf2ebc154.ngrok-free.app`
- **⚙️ Backend API**: `https://acabf2ebc154.ngrok-free.app/health`
- **📖 Documentação**: `https://acabf2ebc154.ngrok-free.app/docs`
- **🤖 Webhook**: `https://acabf2ebc154.ngrok-free.app/channels/telegram/webhook`
- **📊 Ngrok Dashboard**: `http://localhost:4040`

### 🧪 **Validação Smoke (7/7 ✅)**
- ✅ Backend health via ngrok
- ✅ Frontend carregando
- ✅ API docs acessível  
- ✅ Webhook endpoint ativo
- ✅ Redis conectado (real)
- ✅ Componentes Telegram OK

---

## 🚀 **COMO USAR**

### **1. Interface Web**
```bash
# Acessar no navegador:
https://acabf2ebc154.ngrok-free.app

# Funcionalidades disponíveis:
# • Dashboard com estatísticas
# • Procedimentos e automações
# • Simulador de conversas  
# • Configuração de intake/âncoras
```

### **2. API Backend**
```bash
# Health check
curl https://acabf2ebc154.ngrok-free.app/health

# Documentação interativa
https://acabf2ebc154.ngrok-free.app/docs

# Exemplos de endpoints:
# • GET /api/leads
# • POST /api/procedures  
# • GET /api/automations
```

### **3. Bot Telegram**
```bash
# Webhook já configurado para:
https://acabf2ebc154.ngrok-free.app/channels/telegram/webhook

# Para testar:
# 1. Envie mensagem para seu bot no Telegram
# 2. Acompanhe logs: ./logs.sh live
# 3. Verifique processamento na interface
```

---

## 🛠️ **Comandos de Controle**

### **Monitoramento**
```bash
# Logs em tempo real
./logs.sh live

# Status dos processos  
ps aux | grep -E "(uvicorn|vite|ngrok)"

# Verificar health
curl http://localhost:8000/health
```

### **Parar Sistema**
```bash
# Parar tudo de uma vez
./stop.sh

# Ou individual:
pkill -f uvicorn     # Backend
pkill -f vite        # Frontend  
pkill -f ngrok       # Ngrok
```

### **Reiniciar**
```bash
# Reinício completo
./stop.sh && sleep 3 && ./quick_start.sh

# Ou apenas sistemas:
./restart.sh
```

---

## 🔧 **Configurações Ativas**

### **Ambiente DEV**
```bash
APP_ENV=dev
DB_NAME=manyblack_v2
REDIS_URL=redis://127.0.0.1:6379  
UVICORN_WORKERS=1
GATE_YESNO_DETERMINISTICO=false
```

### **Webhook Telegram**
```bash
TELEGRAM_BOT_TOKEN=***FzXSnI (configurado ✅)
TELEGRAM_WEBHOOK_SECRET=troque (configurado ✅)  
URL_ATIVA=https://acabf2ebc154.ngrok-free.app/channels/telegram/webhook
```

---

## 📊 **Logs Estruturados Ativos**

```json
{"evt":"dev_preflight","db_migrated":true,"redis":"ok","webhook_ready":true}
{"evt":"smoke_dev_complete","success_count":7,"total_tests":7,"all_passed":true}
{"evt":"redis_connected","mode":"real"}
```

---

## 🎯 **PRÓXIMAS AÇÕES**

### **Validação Manual**
1. **🌐 Teste Interface**: Acesse `https://acabf2ebc154.ngrok-free.app`
2. **📱 Teste Telegram**: Envie mensagem para seu bot
3. **⚙️ Teste API**: Acesse `/docs` e teste endpoints
4. **📊 Monitore**: Use `./logs.sh live` para acompanhar

### **Desenvolvimento**
- ✅ Backend + Frontend rodando  
- ✅ Hot reload ativo (mudanças automaticamente refletidas)
- ✅ Redis para cache/locks
- ✅ PostgreSQL para persistência
- ✅ Ngrok para exposição pública
- ✅ Webhook Telegram configurado

**🎉 SISTEMA PRONTO PARA DESENVOLVIMENTO E TESTES REAIS!**
