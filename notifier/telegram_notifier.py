# notifier/telegram_notifier.py

from telegram.constants import ParseMode
from telegram import Bot
from utils.logger import AppLogger
from config.telegram_config import TelegramConfig
from notifier.message_formatter import MessageFormatter
from typing import List, Union, Dict, Any

logger = AppLogger(__name__).get_logger()

class TelegramNotifier:
    def __init__(self):
        self.bot_token = TelegramConfig.BOT_TOKEN
        # chat_id padrão (pode ser usado para notificações genéricas)
        self.chat_id = TelegramConfig.CHAT_ID

        if not self.bot_token or not self.chat_id:
            logger.error("Token do bot ou ID do chat do Telegram não configurados.")
            self.is_configured = False
        else:
            self.bot = Bot(token=self.bot_token)
            self.is_configured = True

    async def send_message(self, message: str, parse_mode: ParseMode = ParseMode.MARKDOWN_V2):
        """
        Envia uma mensagem para o Telegram (chat_id padrão).
        """
        if not self.is_configured:
            logger.warning("Telegram Bot não configurado. Pulando envio de mensagem.")
            return
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode=parse_mode,
                disable_web_page_preview=True,
            )
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem para o Telegram: {e}\n{repr(message)}")

    async def send_tech(self, message: str, parse_mode: ParseMode = ParseMode.MARKDOWN_V2):
        """
        Envia sinal técnico para o canal VIP de sinais TECH.
        """
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
            logger.error(f"Erro ao enviar sinal TECH: {e}\n{repr(message)}")

    async def send_ai(self, message: str, parse_mode: ParseMode = ParseMode.MARKDOWN_V2):
        """
        Envia sugestão da IA para o canal VIP de sinais AI.
        """
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
            logger.error(f"Erro ao enviar sugestão AI: {e}\n{repr(message)}")

    def format_trade_signal(
        self,
        symbol: str,
        entry: float,
        stop_loss: float,
        take_profit: float,
        indicators: Dict[str, Any]
    ) -> str:
        return MessageFormatter.format_trade_signal(
            symbol=symbol,
            entry=entry,
            stop_loss=stop_loss,
            take_profit=take_profit,
            indicators=indicators
        )

    def format_screener_results(
        self,
        results: List[Union[Dict[str, Any], tuple]],
        suggestion: str = None
    ) -> str:
        return MessageFormatter.format_screener_results(results, suggestion)

# Alias legacy
TelegramBot = TelegramNotifier
