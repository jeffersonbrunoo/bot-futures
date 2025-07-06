from textblob import TextBlob
from typing import List, Dict, Any
from utils.logger import AppLogger

logger = AppLogger(__name__).get_logger()

class NLPSentimentAnalyzer:
    def __init__(self):
        pass

    def analyze_sentiment(self, text: str) -> Dict[str, float]:
        """
        Analisa o sentimento de um texto usando TextBlob.
        Retorna a polaridade (positiva/negativa) e a subjetividade (objetiva/subjetiva).
        """
        analysis = TextBlob(text)
        sentiment = {
            "polarity": analysis.sentiment.polarity,  # -1.0 (negativo) a 1.0 (positivo)
            "subjectivity": analysis.sentiment.subjectivity  # 0.0 (objetivo) a 1.0 (subjetivo)
        }
        logger.debug(f"Sentimento analisado: {sentiment}")
        return sentiment

    def get_overall_sentiment(self, articles: List[Dict[str, Any]]) -> str:
        """
        Calcula o sentimento geral de uma lista de artigos.
        """
        if not articles:
            return "neutro"

        total_polarity = 0.0
        for article in articles:
            if title := article.get("title"):
                total_polarity += self.analyze_sentiment(title)["polarity"]
            if desc := article.get("description"):
                total_polarity += self.analyze_sentiment(desc)["polarity"]

        avg_polarity = total_polarity / len(articles)

        if avg_polarity > 0.1:
            return "positivo"
        elif avg_polarity < -0.1:
            return "negativo"
        else:
            return "neutro"
