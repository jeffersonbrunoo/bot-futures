import os
from typing import List, Dict, Any
import httpx
from utils.logger import AppLogger

logger = AppLogger(__name__).get_logger()

class NewsAPIWrapper:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("NEWS_API_KEY")
        self.base_url = "https://newsapi.org/v2/everything"
        if not self.api_key:
            logger.warning("NEWS_API_KEY não configurada. A funcionalidade de notícias pode estar limitada.")

    async def fetch_news(self, query: str, language: str = "en", page_size: int = 5) -> List[Dict[str, Any]]:
        if not self.api_key:
            logger.error("API Key para NewsAPI não fornecida.")
            return []

        params = {
            "q": query,
            "language": language,
            "pageSize": page_size,
            "apiKey": self.api_key
        }
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.base_url, params=params)
                response.raise_for_status()  # Raise an exception for 4xx or 5xx status codes
                data = response.json()
                articles = data.get("articles", [])
                logger.info(f"Notícias encontradas para '{query}': {len(articles)}")
                return articles
        except httpx.RequestError as e:
            logger.error(f"Erro de requisição ao buscar notícias para '{query}': {e}")
        except httpx.HTTPStatusError as e:
            logger.error(f"Erro HTTP ao buscar notícias para '{query}': {e.response.status_code} - {e.response.text}")
        except Exception as e:
            logger.error(f"Erro inesperado ao buscar notícias para '{query}': {e}")
        return []


