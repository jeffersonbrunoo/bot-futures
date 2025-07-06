import asyncio
from typing import Dict, Any

from utils.logger import AppLogger
from external_data.news_api_wrapper import NewsAPIWrapper
from external_data.nlp_sentiment_analyzer import NLPSentimentAnalyzer

logger = AppLogger(__name__).get_logger()

class ExternalFactorsEvaluator:
    def __init__(self):
        self.news_wrapper = NewsAPIWrapper()
        self.sentiment_analyzer = NLPSentimentAnalyzer()

    async def evaluate_external_factors(self, symbol: str, df) -> Dict[str, Any]:
        """
        Busca notícias e avalia sentimento, além de medir volume anômalo.
        Retorna campos: anomalous_volume (bool), sentiment (str), news_count (int).
        """
        # 1) Notícias e sentimento
        try:
            articles = await self.news_wrapper.fetch_news(symbol, language="pt", page_size=5)
            sentiment = self.sentiment_analyzer.get_overall_sentiment(articles)
            news_count = len(articles)
        except Exception as e:
            logger.warning(f"Erro ao buscar ou analisar notícias para {symbol}: {e}")
            sentiment = "neutro"
            news_count = 0

        # 2) Volume anômalo: z-score da última barra vs média móvel
        try:
            volumes = df['volume'].tail(20)
            mean = volumes.mean()
            std = volumes.std()
            last_vol = volumes.iloc[-1]
            z_score = (last_vol - mean) / std if std else 0.0
            anomalous = abs(z_score) > 2
        except Exception as e:
            logger.warning(f"Erro calculando volume anômalo para {symbol}: {e}")
            anomalous = False
            z_score = 0.0

        return {
            'sentiment': sentiment,
            'news_count': news_count,
            'anomalous_volume': anomalous,
            'anomalous_volume_z': round(z_score, 2)
        }
