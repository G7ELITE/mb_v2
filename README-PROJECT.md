# ManyBlack V2 — README-PROJECT (Atualizado • Backend + Frontend Studio + Novas Funcionalidades)

📋 **COMANDOS IMPORTANTES**

⚠️ **SEMPRE ATIVE O .VENV ANTES DE QUALQUER COMANDO:**
```bash
# Na raiz do projeto
devbael@DESKTOP-7B8L8U5:~/mb-v2$ source .venv/bin/activate
```

🎨 **Use os comandos dos arquivos .sh de acordo com a necessidade:**
```bash
# Documentação dos comandos estão no arquivo COMANDOS.md na raiz do projeto
(.venv) devbael@DESKTOP-7B8L8U5:~/mb-v2$ 
```

---

## 🎯 Visão Geral do Projeto

> **Status Atual**: Sistema completo com **Backend FastAPI** + **Frontend Studio** + **Novas Funcionalidades Avançadas** em produção
> 
> **Arquitetura Principal**: 
> - **🤖 Intake Agent** (inteligente) processa mensagens e enriquece fatos
> - **🎛️ Orquestrador** toma decisões baseadas em regras em português natural  
> - **⚙️ Workers/Tools** executam verificações externas e ações
> - **📚 Catálogo/Procedimentos** em **PT-BR** controlam respostas automáticas
> - **🎨 ManyBlack Studio** interface visual para configuração e testes
> - **🧠 Contexto Persistente** mantém estado entre turnos
> - **💬 Entendimento de Respostas Curtas** via regex + LLM fallback
> - **🔍 RAG Inteligente** por turno com cache
> - **⚖️ Comparador Semântico** prefere automações quando similar
> - **📋 Fila de Revisão Humana** para respostas geradas
> - **🎯 Sistema de Confirmação LLM-first** entende 'sim/não' inteligentemente

### 🚀 Funcionalidades Implementadas

- ✅ **Backend FastAPI** com arquitetura orientada a contexto
- ✅ **Frontend React** com interface em português brasileiro
- ✅ **Duas trilhas de conversação**: Dúvida (resposta controlada) e Procedimento (funis flexíveis)
- ✅ **Intake inteligente** com processamento de linguagem natural
- ✅ **Simulador integrado** para teste de conversas
- ✅ **Dashboard em tempo real** com métricas do sistema
- ✅ **Bot Telegram funcional** com resposta automática implementada
- ✅ **Pipeline de automações** completamente funcional com procedimentos em YAML
- ✅ **Persistência completa** de leads, perfis e eventos de jornada no PostgreSQL  
- ✅ **Tools reais** implementados (verify_signup, check_deposit) com simulação
- ✅ **Catálogo expandido** com 10+ automações e knowledge base detalhada
- ✅ **Modo escuro completo** com alto contraste
- ✅ **Interface responsiva** e acessível
- ✅ **Contexto persistente** do lead entre turnos e reinicializações
- ✅ **Página de Leads** com filtros avançados e integração com simulador
- ✅ **Entendimento de respostas curtas** ("sim/não") via regex e LLM fallback
- ✅ **RAG por turno** com cache inteligente e contexto da KB
- ✅ **Comparador semântico** que prefere automações quando similar (limiar 80%)
- ✅ **Fila de revisão humana** para respostas geradas sem automação equivalente
- ✅ **Envio seguro** de mensagens blindado contra nulos e botões inválidos
- ✅ **Telemetria consistente** com action_type padronizado e idempotência
- ✅ **Merge não-regressivo** do snapshot que não rebaixa fatos sem evidência melhor

---

## 1) Objetivo do projeto

- **Responder com controle**: priorizar **Catálogo de Automações**; usar **KB (fallback)** somente quando não houver match confiável.  
- **Decidir em 1 turno**: o **Orquestrador** lê um **Lead Snapshot** já **enriquecido** (fatos atuais + acordos do lead + resumo de histórico) e monta um **plano** idempotente de ações.  
- **Sem “ping-pong” de prompts**: orçamento curto, respostas objetivas e passos claros.  
- **Sem Docker / Sem UI nesta fase**: execução local via `venv`; contratos de API, dados e exemplos completos.

---

## 2) Stack & Requisitos

- **Python** 3.11+
- **FastAPI** (ASGI) + **Uvicorn**
- **PostgreSQL** 14+ (SQLAlchemy + Alembic)
- **Redis** 6+ (opcional: rate limit, filas leves)
- **LLM provider** (ex.: OpenAI) – chave via `OPENAI_API_KEY`
- **Telegram Bot** (token + webhook secreto)

> WhatsApp Cloud API: conector preparado, ativado em fase posterior.

---

## 3) Instalação (local, sem Docker)

### 3.1 Ambiente
```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -U pip wheel
pip install -r requirements.txt
```

### 3.2 Banco de dados
Crie o banco e o usuário:
```sql
CREATE DATABASE manyblack_v2 ENCODING 'UTF8';
CREATE USER mbuser WITH PASSWORD 'change-me';
GRANT ALL PRIVILEGES ON DATABASE manyblack_v2 TO mbuser;
```

### 3.3 Variáveis de ambiente (`.env`)
Copie e configure o arquivo de ambiente:
```bash
cp env.example .env
# Edite .env com suas configurações
```

### 3.4 Frontend Studio (Novo!)
Configure e execute o frontend:
```bash
# 1. Entre na pasta do studio
cd studio/

# 2. Instale dependências do Node.js
npm install

# 3. Execute em modo desenvolvimento
npm run dev

# O frontend estará disponível em http://localhost:5173
```

**Recursos do Studio:**
- 🎨 Interface 100% em português brasileiro
- 🌙 Modo escuro com alto contraste
- 📱 Design responsivo e acessível
- 🔄 Integração em tempo real com o backend
- 🧪 Simulador de conversas integrado
- 👥 Página de Leads com filtros avançados
- 🤖 Sistema de confirmação LLM-first

**🌐 Nova Implementação Ngrok Unificado:**
```bash
# Para expor frontend + backend via um único link:
./start.sh          # Inicia backend + frontend
ngrok http 5173     # Expõe frontend (inclui backend via proxy)

# Resultado: https://xxx.ngrok-free.app
# ✅ Frontend: https://xxx.ngrok-free.app
# ✅ Backend: https://xxx.ngrok-free.app/api/...
# ✅ Health: https://xxx.ngrok-free.app/health

# Comando para obtendo URL do ngrok e ativar webhook:
./activate_webhook.sh
```

**Benefícios:**
- ✅ **Um único domínio** para frontend e backend
- ✅ **Proxy automático** configurado no Vite
- ✅ **Mais simples** para compartilhar e testar
- ✅ **Funciona** localmente e via ngrok

Conteúdo do `.env`:
```dotenv
APP_ENV=dev
APP_PORT=8000

# LLM
OPENAI_API_KEY=sk-xxx

# Postgres
DB_HOST=127.0.0.1
DB_PORT=5432
DB_NAME=manyblack_v2
DB_USER=mbuser
DB_PASSWORD=change-me

# Redis (opcional)
REDIS_URL=redis://127.0.0.1:6379/0

# Telegram
TELEGRAM_BOT_TOKEN=123:ABC
TELEGRAM_WEBHOOK_SECRET=troque

# Security
JWT_SECRET=uma-frase-muito-longa-e-aleatoria
```

## 🧪 **Testes**

### **Executar Testes Unitários**
```bash
# Testes do sistema de confirmação
pytest tests/test_confirmation_gate.py -v

# Testes específicos
pytest tests/test_confirmation_gate.py::test_fase_1_e2e_hook_gate_actions -v
pytest tests/test_confirmation_gate.py::test_fase_2_intake_sempre_llm -v
pytest tests/test_confirmation_gate.py::test_gate_deterministico_curto -v
```

### **MAX MODE – Fases 1–2 (Teste)**

#### **Flags de Configuração**
```bash
# Ativar Gate determinístico para respostas curtas (testes)
export GATE_YESNO_DETERMINISTICO=true

# Configurar modo do intake
export INTAKE_LLM_CONFIG_MODE=always_llm
```

#### **Testes E2E**
```bash
# FASE 1: Hook + Gate + Aplicação de ações
python -c "
import asyncio
from tests.test_confirmation_gate import test_fase_1_e2e_hook_gate_actions
asyncio.run(test_fase_1_e2e_hook_gate_actions())
"

# FASE 2: Intake sempre-LLM
python -c "
import asyncio
from tests.test_confirmation_gate import test_fase_2_intake_sempre_llm
asyncio.run(test_fase_2_intake_sempre_llm())
"

# Gate determinístico
python -c "
import asyncio
from tests.test_confirmation_gate import test_gate_deterministico_curto
asyncio.run(test_gate_deterministico_curto())
"
```

#### **Logs Esperados**
```json
// FASE 1 - Hook
{"event":"hook_waiting_set", "automation_id":"ask_deposit_for_test", "lead_id":8, "target":"confirm_can_deposit", "ttl_seconds":1800}

// FASE 1 - Gate
{"event":"gate_eval", "has_waiting":true, "retro_active":false, "decision":"yes", "reason_summary":"deterministic_fallback"}

// FASE 1 - Aplicação de ações
{"event":"test_apply_actions", "set_facts":true, "clear_waiting":true}

// FASE 2 - Intake
{"event":"intake_llm", "intents":2, "polarity":"other", "targets":0, "facts_count":0, "propose_automations_count":1, "used_samples":2}

// Gate determinístico
{"event":"gate_short_circuit", "used":true, "polarity":"yes"}
```

#### **Fase 2 — Intake Blindado (Teste)**
O teste da FASE 2 agora inclui validações blindadas completas:

```python
# Validações principais
assert hasattr(enriched_env.snapshot, 'llm_signals')
assert signals.get('error') in (None, '')  # sem fallback silencioso
assert signals.get('used_samples', 1) == 2  # self-consistency aplicada
assert len(intents) > 0  # intents não vazio
assert polarity in ['yes', 'no', 'other', 'sarcastic']  # polarity válida
assert has_content  # pelo menos um entre targets, facts ou propose_automations
```

**Resumo esperado:**
```
📊 RESUMO FASE 2 - Intake Blindado:
  • Intents: 2 (test, deposit...)
  • Polarity: other
  • Has targets: True
  • Facts count: 0
  • Propose count: 1
  • Used samples: 2
  • Agreement score: 0.85
  • Error: None
```

#### **Gate Determinístico (Teste)**
Para respostas curtas em testes, use a flag `GATE_YESNO_DETERMINISTICO`:

```bash
export GATE_YESNO_DETERMINISTICO=true
```

**Mapeamento:**
- Afirmativas: `['sim','ok','👍','claro']` → YES
- Negativas: `['não','agora não']` → NO  
- Neutras: `['depois','talvez']` → OTHER

**Ações esperadas:**
- YES: `clear_waiting` + `set_facts` (quando aplicável)
- NO/OTHER: `clear_waiting` (sem `set_facts` irreversível)

### 3.4 Migrações
```bash
alembic upgrade head
```

### 3.5 Executar API
```bash
# Opção 1: usando uvicorn diretamente
uvicorn app.main:app --reload --port ${APP_PORT:-8000}

# Opção 2: usando módulo Python
python -m app.main

# Opção 3: usando gunicorn (produção)
# gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

### 3.6 Registrar webhook do Telegram (Nova Implementação)
```bash
# 1. Iniciar sistema com ngrok unificado:
./start.sh                # Backend + Frontend
ngrok http 5173          # Túnel único para frontend+backend

# 2. Configurar webhook (substitua pela URL real do ngrok):
curl -X POST "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/setWebhook" \
  -d "url=https://SEU-NGROK.ngrok-free.app/channels/telegram/webhook?secret=$TELEGRAM_WEBHOOK_SECRET"

# 3. Verificar configuração:
curl "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getWebhookInfo"
```

**Vantagens da nova implementação:**
- ✅ Um único domínio ngrok para frontend e backend
- ✅ Mais fácil de compartilhar e debugar
- ✅ Frontend e backend acessíveis simultaneamente

### 3.7 Validar instalação
```bash
# Health check (backend direto)
curl http://localhost:8000/health

# Health check (via proxy do frontend)
curl http://localhost:5173/health

# Informações do sistema  
curl http://localhost:8000/info

# Info do canal Telegram
curl http://localhost:8000/channels/telegram/info

# Testar frontend
curl http://localhost:5173

# Testar via ngrok (se configurado)
curl https://SEU-NGROK.ngrok-free.app/health
```

### 3.8 Executar testes
```bash
# Ativar ambiente virtual
source .venv/bin/activate

# Executar todos os testes
pytest

# Testes do sistema de confirmação LLM-first
pytest tests/test_confirmation_gate.py -v

# Com verbosidade
pytest -v

# Com coverage (se instalado)
pytest --cov=app tests/
```

### 3.9 Testar endpoints manualmente
```bash
# Testar decisão do orchestrador
curl -X POST http://localhost:8000/engine/decide \
  -H "Content-Type: application/json" \
  -d '{
    "lead": {"id": 1, "nome": "Test", "lang": "pt-BR"},
    "snapshot": {
      "accounts": {"quotex": "desconhecido"},
      "deposit": {"status": "nenhum"},
      "agreements": {"wants_test": true},
      "flags": {}
    },
    "candidates": {},
    "messages_window": [{"id": "1", "text": "quero testar"}],
    "apply": true
  }'

# Testar aplicação de plano
curl -X POST http://localhost:8000/api/tools/apply_plan \
  -H "Content-Type: application/json" \
  -H "X-Idempotency-Key: test_123" \
  -d '{
    "decision_id": "test_decision",
    "actions": [
      {
        "type": "send_message",
        "text": "Teste de aplicação de plano"
      }
    ]
  }'
```

---

## 4) Estrutura do repositório

```
app/
  main.py                     # FastAPI app + lifespan
  settings.py                 # Carrega .env
  channels/
    telegram.py               # Webhook + normalização
    whatsapp.py               # Adaptador preparado (futuro)
    adapter.py                # Converte payload unificado → canal
  core/
    snapshot_builder.py       # Pré-processa evento e funde estado (determinístico)
    intake_agent.py           # Interpreta msg crua (LLM) + chama até 2 tools
    orchestrator.py           # Decide Dúvida x Procedimento e gera plano
    selector.py               # Catálogo (PT-BR→predicados) e score/eligibilidade
    procedures.py             # Runtime de procedimentos (passos ordenados)
    fallback_kb.py            # Fallback com KB (RAG-lite) + guardrails
    planner.py                # Render de automações → actions, guardrails
    contexto_lead.py          # Contexto persistente do lead entre turnos
    resposta_curta.py         # Entendimento de respostas curtas (sim/não)
    confirmation_gate.py      # Gate de confirmação LLM-first com guardrails
    automation_hook.py        # Hook para expects_reply automático
    rag_service.py            # RAG por turno com cache inteligente
    comparador_semantico.py   # Comparação semântica vs automações
    fila_revisao.py           # Fila de revisão humana para respostas geradas
    config_melhorias.py       # Configurações centralizadas das melhorias
  tools/
    verify_signup.py          # Verifica cadastro (corretora)
    check_deposit.py          # Consulta status de depósito
    apply_plan.py             # Aplica plano (batch idempotente)
  data/
    models.py                 # SQLAlchemy models
    schemas.py                # Pydantic (envelopes/planos/payloads)
    repo.py                   # Repositórios
  metrics/
    tracking.py               # Eventos (message_sent, button_clicked, ...)
    utm.py                    # Preparação p/ facts & views (fase posterior)
  infra/
    db.py                     # Engine/Session + Alembic helpers
    redis_client.py           # Cliente Redis (opcional)
    logging.py                # Logs JSON estruturados
  policies/
    catalog.yml               # Automações em PT-BR (com expects_reply)
    procedures.yml            # Procedimentos em PT-BR
    confirm_targets.yml       # Targets de confirmação LLM-first
    policy_intake.yml         # Política do Intake Agent (budget/thresholds)
    kb.md                     # Base de conhecimento (fallback)
tests/
  unit/ integration/ e2e/
  test_melhorias.py           # Testes das novas funcionalidades
alembic/
requirements.txt
MELHORIAS_IMPLEMENTADAS.md    # Documentação das melhorias
```

---

## 4.1) Sistema de Confirmação LLM-first

### 🎯 Visão Geral

O sistema de confirmação inteligente intercepta mensagens antes do orquestrador para detectar e processar confirmações (sim/não) automaticamente usando **LLM-first com fallback determinístico**.

### 🔧 Componentes Principais

#### **ConfirmationGate** (`app/core/confirmation_gate.py`)
- **Gate único** no pipeline chamado ANTES do `decide_and_plan`
- **LLM-first**: Usa GPT-4o-mini com function calling para interpretar confirmações
- **Fallback determinístico**: Reconhece padrões simples se LLM falhar/timeout
- **Guardrails**: TTL, whitelist de targets, limiar de confiança (0.80)

#### **AutomationHook** (`app/core/automation_hook.py`)
- **Hook automático** após envio de automações com `expects_reply`
- **Seta estado `aguardando`** baseado no target da confirmação
- **TTL dinâmico** baseado na configuração do target

#### **Targets de Confirmação** (`policies/confirm_targets.yml`)
```yaml
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

### 🎛️ Configurações ENV

```bash
# Modo de operação
CONFIRM_AGENT_MODE=llm_first  # llm_first | hybrid | det_only

# Parâmetros de performance  
CONFIRM_AGENT_TIMEOUT_MS=1000      # Timeout do LLM
CONFIRM_AGENT_THRESHOLD=0.80       # Limiar de confiança mínima
CONFIRM_AGENT_MAX_HISTORY=10       # Máximo de mensagens no contexto
```

### 📊 Fluxo de Decisão

1. **Pergunta enviada**: Automação com `expects_reply.target` → seta `aguardando` automaticamente
2. **Resposta recebida**: Gate verifica se há confirmação pendente
3. **LLM Analysis**: GPT interpreta mensagem com contexto estruturado
4. **Guardrails**: Valida confiança, TTL, whitelist de targets
5. **Aplicação**: Define fatos, limpa `aguardando`, dispara automação (se NO)
6. **Fallback**: Se LLM falhar, usa padrões determinísticos

### 🔒 Segurança e Confiabilidade

- **Determinismo**: Side-effects críticos só aplicados com alta confiança
- **TTL**: Confirmações só válidas dentro do prazo configurado
- **Idempotência**: Integração mantém idempotência do pipeline existente
- **Rollback**: Flag global para desativar (fallback para fluxo atual)

### 📈 Telemetria

```json
{
  "event": "confirmation_processed",
  "lead_id": 123,
  "target": "confirm_can_deposit", 
  "polarity": "yes",
  "confidence": 0.92,
  "source": "llm",
  "latency_ms": 847,
  "outcome": "applied"
}
```

---

## 5) Papéis e responsabilidades

- **Snapshot Builder** (determinístico): normaliza evento (Telegram/WA), extrai evidências (regex/âncoras), funde com estado do lead, **não decide**. Pode enfileirar jobs para workers (ex.: `verify_signup`) e marcar `pending_ops` no snapshot.  
- **Intake Agent** (inteligente): usa *contexto* (último passo/objetivo), histórico curto e padrões ID/e-mail por corretora. Faz **1 LLM + até 2 tools** (paralelas quando útil) para retornar **fatos prontos** (ex.: `accounts.nyrion="com_conta"`).  
- **Orquestrador** (LLM supervisor): dado o **Lead Snapshot**, decide **Dúvida** (catálogo/KB) ou **Procedimento** (passos). **Não chama APIs externas**; apenas monta e devolve **plano idempotente**.  
- **Workers/Tools**: executam verificações externas; ao concluir, **atualizam estado** e disparam **turno de sistema**.  
- **Selector (Catálogo)**: escolhe automação por regras em **PT-BR** compiladas; prioriza templates a geração livre.  
- **Procedures Runtime**: avalia passos em ordem; no primeiro não cumprido, dispara a automação e termina o turno.

---

## 6) Formato do Lead Snapshot (entrada do Orquestrador)

```json
{
  "lead": {"id": 9123, "nome": "Gabriel", "lang": "pt-BR"},
  "snapshot": {
    "accounts": {"quotex": "com_conta", "nyrion": "sem_conta"},
    "deposit": {"status": "pendente"},
    "agreements": {"can_deposit": true, "wants_test": true},
    "flags": {"explained": true},
    "history_summary": "Perguntou OTC; disse que vai depositar; quer testar.",
    "verifications": [
      {"kind":"signup","broker":"nyrion","input":{"account_id":"8989453289"},"outcome":"verified","confidence":0.92}
    ]
  },
  "messages_window": [{"id":"m1","text":"quero testar"}],
  "apply": true
}
```
> Observação: **se o lead disse que pode depositar**, isso basta (`agreements.can_deposit=true`). Não usamos saldo.

---

## 7) Catálogo de automações (PT-BR)

### 7.1 Schema
```yaml
- id: string
  topic: string
  use_when: string                 # linguagem natural
  eligibility: string              # linguagem natural (compilada → predicado)
  priority: 0.0..1.0
  cooldown: "1h" | "24h" | seconds
  output:
    type: "message"
    text: "texto com {{variaveis}}"
    media:
      - {kind: "photo|video|document", url: "https://...", caption: "opcional"}
    buttons:
      - id: "btn_id"
        label: "rótulo"
        kind: "url|callback|quick_reply"
        url: "https://..."             # apenas em kind=url
        set_facts: {agreements.can_deposit: true}  # apenas callback/quick_reply
        track: {event: "nome_evento", utm_passthrough: true}
```

### 7.2 Exemplo
```yaml
- id: ask_deposit_for_test
  topic: "teste"
  use_when: "o lead quer testar"
  eligibility: "não concordou em depositar e não depositou"
  priority: 0.85
  cooldown: 24h
  output:
    type: message
    text: "Para liberar o teste, você consegue fazer um pequeno depósito?"
    buttons:
      - id: btn_yes_deposit
        label: "Sim, consigo"
        kind: callback
        set_facts: {agreements.can_deposit: true}
        track: {event: "click_yes_deposit", utm_passthrough: true}
      - id: btn_help_deposit
        label: "Como deposito?"
        kind: url
        url: "{{deposit_help_link}}"
        track: {event: "open_deposit_help"}
```

---

## 8) Procedimentos (funil de procedimentos, sem verificação ativa)

### 8.1 Definição (PT-BR)
```yaml
id: liberar_teste
title: "Liberar teste"
steps:
  - name: "Concorda em depositar"
    condition: "o lead concordou em depositar ou já depositou"
    if_missing: {automation: "ask_deposit_for_test"}

  - name: "Criou conta"
    condition: "tem conta em alguma corretora suportada"
    if_missing: {automation: "signup_link"}

  - name: "Depósito confirmado"
    condition: "depósito confirmado"
    if_missing: {automation: "prompt_deposit"}

  - name: "Liberar"
    condition: "todas as etapas anteriores cumpridas"
    do: {automation: "trial_unlock"}
```

### 8.2 Execução
- O runtime percorre os **passos em ordem**; no primeiro passo **não satisfeito**, dispara a automação e encerra o turno.  
- Quando todos os passos passam, dispara a automação final (ex.: `trial_unlock`).

---

## 9) Mensagens (texto/mídia/botões) e rastreamento

### 9.1 Payload unificado
```json
{
  "type":"message",
  "channel":"telegram",
  "text":"Crie sua conta: {{signup_link}}",
  "media":[{"kind":"photo","url":"https://cdn/step.png","caption":"Passo a passo"}],
  "buttons":[
    {"id":"btn_open_signup","label":"Abrir cadastro","kind":"url","url":"{{signup_link}}",
     "track":{"event":"open_signup","utm_passthrough":true}}
  ],
  "meta":{"parse_mode":"HTML"}
}
```

### 9.2 Mapeamento por canal
- **Telegram**: `url` → *inline keyboard URL*; `callback` → *callback_data*; `photo/video/document` com `caption`.  
- **WhatsApp**: `url` → *URL button*; `quick_reply` → *Quick Reply*; mídia suportada semelhante (limites de tamanho).

### 9.3 Eventos
- `message_sent`, `automation_run`, `button_clicked`, `procedure_run`, `journey_event` (armazenados para métricas/UTM).

---

## 10) Endpoints (contratos)

- **Webhook Telegram**: `POST /channels/telegram/webhook?secret=...`  
  Recebe update → normaliza → Snapshot Builder → Intake → Orquestrador → Apply Plan.

- **Decisão do turno**: `POST /engine/decide`  
  Entrada: **Lead Snapshot**; Saída: **plano** (lista de ações + logs).

- **Aplicação (idempotente)**: `POST /api/tools/apply_plan`  
  Cabeçalho: `X-Idempotency-Key: <decision_id>`.

- **Tools (workers)**:  
  `POST /tools/verify_signup` → `{broker, email?, account_id?} -> {verified, details?}`  
  `POST /tools/check_deposit` → `{broker, email?/account_id} -> {status}`

---

## 11) Modelos de dados (SQLAlchemy — resumo)

- `lead(id, platform_user_id, name, lang, created_at, ...)`
- `lead_profile(lead_id PK, accounts JSONB, deposit JSONB, agreements JSONB, flags JSONB)`
- `automation_run(id, lead_id, automation_id, payload JSONB, created_at)`
- `procedure_run(id, lead_id, procedure_id, step, outcome, created_at)`
- `journey_event(id, lead_id, type, payload JSONB, created_at)`
- `lead_touchpoint(id, lead_id, utm_id, event, ts)`
- `idempotency_key(key PK, response JSONB, created_at)`
- `contexto_lead(lead_id PK, procedimento_ativo, etapa_ativa, aguardando JSONB, ultima_automacao_enviada, ultimo_topico_kb, atualizado_em)`
- `fila_revisao(id, lead_id, pergunta, resposta, fontes_kb JSONB, automacao_equivalente, pontuacao_similaridade, contexto_do_lead JSONB, aprovado, criado_em)`

Índices: `(lead_id, created_at desc)` + `GIN` em JSONB.

---

## 12) Testes

- **Unit**: compilador PT-BR→predicados; selector; procedures; planner.  
- **Integração**: snapshot builder + intake + tools + orquestrador.  
- **E2E**: telegram webhook → intake → decide → apply → ledger.  
- **Dados de teste**: automações de “teste/explicar”, procedimento “liberar_teste”.

---

## 13) Operação & Qualidade

- **Idempotência**: todas as execuções com `decision_id` + `X-Idempotency-Key`.  
- **Concorrência**: coalescer 1.5–3s por lead; mutex por lead; ordem garantida.  
- **Orçamento**: Intake (`1 LLM + 2 tools`, ≤3s), Orquestrador (`1 LLM`, ≤2s).  
- **Logs**: JSON com `lead_id`, `turn_id`, `decision_id`, `latência`, `tools_used`.
- **Contexto persistente**: TTL 30min para estados voláteis; merge não-regressivo.
- **RAG**: Cache 60s por tópico; top-k=3 resultados; busca semântica.
- **Comparador semântico**: Limiar 80% para preferir automações; timeout 3s para geração.
- **Resposta curta**: Timeout 1.5s para LLM fallback; regex para detecção direta.

---

## 14) Próximos passos (fora deste README)

- **WhatsApp Cloud API**;  
- **Métricas/UTM completas** (facts/views, presets);  
- **Painel** (shadcn) de **cards de procedimentos** (CRUD).

**FIM — README-PROJECT**