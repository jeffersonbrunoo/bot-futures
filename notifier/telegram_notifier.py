# notifier/telegram_notifier.py

from telegram.constants import ParseMode
from telegram import Bot
from utils.logger import AppLogger
from config.telegram_config import TelegramConfig
from notifier.message_formatter import MessageFormatter

logger = AppLogger(__name__).get_logger()

class TelegramNotifier:
    def __init__(self):
        self.bot_token = TelegramConfig.BOT_TOKEN
        self.chat_id = TelegramConfig.CHAT_ID
        self.is_configured = bool(self.bot_token and self.chat_id)
        if not self.is_configured:
            logger.error("Token do bot ou ID do chat do Telegram não configurados.")
        else:
            self.bot = Bot(token=self.bot_token)

    async def send_message(self, message: str, parse_mode: ParseMode = ParseMode.MARKDOWN_V2):
        if not self.is_configured:
            return
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode=parse_mode,
                disable_web_page_preview=True,
            )
        except Exception as e:
            # Erros pontuais só em DEBUG
            logger.debug(f"Erro ao enviar mensagem genérica: {e}\n{repr(message)}")

    async def send_tech(self, message: str, parse_mode: ParseMode = ParseMode.MARKDOWN_V2):
        if not self.is_configured:
            return
        try:
            await self.bot.send_message(
                chat_id=TelegramConfig.CHAT_ID_TECH,
                text=message,
                parse_mode=parse_mode,
                disable_web_page_preview=True,
            )
        except Exception as e:
            # Reduce noise: apenas em DEBUG
            logger.debug(f"Erro ao enviar sinal TECH: {e}\n{repr(message)}")

    async def send_ai(self, message: str, parse_mode: ParseMode = ParseMode.MARKDOWN_V2):
        if not self.is_configured:
            return
        try:
            await self.bot.send_message(
                chat_id=TelegramConfig.CHAT_ID_AI,
                text=message,
                parse_mode=parse_mode,
                disable_web_page_preview=True,
            )
        except Exception as e:
            logger.debug(f"Erro ao enviar sugestão AI: {e}\n{repr(message)}")

    def format_trade_signal(
        self,
        symbol: str,
        entry: float,
        stop_loss: float,
        take_profit: float,
        indicators: dict
    ) -> str:
        return MessageFormatter.format_trade_signal(
            symbol=symbol,
            entry=entry,
            stop_loss=stop_loss,
            take_profit=take_profit,
            indicators=indicators
        )

    def format_screener_results(self, results, suggestion=None) -> str:
        return MessageFormatter.format_screener_results(results, suggestion)

# Alias para compatibilidade
TelegramBot = TelegramNotifier
