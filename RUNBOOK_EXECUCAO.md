# 🚀 ManyBlack V2 — RUNBOOK DE EXECUÇÃO

## 📋 **Comandos Essenciais**

### **🎯 Comando Único - Validação Completa**
```bash
# Executa: audit + testes unit + E2E + validação
python3 test_runner.py
```
**Saída esperada:** `4/4 passos completos, 12/12 testes passando` ✅

### **🚀 Comando Único - Quick Start Completo**
```bash
# Executa: pré-voo + sistemas + ngrok + webhook + smoke
./quick_start.sh
```
**Saída esperada:** URLs públicas + smoke DEV 7/7 testes ✅

---

## 🔍 **Troubleshooting Autodetect**

### **Database Issues**
```bash
# Verificar permissões detectadas
python3 dev_audit.py | grep "CREATE"

# ✅ Esperado (atual):
# ❌ CREATE DATABASE: NÃO (permission denied)
# ✅ CREATE SCHEMA: SIM
# 🎯 Estratégia: Usar schema temporário
```

### **Redis Issues**
```bash
# Verificar fallback automático
python3 dev_preflight.py | grep -i redis

# ✅ Esperado:
# ⚠️ Redis fallback in-memory ativo
# {"evt":"redis_fallback", "mode":"inmemory"}
```

### **Ngrok Issues**
```bash
# Verificar túnel ativo
curl -s http://localhost:4040/api/tunnels | python3 -c "
import sys, json
data = json.load(sys.stdin)
for t in data['tunnels']:
    if '5173' in t['config']['addr']:
        print(f'✅ Túnel: {t[\"public_url\"]}')
"
```

---

## 🧪 **Validação DEV Real**

### **1. Backend Health**
```bash
NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | python3 -c "import sys,json; data=json.load(sys.stdin); print([t['public_url'] for t in data['tunnels'] if '5173' in t['config']['addr']][0])")

curl "$NGROK_URL/health"
# ✅ Esperado: {"status":"healthy","timestamp":"..."}
```

### **2. Frontend Loading**
```bash
curl -s "$NGROK_URL" | head -20
# ✅ Esperado: <!DOCTYPE html> + Vite/React content
```

### **3. Webhook Endpoint**
```bash
curl "$NGROK_URL/channels/telegram/webhook?secret=$TELEGRAM_WEBHOOK_SECRET"
# ✅ Esperado: HTTP 405 (método não permitido) ou 422
```

### **4. Componentes Internos**
```bash
python3 -c "
from app.core.confirmation_gate import get_confirmation_gate
from app.core.orchestrator import decide_and_plan
from app.redis_adapter import get_redis

gate = get_confirmation_gate()
redis = get_redis()

print(f'✅ Gate: {bool(gate)}')
print(f'✅ Redis: {redis.ping()}')
"
```

---

## 📱 **Telegram - Teste Manual**

1. **Enviar mensagem** para seu bot via Telegram
2. **Verificar logs** do sistema:
   ```bash
   # Logs em tempo real (se implementado)
   ./logs.sh live
   
   # Ou verificar processo uvicorn
   ps aux | grep uvicorn
   ```
3. **Verificar comportamento esperado**:
   - Gate processa mensagens
   - Orquestrador seleciona automações
   - Respostas enviadas corretamente

---

## 🔧 **Modos de Operação**

### **Modo DEV (atual)**
```bash
APP_ENV=dev
REDIS_URL=redis://127.0.0.1:6379  # Com fallback automático
UVICORN_WORKERS=1                 # Processo único
GATE_YESNO_DETERMINISTICO=false   # LLM para confirmações
```

### **Modo TEST**
```bash
APP_ENV=test
TEST_SCHEMA_MODE=true             # Schema efêmero
GATE_YESNO_DETERMINISTICO=true    # Determinístico para estabilidade
UVICORN_WORKERS=1                 # Locks in-memory funcionam
```

### **Modo PROD (futuro)**
```bash
APP_ENV=prod
REDIS_URL=redis://prod-redis:6379  # Redis real obrigatório
UVICORN_WORKERS=4                  # Múltiplos processos
GATE_YESNO_DETERMINISTICO=false    # LLM completo
```

---

## 📊 **Logs Estruturados - Monitoring**

### **Eventos Importantes**
```json
// Infraestrutura
{"evt":"infra_audit", "db_mode":"schema", "redis_available":false}
{"evt":"dev_preflight", "db_migrated":true, "redis":"inmemory"}

// Gate & Orquestrador  
{"evt":"gate_eval", "retro_active":true, "decision":"yes", "idempotent_skip":false}
{"evt":"orchestrator_select", "used_llm_proposal":true, "chosen":"ask_deposit_v3"}

// Testes
{"evt":"test_schema", "schema":"test_mb_1234_5678", "created":true}
{"evt":"smoke_dev_complete", "success_count":7, "all_passed":true}
```

### **Alertas Importantes**
- `redis_fallback` em PROD → Redis down
- `db_migrated:false` → Migrations falharam
- `webhook_ready:false` → Bot não funciona
- `all_passed:false` → Sistema com problemas

---

## ✅ **Critérios de Sucesso**

### **DEV OK**
- `python3 test_runner.py` → 4/4 passos ✅
- `./quick_start.sh` → URLs públicas + smoke 7/7 ✅
- Telegram responde mensagens ✅

### **TEST OK**  
- Testes unitários: 12/12 sempre ✅
- Schema efêmero: criado + migrado + limpo ✅
- E2E quando possível ✅

### **Smoke DEV OK**
- Backend `/health` → 200 ✅
- Frontend carrega → HTML válido ✅ 
- Webhook endpoint → acessível ✅
- Componentes → carregam sem erro ✅
