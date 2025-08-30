# ManyBlack V2 — README-ROADMAP (Completo • sem Docker • sem UI)

> **Visão**: Plataforma de conversão/atendimento orientada a **contexto**, com dois tipos de interação por turno: **Dúvida** (resposta pontual, controlada por catálogo/KB) e **Procedimento** (funil de procedimentos flexível, passo a passo).  
> **Arquitetura**: **Intake Agent** (inteligente) entende mensagens cruas e executa tools; **Orquestrador** decide com base em **Lead Snapshot** enriquecido; **Workers/Tools** realizam verificações externas; **Catálogo** e **Procedimentos** são editados em **PT‑BR**.  
> **Escopo**: **sem UI** nesta fase e **sem Docker**. Foco em contratos, dados, runtime, testes e operação.

---

## 0) Metas & Princípios

1. **Controle com previsibilidade**: priorizar **automações do catálogo** (templates) para respostas críticas; **fallback** com KB apenas quando necessário.
2. **Decisão em 1 turno**: minimizar ping‑pong de prompts; orquestrador constrói e aplica **plano idempotente** (um batch de ações).
3. **Inteligência com segurança**: **Intake Agent** interpreta entradas ambíguas (“`8989453289`”, “`email@gmail.com`”) usando contexto do fluxo e **executa até 2 tools**; só pergunta quando necessário (com botões rastreáveis).
4. **Sem duplicação de verificações**: o orquestrador **não chama APIs externas** — ele **decide** com base nos **fatos** que chegam no snapshot.
5. **Observabilidade/qualidade desde o início**: logs estruturados, métricas de latência e utilização, auditoria de decisões.
6. **Edição em PT‑BR**: catálogo/procedimentos/regras são escritos em linguagem natural e **compilados** para predicados internos (DSL “por baixo do capô”).

---

## 1) Glossário

- **Turno**: ciclo de decisão referente a uma janela coalescida de mensagens do lead ou a um evento de sistema (ex.: verificação concluída).  
- **Lead Snapshot**: estado consolidado (contas, depósito, acordos/concordâncias, flags, resumo de histórico e verifications).  
- **Dúvida**: pergunta pontual respondida por catálogo/KB; não altera fluxo de marcos.  
- **Procedimento**: sequência ordenada de passos que guiam o lead até um objetivo (ex.: *Liberar teste*, *Liberar VIP*).  
- **Intake Agent**: agente de entrada que interpreta mensagem crua, usa contexto e **executa tools** com orçamento controlado.
- **Workers/Tools**: serviços que verificam cadastro/depósito e atualizam o estado.  
- **Apply Plan**: endpoint que aplica ações (mensagens, botões, tags…), **idempotente**.

---

## 2) Arquitetura (alto nível)

```
[ Telegram / WhatsApp ]
        │
        ▼
[ Webhook ] ──► [ Snapshot Builder ] ──► [ Intake Agent ] ──► [ Orquestrador ] ──► [ Apply Plan ]
                                   │                        (decide/planeja)        (batch idempotente)
                                   └──► [ Workers/Tools (verify_signup, check_deposit) ]
                                            ▲
                                            └── Atualizam estado e disparam turno de sistema
```

**Papéis**  
- **Snapshot Builder (determinístico)**: normaliza evento (canal), extrai evidências (regex/âncoras), funde com estado e **não decide**. Pode enfileirar jobs para workers e marcar `pending_ops`.  
- **Intake Agent (inteligente)**: usa contexto do fluxo (passo ativo, histórico curto) + padrões confiáveis (e‑mail/ID por corretora) + 1 chamada LLM para desambiguar e **executa até 2 tools** (paralelas quando útil).  
- **Orquestrador**: lê o snapshot e decide **Dúvida** x **Procedimento**; escolhe automação/checkpoint; constrói **plano**; **não verifica** externamente.  
- **Workers/Tools**: executam verificações; ao concluir, **persistem fatos** e disparam **turno de sistema** com o snapshot atualizado.  
- **Apply Plan**: aplica ações (texto, mídia, botões com tracking) em batch idempotente.

---

## 3) Fluxos canônicos

### 3.1 Dúvida
1. Webhook → Snapshot Builder → Intake (geralmente sem tools).  
2. Orquestrador tenta **catálogo**; se não houver, **KB** (RAG‑lite com guardrails).  
3. Apply Plan envia resposta; registra `automation_run` e `message_sent`.

### 3.2 Procedimento (ex.: “Liberar teste”)
1. Webhook → Snapshot Builder → Intake: detecta `email`/`account_id` e **verifica** com alta confiança (Nyrion/Quotex conforme contexto).  
2. Snapshot enriquecido (ex.: `accounts.nyrion="com_conta"`, `agreements.can_deposit=true`).  
3. Orquestrador executa **passos**:  
   - *Concorda em depositar* → usa `agreements.can_deposit` (não pergunta).  
   - *Criou conta* → se não, dispara `signup_link`.  
   - *Depósito confirmado* → se não, `prompt_deposit`; se sim, `trial_unlock`.  
4. Apply Plan registra `procedure_run + automation_run`.  
5. Se depósito confirmar depois → **turno de sistema** conclui.

---

## 4) Lead Snapshot (contrato)

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
  "apply": true,
  "now": "2025-08-30T14:45:00-03:00"
}
```

**Observações**  
- Concordância do lead vale como fato: `agreements.can_deposit=true` (não usamos saldo).  
- `verifications[]` documenta o que o Intake/Workers checaram (auditoria).

---

## 5) Catálogo (PT‑BR) e compilação

### 5.1 Modelo de automação
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
    media:
      - kind: photo
        url: "https://cdn/dep.png"
        caption: "Passo a passo"
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

### 5.2 Compilação PT‑BR → predicados
- “não concordou em depositar e não depositou” → `not agreements.can_deposit and deposit.status in ["nenhum","pendente"]` (exemplo).  
- Compilador retorna: `predicate_ast`, `confidence`, `mapping` (para auditoria).  
- A equipe **só escreve PT‑BR**; a DSL é interna.

---

## 6) Procedimentos (PT‑BR)

### 6.1 Modelo
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

### 6.2 Execução (runtime)
- Avalia **em ordem**; primeiro passo não satisfeito → dispara `if_missing.automation` e encerra turno.  
- Se todos satisfeitos → executa `do`.  
- **Sem verificação ativa**; usa somente os **fatos do snapshot**.

### 6.3 Pseudocódigo
```python
def run_procedure(proc, snapshot):
    for step in proc.steps:
        if not satisfies(step.condition, snapshot):
            return Action("run_automation", automation_id=step.if_missing.automation, step=step.name)
    return Action("run_automation", automation_id=proc.final or "trial_unlock", step="done")
```

---

## 7) Intake Agent — política, confiança e ferramentas

### 7.1 Política
```yaml
intake_policy:
  llm_budget: 1
  tool_budget: 2
  max_latency_ms: 3000
  thresholds:
    direct: 0.80         # chamar tool direta (um broker)
    parallel: 0.60       # chamar tools em paralelo (multi-broker)
  broker_priority:
    - by_active_procedure
    - by_profile_known
    - fallback_parallel
  anchors:
    email: ["email", "e-mail", "mail"]
    id: ["id", "conta", "login", "número da conta"]
  id_patterns:
    nyrion: ["\\b[0-9]{6,12}\\b"]
    quotex: ["\\b[a-zA-Z0-9]{6,16}\\b"]
```

### 7.2 Regras
- **Contexto primeiro**: se o passo ativo pede “ID/e‑mail Nyrion”, e chega “`8989453289`”, chame `verify_signup(nyrion)` direto.  
- **Padrões e e‑mail**: regex de e‑mail confiável; padrões por corretora para ID.  
- **Paralelismo**: dúvida de corretora → tentar Nyrion+Quotex em paralelo (dentro do orçamento).  
- **Evitar atrito**: só perguntar se a confiança < `parallel` ou se as tools falham.

### 7.3 Ferramentas (contratos)
- `POST /tools/verify_signup` → `{broker, email?, account_id?}` → `{verified:bool, details?}`  
- `POST /tools/check_deposit` → `{broker, email?/account_id}` → `{status:"nenhum|pendente|confirmado"}`

---

## 8) Mensagens, botões e rastreamento

### 8.1 Payload unificado (independente de canal)
```json
{
  "type":"message",
  "text":"Crie sua conta: {{signup_link}}",
  "media":[{"kind":"photo","url":"https://cdn/step.png","caption":"Passo a passo"}],
  "buttons":[
    {"id":"btn_open_signup","label":"Abrir cadastro","kind":"url","url":"{{signup_link}}",
     "track":{"event":"open_signup","utm_passthrough":true}}
  ]
}
```

### 8.2 Mapeamento por canal
- **Telegram**: inline keyboard (URL/Callback), mídia com `caption`, `parse_mode`.  
- **WhatsApp**: URL buttons e Quick Replies; limites de tamanho/tempo.

### 8.3 Eventos
- `message_sent`, `automation_run`, `button_clicked`, `procedure_run`, `journey_event`.  
- `utm_passthrough`: replica UTM do lead no clique do botão (para atribuição).

---

## 9) Dados & Esquema (SQLAlchemy)

- `lead(id, platform_user_id, name, lang, created_at, ...)`
- `lead_profile(lead_id PK, accounts JSONB, deposit JSONB, agreements JSONB, flags JSONB)`
- `automation_run(id, lead_id, automation_id, payload JSONB, created_at)`
- `procedure_run(id, lead_id, procedure_id, step, outcome, created_at)`
- `journey_event(id, lead_id, type, payload JSONB, created_at)`
- `lead_touchpoint(id, lead_id, utm_id, event, ts)`
- `idempotency_key(key PK, response JSONB, created_at)`

**Índices**: `(lead_id, created_at desc)`; `GIN` em JSONB (`accounts/deposit/agreements`).

---

## 10) Endpoints (contratos)

- `POST /channels/telegram/webhook?secret=...`  
- `POST /engine/decide` (entrada: Lead Snapshot; saída: plano + logs)  
- `POST /api/tools/apply_plan` (idempotente; `X-Idempotency-Key`)  
- `POST /tools/verify_signup` / `POST /tools/check_deposit` (workers)

**Plano (exemplo)**
```json
{
  "decision_id":"dec_9123_777",
  "actions":[
    {"type":"send_message","lead_id":9123,"text":"Crie sua conta: {{signup_link}}",
     "buttons":[{"id":"btn_open_signup","label":"Abrir cadastro","kind":"url","url":"{{signup_link}}"}]}
  ],
  "logs":{"type":"procedimento","proc":"liberar_teste","step":"Criou conta","latency_ms":680}
}
```

---

## 11) Performance & Confiabilidade

- **Orçamentos**: Intake `≤3s` (1 LLM + 2 tools), Orquestrador `≤2s` (1 LLM).  
- **Coalescer**: janela 1.5–3s; mutex por lead; `turn_seq` para ordem.  
- **Idempotência**: `decision_id` + `X-Idempotency-Key`.  
- **Circuit breakers**: para tools externas quando erro ≥ limiar.  
- **Cache curto**: TTL 60s para checks externos frequentes.  
- **SLIs/SLOs**:  
  - p95 latência do turno: **≤ 2.5s** (orquestrador), **≤ 3.5s** (intake).  
  - Taxa de sucesso de apply: **≥ 99.5%**.  
  - Erros 5xx do motor: **≤ 0.5%**.

---

## 12) Segurança & Privacidade

- **Sem valores sensíveis** (saldo): usar apenas `agreements.can_deposit`.  
- **Mascarar PII** em logs (e‑mail parcial, ID truncado).  
- **Auth**: JWT para tools privadas e `/api/tools/apply_plan`.  
- **Permissões** por escopo (leitura/execução/telemetria).

---

## 13) Testes (matriz)

- **Unit**:  
  - compilador PT‑BR→predicados (automações/procedimentos).  
  - selector (eligibility/priority/cooldown).  
  - procedures runtime (ordem/short‑circuit).  
  - planner (render de botões/track/set_facts).

- **Integração**:  
  - intake (mensagens curtas “`8989453289`”/“`email@gmail.com`” → verify).  
  - snapshot builder + intake + orquestrador (Dúvida/Procedimento).  
  - workers (verify/check) + turno de sistema.

- **E2E**:  
  - Telegram webhook → intake → decide → apply → ledger.  
  - Cenários: *Liberar teste*, *Dúvida ⚙ KB fallback*, concorrência de mensagens.

- **Dados sintéticos**:  
  - leads com UTM variada;  
  - procedimentos “liberar_teste” e “liberar_vip”;  
  - automações de “explicar”, “teste já usado”, “cadastro”.

---

## 14) Operação & Runbook

- **Erros de canal** (Telegram/WA): registrar update bruto + causa; reprocessar se transitório.  
- **Verificação lenta**: responder com ACK (“conferindo…”) e registrar `pending_ops`; resultado chega por **turno de sistema**.  
- **Mensagens simultâneas**: coalescer; prioridade a callbacks de botão para fechar janela.  
- **Feature flags**: ligar/desligar procedimentos, políticas do intake e automações específicas.  
- **Backups**: pg_dump diário (fora do escopo deste doc, mas recomendado).

---

## 15) Amostras (prontas para copiar)

### 15.1 `policies/procedures.yml`
```yaml
- id: liberar_teste
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

### 15.2 `policies/catalog.yml`
```yaml
- id: signup_link
  topic: "cadastro"
  use_when: "precisa criar conta"
  eligibility: "não tem conta em nenhuma corretora suportada"
  output:
    type: message
    text: "Crie sua conta aqui: {{signup_link}}"
    buttons:
      - id: btn_open_signup
        label: "Abrir cadastro"
        kind: url
        url: "{{signup_link}}"
        track: {event: "open_signup", utm_passthrough: true}

- id: trial_unlock
  topic: "teste"
  use_when: "todas as etapas cumpridas"
  eligibility: "depósito confirmado"
  output:
    type: message
    text: "Tudo certo! ✅ Seu teste está liberado. Quer ajuda para começar?"
```

### 15.3 `policies/policy_intake.yml`
```yaml
llm_budget: 1
tool_budget: 2
max_latency_ms: 3000
thresholds:
  direct: 0.80
  parallel: 0.60
anchors:
  email: ["email", "e-mail", "mail"]
  id: ["id", "conta", "login", "número da conta"]
id_patterns:
  nyrion: ["\\b[0-9]{6,12}\\b"]
  quotex: ["\\b[a-zA-Z0-9]{6,16}\\b"]
```

---

## 16) Roadmap de entrega (fases)

- **F1 (Core)**: Snapshot Builder, Intake Agent, Orquestrador, Catálogo (PT‑BR), Procedimentos base (liberar_teste), Apply Plan idempotente, Telegram webhook.  
- **F2 (Conteúdo & Métricas)**: KB fallback, tracking completo de botões, preparo de UTM (facts/views).  
- **F3 (Escala & Confiabilidade)**: WhatsApp, circuit breakers, cache, otimizações de p95, observabilidade (latência, erros, tokens).  
- **F4 (Painel futuro)**: CRUD de **cards de procedimentos** (shadcn), presets de métricas — **fora deste escopo**.

---

## 17) Critérios de aceite (MVP)

- **Procedimento “liberar_teste”** operando fim‑a‑fim.  
- Mensagens curtas “`8989453289`”/“`email@gmail.com`” tratadas pelo **Intake**:  
  - com contexto → verifica em silêncio e avança;  
  - sem contexto suficiente → pergunta mínima com botões rastreáveis.  
- **Dúvidas** respondidas por catálogo/KB.  
- **Planos idempotentes**; **logs** e **eventos** persistidos.  
- p95 **≤ 3.5s** (Intake) / **≤ 2.5s** (Orquestrador).

**FIM — README-ROADMAP**