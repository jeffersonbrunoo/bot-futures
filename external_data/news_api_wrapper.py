import os
from typing import List, Dict, Any
import httpx
from utils.logger import AppLogger

logger = AppLogger(__name__).get_logger()

class NewsAPIWrapper:
    """
    Wrapper para NewsAPI.org que evita poluir o log com múltiplos erros de rate-limit:
    - Sucesso de fetch agora vai para DEBUG
    - Ao receber HTTP 429 (rate limit), emite apenas UMA mensagem de erro e silencia as próximas chamadas
    """
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("NEWS_API_KEY")
        self.base_url = "https://newsapi.org/v2/everything"
        self._rate_limited = False  # flag para suprimir logs repetidos de 429

        if not self.api_key:
            logger.warning("NEWS_API_KEY não configurada. Funcionalidade de notícias limitada.")

    async def fetch_news(
        self,
        query: str,
        language: str = "en",
        page_size: int = 5
    ) -> List[Dict[str, Any]]:
        # se já estamos em rate limit, não faz mais chamadas
        if self._rate_limited:
            return []

        if not self.api_key:
            logger.error("API Key da NewsAPI não fornecida.")
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
                response.raise_for_status()
                data = response.json()
                articles = data.get("articles", [])

                # Sucesso em nível DEBUG para não poluir o INFO
                logger.debug(f"[NewsAPI] {len(articles)} artigos para '{query}'")
                return articles

        except httpx.HTTPStatusError as e:
            status = e.response.status_code
            if status == 429:
                # só registra uma vez
                logger.error(
                    "NewsAPI rate limit atingido (429). Aplicação não fará mais requisições de notícias."
                )
                self._rate_limited = True
            else:
                logger.error(f"HTTP {status} em NewsAPI para '{query}'.")
            return []

        except httpx.RequestError as e:
            # problemas de rede ou DNS
            logger.error(f"Erro de requisição na NewsAPI para '{query}': {e}")
            return []

        except Exception as e:
            # qualquer outro erro inesperado
            logger.error(f"Erro inesperado na NewsAPI para '{query}': {e}")
            return []
