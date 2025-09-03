# ManyBlack V2 — README-ROADMAP (✅ Completo • Backend + Frontend Studio + Novas Funcionalidades)

> **🎯 Status Atual**: ✅ **Fase 1 Completa** - Sistema totalmente funcional com backend FastAPI, frontend React e funcionalidades avançadas
> 
> **Visão**: Plataforma completa de conversão/atendimento orientada a **contexto**, com interface visual amigável em português para equipes operacionais. Dois tipos de interação por turno: **Dúvida** (resposta pontual, controlada por catálogo) e **Procedimento** (funis flexíveis passo a passo).  
> 
> **Arquitetura**: **Intake Agent** (inteligente) processa mensagens e executa ferramentas; **Orquestrador** decide com base em **Lead Snapshot** enriquecido; **Workers/Tools** realizam verificações externas; **ManyBlack Studio** permite configuração visual em **PT‑BR**.
> 
> **✨ Novidades**: Interface visual completa, modo escuro, simulador integrado, dashboard em tempo real, contexto persistente, entendimento de respostas curtas, RAG inteligente, comparador semântico, fila de revisão humana

---

## ✅ Implementado - ManyBlack Studio (Frontend Visual)

### 🎨 Interface Completa em Português
- **Dashboard**: Visão geral em tempo real com métricas de saúde do sistema
- **Procedimentos**: Editor visual de funis com passos sequenciais
- **Automações**: CRUD completo de mensagens automáticas com botões
- **Intake & Âncoras**: Configuração de detecção de intenções
- **Simulador**: Teste de conversas com modo desenvolvedor
- **Publicação**: Deploy de configurações (estrutura preparada)

### 🌟 Recursos de UX/UI
- **🇧🇷 100% PT-BR**: Interface totalmente em português brasileiro
- **🌙 Modo Escuro**: Design moderno com alto contraste
- **📱 Responsivo**: Funciona em desktop, tablet e mobile
- **🎛️ Sidebar Colapsável**: Maximize área de trabalho
- **⚡ Blocos Colapsáveis**: Visualize apenas o necessário
- **🔄 Transições Suaves**: Experiência fluida e moderna

### 🛠️ Stack Tecnológica do Frontend
- **React 18** + TypeScript para UI robusta
- **Tailwind CSS v4** para estilização moderna
- **React Router** para navegação client-side
- **React Query** para cache e sincronização
- **React Hook Form** para formulários otimizados
- **Heroicons** para ícones consistentes

### 🆕 Novas Funcionalidades Avançadas
- **🧠 Contexto Persistente**: Estado mantido entre turnos e reinicializações
- **💬 Entendimento de Respostas Curtas**: "sim/não" via regex + LLM fallback
- **🔍 RAG Inteligente**: Busca na KB por turno com cache otimizado
- **⚖️ Comparador Semântico**: Prefere automações quando similar (limiar 80%)
- **📋 Fila de Revisão Humana**: Respostas geradas vão para aprovação
- **🛡️ Envio Seguro**: Blindagem contra nulos e botões inválidos
- **📊 Telemetria Consistente**: Logs padronizados e idempotência
- **🔄 Merge Não-Regressivo**: Não rebaixa fatos sem evidência melhor

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
[ Webhook ] ──► [ Snapshot Builder + RAG ] ──► [ Intake Agent ] ──► [ Orquestrador + Contexto ] ──► [ Apply Plan ]
                                   │                        │                                    │
                                   └──► [ Workers/Tools (verify_signup, check_deposit) ]         │
                                   │                                                             │
                                   └──► [ Resposta Curta + Comparador Semântico ] ───────────────┘
```

**Papéis**  
- **Snapshot Builder (determinístico)**: normaliza evento (canal), extrai evidências (regex/âncoras), funde com estado, executa RAG por turno, **não decide**. Pode enfileirar jobs para workers e marcar `pending_ops`.  
- **Intake Agent (inteligente)**: usa contexto do fluxo (passo ativo, histórico curto) + padrões confiáveis (e‑mail/ID por corretora) + 1 chamada LLM para desambiguar e **executa até 2 tools** (paralelas quando útil).  
- **Orquestrador**: lê o snapshot, verifica contexto persistente, processa respostas curtas, decide **Dúvida** x **Procedimento**; escolhe automação/checkpoint; constrói **plano**; **não verifica** externamente.  
- **Workers/Tools**: executam verificações; ao concluir, **persistem fatos** e disparam **turno de sistema** com o snapshot atualizado.  
- **Apply Plan**: aplica ações (texto, mídia, botões com tracking) em batch idempotente com blindagem contra nulos.

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
    ],
    "kb_context": {
      "hits": [
        {"texto": "Para depositar, acesse...", "fonte": "KB: Depósitos", "score": 0.85}
      ],
      "topico": "depósito"
    }
  },
  "messages_window": [{"id":"m1","text":"quero testar"}],
  "apply": true,
  "now": "2025-08-30T14:45:00-03:00"
}
```

**Observações**  
- Concordância do lead vale como fato: `agreements.can_deposit=true` (não usamos saldo).  
- `verifications[]` documenta o que o Intake/Workers checaram (auditoria).
- `kb_context` contém contexto da KB anexado automaticamente por turno.

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
- `contexto_lead(lead_id PK, procedimento_ativo, etapa_ativa, aguardando JSONB, ultima_automacao_enviada, ultimo_topico_kb, atualizado_em)`
- `fila_revisao(id, lead_id, pergunta, resposta, fontes_kb JSONB, automacao_equivalente, pontuacao_similaridade, contexto_do_lead JSONB, aprovado, criado_em)`

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
- **Contexto persistente**: TTL 30min para estados voláteis; merge não-regressivo.
- **RAG**: Cache 60s por tópico; top-k=3 resultados; busca semântica.
- **Comparador semântico**: Limiar 80% para preferir automações; timeout 3s para geração.
- **Resposta curta**: Timeout 1.5s para LLM fallback; regex para detecção direta.
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
- **Contexto persistente** mantido entre turnos e reinicializações.
- **Respostas curtas** ("sim/não") entendidas via regex e LLM fallback.
- **RAG por turno** com contexto da KB anexado ao snapshot.
- **Comparador semântico** prefere automações quando similar (limiar 80%).
- **Fila de revisão** para respostas geradas sem automação equivalente.
- **Envio seguro** blindado contra nulos e botões inválidos.
- **Telemetria consistente** com action_type padronizado e idempotência.

**FIM — README-ROADMAP**

---

## 🎯 **Marcos Concluídos**

### ✅ **Implementação #12: MAX MODE - Fases 1 e 2**
- **FASE 1**: Hook/ApplyPlan/Gate com aplicação de ações E2E
- **FASE 2**: Intake sempre-LLM com schema válido
- **Gate determinístico**: Curto-circuito para respostas curtas
- **Testes E2E**: Validação completa das funcionalidades
- **Observabilidade**: Logs estruturados para todas as operações

### ✅ **Implementação #11: Correção Final do Sistema de Confirmação**
- **Erro crítico corrigido**: `message_sent` → `result.get('message_sent')`
- **Confirmações funcionais**: "sim" → resposta contextual adequada
- **Fluxo completo**: Confirmação → set_facts → mensagem usuário → clear_waiting
- **Pipeline robusto**: Confirmações interceptadas antes do orchestrator

### ✅ **Implementação #10: Correções Críticas + Melhorias na Página de Leads**
- **Filtros JSONB corrigidos**: Busca por leads com/sem conta funciona
- **Ações de lead**: Limpar sessão e deletar lead
- **Informações técnicas**: Debug melhorado com snapshot completo
- **Interface aprimorada**: Dark mode, responsividade e acessibilidade

### ✅ **Implementação #9: Sistema de Confirmação LLM-first V2 (Completo)**
- **ConfirmationGate**: LLM-first com fallback determinístico
- **AutomationHook**: Cria estado aguardando automaticamente
- **Actions estruturadas**: set_facts, send_message, clear_waiting
- **Testes completos**: Unitários e integração
- **Documentação atualizada**: Tutorial e melhorias implementadas

### ✅ **Implementação #8: Página de Leads no Studio**
- **Backend**: Endpoints `/api/leads` com filtros avançados
- **Frontend**: Página completa com tabela, filtros e modal de detalhes
- **Integração**: Reutilização de componentes existentes
- **Funcionalidades**: Paginação, ordenação, busca e ações de lead

### ✅ **Implementação #7: Sistema de Confirmação LLM-first**
- **ConfirmationGate**: Intercepta confirmações antes do intake
- **AutomationHook**: Cria estado aguardando automaticamente
- **Guardrails**: TTL, whitelist, confidence threshold
- **Fallback determinístico**: Para LLM falhas/timeouts
- **Testes**: Unitários e integração completos

### ✅ **Implementação #6: Correções Críticas**
- **Argument mismatch**: `handle_procedure_flow()` corrigido
- **Orchestrator**: Funções atualizadas para aceitar `contexto_lead`
- **Pipeline**: Fluxo de decisão funcionando corretamente
- **Testes**: Validação de correções implementadas

### ✅ **Implementação #5: Studio Frontend Completo**
- **Interface moderna**: React + TypeScript + Tailwind CSS
- **Páginas principais**: Dashboard, Procedimentos, Automações, Intake, Simulador
- **Integração backend**: Proxy Vite + React Query
- **Funcionalidades**: CRUD completo, simulação, visualização de dados

### ✅ **Implementação #4: Sistema de Automações YAML**
- **Catálogo de automações**: YAML estruturado com metadata
- **Sistema de procedimentos**: Funnels configuráveis
- **Orquestrador**: Seleção inteligente de automações
- **Integração**: Pipeline completo funcionando

### ✅ **Implementação #3: Pipeline de Decisão**
- **Orchestrator**: Lógica central de decisão
- **Flow handlers**: Procedimentos, dúvidas, fallbacks
- **Contexto persistente**: Estado do lead mantido
- **Integração**: Telegram + pipeline funcionando

### ✅ **Implementação #2: Integração Telegram**
- **Webhook handler**: Recebe mensagens do Telegram
- **Enriquecimento**: Snapshot do lead + histórico
- **Pipeline**: Integração com sistema de decisão
- **Testes**: Validação de integração

### ✅ **Implementação #1: Estrutura Base**
- **FastAPI**: Backend moderno e rápido
- **PostgreSQL**: Banco de dados robusto
- **SQLAlchemy**: ORM para persistência
- **Estrutura**: Arquitetura escalável definida

## 🚀 **Próximos Passos**

### ✅ **FASE 2: Intake Sempre-LLM (VALIDADA)**
- **Intake sempre-LLM**: Análise estruturada com intents, polarity, targets
- **Self-consistency**: Majority vote com 2 amostras
- **Validações blindadas**: Testes robustos com asserts de conteúdo
- **Logs estruturados**: Observabilidade completa
- **Schema válido**: Function calling sem erros 400
- **Agreement score**: Calculado baseado na concordância de polarity

### ✅ **FASE 3: Gate de Confirmação Retroativo (IMPLEMENTADA)**
- **Timeline leve**: Registro independente de expects_reply para detecção retroativa
- **Detecção retroativa**: Reconhece confirmações mesmo se hook falhar
- **Janela de tempo**: Configurável (GATE_RETROACTIVE_WINDOW_MIN=10min)
- **Idempotência**: Hash baseado em lead_id + mensagem normalizada
- **Lock por lead**: Previne processamento concorrente
- **Testes E2E**: Validação completa de cenários retroativos
- **Logs estruturados**: Observabilidade com `retro_active=true`

### ✅ **FASE 4: Orquestrador com Sinais LLM (IMPLEMENTADA)**
- **Proposta LLM**: Aceita sugestões do Intake quando catálogo vazio
- **Guardrails rigorosos**: Validação de catálogo + aplicabilidade + cooldown
- **Ordem de prioridade**: Catálogo → Proposta LLM → KB fallback
- **Integração com Intake**: Usa `llm_signals.propose_automations[0]`
- **Rejeição inteligente**: Detecta conflitos e cooldowns ativos
- **Testes E2E**: Validação de aceitação e rejeição de propostas
- **Logs estruturados**: `used_llm_proposal=true/false` com motivos

### **FASE 5: RAG Inteligente**
- **Heurística de uso**: Só RAG quando útil
- **Re-rank**: Melhorar qualidade de contexto
- **Filtros por lead**: Personalizar contexto
- **Performance**: Otimizar latência

### **FASE 6: Observabilidade Completa**
- **Métricas**: Tokens, custo, latency, agreement
- **Prometheus**: Métricas estruturadas
- **Idempotência**: Confirmar headers/chaves
- **Debug**: Logs detalhados para troubleshooting

### **FASE 7: Multi-modelo (Opcional)**
- **Segundo modelo**: Para high-stakes decisions
- **Arbitro**: Resolver divergências
- **Agreement score**: Medir concordância
- **Feature flags**: Controle granular