
import pandas as pd

from utils.logger import AppLogger

logger = AppLogger(__name__).get_logger()

def calculate_rsi(data: pd.Series, period: int) -> pd.Series:
    """
    Calcula o Índice de Força Relativa (RSI).

    Args:
        data (pd.Series): Série de dados (geralmente preços de fechamento).
        period (int): Período do RSI.

    Returns:
        pd.Series: Série contendo os valores do RSI.
    """
    if not isinstance(data, pd.Series):
        logger.error("Os dados para RSI devem ser uma série pandas.")
        return pd.Series()
    if period <= 0:
        logger.error("O período do RSI deve ser um número inteiro positivo.")
        return pd.Series()
    if len(data) < period:
        logger.warning(f"Dados insuficientes ({len(data)}) para calcular RSI com período {period}.")
        return pd.Series()

    try:
        delta = data.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        avg_gain = gain.ewm(span=period, adjust=False).mean()
        avg_loss = loss.ewm(span=period, adjust=False).mean()

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    except Exception as e:
        logger.error(f"Erro ao calcular RSI: {e}")
        return pd.Series()


