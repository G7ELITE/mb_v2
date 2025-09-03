# 🎯 Guia do Fluxo de Confirmações - ManyBlack V2

## Visão Geral

Este guia explica como funciona o sistema de confirmações por texto (sim/não) após perguntas que esperam confirmação do lead.

## 🔄 Fluxo Completo

### 1. Criação da Automação com Confirmação

```yaml
- id: ask_deposit_for_test
  topic: "teste"
  eligibility: "não concordou em depositar"
  priority: 0.85
  cooldown: 24h
  expects_reply:
    target: confirm_can_deposit  # Target de confirmação
  output:
    type: message
    text: "Para liberar o teste, você consegue fazer um pequeno depósito? 💰"
```

### 2. Definição do Target de Confirmação

```yaml
# policies/confirm_targets.yml
confirm_can_deposit:
  max_age_minutes: 30
  on_yes:
    facts:
      agreements.can_deposit: true
  on_no:
    facts:
      agreements.can_deposit: false
    automation: deposit_help_detailed
```

### 3. Pipeline de Processamento

#### 3.1 ApplyPlan → Hook de Automação

Quando uma automação com `expects_reply` é enviada:

```python
# app/tools/apply_plan.py
await automation_hook.on_automation_sent(
    automation_id=automation_id,
    lead_id=lead_id,
    success=True,
    provider_message_id=provider_message_id,
    prompt_text=prompt_text
)
```

O hook salva o estado "aguardando":

```python
aguardando = {
    "tipo": "confirmacao",
    "target": target,
    "automation_id": automation_id,
    "lead_id": lead_id,
    "provider_message_id": provider_message_id,
    "prompt_text": prompt_text,
    "ttl": int(time.time()) + ttl_seconds,
    "created_at": int(time.time())
}
```

#### 3.2 Gate de Confirmação

Quando o lead responde:

```python
# app/core/confirmation_gate.py
confirmation_result = await confirmation_gate.process_message(env)

if confirmation_result.handled:
    # Confirmação processada - aplicar efeitos
    plan = Plan(actions=confirmation_result.actions)
else:
    # Não há confirmação pendente - continuar orquestração normal
    plan = await decide_and_plan(env)
```

#### 3.3 Orquestrador Inteligente

Se nenhuma confirmação foi processada pelo Gate:

```python
# app/core/orchestrator.py
if catalog_empty and procedures_empty:
    message = "🤖 Sistema em configuração inicial..."
elif is_simple_confirmation:
    message = "Entendi sua confirmação! Porém, no momento não tenho uma pergunta ativa..."
```

## 🧪 Como Testar

### 1. Teste Manual Básico

```bash
# 1. Resetar catálogo para começar limpo
python3 reset_catalog.py

# 2. Criar automação que espera confirmação via UI
# 3. Enviar mensagem que dispara a automação
# 4. Responder "sim" ou "não"
# 5. Verificar logs estruturados
```

### 2. Verificar Estado de Aguardando

```bash
curl -s "http://localhost:8000/api/leads/123" | python3 -c "
import sys, json
data = json.load(sys.stdin)
context = data.get('context', {})
waiting = context.get('waiting')
print(f'Estado aguardando: {waiting}')
"
```

### 3. Executar Testes Automatizados

```bash
python3 test_runner.py
```

## 📊 Logs Estruturados

### Eventos Principais

```json
{"evt": "hook_waiting_set", "automation_id": "ask_deposit_for_test", "lead_id": 123, "target": "confirm_can_deposit", "ttl_seconds": 1800}

{"evt": "gate_eval", "has_waiting": true, "retro_active": false, "decision": "yes", "reason_summary": "llm_classification"}

{"evt": "orchestrator_fallback", "reason": "orphaned_confirmation", "catalog_empty": false, "is_simple_confirmation": true}
```

## 🔧 Configurações

### Environment Variables

```bash
# Modo de confirmação
CONFIRM_AGENT_MODE=llm_first  # llm_first | hybrid | det_only

# Parâmetros LLM
CONFIRM_AGENT_TIMEOUT_MS=1000
CONFIRM_AGENT_THRESHOLD=0.80
CONFIRM_AGENT_MAX_HISTORY=10

# Gate determinístico
GATE_YESNO_DETERMINISTICO=true
```

### TTL dos Targets

Configurado em `policies/confirm_targets.yml`:

```yaml
confirm_can_deposit:
  max_age_minutes: 30  # Confirmação válida por 30 minutos
```

## 🐛 Troubleshooting

### Problema: Lead diz "sim" mas recebe "Não entendi"

**Causa**: Estado 'aguardando' não foi salvo ou expirou

**Solução**:
1. Verificar logs `hook_waiting_set`
2. Verificar se `automation_id` e `lead_id` estão sendo passados corretamente
3. Verificar TTL do target

### Problema: Confirmação não funciona após restart

**Causa**: Estado volátil perdido

**Solução**:
- Implementar persistência em banco de dados para estados críticos
- Verificar timeline retroativo (FASE 3)

### Problema: Catálogo vazio causa erros

**Solução**:
```bash
# Resetar com automações de exemplo
python3 reset_catalog.py

# Ou criar primeira automação via UI
```

## 🔄 Catálogo Reset

### Via CLI

```bash
python3 reset_catalog.py
```

### Via API

```bash
curl -X POST "http://localhost:8000/api/catalog/reset" \
  -H "Content-Type: application/json" \
  -d '{"create_backup_first": true, "keep_confirm_targets": true}'
```

### Via UI

Botão "Resetar Catálogo" na página de Automações.

## 📝 Criando Automações com Confirmação

### 1. Via YAML (Direto)

```yaml
- id: minha_pergunta
  topic: "confirmacao"
  eligibility: "lead ativo"
  priority: 0.8
  cooldown: 24h
  expects_reply:
    target: meu_target_customizado
  output:
    type: message
    text: "Você quer continuar com o processo?"
```

### 2. Via UI

1. Ir em `/automations/new`
2. Preencher campos básicos
3. Marcar "Espera Confirmação"
4. Definir target de confirmação
5. Configurar ações para YES/NO

### 3. Definir Target

```yaml
# policies/confirm_targets.yml
meu_target_customizado:
  max_age_minutes: 45
  on_yes:
    facts:
      meu_fato.confirmado: true
  on_no:
    facts:
      meu_fato.rejeitado: true
    automation: automacao_de_ajuda
```

## ⚡ Performance

### Caches

- Catálogo YAML: cached por 30s
- Targets de confirmação: cached por 30s
- Clear cache: `/api/catalog/clear-caches`

### Timeouts

- LLM confirmação: 1000ms (configurável)
- TTL padrão: 30 minutos
- Timeline retroativo: 60 minutos

## 🎯 Próximos Passos

### FASE 3 - Sistema Retroativo
- Timeline leve independente do Hook
- Detecção de confirmações órfãs
- Recuperação automática de estados

### FASE 4 - Orquestrador Inteligente  
- Sinais do Intake LLM
- Validação de propostas
- Context-aware fallbacks
