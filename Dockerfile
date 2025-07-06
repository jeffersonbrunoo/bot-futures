# 1) Imagem base Debian slim (com apt-get disponível)
FROM python:3.10-slim-alpine

# 2) Garantir saída de logs sem buffer
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# 3) Instalar compiladores (para dependências nativas, se houver)
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

# 4) Copiar e instalar só as dependências
COPY requirements.txt ./
RUN pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install pip-audit \
    && pip-audit --fail-on high

# 5) Copiar o restante do código
COPY . .

# 6) Comando padrão para rodar o scheduler
CMD ["python", "main.py", "scheduler"]
