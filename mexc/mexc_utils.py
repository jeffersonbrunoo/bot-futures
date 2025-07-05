# mexc/mexc_utils.py

import pandas as pd
from utils.logger import AppLogger

logger = AppLogger(__name__).get_logger()

class MexcUtils:
    @staticmethod
    def parse_kline_data(raw):
        """
        Converte a resposta da API de kline da MEXC em um DataFrame pandas padronizado.

        Aceita:
          raw = [ [ts, open, high, low, close, volume], ... ]
          raw = {"success": True, "data": [ [ts, open, high, low, close, volume], ... ] }
          raw = [ {"timestamp": ..., "open": ..., ...}, ... ]

        Retorna um DataFrame com colunas:
          ["open", "high", "low", "close", "volume"]
        indexado por timestamp (em datetime).
        """
        # 1) Desembrulha o campo "data", se existir
        if isinstance(raw, dict) and "data" in raw:
            data = raw["data"]
        else:
            data = raw

        # 2) Se for lista de listas, transforma em lista de dicts
        if isinstance(data, list) and data and isinstance(data[0], list):
            records = []
            for item in data:
                try:
                    records.append({
                        "timestamp": item[0],
                        "open": float(item[1]),
                        "high": float(item[2]),
                        "low": float(item[3]),
                        "close": float(item[4]),
                        "volume": float(item[5]),
                    })
                except (ValueError, IndexError) as e:
                    logger.error(f"Erro ao analisar candle bruto {item}: {e}")
            data = records

        # 3) Se não for lista de dicts, aborta
        if not isinstance(data, list) or not data or not isinstance(data[0], dict):
            logger.warning("Dados de kline inválidos ou vazios.")
            return pd.DataFrame()

        # 4) Monta DataFrame
        df = pd.DataFrame(data)
        if "timestamp" in df:
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
            df = df.set_index("timestamp").sort_index()
        else:
            logger.warning("Campo 'timestamp' não encontrado nos dados de kline.")
        return df

    @staticmethod
    def calculate_liquidity(ticker_data, open_interest_data):
        """
        Calcula liquidez (volume 24h USD + open interest USD) a partir do ticker e do open interest.
        """
        volume_24h_usd = 0.0
        open_interest_usd = 0.0

        # volume24H * lastPrice
        if ticker_data and ticker_data.get("success") and ticker_data.get("data"):
            d = ticker_data["data"]
            try:
                volume_24h_usd = float(d.get("volume24", d.get("amount24", 0))) * float(d.get("lastPrice", 0))
            except (ValueError, TypeError) as e:
                logger.error(f"Erro ao calcular volume 24h USD: {e}")

        # holdVol * lastPrice
        if open_interest_data and open_interest_data.get("success") and open_interest_data.get("data") and ticker_data.get("data"):
            try:
                holding = float(open_interest_data["data"].get("holding", 0))
                last_price = float(ticker_data["data"].get("lastPrice", 0))
                open_interest_usd = holding * last_price
            except (ValueError, TypeError) as e:
                logger.error(f"Erro ao calcular open interest USD: {e}")

        return {
            "volume_24h_usd": volume_24h_usd,
            "open_interest_usd": open_interest_usd
        }
