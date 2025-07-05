# Escolha uma base mais recente
FROM python:3.10-slim-alpine

WORKDIR /app

# 1) Atualiza o SO e limpa caches
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install --no-install-recommends -y build-essential && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 2) Copia e instala dependências Python
COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install pip-audit && \
    pip-audit --fail-on high

# 3) Copia o restante do código
COPY . .

# 4) Comando padrão
CMD ["python", "main.py", "scheduler"]
