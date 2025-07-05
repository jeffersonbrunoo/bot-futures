
import pandas as pd

from utils.logger import AppLogger

logger = AppLogger(__name__).get_logger()

def calculate_volume_ma(data: pd.Series, period: int) -> pd.Series:
    """
    Calcula a Média Móvel Simples (SMA) do volume.

    Args:
        data (pd.Series): Série de dados de volume.
        period (int): Período da Média Móvel.

    Returns:
        pd.Series: Série contendo os valores da Média Móvel do Volume.
    """
    if not isinstance(data, pd.Series):
        logger.error("Os dados de volume devem ser uma série pandas.")
        return pd.Series()
    if period <= 0:
        logger.error("O período da Média Móvel do Volume deve ser um número inteiro positivo.")
        return pd.Series()
    if len(data) < period:
        logger.warning(f"Dados insuficientes ({len(data)}) para calcular Média Móvel do Volume com período {period}.")
        return pd.Series()

    try:
        volume_ma = data.rolling(window=period).mean()
        return volume_ma
    except Exception as e:
        logger.error(f"Erro ao calcular Média Móvel do Volume: {e}")
        return pd.Series()


