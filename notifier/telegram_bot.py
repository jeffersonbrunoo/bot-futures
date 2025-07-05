# notifier/telegram_bot.py ENVIA MENSAGEM

from telegram import Bot
from telegram.constants import ParseMode
from telegram.error import TelegramError

from config.telegram_config import TelegramConfig
from utils.logger import AppLogger

logger = AppLogger(__name__).get_logger()

class TelegramBot:
    def __init__(self):
        self.bot_token = TelegramConfig.BOT_TOKEN
        self.chat_id = TelegramConfig.CHAT_ID

        if not self.bot_token or not self.chat_id:
            logger.error("Token do bot ou ID do chat do Telegram não configurados.")
            self.is_configured = False
        else:
            self.bot = Bot(token=self.bot_token)
            self.is_configured = True

    async def send_message(self, message: str):
        if not self.is_configured:
            logger.warning("Telegram Bot não configurado. Pulando envio de mensagem.")
            return
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode=ParseMode.MARKDOWN
            )
            logger.info("Mensagem enviada com sucesso para o Telegram.")
        except TelegramError as e:
            logger.error(f"Erro ao enviar mensagem para o Telegram: {e}")
