# Como Funciona o Caminho da Dúvida no ManyBlack V2

## ⚠️ **STATUS ATUAL DO SISTEMA**

**IMPORTANTE:** No momento, o sistema está em **configuração inicial**:
- ❌ Catálogo de automações vazio (`policies/catalog.yml`)
- ❌ Procedimentos vazios (`policies/procedures.yml`)
- ✅ Base de conhecimento funcionando (`policies/kb.md`)

**Resultado atual:** Sistema sempre usa fallback genérico para todas as mensagens:
> "🤖 Olá! Recebi sua mensagem: '[mensagem]' ✅ O sistema está processando sua solicitação..."

### 📊 O que está acontecendo nos logs (situação real):

**Lead manda:** "quero testar"
```
✅ Sistema recebe e normaliza mensagem
✅ Constrói snapshot do lead  
✅ Intake detecta intenção: "quero testar"
✅ Orquestrador classifica: PROCEDIMENTO
❌ Tenta executar procedimento "liberar_teste" 
❌ Procedimentos carregados: 0
❌ Procedimento não encontrado
❌ Retorna plano vazio (0 ações)
❌ Usa fallback: "Olá! Recebi sua mensagem..."
```

## O que acontece quando alguém faz uma pergunta?

**⚡ FUNCIONAMENTO COMPLETO** (quando automações e procedimentos estiverem configurados):

Quando um lead manda uma mensagem com dúvida pelo Telegram, o sistema passa por várias etapas para dar a melhor resposta possível. Vamos acompanhar esse caminho passo a passo.

## 📱 Passo 1: Lead Envia Mensagem

**Exemplo real:**
> João manda no Telegram: "como faço depósito na quotex?"

O sistema recebe essa mensagem através do webhook do Telegram e precisa processá-la.

---

## 🧠 Passo 2: Sistema Monta o "Perfil" do Lead 

Antes de responder, o sistema constrói um "retrato" do que sabe sobre João:

```
Perfil atual do João:
- Nome: João Silva
- Contas: Não sabemos se tem conta na Quotex ou Nyrion
- Depósito: Ainda não fez depósito
- Interesse em teste: Não manifestou
- Já foi explicado como funciona: Não
```

**Ao mesmo tempo**, o sistema busca informações relacionadas ao que João perguntou na nossa base de conhecimento:

```
Busca por "depósito na quotex" encontrou:
✅ Como fazer depósito (relevância: 85%)
✅ Informações da Quotex (relevância: 72%) 
✅ Processo de liberação (relevância: 68%)
```

---

## 🤖 Passo 3: Sistema Decide o Tipo de Interação

O sistema analisa a mensagem de João e percebe:
- Tem palavra "como" → é uma dúvida
- Não tem palavras como "quero testar" → não é interesse em procedimento
- **Conclusão:** É uma DÚVIDA que precisa ser respondida

---

## 📚 Passo 4: Buscando a Melhor Resposta

Agora começa a busca pela melhor resposta, seguindo esta ordem:

### 4.1 Primeiro: Procura em Automações Prontas
O sistema verifica se existe alguma resposta automática para "depósito na quotex".

**No nosso caso:** ⚠️ **SITUAÇÃO ATUAL** - Catálogo e procedimentos estão vazios (sistema em configuração inicial), então não encontra nada.

### 4.2 Segundo: Consulta Base de Conhecimento
Como não achou automação pronta, o sistema vai na base de conhecimento e monta uma resposta personalizada usando:
- O que sabemos sobre João (perfil dele)
- As informações que encontrou sobre depósito na Quotex

**O sistema "pensa" assim:**
```
"João está perguntando sobre depósito na Quotex. 
Pelo perfil dele:
- Ainda não tem conta confirmada
- Não fez depósito ainda  
- Não foi explicado o processo

Vou explicar o processo completo baseado na nossa KB."
```

---

## ⚡ Passo 5: Sistema Gera Resposta Inteligente

O robô cria uma resposta personalizada:

**Resposta criada:**
> 🤖 Oi João! Para fazer depósito na Quotex é bem simples:
> 
> 1️⃣ Primeiro você precisa criar sua conta na Quotex
> 2️⃣ Depois fazer o depósito mínimo de $10 (aceita PIX!)  
> 3️⃣ Me confirmar que fez o depósito
> 4️⃣ Aí eu te libero no grupo de sinais
> 
> Quer que eu te ajude a criar a conta na Quotex agora?

---

## 🔍 Passo 6: Verificação de Qualidade (Opcional)

Se houvesse automações no catálogo, o sistema faria uma verificação:
- **Compara** a resposta criada com automações similares
- **Se muito parecida** (score ≥ 80%): usa a automação (mais confiável)  
- **Se diferente** (score < 80%): usa a resposta criada e manda para revisão

---

## 📤 Passo 7: Envio da Resposta

O sistema envia a resposta para João via Telegram e registra tudo:
- Que tipo de pergunta foi
- Qual resposta foi dada
- Se foi automação ou resposta gerada
- Tempo que levou para processar

---

## 🎯 Exemplos Práticos de Diferentes Situações

### Situação 1: Pergunta Simples
**Lead pergunta:** "qual o depósito mínimo?"
**Sistema responde:** Resposta rápida da base de conhecimento sobre valores mínimos.

### Situação 2: Pergunta Complexa  
**Lead pergunta:** "como funciona o gale e qual a taxa de acerto do robô?"
**Sistema responde:** Resposta detalhada explicando estratégia Gale e estatísticas, usando múltiplas seções da KB.

### Situação 3: Pergunta Vaga
**Lead pergunta:** "oi"
**Sistema responde:** "Como posso te ajudar hoje?" (fallback amigável)

### Situação 4: Lead Já Conhecido
**Lead João (que já tem conta) pergunta:** "quando vem o próximo sinal?"
**Sistema responde:** Resposta personalizada considerando que ele já está liberado.

---

## ⏱️ Tempos de Resposta

O sistema é otimizado para responder rápido:
- **Perguntas simples:** ~0.5 segundos
- **Perguntas complexas:** ~1-2 segundos  
- **Máximo tolerado:** 3 segundos

Se passar do tempo limite, o sistema dá uma resposta padrão como:
> "🤖 Tive um pequeno problema técnico, mas estou funcionando. Como posso ajudar?"

---

## 🧰 Como o Sistema "Lembra" das Coisas

O sistema tem uma memória inteligente:

### Cache Rápido (60 segundos)
Se vários leads perguntam sobre "depósito" em pouco tempo, o sistema reutiliza a busca na base de conhecimento, respondendo mais rápido.

### Perfil do Lead
Cada lead tem um perfil que vai sendo construído:
- Primeira vez que fala com o bot
- Se já demonstrou interesse em teste
- Se já fez depósito
- Última automação que recebeu

### Histórico de Conversas
O sistema lembra das últimas mensagens para dar contexto nas respostas.

---

## 🛡️ O que Acontece Quando Algo Dá Errado?

O sistema tem várias proteções:

### Base de Conhecimento Corrompida
**Se** o arquivo `kb.md` estiver com problema:
**Então** sistema usa resposta padrão: "Não entendi bem sua mensagem. Pode me explicar melhor?"

### Demora na Resposta da IA
**Se** a IA demorar mais que 3 segundos:
**Então** sistema cancela e usa resposta padrão amigável.

### Catálogo Vazio  
**Se** não houver automações configuradas:
**Então** sistema sempre vai para base de conhecimento.

### Lead Manda Mensagem Muito Curta
**Se** lead manda só "ok" sem contexto:
**Então** sistema pede mais detalhes: "Pode me dar um pouco mais de detalhes? Assim posso te ajudar melhor! 😊"

---

## 📊 Como Saber Se Está Funcionando?

O sistema registra tudo nos logs para acompanharmos:

```
✅ Mensagem recebida de João (ID: 123456789)
✅ Perfil montado em 50ms  
✅ Busca na KB encontrou 3 resultados
✅ Resposta gerada em 800ms
✅ Mensagem enviada com sucesso
📊 Tempo total: 1.2 segundos
```

---

## 🔧 Para Desenvolvedores: Como Testar

### Teste Rápido via Terminal
```bash
# Simular mensagem do João perguntando sobre depósito
curl -X POST "http://localhost:8000/channels/telegram/webhook?secret=SEU_SECRET" \
  -H "Content-Type: application/json" \
  -d '{
    "update_id": 1,
    "message": {
      "from": {"id": 123456789, "first_name": "João"},
      "chat": {"id": 123456789},
      "text": "como faço depósito na quotex?"
    }
  }'
```

### Ver Logs em Tempo Real
```bash
tail -f backend.log
```

### Testar Diferentes Tipos de Dúvida
- "como funciona o robô?" → Resposta explicativa
- "qual o valor mínimo?" → Resposta específica  
- "oi" → Resposta de boas-vindas
- "não entendi nada" → Pedido de esclarecimento

---

## 📈 Melhorias Futuras

O sistema está preparado para evoluir:

1. **Mais Automações:** Conforme adicionamos respostas prontas no catálogo, menos dependemos da IA
2. **Respostas Mais Inteligentes:** IA aprende com feedbacks e fica melhor
3. **Personalização:** Respostas cada vez mais adequadas ao perfil de cada lead
4. **Velocidade:** Cache mais inteligente para respostas ainda mais rápidas

---

## 💡 Resumo para Gestores

**O que o sistema faz bem:**
- ✅ Responde dúvidas automaticamente 24/7
- ✅ Personaliza respostas baseado no perfil do lead
- ✅ É rápido (1-2 segundos na maioria dos casos)
- ✅ Tem fallbacks seguros se algo der errado
- ✅ Registra tudo para análise posterior

**Onde pode melhorar:**
- 📝 Adicionar mais automações prontas (mais confiáveis)
- 📊 Análise dos logs para identificar dúvidas frequentes  
- 🎯 Ajustar base de conhecimento baseado nas perguntas reais

**Impacto no negócio:**
- 🚀 Leads são atendidos imediatamente
- 💰 Reduz necessidade de atendimento manual
- 📈 Melhora experiência do usuário
- 🎯 Padroniza informações sobre o produto

---

## 🛠️ **COMO CORRIGIR A SITUAÇÃO ATUAL**

### Para que o sistema funcione conforme documentado, é preciso configurar:

#### 1. **Procedimento de Teste** (`policies/procedures.yml`)
```yaml
---
- id: liberar_teste
  name: "Liberar Acesso de Teste"
  steps:
    - type: "send_message"
      text: "🎯 Ótimo! Vou te ajudar a liberar o teste gratuito do ManyBlack.\n\nPrimeiro, você precisa criar uma conta em uma das corretoras parceiras:\n\n🔹 **Quotex** (Recomendada para iniciantes)\n- Depósito mínimo: $10\n- Aceita PIX\n- Interface em português\n\n🔹 **Nyrion** (Para experientes)\n- Depósito mínimo: $25\n- Ferramentas avançadas\n\nQual corretora você prefere?"
      buttons:
        - label: "📊 Quotex ($10)"
          kind: "callback"
          set_facts:
            broker_chosen: "quotex"
        - label: "📈 Nyrion ($25)"
          kind: "callback"  
          set_facts:
            broker_chosen: "nyrion"
```

#### 2. **Automações de Dúvida** (`policies/catalog.yml`)
```yaml
---
- id: deposito_quotex
  topic: "depósito quotex"
  eligibility: "sempre"
  priority: 0.8
  output:
    type: "send_message"
    text: "💰 Para depositar na Quotex:\n\n1️⃣ Acesse sua conta Quotex\n2️⃣ Vá em 'Depósito'\n3️⃣ Escolha PIX (mais rápido)\n4️⃣ Valor mínimo: $10\n5️⃣ Confirme comigo após depositar\n\n✅ Precisa de ajuda para criar a conta?"

- id: como_funciona
  topic: "como funciona"
  eligibility: "sempre"  
  priority: 0.7
  output:
    type: "send_message"
    text: "🤖 O ManyBlack é um robô de sinais para opções binárias:\n\n📊 **Opera em M5** (gráficos 5 minutos)\n🎯 **75-80% de precisão** com estratégia Gale\n⚡ **Sinais automáticos** via Telegram\n💰 **Depósito mínimo:** $10 (Quotex) ou $25 (Nyrion)\n\nQuer liberar seu teste gratuito?"
```

#### 3. **Após Configurar**
- ✅ "quero testar" → Executa procedimento completo
- ✅ "como depositar" → Resposta automática do catálogo  
- ✅ Dúvidas não mapeadas → Base de conhecimento + IA
- ✅ Respostas personalizadas e inteligentes

### 🚀 **Resultado Esperado Após Configuração**

**Lead:** "quero testar"
**Bot:** "🎯 Ótimo! Vou te ajudar a liberar o teste gratuito do ManyBlack..." + botões interativos

**Lead:** "como depositar na quotex?"  
**Bot:** "💰 Para depositar na Quotex: 1️⃣ Acesse sua conta..." + instruções completas
