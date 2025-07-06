import asyncio
import pandas as pd

from screener.screener_core import ScreenerCore
from notifier.telegram_notifier import TelegramNotifier
from screener.signal_generator import SignalGenerator
import ai.ai_suggester as ai_suggester

class DummyAPI:
    async def init(self):
        return self

    async def get_futures_contracts(self):
        return [{"symbol": "ARPA_USDT"}]

    async def get_klines(self, sym, interval, start, end):
        return [
            {"open": 1,    "high": 1.3, "low": 1.0, "close": 1.23, "volume": 1000},
            {"open": 1.23, "high": 1.25, "low": 1.2, "close": 1.22, "volume": 1100},
            {"open": 1.22, "high": 1.24, "low": 1.21,"close": 1.21, "volume": 900},
            {"open": 1.21, "high": 1.23, "low": 1.2, "close": 1.22, "volume": 950},
            {"open": 1.22, "high": 1.24, "low": 1.2, "close": 1.23, "volume": 980},
            {"open": 1.23, "high": 1.26, "low": 1.22,"close": 1.25, "volume": 990},
            {"open": 1.25, "high": 1.27, "low": 1.24,"close": 1.26, "volume":1010},
            {"open": 1.26, "high": 1.28, "low": 1.25,"close": 1.27, "volume":1020},
        ]

    def klines_to_dataframe(self, candles, sym):
        df = pd.DataFrame(candles)
        df['symbol'] = sym
        return df

    async def close(self):
        pass

class DummyNotifier(TelegramNotifier):
    def __init__(self):
        self.sent = []

    async def send_message(self, msg, parse_mode=None):
        self.sent.append(msg)

class DummyExtEvaluator:
    async def evaluate_external_factors(self, symbol, df):
        return {"anomalous_volume": False, "sentiment": "neutro"}

class DummySignalGen(SignalGenerator):
    pass

class DummyAI:
    @staticmethod
    def suggest_best_coin(signals):
        return 'ARPA_USDT'

# Patch dependencies for ScreenerCore
import pytest

def test_screener_core_full_flow(monkeypatch):
    api = DummyAPI()
    notifier = DummyNotifier()
    ext_eval = DummyExtEvaluator()

    # Instantiate core
    core = ScreenerCore(api, notifier, ext_eval)

    # Patch filter_by_liquidez
    async def always_pass(api_obj, symbols):
        return symbols
    monkeypatch.setattr('screener.filter_engine.filter_by_liquidez', always_pass)

    # Patch SignalGenerator methods
    monkeypatch.setattr(SignalGenerator, 'check_context', lambda self, df: True)
    monkeypatch.setattr(SignalGenerator, 'calculate_resistance_h1', lambda self, df: 1.25)
    monkeypatch.setattr(
        SignalGenerator,
        'check_trigger',
        lambda self, df, res: {
            'symbol': df['symbol'].iloc[-1],
            'entry_price': 1.23,
            'stop_loss': 1.15,
            'take_profit': 1.30,
            'indicators': {}
        }
    )

    # Patch ExternalFactorsEvaluator
    monkeypatch.setattr('screener.external_factors_evaluator.ExternalFactorsEvaluator', DummyExtEvaluator)

    # Patch AI suggester
    monkeypatch.setattr(ai_suggester, 'suggest_best_coin', lambda signals: 'ARPA_USDT')

    # Run the core and capture results
    results = asyncio.run(core.run())

    # Assertions
    assert len(results) == 1, "Should produce one signal"
    # Two messages: trade + IA suggestion
    assert len(notifier.sent) == 2, "Notifier should send two messages"

    trade_msg = notifier.sent[0]
    assert 'ARPA_USDT' in trade_msg, "Trade message must include symbol"

    ia_msg = notifier.sent[1]
    assert ia_msg.startswith('🤖 <b>Sugestão da IA'), "IA message formatting"
