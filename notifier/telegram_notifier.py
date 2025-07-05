from telegram.constants import ParseMode
from config.telegram_config import TelegramConfig
from telegram import Bot
from utils.logger import AppLogger
from notifier.message_formatter import MessageFormatter
from typing import List, Union, Dict, Any

logger = AppLogger(__name__).get_logger()

class TelegramNotifier:
    def __init__(self):
        self.bot_token = TelegramConfig.BOT_TOKEN
        self.chat_id = TelegramConfig.CHAT_ID

        if not self.bot_token or not self.chat_id:
            logger.error("Token do bot ou ID do chat do Telegram não configurados.")
            self.is_configured = False
        else:
            self.bot = Bot(token=self.bot_token)
            self.is_configured = True

    async def send_message(self, message: str, parse_mode=ParseMode.MARKDOWN_V2):
        """
        Envia uma mensagem para o Telegram usando Markdown V2 escapado.
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
            logger.info("Mensagem enviada com sucesso para o Telegram.")
        except Exception as e:
            logger.error(
                f"Erro ao enviar mensagem para o Telegram: {e}\nCorpo da mensagem: {repr(message)}"
            )

    def format_trade_signal(
        self,
        symbol: str,
        entry: float,
        stop_loss: float,
        take_profit: float,
        indicators: Dict[str, Any]
    ) -> str:
        """
        Wrapper para format_trade_signal do MessageFormatter.
        """
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
        """
        Formata o conjunto de sinais (e sugestão da IA) em um único bloco de texto.
        """
        return MessageFormatter.format_screener_results(results, suggestion)

# Alias para compatibilidade com o import em main.py
TelegramBot = TelegramNotifier
