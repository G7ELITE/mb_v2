# Base de Conhecimento - ManyBlack V2

## Sobre o ManyBlack

O ManyBlack é uma plataforma de automação para atendimento e gestão de leads, focada em operações financeiras e de trading.

## Funcionalidades Principais

### 1. Automações
- Criação de fluxos automatizados de atendimento
- Respostas inteligentes baseadas em contexto
- Botões interativos para engagement

### 2. Procedures (Procedimentos)
- Definição de procedimentos operacionais
- Fluxos estruturados para processos internos
- Padronização de atendimento

### 3. RAG (Retrieval-Augmented Generation)
- Sistema de busca inteligente na base de conhecimento
- Respostas contextualizadas usando IA
- Integração com OpenAI para processamento de linguagem natural

### 4. Gestão de Leads
- Cadastro e acompanhamento de leads
- Histórico de interações
- Segmentação e qualificação

## Configurações

### APIs Integradas
- **OpenAI**: Processamento de linguagem natural
- **Telegram**: Bot para atendimento automatizado
- **PostgreSQL**: Banco de dados principal
- **Redis**: Cache e sessões

### Domínios
- **Produção**: https://equipe.manyblack.com
- **Desenvolvimento**: Via ngrok (ambiente local)

## Troubleshooting

### Problemas Comuns
1. **Erro 500 na API RAG**: Verificar se base de conhecimento existe
2. **Webhook Telegram**: Confirmar configuração da URL
3. **Performance**: Verificar cache Redis

### Logs
- Acessar logs via: `docker compose logs app`
- Health check: `/health`
- Documentação API: `/docs`

---

*Última atualização: Setembro 2025*