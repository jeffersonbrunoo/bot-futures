import asyncio
import pytest
import pandas as pd
from typing import List, Dict

from notifier.telegram_notifier import TelegramNotifier

@pytest.mark.asyncio
async def test_send_message_flow(monkeypatch):
    tn = TelegramNotifier()
    tn.is_configured = True
    class FakeBot:
        async def send_message(self, chat_id, text, parse_mode): return True
    tn.bot = FakeBot()
    await tn.send_message('hello')