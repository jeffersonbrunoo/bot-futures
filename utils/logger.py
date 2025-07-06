import logging
from config.settings import LOG_LEVEL

class AppLogger:
    """
    Centraliza a configuração de logging da aplicação.
    Exibe apenas INFO dos módulos principais e silencia logs verbose de bibliotecas externas.
    """
    def __init__(self, name: str = __name__):
        # Raiz: nível WARNING e handler console em INFO
        root = logging.getLogger()
        if not root.handlers:
            root.setLevel(logging.WARNING)
            fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            console = logging.StreamHandler()
            console.setLevel(logging.INFO)
            console.setFormatter(logging.Formatter(fmt))
            root.addHandler(console)

        # Silencia bibliotecas muito verbosas
        for noisy in ("httpx", "aiohttp", "websockets", "urllib3", "asyncio", "external_data.news_api_wrapper"):
            logging.getLogger(noisy).setLevel(logging.WARNING)

        # Garante INFO apenas nos nossos módulos principais
        for mod in ("__main__", "screener.screener_core", "screener.liquidity_filter", "notifier.telegram_notifier"):
            logging.getLogger(mod).setLevel(logging.INFO)

        # Logger do chamador em INFO
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)

    def get_logger(self) -> logging.Logger:
        return self.logger
