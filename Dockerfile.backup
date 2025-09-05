# Dockerfile para produção - ManyBlack V2
FROM node:18-alpine AS frontend-builder

# Build do Frontend (Studio)
WORKDIR /app/studio
COPY studio/package*.json ./
RUN npm install

COPY studio/ ./
RUN npm run build

# Imagem principal com Python
FROM python:3.11-slim

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Criar usuário não-root
RUN useradd --create-home --shell /bin/bash app

# Diretório da aplicação
WORKDIR /app

# Copiar requirements e instalar dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código do backend
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini .

# Copiar frontend buildado
COPY --from=frontend-builder /app/studio/dist ./static

# Copiar scripts
COPY scripts/ ./scripts/
RUN chmod +x scripts/*.sh

# Mudar para usuário não-root
RUN chown -R app:app /app
USER app

# Expor porta
EXPOSE 8000

# Script de inicialização
CMD ["./scripts/start-production.sh"]
