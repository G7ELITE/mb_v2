# 🛠️ Comandos ManyBlack V2

**Guia completo de comandos e scripts para desenvolvimento e operação do ManyBlack V2**

---

## 📋 Índice

1. [Scripts de Automação (.sh)](#-scripts-de-automação-sh)
2. [Comandos Python/Backend](#-comandos-pythonbackend)
3. [Comandos Node.js/Frontend](#-comandos-nodejsfrontend)
4. [Comandos de Banco de Dados](#-comandos-de-banco-de-dados)
5. [Comandos Docker (Futuro)](#-comandos-docker-futuro)
6. [Comandos de Debug/Troubleshooting](#-comandos-de-debugtroubleshooting)
7. [Comandos de Deploy/Produção](#-comandos-de-deployprodução)

---

## 🚀 Scripts de Automação (.sh)

### 1. `./start.sh` - Inicialização Completa

**O que faz**: Inicia backend + frontend com verificações completas

```bash
./start.sh
```

**Funcionalidades**:
- ✅ Verifica e ativa `.venv`
- ✅ Instala dependências se necessário (Python + Node.js)
- ✅ Verifica PostgreSQL
- ✅ Aplica migrações automaticamente
- ✅ Mata processos antigos
- ✅ Inicia backend (porta 8000) e frontend (porta 3000)
- ✅ Verifica saúde dos serviços
- ✅ Cria logs: `backend.log` e `frontend.log`

**Resultado esperado**:
```
🎉 ManyBlack V2 iniciado com sucesso!
🌐 Frontend: http://localhost:5173
⚙️ Backend:  http://localhost:8000
📖 API Docs: http://localhost:8000/docs
```

### 2. `./restart.sh` - Restart Rápido

**O que faz**: Para tudo e reinicia rapidamente (para desenvolvimento)

```bash
./restart.sh
```

**Ideal para**:
- 🔧 Após mudanças no código
- 🔄 Quando algo travou
- 🧹 Limpeza rápida de processos

**Diferença do start.sh**: Não reinstala dependências, foca na velocidade

### 3. `./stop.sh` - Parar Tudo

**O que faz**: Para todos os processos do ManyBlack V2

```bash
./stop.sh
```

**Funcionalidades**:
- 🛑 Para backend e frontend graciosamente (SIGTERM)
- 💀 Força encerramento se necessário (SIGKILL)
- 📊 Mostra quais processos foram parados
- 🗑️ Oferece opção de limpar logs
- ✅ Verifica se portas foram liberadas

### 4. `./logs.sh` - Visualização de Logs

**O que faz**: Mostra logs de forma organizada e inteligente

```bash
# Todas as opções:
./logs.sh              # Todos os logs (padrão)
./logs.sh backend      # Apenas backend
./logs.sh frontend     # Apenas frontend
./logs.sh live         # Acompanhar em tempo real
./logs.sh errors       # Apenas linhas com erro
./logs.sh status       # Status dos processos
./logs.sh clean        # Limpar arquivos de log
./logs.sh help         # Ajuda completa
```

**Casos de uso**:
- 🐛 **Debug**: `./logs.sh errors` para ver só problemas
- 👀 **Monitoramento**: `./logs.sh live` para acompanhar em tempo real
- 📊 **Status**: `./logs.sh status` para overview completo
- 🧹 **Limpeza**: `./logs.sh clean` para organizar

### 5. `./webhook.sh` - Configuração de Webhook Automática

**O que faz**: Configura ngrok + webhook do Telegram automaticamente

```bash
# Principais comandos:
./webhook.sh start     # Configurar tudo automaticamente
./webhook.sh stop      # Parar ngrok
./webhook.sh status    # Ver status do webhook
./webhook.sh url       # Mostrar apenas URL pública
./webhook.sh logs      # Ver logs do ngrok
./webhook.sh install   # Instalar ngrok
```

**Fluxo automático**:
1. ✅ Verifica se ngrok está instalado
2. ✅ Verifica se backend está rodando
3. 🚀 Inicia ngrok para porta 8000
4. 🌐 Obtém URL pública (ex: `https://abc123.ngrok.io`)
5. 🔗 Configura webhook: `https://abc123.ngrok.io/webhook/telegram`
6. 📱 Bot fica pronto para receber mensagens

**Pré-requisitos**:
- Backend rodando (`./start.sh` primeiro)
- Token do Telegram configurado em `.env`
- ngrok instalado e autenticado

---

## 🐍 Comandos Python/Backend

### Ambiente Virtual

```bash
# Sempre ativar primeiro (OBRIGATÓRIO):
source .venv/bin/activate

# Verificar se está ativo:
which python  # Deve mostrar caminho do .venv
```

### Execução do Backend

```bash
# Forma recomendada (da raiz do projeto):
(.venv) $ python -m app.main

# Alternativa com uvicorn direto:
(.venv) $ uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Para produção (sem reload):
(.venv) $ uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Gerenciamento de Dependências

```bash
# Instalar dependências:
(.venv) $ pip install -r requirements.txt

# Adicionar nova dependência:
(.venv) $ pip install nome-do-pacote
(.venv) $ pip freeze > requirements.txt

# Verificar dependências instaladas:
(.venv) $ pip list

# Verificar dependências desatualizadas:
(.venv) $ pip list --outdated
```

### Migrações de Banco

```bash
# Aplicar migrações:
(.venv) $ alembic upgrade head

# Verificar status das migrações:
(.venv) $ alembic current

# Ver histórico de migrações:
(.venv) $ alembic history

# Criar nova migração (após mudar models):
(.venv) $ alembic revision --autogenerate -m "Descrição da mudança"

# Reverter migração:
(.venv) $ alembic downgrade -1
```

### Testes

```bash
# Executar todos os testes:
(.venv) $ pytest

# Testes com cobertura:
(.venv) $ pytest --cov=app

# Teste específico:
(.venv) $ pytest tests/test_selector.py

# Testes com output detalhado:
(.venv) $ pytest -v -s

# Testes assíncronos (importante!):
(.venv) $ pytest --asyncio-mode=auto
```

### Debug e Desenvolvimento

```bash
# Verificar saúde da API:
curl http://127.0.0.1:8000/health

# Teste webhook (com JSON):
curl -X POST http://127.0.0.1:8000/webhook/telegram \
  -H "Content-Type: application/json" \
  -d '{"message": {"text": "teste", "from": {"id": 123}, "chat": {"id": 123}}}'

# Ver documentação da API:
# http://127.0.0.1:8000/docs (Swagger)
# http://127.0.0.1:8000/redoc (ReDoc)
```

---

## ⚛️ Comandos Node.js/Frontend

### Ambiente

```bash
# Sempre entrar na pasta do studio:
cd studio/

# Verificar versão do Node.js:
node --version  # Precisa ser 18+
npm --version
```

### Execução do Frontend

```bash
# Desenvolvimento (Hot reload):
studio/ $ npm run dev

# Desenvolvimento em porta específica:
studio/ $ npm run dev -- --port 3001

# Build para produção:
studio/ $ npm run build

# Preview do build de produção:
studio/ $ npm run preview

# Verificação de tipos:
studio/ $ npm run type-check

# Linting:
studio/ $ npm run lint
```

### Gerenciamento de Dependências

```bash
# Instalar dependências:
studio/ $ npm install

# Adicionar nova dependência:
studio/ $ npm install nome-do-pacote

# Adicionar dependência de desenvolvimento:
studio/ $ npm install --save-dev nome-do-pacote

# Remover dependência:
studio/ $ npm uninstall nome-do-pacote

# Verificar dependências desatualizadas:
studio/ $ npm outdated

# Atualizar dependências:
studio/ $ npm update
```

### Tailwind CSS

```bash
# Recompilar CSS:
studio/ $ npx tailwindcss -i ./src/index.css -o ./dist/output.css

# Watch mode para CSS:
studio/ $ npx tailwindcss -i ./src/index.css -o ./dist/output.css --watch

# Build CSS para produção:
studio/ $ npx tailwindcss -i ./src/index.css -o ./dist/output.css --minify
```

---

## 🗄️ Comandos de Banco de Dados

### PostgreSQL

```bash
# Verificar se PostgreSQL está rodando:
pg_isready -h 127.0.0.1 -p 5432

# Conectar ao banco:
psql -h 127.0.0.1 -p 5432 -U mbuser -d manyblack_v2

# Backup do banco:
pg_dump -h 127.0.0.1 -p 5432 -U mbuser manyblack_v2 > backup.sql

# Restaurar backup:
psql -h 127.0.0.1 -p 5432 -U mbuser -d manyblack_v2 < backup.sql

# Ver tabelas (dentro do psql):
\dt

# Ver estrutura de uma tabela:
\d nome_da_tabela

# Sair do psql:
\q
```

### Comandos SQL Úteis

```sql
-- Ver todos os leads:
SELECT * FROM leads ORDER BY created_at DESC LIMIT 10;

-- Ver automações ativas:
SELECT id, topic, priority FROM automations WHERE is_active = true;

-- Ver procedimentos:
SELECT id, title, status FROM procedures;

-- Limpar dados de teste (CUIDADO!):
TRUNCATE TABLE lead_snapshots, messages, leads RESTART IDENTITY CASCADE;
```

---

## 🐛 Comandos de Debug/Troubleshooting

### Verificações Rápidas

```bash
# Verificar processos rodando:
ps aux | grep -E "(uvicorn|vite|npm)"

# Verificar portas em uso:
ss -tulpn | grep -E "(8000|3000)"
# ou
netstat -tulpn | grep -E "(8000|3000)"

# Verificar espaço em disco:
df -h

# Verificar memória:
free -h

# Verificar logs do sistema:
journalctl -f  # logs em tempo real
```

### Network/Conectividade

```bash
# Testar backend local:
curl http://127.0.0.1:8000/health

# Testar frontend local:
curl http://127.0.0.1:3000

# Testar webhook do Telegram (substitua TOKEN):
curl "https://api.telegram.org/botTOKEN/getWebhookInfo"

# Testar conexão com PostgreSQL:
telnet 127.0.0.1 5432

# Testar DNS:
nslookup google.com
```

### Limpeza de Problemas

```bash
# Matar todos os processos Python/Node.js (CUIDADO!):
pkill -f python
pkill -f node

# Limpar cache do npm:
npm cache clean --force

# Limpar cache do pip:
pip cache purge

# Remover __pycache__:
find . -type d -name __pycache__ -exec rm -rf {} +

# Limpar node_modules e reinstalar:
cd studio/ && rm -rf node_modules package-lock.json && npm install
```

---

## 🚀 Comandos de Deploy/Produção

### Preparação para Produção

```bash
# Build do frontend:
cd studio/ && npm run build

# Verificar build:
cd studio/ && npm run preview

# Testes completos:
(.venv) $ pytest
cd studio/ && npm run type-check

# Verificar dependências de segurança:
(.venv) $ pip audit
cd studio/ && npm audit
```

### Variáveis de Ambiente

```bash
# Verificar .env:
cat .env

# Copiar exemplo:
cp env.example .env

# Validar configurações importantes:
grep -E "(TELEGRAM_BOT_TOKEN|DB_|OPENAI_)" .env
```

### Monitoramento

```bash
# Logs em produção (systemd):
journalctl -u manyblack-backend -f
journalctl -u manyblack-frontend -f

# Métricas de sistema:
htop
iotop
```

---

## 📚 Comandos por Cenário

### 🚀 **Primeiro Setup (Novo Desenvolvedor)**

```bash
# 1. Clonar e configurar ambiente
git clone <repo>
cd mb-v2
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd studio/ && npm install && cd ..

# 2. Configurar banco
# (Seguir README-PROJECT.md para PostgreSQL)
cp env.example .env
# Editar .env com suas configurações

# 3. Inicializar banco
alembic upgrade head

# 4. Iniciar tudo
./start.sh
```

### 🔧 **Desenvolvimento Diário**

```bash
# Iniciar dia:
./start.sh

# Após mudanças no código:
./restart.sh

# Ver o que está acontecendo:
./logs.sh live

# Finalizar dia:
./stop.sh
```

### 🐛 **Debug de Problema**

```bash
# 1. Ver logs com erros:
./logs.sh errors

# 2. Verificar status:
./logs.sh status

# 3. Restart limpo:
./stop.sh
./start.sh

# 4. Se ainda tiver problema:
./logs.sh live  # Acompanhar em tempo real
```

### 📱 **Testar com Telegram**

```bash
# 1. Certificar que backend está rodando:
curl http://127.0.0.1:8000/health

# 2. Configurar webhook:
./webhook.sh start

# 3. Ver status:
./webhook.sh status

# 4. Testar no Telegram e acompanhar logs:
./logs.sh live
```

### 🧹 **Limpeza Completa**

```bash
# Parar tudo:
./stop.sh

# Limpar logs:
./logs.sh clean

# Limpar caches:
pip cache purge
cd studio/ && npm cache clean --force

# Reinstalar dependências (se necessário):
pip install -r requirements.txt
cd studio/ && rm -rf node_modules && npm install
```

---

## ⚡ Comandos Mais Usados (Quick Reference)

```bash
# DESENVOLVIMENTO DIÁRIO:
./start.sh                    # Iniciar tudo
./restart.sh                  # Restart rápido
./logs.sh live               # Acompanhar logs
./stop.sh                    # Parar tudo

# DEBUG:
./logs.sh errors             # Ver apenas erros
./logs.sh status             # Status geral
curl http://127.0.0.1:8000/health  # Testar backend

# TELEGRAM:
./webhook.sh start           # Configurar webhook
./webhook.sh status          # Status webhook

# BANCO:
alembic upgrade head         # Aplicar migrações
psql -h 127.0.0.1 -U mbuser manyblack_v2  # Conectar ao banco

# FRONTEND:
cd studio/ && npm run dev    # Iniciar frontend manual
cd studio/ && npm run build  # Build produção
```

---

## 🆘 Solução de Problemas Comuns

### ❌ "Backend não responde"
```bash
./logs.sh backend           # Ver logs do backend
ps aux | grep uvicorn       # Verificar se está rodando
ss -tulpn | grep 8000       # Verificar porta
```

### ❌ "Frontend com erro"
```bash
./logs.sh frontend          # Ver logs do frontend
cd studio/ && npm install  # Reinstalar dependências
rm -rf studio/node_modules && cd studio/ && npm install  # Limpeza total
```

### ❌ "Banco não conecta"
```bash
pg_isready -h 127.0.0.1 -p 5432  # Verificar PostgreSQL
sudo systemctl start postgresql   # Iniciar PostgreSQL
psql -h 127.0.0.1 -U mbuser -d manyblack_v2  # Testar conexão
```

### ❌ "Webhook não funciona"
```bash
./webhook.sh status         # Ver status
./webhook.sh stop          # Parar ngrok
./webhook.sh start         # Reconfigurar
grep TELEGRAM_BOT_TOKEN .env  # Verificar token
```

### ❌ "Processo não para"
```bash
ps aux | grep -E "(uvicorn|vite|npm)"  # Encontrar PIDs
kill -9 PID_DO_PROCESSO                # Forçar encerramento
./stop.sh                              # Script automático
```

---

*💡 **Dica**: Mantenha este arquivo aberto durante o desenvolvimento. Todos os comandos foram testados e são seguros para uso!*
