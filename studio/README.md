# ManyBlack Studio

🎨 **Interface visual amigável em português brasileiro** para configuração e teste do ManyBlack V2 - Sistema inteligente de orquestração de leads com automações em linguagem natural.

## 🎯 Visão Geral

O ManyBlack Studio foi desenvolvido especificamente para **equipes operacionais brasileiras** (não técnicas) configurarem funis de conversação, automações e testarem cenários de forma visual e intuitiva, sem necessidade de programação ou edição de arquivos técnicos.

### ✨ Características da Interface

- **🇧🇷 100% em Português Brasileiro** - Termos técnicos traduzidos e contextualizados
- **🌙 Modo Escuro Completo** - Interface moderna com alto contraste para longas jornadas de trabalho
- **📱 Responsiva & Acessível** - Funciona perfeitamente em desktop, tablet e mobile
- **🎛️ Sidebar Colapsável** - Maximize a área de trabalho quando necessário
- **⚡ Blocos Colapsáveis** - Visualize apenas as informações relevantes no momento
- **🔍 Auto-complete Inteligente** - Sugestões contextuais em português natural

### 🚀 Funcionalidades Principais

- **📊 Dashboard** - Visão geral em tempo real do sistema com métricas importantes
- **🔄 Procedimentos** - Editor visual de funis com etapas sequenciais e condições em português
- **⚡ Automações** - Criação e gerenciamento de mensagens automáticas com botões interativos
- **🎯 Intake & Âncoras** - Configuração de palavras-chave e detecção de intenções dos leads
- **🧪 Simulador** - Teste completo de conversas antes de publicar, com modo desenvolvedor
- **🚀 Publicação** - Deploy seguro de configurações com validação prévia

## 🏗️ Arquitetura Técnica

```
studio/
├── src/
│   ├── components/          # Componentes reutilizáveis
│   │   ├── Layout.tsx       # Layout principal com sidebar colapsável
│   │   ├── CollapsibleSection.tsx  # Seções com botões de ação
│   │   ├── AutocompleteInput.tsx   # Input inteligente 
│   │   └── ThemeToggle.tsx         # Alternador modo escuro
│   ├── contexts/            # Contextos React
│   │   └── ThemeContext.tsx # Gerenciamento do tema dark/light
│   ├── pages/              # Páginas da aplicação
│   │   ├── Dashboard.tsx   # Visão geral com métricas em tempo real
│   │   ├── Procedures.tsx  # Listagem e gerenciamento de procedimentos
│   │   ├── Automations.tsx # CRUD de automações de mensagens
│   │   ├── Intake.tsx      # Configuração de intake e âncoras
│   │   ├── Simulator.tsx   # Simulador de conversas com modo dev
│   │   └── Publication.tsx # Deploy de configurações
│   ├── services/           # Integração com APIs
│   │   └── api.ts         # Cliente HTTP para ManyBlack V2 Backend
│   ├── types/             # Definições TypeScript
│   │   └── index.ts      # Interfaces de Procedures, Automations, etc.
│   └── hooks/            # React Hooks customizados
└── package.json          # Dependências e scripts
```

### 🛠️ Stack Tecnológica

- **⚡ Vite** - Build tool ultra-rápido
- **⚛️ React 18** - UI Library com Hooks
- **📘 TypeScript** - Tipagem estática
- **🎨 Tailwind CSS v4** - Framework CSS utility-first
- **🧭 React Router** - Roteamento client-side
- **📋 React Hook Form** - Gerenciamento de formulários
- **🔄 React Query** - Cache e sincronização de dados
- **🎛️ Headless UI** - Componentes acessíveis
- **🎯 Heroicons** - Ícones SVG otimizados

## 🚀 Instalação e Execução

### 📋 Pré-requisitos

- **Node.js 18+** (recomendado LTS)
- **npm** ou **yarn** 
- **Backend ManyBlack V2** rodando em `http://localhost:8000`
- **Virtual environment** ativo (`.venv`) no diretório raiz do projeto

### ⚙️ Configuração Inicial

```bash
# 1. Navegue até o diretório do studio
cd studio/

# 2. Instale as dependências
npm install

# 3. Configure as variáveis de ambiente (se necessário)
cp .env.example .env

# 4. Execute em modo desenvolvimento
npm run dev
```

### 🌐 Acessando a Aplicação

- **Interface Principal**: `http://localhost:5173`
- **Modo Hot Reload**: Ativo por padrão em desenvolvimento
- **Backend API**: Certifique-se que `http://localhost:8000` está acessível

### 🛠️ Scripts Disponíveis

```bash
npm run dev       # Servidor de desenvolvimento (porta 5173)
npm run build     # Build para produção
npm run preview   # Preview do build de produção
npm run lint      # Verificação de código com ESLint
npm run type-check # Verificação de tipos TypeScript
```

### Instalação

```bash
# Instalar dependências
npm install

# Executar em modo desenvolvimento
npm run dev

# Build para produção
npm run build
```

### Acesso

- **Desenvolvimento**: http://localhost:5173
- **Backend**: http://localhost:8000 (deve estar rodando)

## 🎨 Design System

### Cores Principais
- **Primary**: Blue-600 (#2563eb)
- **Secondary**: Gray-600 (#4b5563)
- **Success**: Green-600 (#059669)
- **Warning**: Yellow-600 (#d97706)
- **Error**: Red-600 (#dc2626)

### Componentes Base
- **Botões**: `.btn-primary`, `.btn-secondary`
- **Cards**: `.card`
- **Inputs**: `.input-field`
- **Navegação**: `.sidebar-nav-item`

## 📋 Funcionalidades Implementadas

### ✅ Concluído

1. **Dashboard**
   - Cards de resumo do sistema
   - Ações rápidas
   - Status de saúde do backend
   - Atividade recente

2. **Simulador**
   - Interface para testar mensagens
   - Helpers para configurar snapshot do lead
   - Modo dev com logs técnicos
   - Integração real com backend
   - Roteiros de teste sugeridos

3. **Procedimentos**
   - Lista visual de procedimentos existentes
   - Editor com drag-and-drop (conceitual)
   - Modal para configurar passos
   - Autocomplete para condições e automações
   - Validações amigáveis em PT-BR

4. **Automações**
   - CRUD visual de automações
   - Preview de mensagens e botões
   - Configuração de prioridade e cooldown
   - Filtros por tópico e prioridade

5. **Intake & Âncoras**
   - Configuração de thresholds
   - Editor de âncoras por grupo
   - Patterns regex para IDs
   - Métricas de performance

6. **Componentes Base**
   - Layout responsivo com sidebar
   - Sistema de autocomplete inteligente
   - Modais e formulários com validação
   - Integração com React Query

### 🔄 Em Desenvolvimento

- Editor de automações (criar/editar)
- Sistema de publicação
- Histórico de atividades
- Métricas avançadas

## 🎯 Princípios UX

### Para Equipe Operacional
- **Menos campos possível** - apenas o essencial
- **Nomes simples** - português claro e direto
- **Autocomplete everywhere** - não digitar, apenas escolher
- **Simulação obrigatória** - testar antes de publicar
- **Mensagens amigáveis** - validações em português

### Para Desenvolvedores
- **Modo Dev** - logs técnicos detalhados
- **Integração real** - endpoints do backend
- **Extensibilidade** - componentes reutilizáveis
- **TypeScript** - tipagem forte em todo código

## 🔧 Integração com Backend

### Endpoints Utilizados
- `GET /health` - Status do sistema
- `POST /engine/decide` - Simulação de decisões
- `GET /channels/telegram/info` - Info do canal
- `POST /api/tools/apply_plan` - Execução real (opcional)

### Dados Mock
Enquanto o backend não tem CRUD completo, usa dados mock para:
- Lista de procedimentos
- Lista de automações  
- Configurações do intake

## 🧪 Como Testar

### Fluxo Básico
1. Acesse o **Dashboard**
2. Vá para **Simulador**
3. Digite: "quero testar o robô"
4. Observe a resposta do sistema
5. Use helpers para simular estados do lead
6. Teste diferentes cenários

### Procedimentos
1. Acesse **Procedimentos**
2. Clique "Criar Procedimento"
3. Configure nome e passos
4. Use autocomplete nas condições
5. Teste no simulador
6. Salve como rascunho

### Automações
1. Acesse **Automações**
2. Visualize automações existentes
3. Teste individualmente no simulador
4. Observe prioridades e cooldowns

## 📊 Métricas e Monitoramento

O Studio coleta métricas básicas:
- Tempo de resposta do backend
- Taxa de sucesso das simulações
- Uso de funcionalidades
- Erros de integração

## 🤝 Contribuindo

### Estrutura de Componentes
```typescript
// Componente padrão
interface ComponentProps {
  // Props tipadas
}

export default function Component({ }: ComponentProps) {
  // Hooks no topo
  // Estados
  // Handlers
  // Render
}
```

### Padrões de API
```typescript
// Sempre usar try/catch
try {
  const result = await apiService.method();
  // Handle success
} catch (error) {
  // Handle error
  console.error('Contexto:', error);
}
```

## 📦 Dependências Principais

- **React 18** - Framework base
- **TypeScript** - Tipagem
- **Tailwind CSS** - Styling
- **React Router** - Navegação
- **React Hook Form** - Formulários
- **React Query** - Cache HTTP
- **Headless UI** - Componentes
- **Heroicons** - Ícones

## 🔮 Roadmap

### v1.1
- [ ] Editor completo de automações
- [ ] Sistema de versionamento
- [ ] Export/import de configurações

### v1.2  
- [ ] Dashboards avançados
- [ ] Métricas em tempo real
- [ ] Notificações push

### v2.0
- [ ] Múltiplos ambientes
- [ ] Controle de acesso
- [ ] API própria

---

**ManyBlack Studio** - Tornando a configuração de IA conversacional acessível para todos! 🚀