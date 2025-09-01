# 🎓 Tutorial ManyBlack Studio
*Guia Completo para a Equipe Operacional*

---

## 📖 Índice

1. [Primeiros Passos](#-primeiros-passos)
2. [🏠 Dashboard - Visão Geral](#-dashboard---visão-geral)
3. [🔄 Procedimentos - Criando Funis](#-procedimentos---criando-funis)
4. [⚡ Automações - Mensagens Automáticas](#-automações---mensagens-automáticas)
5. [🎯 Intake & Âncoras - Capturando Intenções](#-intake--âncoras---capturando-intenções)
6. [🧪 Simulador - Testando Conversas](#-simulador---testando-conversas)
7. [🚀 Publicação - Enviando para Produção](#-publicação---enviando-para-produção)
8. [💡 Dicas e Boas Práticas](#-dicas-e-boas-práticas)

---

## 🚀 Primeiros Passos

### Como Acessar o Sistema

1. **Abra seu navegador** e acesse: `http://localhost:3000`
2. **Verifique se o backend está rodando** - deve aparecer "Sistema Saudável" no dashboard
3. **Explore o modo escuro** - clique no ícone da lua no canto superior direito

### Interface Principal

- **📱 Sidebar à esquerda**: Navegação entre as páginas
- **🌙 Botão de tema**: Alterna entre modo claro e escuro
- **📦 Blocos colapsáveis**: Clique para expandir/contrair seções
- **⚙️ Botões de ação**: Sempre visíveis nos cantos dos blocos

---

## 🏠 Dashboard - Visão Geral

O **Dashboard** é sua central de controle. Aqui você vê o "pulso" do sistema em tempo real.

### O que você encontra:

#### 📊 Cards de Estatísticas
- **Leads Ativos**: Quantas pessoas estão sendo atendidas agora
- **Mensagens/Hora**: Velocidade de resposta do sistema
- **Taxa de Conversão**: % de leads que completaram algum funil
- **Tempo Médio**: Quanto tempo demora para um lead ser atendido

#### 🔍 Saúde do Sistema
- **Verde**: Tudo funcionando perfeitamente
- **Vermelho**: Algo está com problema (chame o time técnico)

#### 🎯 Ações Rápidas
- **Criar Procedimento**: Botão para criar um novo funil
- **Testar Conversa**: Acesso direto ao simulador
- **Ver Relatórios**: Estatísticas detalhadas

### ✅ Exemplo Prático
*"João entra no sistema às 14h. No dashboard, vejo que temos 12 leads ativos e taxa de conversão de 85%. Está tudo funcionando bem!"*

---

## 🔄 Procedimentos - Criando Funis

**Procedimentos** são como "receitas" que o robô segue para guiar cada lead até o objetivo final.

### 🎯 Conceito Principal
Imagine um funil de vendas tradicional, mas automatizado. Cada **passo** do procedimento verifica se o lead cumpriu uma condição. Se não, o robô executa uma ação para ajudar.

### 📋 Como Funciona na Prática

#### Estrutura de um Procedimento:
1. **Título**: Ex: "Liberar acesso ao teste"
2. **Descrição**: O que este procedimento faz
3. **Passos**: Lista ordenada de verificações
4. **Configurações**: Tempo limite e cooldown

#### 🔧 Criando um Novo Procedimento

**Passo 1: Informações Básicas**
- **Nome**: Use algo descritivo como "Onboarding para novos leads"
- **Descrição**: Explique em 1-2 frases o objetivo

**Passo 2: Definir os Passos**
Cada passo tem:
- **Nome do passo**: Ex: "Lead concordou em depositar"
- **Condição**: Como verificar (em português natural)
- **Se não satisfeito**: Qual automação executar

### ✅ Exemplo Real - "Liberar Teste do Robô"

```
Passo 1: "Concorda em depositar"
Condição: "o lead concordou em depositar ou já depositou"
Se não: Executar automação "ask_deposit_for_test"

Passo 2: "Tem conta"
Condição: "tem conta em alguma corretora suportada"
Se não: Executar automação "signup_link"

Passo 3: "Depósito confirmado"
Condição: "depósito confirmado"
Se não: Executar automação "prompt_deposit"

Passo 4: "Liberar acesso"
Condição: "todas as etapas anteriores cumpridas"
Ação: Executar automação "trial_unlock"
```

### 🎛️ Usando a Interface

1. **Clique em "Criar Procedimento"**
2. **Preencha o formulário** com as informações básicas
3. **Adicione passos um por um** usando o botão "+"
4. **Use o simulador** para testar antes de publicar
5. **Salve como rascunho** ou **publique** quando estiver pronto

### 💡 Dicas Importantes
- **Sempre teste no simulador primeiro**
- **Use linguagem natural nas condições** (ex: "lead tem mais de 18 anos")
- **Configure timeouts** para evitar leads "presos"
- **Mantenha procedimentos simples** - máximo 5-6 passos

---

## ⚡ Automações - Mensagens Automáticas

**Automações** são as mensagens que o robô envia automaticamente. Cada automação é uma "resposta inteligente" para uma situação específica.

### 🎯 Quando Usar Automações

- **Perguntas frequentes**: "Como funciona o robô?"
- **Solicitações de ação**: "Faça um depósito para continuar"
- **Confirmações**: "Parabéns! Seu acesso foi liberado"
- **Direcionamentos**: "Clique aqui para criar sua conta"

### 📝 Anatomia de uma Automação

#### Informações Básicas:
- **ID**: Nome único (ex: `ask_deposit_for_test`)
- **Tópico**: Categoria (ex: "teste", "conta", "depósito")
- **Elegibilidade**: Quando usar esta automação
- **Prioridade**: 0.0 a 1.0 (1.0 = máxima prioridade)

#### Conteúdo da Mensagem:
- **Texto**: A mensagem que será enviada
- **Botões** (opcional): Ações que o lead pode clicar
- **Cooldown**: Tempo entre execuções

### ✅ Exemplo Real - Pedindo Depósito

```
ID: ask_deposit_for_test
Tópico: teste
Elegibilidade: "não concordou em depositar e não depositou"
Prioridade: 0.85

Mensagem:
"Para liberar o teste, você consegue fazer um pequeno depósito? 💰"

Botões:
[Sim, consigo] → Marca "agreements.can_deposit = true"
[Como deposito?] → Abre link de ajuda
```

### 🎛️ Criando uma Nova Automação

**Passo 1: Configuração Básica**
1. **ID único**: Use formato `acao_contexto` (ex: `explain_robot_benefits`)
2. **Tópico**: Escolha entre: teste, conta, depósito, suporte, etc.
3. **Prioridade**: 
   - 0.9-1.0: Urgente (ex: liberação de acesso)
   - 0.7-0.8: Importante (ex: criar conta)
   - 0.5-0.6: Informativa (ex: explicar benefícios)

**Passo 2: Elegibilidade (Muito Importante!)**
Escreva em português natural **quando** esta automação deve ser usada:
- ✅ Bom: "lead não tem conta e quer fazer teste"
- ✅ Bom: "já depositou mas ainda não criou conta"
- ❌ Ruim: "novo lead" (muito vago)

**Passo 3: Conteúdo da Mensagem**
- **Use emoji** para deixar mais amigável 😊
- **Seja direto** - máximo 2-3 frases
- **Inclua call-to-action** claro

**Passo 4: Botões (Se Necessário)**
Tipos de botão:
- **Callback**: Atualiza informações do lead
- **URL**: Abre um link externo
- **Procedure**: Inicia um procedimento

### 💡 Dicas para Boas Automações
- **Teste sempre no simulador** com diferentes cenários
- **Use cooldown** para evitar spam (mínimo 2h)
- **Mantenha mensagens curtas** e objetivas
- **Crie botões úteis** que realmente ajudem o lead

---

## 🎯 Intake & Âncoras - Capturando Intenções

O **Intake** é o "cérebro" que entende o que o lead está querendo. As **âncoras** são palavras-chave que ajudam a identificar a intenção.

### 🧠 Como Funciona o Intake

1. **Lead envia mensagem**: "Oi, quero saber sobre o robô"
2. **Intake analisa**: Identifica palavras como "robô", "quero saber"
3. **Classifica intenção**: "Dúvida sobre o produto"
4. **Orquestrador decide**: Busca automação apropriada
5. **Resposta enviada**: Explicação sobre o robô

### ⚙️ Configurações do Intake

#### 🎚️ Precisão vs. Custo
- **Slider esquerda (econômico)**: Mais rápido, menos preciso
- **Slider direita (preciso)**: Mais lento, mais assertivo
- **Recomendado**: Posição 75% para bom equilíbrio

#### 🔍 Palavras de Intenção
Adicione palavras que indicam que o lead quer algo específico:
- **Teste**: "teste", "testar", "experimentar", "demo"
- **Conta**: "conta", "cadastro", "registrar", "criar"
- **Depósito**: "depositar", "transferir", "investir", "aplicar"
- **Suporte**: "ajuda", "problema", "dúvida", "socorro"

#### 🆔 Identificadores de Conta
Padrões que identificam IDs de contas:
- **Quotex**: `\b[a-zA-Z0-9]{6,16}\b` (alfanumérico, 6-16 caracteres)
- **IQ Option**: `\b\d{8,12}\b` (apenas números, 8-12 dígitos)
- **Email**: `[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}`

### 📊 Métricas de Performance

Monitor importante para acompanhar:
- **Taxa de Acerto**: % de intenções identificadas corretamente
- **Tempo Médio**: Quanto demora para processar
- **Falsos Positivos**: Quando identifica errado
- **Falsos Negativos**: Quando não identifica

### ✅ Exemplo de Configuração Intake

```
Precisão vs. Custo: 75%

Palavras de Intenção:
- Teste: teste, testar, demo, experimentar, prova
- Conta: conta, cadastro, registro, criar conta
- Depósito: depositar, investir, aplicar, transferir
- Dúvida: dúvida, ajuda, como, quando, onde

Identificadores:
- Quotex ID: \b[a-zA-Z0-9]{6,16}\b
- Email: [\w\.-]+@[\w\.-]+\.\w+
```

### 💡 Dicas para Otimizar o Intake
- **Monitore as métricas** semanalmente
- **Adicione palavras novas** conforme identifica padrões
- **Teste diferentes configurações** no simulador
- **Ajuste a precisão** baseado no volume vs. qualidade

---

## 🧪 Simulador - Testando Conversas

O **Simulador** é seu ambiente de testes. Aqui você pode simular conversas reais **antes** de publicar qualquer mudança.

### 🎯 Por que Usar o Simulador

- **Evita erros em produção**: Teste antes que leads reais vejam
- **Valida fluxos completos**: Do primeiro contato até a conversão
- **Testa cenários extremos**: E se o lead fizer algo inesperado?
- **Modo desenvolvedor**: Veja logs técnicos detalhados

### 🎮 Como Usar

#### Iniciando uma Simulação

1. **Vá para "Simulador"** no menu lateral
2. **Escolha um cenário**:
   - Novo lead (primeira interação)
   - Lead existente (continuar conversa)
   - Cenário específico (ex: "lead com conta mas sem depósito")

3. **Configure o perfil do lead**:
   - Tem conta? Em qual corretora?
   - Já depositou? Quanto?
   - Concordou com termos?
   - Histórico de interações

#### Durante a Simulação

- **Digite mensagens** como se fosse o lead
- **Veja as respostas** do robô em tempo real
- **Clique nos botões** para testar ações
- **Acompanhe o progresso** nos procedimentos

#### 🛠️ Modo Desenvolvedor

Ative para ver informações técnicas:
- **Logs de processamento**: Como o Intake analisou a mensagem
- **Fatos identificados**: O que o sistema "entendeu"
- **Automações consideradas**: Quais foram avaliadas
- **Decisão do orquestrador**: Por que escolheu X em vez de Y

### ✅ Cenários de Teste Recomendados

#### 1. Lead Novo Interessado
```
Mensagem: "Oi, quero saber sobre o robô"
Esperado: Explicação do robô + pergunta sobre teste
```

#### 2. Lead Quer Testar
```
Mensagem: "Quero testar o robô"
Esperado: Verificar se tem conta e se pode depositar
```

#### 3. Lead com Conta
```
Perfil: Tem conta Quotex, ID: ABC123
Mensagem: "Tenho conta, quero o teste"
Esperado: Pedir depósito para liberar
```

#### 4. Lead Depositou
```
Perfil: Tem conta, depositou $50
Mensagem: "Já depositei, onde está o robô?"
Esperado: Liberar acesso imediatamente
```

#### 5. Lead Confuso
```
Mensagem: "Não entendi nada, como funciona?"
Esperado: Explicação simples + oferecer ajuda
```

### 💡 Boas Práticas de Teste

- **Teste TODOS os procedimentos** antes de publicar
- **Simule leads "difíceis"** que fazem perguntas estranhas
- **Verifique botões e links** - clique em tudo
- **Use modo dev** quando algo não funcionar como esperado
- **Documente bugs** e reporte para o time técnico

---

## 🚀 Publicação - Enviando para Produção

A **Publicação** é onde você "liga" suas mudanças para que leads reais vejam. ⚠️ **Cuidado**: tudo que publicar afeta o sistema real!

### 🔄 Fluxo de Publicação

#### 1. Preparação
- ✅ **Testou no simulador?** Todos os cenários importantes
- ✅ **Revisou textos?** Gramática, tom, emojis adequados
- ✅ **Validou links?** Todos funcionam corretamente
- ✅ **Verificou cooldowns?** Não vão fazer spam

#### 2. Preview das Mudanças
Antes de publicar, veja:
- **Automações novas/alteradas**: O que será adicionado
- **Procedimentos modificados**: Quais fluxos mudam
- **Configurações do intake**: Ajustes na detecção

#### 3. Publicação
- **Backup automático**: Sistema salva estado atual
- **Deploy gradual**: Mudanças são aplicadas uma por vez
- **Monitoramento**: Acompanha se tudo funcionou

#### 4. Validação Pós-Deploy
- **Teste rápido**: Simulate uma conversa real
- **Monitor dashboard**: Veja se métricas estão normais
- **Primeiro lead real**: Acompanhe cuidadosamente

### ⚠️ Cuidados Importantes

#### Antes de Publicar:
- **NUNCA publique sem testar** no simulador
- **Evite horários de pico** (9h-18h em dias úteis)
- **Comunique o time** sobre mudanças grandes
- **Tenha um plano B** caso algo dê errado

#### Erros Comuns:
- ❌ Automação com prioridade muito alta (spam)
- ❌ Condições muito vagas ("lead novo")
- ❌ Links quebrados ou expirados
- ❌ Mensagens muito longas ou confusas
- ❌ Cooldown muito baixo (menos de 1h)

### 🚨 Em Caso de Emergência

Se algo der errado após publicar:
1. **Acesse o dashboard** - veja se o sistema está saudável
2. **Verifique os logs** no modo desenvolvedor
3. **Use o botão "Rollback"** para voltar ao estado anterior
4. **Chame o time técnico** se o problema persistir

### ✅ Checklist de Publicação

```
□ Todas as automações testadas no simulador
□ Procedimentos validados com diferentes cenários
□ Textos revisados (gramática, tom, emojis)
□ Links e botões funcionando
□ Cooldowns configurados adequadamente
□ Time avisado sobre mudanças significativas
□ Plano de rollback definido
□ Monitoramento pós-deploy preparado
```

---

## 💡 Dicas e Boas Práticas

### 🎯 Estratégias Gerais

#### Para Automações:
- **Seja humano**: Use linguagem natural e amigável
- **Seja direto**: Máximo 2-3 frases por mensagem
- **Use emojis**: Mas com moderação (1-2 por mensagem)
- **Teste muito**: Antes de publicar qualquer coisa

#### Para Procedimentos:
- **Mantenha simples**: Máximo 5-6 passos
- **Use português natural**: "lead tem mais de 18 anos"
- **Configure timeouts**: Evite leads presos no funil
- **Documente bem**: Descrições claras do objetivo

#### Para o Intake:
- **Monitore métricas**: Ajuste baseado em dados reais
- **Adicione palavras**: Conforme identifica padrões novos
- **Balance precisão vs. custo**: 70-80% é um bom meio termo
- **Teste cenários edge**: Mensagens estranhas ou ambíguas

### 🔧 Troubleshooting Comum

#### "Lead não está recebendo resposta"
1. Verifique se o intake está identificando a intenção
2. Confirme se existe automação para essa situação
3. Veja se a elegibilidade está muito restritiva
4. Teste no simulador com o perfil exato do lead

#### "Robô enviando mensagem errada"
1. Revise a prioridade das automações
2. Confirme se as condições de elegibilidade estão corretas
3. Verifique se não há conflito entre automações
4. Use o modo desenvolvedor para entender a decisão

#### "Procedimento não avança"
1. Teste cada passo individualmente no simulador
2. Verifique se as condições estão em português claro
3. Confirme se os fatos estão sendo coletados corretamente
4. Ajuste timeouts se necessário

### 📈 Otimização de Performance

#### Monitore Estas Métricas:
- **Taxa de conversão por procedimento**: Qual está funcionando melhor?
- **Tempo médio de resposta**: Está dentro do aceitável?
- **Taxa de abandono**: Em que ponto leads desistem?
- **Satisfação qualitativa**: Leads parecem satisfeitos?

#### Melhoria Contínua:
- **Análise semanal**: Revise métricas e ajuste
- **A/B testing**: Teste versões diferentes de mensagens
- **Feedback do time**: Colete opinões dos operadores
- **Monitore concorrência**: Como outros estão se comunicando?

### 🤝 Colaboração com o Time

#### Com Desenvolvedores:
- **Reporte bugs** com cenários detalhados para reproduzir
- **Sugira melhorias** baseadas na experiência de uso
- **Participe de reuniões** de planejamento de novas features

#### Com Vendas/Marketing:
- **Compartilhe insights** sobre o que os leads perguntam
- **Alinhe tom de voz** entre automações e outras comunicações
- **Valide ofertas** antes de criar automações

#### Com Suporte:
- **Documente FAQ** para criar automações preventivas
- **Identifique pain points** comuns dos leads
- **Crie fluxos de escalação** quando automação não resolve

---

## 🎓 Conclusão

O **ManyBlack Studio** é uma ferramenta poderosa que coloca o controle da conversação automatizada nas suas mãos. Com ele, você pode:

- ✅ **Criar funis inteligentes** que guiam leads até a conversão
- ✅ **Automatizar respostas** para dúvidas e solicitações comuns  
- ✅ **Testar tudo** antes que leads reais vejam
- ✅ **Monitorar performance** e otimizar continuamente
- ✅ **Colaborar com o time** de forma mais eficiente

### 🚀 Próximos Passos

1. **Explore cada página** seguindo este tutorial
2. **Faça seus primeiros testes** no simulador
3. **Crie uma automação simples** e publique
4. **Configure o intake** para seu contexto
5. **Monte seu primeiro procedimento** completo
6. **Monitore as métricas** e otimize

**Lembre-se**: a prática leva à perfeição. Quanto mais você usar o sistema, mais eficiente será em criar conversas automatizadas que realmente convertem! 🎯

---

*💌 Dúvidas? Entre em contato com o time técnico ou consulte a documentação técnica em `README-PROJECT.md`*
