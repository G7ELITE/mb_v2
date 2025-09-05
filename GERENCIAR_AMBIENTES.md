# 🔄 Gerenciamento de Ambientes Dev/Prod - ManyBlack V2

## 📋 **VISÃO GERAL**

Este guia documenta como gerenciar atualizações entre:
- **Ambiente de Desenvolvimento** (local, com ngrok)
- **Ambiente de Produção** (VPS, domínio fixo)

**Objetivo**: Sincronizar código sem quebrar configurações específicas de cada ambiente.

---

## 🏗️ **ARQUITETURA DOS AMBIENTES**

### 🔧 **DESENVOLVIMENTO LOCAL**
```
┌─────────────────────────────────────┐
│  🏠 Ambiente Local (Seu PC)         │
├─────────────────────────────────────┤
│  Frontend: Vite dev server :5173    │
│  Backend: FastAPI :8000             │
│  Database: PostgreSQL local         │
│  Proxy: ngrok (tunelamento)         │
│  Config: vite.config.ts (dev mode)  │
│  Env: .env (com localhost/ngrok)    │
└─────────────────────────────────────┘
```

### 🚀 **PRODUÇÃO VPS**
```
┌─────────────────────────────────────┐
│  ☁️  VPS Produção                   │
├─────────────────────────────────────┤
│  Frontend: Build estático (Nginx)   │
│  Backend: Docker + FastAPI          │
│  Database: Docker PostgreSQL        │
│  Proxy: Nginx + SSL (domínio fixo)  │
│  Config: vite.config.build.js       │
│  Env: .env (com domínio/docker)     │
└─────────────────────────────────────┘
```

---

## ⚙️ **DIFERENÇAS CRÍTICAS ENTRE AMBIENTES**

### 📄 **Arquivos que DIFEREM:**

| Arquivo | Desenvolvimento | Produção |
|---------|----------------|-----------|
| **vite.config.ts** | Proxy para localhost:8000, ngrok hosts | Build estático, sem proxy |
| **.env** | DB_HOST=127.0.0.1, ngrok URLs | DB_HOST=postgres, domínio fixo |
| **docker-compose** | Não usado | docker-compose.prod.yml |
| **Dockerfile** | Build apenas backend | Dockerfile completo ou Dockerfile.backend-only |

### 🔧 **Configurações Frontend:**

#### **DEV (vite.config.ts)**:
```typescript
server: {
  host: '0.0.0.0',
  port: 5173,
  allowedHosts: ['.ngrok-free.app', '.ngrok.io'],
  proxy: {
    '/api': 'http://127.0.0.1:8000'
  }
}
```

#### **PROD (vite.config.build.js)**:
```typescript
build: {
  outDir: 'dist',
  minify: 'terser',
  rollupOptions: { /* otimizações */ }
}
```

### 🔐 **Configurações Backend (.env):**

#### **DEV**:
```env
DB_HOST=127.0.0.1
REDIS_URL=redis://127.0.0.1:6379/0  
FRONTEND_URL=https://abc123.ngrok-free.app
BACKEND_URL=https://abc123.ngrok-free.app
```

#### **PROD**:
```env
DB_HOST=postgres
REDIS_URL=redis://redis:6379/0
FRONTEND_URL=https://equipe.manyblack.com
BACKEND_URL=https://equipe.manyblack.com
```

---

## 🔄 **PROCESSO DE ATUALIZAÇÃO SEM CONFLITOS**

### 🎯 **FLUXO RECOMENDADO:**

```mermaid
graph LR
    A[Branch Feature] --> B[Merge na main local]
    B --> C[Push main]
    C --> D[Pull na VPS]
    D --> E[Verificar configs]
    E --> F[Deploy]
```

### 📝 **PASSO A PASSO:**

#### **1. NO AMBIENTE DE DESENVOLVIMENTO:**

```bash
# ✅ Finalizar feature
git add .
git commit -m "feat: implementar lead-simulação"

# ✅ Ir para main
git checkout main
git pull origin main

# ✅ Merge da feature
git merge criar-lead-simulação

# ✅ Push da main atualizada
git push origin main

# 🗑️ Opcional: deletar branch feature
git branch -d criar-lead-simulação
```

#### **2. NA VPS DE PRODUÇÃO:**

```bash
# 🛡️ BACKUP DE ARQUIVOS CRÍTICOS (já feito automaticamente)
cp .env .env.production.backup
cp studio/vite.config.ts studio/vite.config.ts.backup

# 📥 Puxar atualizações
git pull origin main

# 🔍 Verificar se houve conflitos nos arquivos críticos
git status

# 🔧 Se necessário, restaurar configurações de produção:
# cp .env.production.backup .env
# cp studio/vite.config.ts.backup studio/vite.config.ts

# 🚀 Fazer deploy
./deploy-prod.sh
```

---

## 🛡️ **ESTRATÉGIAS DE PROTEÇÃO**

### 📁 **Arquivos Protegidos Automaticamente:**
- `.env.production.backup`
- `studio/vite.config.ts.backup`

### 🔒 **Gitignore Configurado:**
```gitignore
# Arquivos de ambiente específicos
.env
.env.local
.env.production
.env.development

# Builds
studio/dist/
studio/node_modules/

# Backups
*.backup
```

### ⚠️ **Arquivos que NUNCA devem ir pro Git:**
- `.env` (com chaves reais)
- `studio/dist/` (build gerado)
- `*.backup` (backups locais)

---

## 🚨 **RESOLUÇÃO DE CONFLITOS**

### 🔧 **Se `vite.config.ts` conflitar:**

```bash
# Restaurar versão de produção
cp studio/vite.config.ts.backup studio/vite.config.ts

# OU editar manualmente mantendo:
# - Sem configurações de servidor (dev)
# - Apenas configurações de build (prod)
```

### 🔧 **Se `.env` conflitar:**

```bash
# Restaurar versão de produção
cp .env.production.backup .env

# Verificar se tem novas variáveis e adicionar:
# - Manter DB_HOST=postgres (não localhost)
# - Manter URLs com domínio (não ngrok)
```

---

## 🔍 **VERIFICAÇÃO PÓS-UPDATE**

### ✅ **Checklist de Validação:**

```bash
# 1. Verificar se containers estão rodando
docker compose -f docker-compose.prod.yml ps

# 2. Testar health check
curl https://equipe.manyblack.com/health

# 3. Testar frontend
curl -I https://equipe.manyblack.com/

# 4. Testar API específica (ex: leads)
curl https://equipe.manyblack.com/api/leads

# 5. Verificar logs
docker compose -f docker-compose.prod.yml logs --tail=20 app
```

### 🐛 **Se algo der errado:**

```bash
# Rollback rápido
git log --oneline -5
git checkout HASH_DO_COMMIT_ANTERIOR

# Ou restaurar backups
cp .env.production.backup .env
cp studio/vite.config.ts.backup studio/vite.config.ts

# E fazer deploy novamente
./deploy-prod.sh
```

---

## 🚀 **DEPLOY AUTOMÁTICO**

### 📜 **Script `deploy-prod.sh`:**

```bash
#!/bin/bash
echo "🚀 Iniciando deploy de produção..."

# Backup automático
cp .env .env.production.backup
cp studio/vite.config.ts studio/vite.config.ts.backup

# Build e deploy
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d --build

echo "✅ Deploy concluído: https://equipe.manyblack.com"
```

---

## 📚 **COMANDOS ÚTEIS**

### 🔍 **Desenvolvimento:**
```bash
# Ver branches
git branch -a

# Comparar com produção
git diff origin/main arquivo.ts

# Testar build local
npm run build
```

### 🚀 **Produção:**
```bash
# Status completo
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs app

# Restart serviço específico
docker compose -f docker-compose.prod.yml restart app

# Rebuild completo
docker compose -f docker-compose.prod.yml up -d --build --force-recreate
```

---

## 📋 **RESUMO EXECUTIVO**

### ✅ **SEMPRE FAZER:**
1. **Backup** antes de pull
2. **Verificar** configs específicas 
3. **Testar** após deploy
4. **Monitorar** logs

### ❌ **NUNCA FAZER:**
1. Commitar arquivos `.env` reais
2. Fazer merge sem testar
3. Deploy sem backup
4. Ignorar conflitos

### 🎯 **RESULTADO:**
- **✅ Ambientes sincronizados** sem perder configurações
- **✅ Zero downtime** em produção  
- **✅ Rollback rápido** se necessário
- **✅ Configurações protegidas** automaticamente

---

**📧 Em caso de dúvidas, consulte este guia ou revise os logs de deploy.**

*Última atualização: Setembro 2025*
