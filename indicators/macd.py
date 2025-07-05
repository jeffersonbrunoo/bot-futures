# indicators\macd.py

import pandas as pd

from indicators.ema import calculate_ema
from utils.logger import AppLogger

logger = AppLogger(__name__).get_logger()

def calculate_macd(data: pd.Series, fast_period: int, slow_period: int, signal_period: int) -> tuple[pd.Series, pd.Series, pd.Series]:
    """
    Calcula o Moving Average Convergence Divergence (MACD).

    Args:
        data (pd.Series): Série de dados (geralmente preços de fechamento).
        fast_period (int): Período da EMA rápida.
        slow_period (int): Período da EMA lenta.
        signal_period (int): Período da linha de sinal.

    Returns:
        tuple[pd.Series, pd.Series, pd.Series]: Tupla contendo (MACD Line, Signal Line, Histogram).
    """
    if not isinstance(data, pd.Series):
        logger.error("Os dados para MACD devem ser uma série pandas.")
        return pd.Series(), pd.Series(), pd.Series()
    if not all(p > 0 for p in [fast_period, slow_period, signal_period]):
        logger.error("Todos os períodos do MACD devem ser números inteiros positivos.")
        return pd.Series(), pd.Series(), pd.Series()
    if len(data) < max(fast_period, slow_period) + signal_period:
        logger.warning(f"Dados insuficientes para calcular MACD com os períodos fornecidos.")
        return pd.Series(), pd.Series(), pd.Series()

    try:
        ema_fast = calculate_ema(data, fast_period)
        ema_slow = calculate_ema(data, slow_period)

        macd_line = ema_fast - ema_slow
        signal_line = calculate_ema(macd_line, signal_period)
        histogram = macd_line - signal_line

        return macd_line, signal_line, histogram
    except Exception as e:
        logger.error(f"Erro ao calcular MACD: {e}")
        return pd.Series(), pd.Series(), pd.Series()


