Monitor de Futuros MEXC

Uma aplicação Python para monitorar contratos futuros perpétuos na MEXC, filtrar por liquidez, aplicar análise técnica para detectar gatilhos de entrada em posições vendidas (short) e enviar notificações via Telegram.

Estrutura do Projeto

Plain Text


monitor-futuros-mexc/
├── config/          # settings.py, telegram_config.py
├── mexc/            # mexc_api.py, mexc_endpoints.py, mexc_utils.py
├── indicators/      # ema.py, rsi.py, macd.py, volume.py
├── screener/        # liquidez.py, filtros.py, screener_core.py
├── notifier/        # telegram_bot.py, message_formatter.py
├── scheduler/       # job_scheduler.py
├── utils/           # logger.py
├── main.py
├── requirements.txt
├── Dockerfile       # opcional para containerização
└── README.md        # instruções de instalação, configuração e uso


Funcionalidades

•
Lista contratos futuros perpétuos ativos da MEXC.

•
Filtra por liquidez (volume 24h e open interest).

•
Baixa candles OHLCV em timeframe configurável.

•
Calcula indicadores de análise técnica (EMA, RSI, MACD, Média de Volume).

•
Detecta gatilhos de entrada em posições vendidas (short) com base em múltiplos critérios:

•
Preço abaixo de EMA curta < EMA longa.

•
RSI abaixo de 50.

•
Cruzamento de MACD para baixo da linha de sinal.

•
Volume do último candle acima da média dos N últimos.

•
Fechamento abaixo da mínima dos 3 candles anteriores.



•
Envia notificações formatadas via Telegram Bot.

•
Possui scheduler interno para execução periódica.

•
Configurações parametrizáveis via variáveis de ambiente e arquivo .env.

•
Inclui logging, tratamento de erros e paralelização para desempenho.

Instalação

1.
Clone o repositório:

2.
Crie e ative um ambiente virtual (recomendado):

3.
Instale as dependências:

Configuração

Crie um arquivo .env na raiz do projeto (monitor-futuros-mexc/.env) com as seguintes variáveis de ambiente:

Plain Text


# MEXC API
MEXC_API_KEY=SUA_API_KEY_MEXC
MEXC_SECRET_KEY=SUA_SECRET_KEY_MEXC

# Telegram Bot
TELEGRAM_BOT_TOKEN=SEU_BOT_TOKEN_TELEGRAM
TELEGRAM_CHAT_ID=SEU_CHAT_ID_TELEGRAM

# Screener Settings
MIN_VOLUME_24H_USD=10000000  # Volume mínimo em USD nas últimas 24h (ex: 10 milhões)
MIN_OPEN_INTEREST_USD=50000000 # Open Interest mínimo em USD (ex: 50 milhões)
TIMEFRAME=15m               # Timeframe dos candles (ex: 1m, 5m, 15m, 1h, 4h, 1d)
CANDLE_LIMIT=200             # Número de candles para baixar

# Indicator Settings
EMA_SHORT_PERIOD=9
EMA_LONG_PERIOD=21
RSI_PERIOD=14
MACD_FAST_PERIOD=12
MACD_SLOW_PERIOD=26
MACD_SIGNAL_PERIOD=9
VOLUME_MA_PERIOD=20

# Logging Settings
LOG_LEVEL=INFO               # Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)

# Scheduler Settings
SCHEDULER_INTERVAL_MINUTES=60 # Intervalo em minutos para rodar o screener no modo scheduler


•
MEXC API Key/Secret: Obtenha suas chaves API na sua conta MEXC.

•
Telegram Bot Token: Crie um bot no Telegram via BotFather e obtenha o token.

•
Telegram Chat ID: Inicie uma conversa com seu bot e use a API do Telegram para obter seu chat_id. Você pode enviar uma mensagem para https://api.telegram.org/bot<SEU_BOT_TOKEN>/getUpdates e procurar por "chat":{"id":...}.

Uso

Você pode rodar a aplicação de duas formas:

1. Modo Screener (Execução Única)

Executa o screener uma única vez e envia os resultados para o Telegram.

Bash


python main.py screener


2. Modo Scheduler (Execução Periódica)

Inicia o scheduler que rodará o screener em intervalos definidos pela variável SCHEDULER_INTERVAL_MINUTES no seu arquivo .env.

Bash


python main.py scheduler


Para parar o scheduler, pressione Ctrl+C.

Containerização com Docker (Opcional)

Você pode construir e rodar a aplicação usando Docker para um ambiente isolado e fácil de implantar.

1.
Construa a imagem Docker:

2.
Execute o contêiner:

