
import logging
import os
from config.settings import LOG_LEVEL

class AppLogger:
    def __init__(self, name=__name__):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(LOG_LEVEL)

        # Formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        # Console Handler
        ch = logging.StreamHandler()
        ch.setLevel(LOG_LEVEL)
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)

        # File Handler (optional)
        # log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'app.log')
        # fh = logging.FileHandler(log_file)
        # fh.setLevel(LOG_LEVEL)
        # fh.setFormatter(formatter)
        # self.logger.addHandler(fh)

    def get_logger(self):
        return self.logger

# Exemplo de uso:
# from utils.logger import AppLogger
# logger = AppLogger(__name__).get_logger()
# logger.info("Isso é uma mensagem de informação.")


