# test_telegram.py
from notifier.telegram_bot import TelegramBot

bot = TelegramBot()
bot.send_message("🚀 Teste de notificação do Screener")
