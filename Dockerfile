# Estágio 1: Build
FROM python:3.10-slim AS builder

# Definir variáveis de ambiente
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Definir o diretório de trabalho
WORKDIR /app

# Copiar apenas os arquivos necessários
COPY requirements.txt .

# Instalar dependências no estágio de build
RUN pip install --no-cache-dir -r requirements.txt

# Estágio 2: Produção
FROM python:3.10-slim

# Definir variáveis de ambiente
ENV PYTHONUNBUFFERED=1

# Definir o diretório de trabalho
WORKDIR /app

# Copiar dependências instaladas do estágio de build
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copiar o código da aplicação
COPY . .

# Expor a porta em que a API rodará
EXPOSE 8000

# Adicionar um comando de saúde
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/healthz || exit 1

# Comando para iniciar o servidor FastAPI com Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
