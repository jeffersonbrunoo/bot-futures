# indicators\ema.py

import pandas as pd

from utils.logger import AppLogger

logger = AppLogger(__name__).get_logger()

def calculate_ema(data: pd.Series, period: int) -> pd.Series:
    """
    Calcula a Média Móvel Exponencial (EMA) para uma série de dados.

    Args:
        data (pd.Series): Série de dados (geralmente preços de fechamento).
        period (int): Período da EMA.

    Returns:
        pd.Series: Série contendo os valores da EMA.
    """
    empty = pd.Series([], index=data.index if isinstance(data, pd.Series) else [], dtype=float)
    if not isinstance(data, pd.Series):
        logger.error("Os dados para EMA devem ser uma série pandas.")
        return empty
    if period <= 0:
        logger.error("O período da EMA deve ser um número inteiro positivo.")
        return empty
    if len(data) < period:
        logger.warning(f"Dados insuficientes ({len(data)}) para calcular EMA com período {period}.")
        return empty

    try:
        return data.ewm(span=period, adjust=False).mean()
    except Exception as e:
        logger.error(f"Erro ao calcular EMA: {e}")
        return empty


