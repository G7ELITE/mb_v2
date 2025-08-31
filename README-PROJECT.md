# ManyBlack V2 — README-PROJECT (Atualizado • sem Docker • sem UI)

** QUANDO FOR USAR O TERMINAL ATIVE O .VENV NA RAIZ:
devbael@DESKTOP-7B8L8U5:~/mb-v2 source .venv/bin/activate **

** QUANDO FOR EXECUTAR ALGUM COMANDO RELACIONADO AO FRONTEND, VERIFIQUE SE O .VENV ESTA ATIVADO E USE O COMANDO NA PASTA DO FRONTEND:
(.venv) devbael@DESKTOP-7B8L8U5:~/mb-v2/studio$ **

** QUANDO FOR EXECUTAR ALGUM COMANDO RELACIONADO AO BACKEND, VERIFIQUE SE O .VENV ESTA ATIVADO E USE O COMANDO NA RAIZ DO PROJETO:
(.venv) devbael@DESKTOP-7B8L8U5:~/mb-v2 **

> **Status**: backend do zero para **Telegram** (WhatsApp preparado).  
> **Foco**: duas trilhas por turno — **Dúvida** (resposta controlada) e **Procedimento** (funil de procedimentos flexível).  
> **Arquitetura-chave**: **Intake Agent** (inteligente) prepara fatos; **Orquestrador** decide; **Workers/Tools** verificam fora; **Catálogo/Procedimentos** em **PT-BR** ditam o que enviar (texto/mídia/botões com rastreamento).

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

### 3.6 Registrar webhook do Telegram
```bash
curl -X POST "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/setWebhook" \
  -d "url=$PUBLIC_URL/channels/telegram/webhook?secret=$TELEGRAM_WEBHOOK_SECRET"
```

### 3.7 Validar instalação
```bash
# Health check
curl http://localhost:8000/health

# Informações do sistema  
curl http://localhost:8000/info

# Info do canal Telegram
curl http://localhost:8000/channels/telegram/info
```

### 3.8 Executar testes
```bash
# Ativar ambiente virtual
source .venv/bin/activate

# Executar todos os testes
pytest

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
    catalog.yml               # Automações em PT-BR
    procedures.yml            # Procedimentos em PT-BR
    policy_intake.yml         # Política do Intake Agent (budget/thresholds)
    kb.md                     # Base de conhecimento (fallback)
tests/
  unit/ integration/ e2e/
alembic/
requirements.txt
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

---

## 14) Próximos passos (fora deste README)

- **WhatsApp Cloud API**;  
- **Métricas/UTM completas** (facts/views, presets);  
- **Painel** (shadcn) de **cards de procedimentos** (CRUD).

**FIM — README-PROJECT**