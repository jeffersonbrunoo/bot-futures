"""
Configurações globais da aplicação.
Carrega variáveis de ambiente do arquivo .env.
"""

import os
import time
from dotenv import load_dotenv

load_dotenv()


def _get_env(name: str, default: str = None) -> str:
    """
    Lê variável de ambiente e remove comentários inline após '#'.
    """
    raw = os.getenv(name, default)
    if raw is None:
        return None
    # remove texto após '#' (comentários inline)
    return raw.split('#')[0].strip()


# --- Configurações da API MEXC ---
MEXC_API_KEY      = _get_env("MEXC_API_KEY")
MEXC_SECRET_KEY   = _get_env("MEXC_SECRET_KEY")
MEXC_BASE_URL     = "https://contract.mexc.com"
MEXC_WS_URL       = _get_env("MEXC_WS_URL", "wss://contract.mexc.com/edge")


# --- Configurações do Telegram ---
TELEGRAM_BOT_TOKEN = _get_env("TELEGRAM_BOT_TOKEN")
# Converte para int; falha rápido em caso de valor inválido
TELEGRAM_CHAT_ID   = int(_get_env("TELEGRAM_CHAT_ID"))
TELEGRAM_CHAT_ID_TECH = int(_get_env("TELEGRAM_CHAT_ID_TECH"))
TELEGRAM_CHAT_ID_AI = int(_get_env("TELEGRAM_CHAT_ID_AI"))

# --- Configurações do Screener ---
MIN_VOLUME_24H_USD    = float(_get_env("MIN_VOLUME_24H_USD", "1000"))
MIN_OPEN_INTEREST_USD = float(_get_env("MIN_OPEN_INTEREST_USD", "1000"))
TIMEFRAME_TREND       = _get_env("TIMEFRAME_TREND", "Min60")
TIMEFRAME_ENTRY       = _get_env("TIMEFRAME_ENTRY", "Min15")
CANDLE_LIMIT          = int(_get_env("CANDLE_LIMIT", "200"))

# --- Cálculo dinâmico de timestamps para consulta de klines ---
# Mapeia cada timeframe ao seu período em segundos
_PERIODS = {
    "Min1":   60,
    "Min5":   5 * 60,
    "Min15":  15 * 60,
    "Min30":  30 * 60,
    "Min60":  60 * 60,
    "Hour4":  4  * 60 * 60,
    "Day1":   24 * 60 * 60,
}

_now      = int(time.time())
# pega cada timeframe do .env
TIMEFRAME_TREND = _get_env("TIMEFRAME_TREND", "Min60")
TIMEFRAME_ENTRY = _get_env("TIMEFRAME_ENTRY", "Min15")

# define dois intervalos antes de usar
_interval_trend = _PERIODS.get(TIMEFRAME_TREND, _PERIODS["Min60"])
_interval_entry = _PERIODS.get(TIMEFRAME_ENTRY, _PERIODS["Min15"])
_interval = _interval_entry    # usamos o entry aqui para buscar os candles de entrada

KLINES_END_TS   = _now
KLINES_START_TS = _now - (CANDLE_LIMIT * _interval)

# KLINES_START_TS = 1714521600  # 2025-05-01 00:00:00 UTC
# KLINES_END_TS   = 1717286399  # 2025-05-31 23:59:59 UTC

# --- Configurações de Indicadores ---
EMA_SHORT_PERIOD   = int(_get_env("EMA_SHORT_PERIOD", "9"))
EMA_LONG_PERIOD    = int(_get_env("EMA_LONG_PERIOD", "21"))
RSI_PERIOD         = int(_get_env("RSI_PERIOD", "14"))
MACD_FAST_PERIOD   = int(_get_env("MACD_FAST_PERIOD", "12"))
MACD_SLOW_PERIOD   = int(_get_env("MACD_SLOW_PERIOD", "26"))
MACD_SIGNAL_PERIOD = int(_get_env("MACD_SIGNAL_PERIOD", "9"))
VOLUME_MA_PERIOD   = int(_get_env("VOLUME_MA_PERIOD", "20"))


# --- Configurações de Logging ---
LOG_LEVEL = _get_env("LOG_LEVEL", "INFO")


# --- Configurações do Scheduler ---
SCHEDULER_INTERVAL_MINUTES = int(_get_env("SCHEDULER_INTERVAL_MINUTES", "5"))  # em minutos
