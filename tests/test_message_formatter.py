import asyncio
import pytest
import pandas as pd
from typing import List, Dict

from notifier.message_formatter import MessageFormatter

def test_format_trade_signal():
    d={'ema_short':1,'ema_long':2,'rsi':30,'macd':0,'macd_signal':0,'volume':100,'volume_ma':50}
    msg = MessageFormatter.format_trade_signal('SYM',1,2,3,d)
    assert '*Símbolo:* `SYM`' in msg

def test_format_screener_results_multi():
    signals = [{'symbol':'B','entry_price':1,'stop_loss':2,'take_profit':3,'indicators':{}}]
    r = MessageFormatter.format_screener_results(signals,'sug')
    assert 'Sugestão da IA' in r
