import asyncio
import pandas as pd

import pytest

from screener.screener_core import ScreenerCore
from screener.liquidity_filter import LiquidityFilter
from screener.signal_generator import SignalGenerator
import ai.ai_suggester as ai_suggester


class DummyAPI:
    async def init(self):
        return self

    async def get_futures_contracts(self):
        return [{"symbol": "ARPA_USDT"}]

    async def get_klines(self, sym, interval, start, end):
        # 8 candles fictícios
        return [
            {"open": 1,    "high": 1.3, "low": 1.0, "close": 1.23, "volume": 1000},
            {"open": 1.23, "high": 1.25, "low": 1.2, "close": 1.22, "volume": 1100},
            {"open": 1.22, "high": 1.24, "low": 1.21,"close": 1.21, "volume":  900},
            {"open": 1.21, "high": 1.23, "low": 1.2, "close": 1.22, "volume":  950},
            {"open": 1.22, "high": 1.24, "low": 1.2, "close": 1.23, "volume":  980},
            {"open": 1.23, "high": 1.26, "low": 1.22,"close": 1.25, "volume":  990},
            {"open": 1.25, "high": 1.27, "low": 1.24,"close": 1.26, "volume": 1010},
            {"open": 1.26, "high": 1.28, "low": 1.25,"close": 1.27, "volume": 1020},
        ]

    def klines_to_dataframe(self, candles, sym):
        df = pd.DataFrame(candles)
        df["symbol"] = sym
        return df

    async def close(self):
        pass


class DummyNotifier:
    def __init__(self):
        self.sent = []

    async def send_tech(self, msg, parse_mode=None):
        self.sent.append(msg)

    async def send_ai(self, msg, parse_mode=None):
        self.sent.append(msg)


class DummyExtEvaluator:
    async def evaluate_external_factors(self, symbol, df):
        return {}


def test_screener_core_full_flow(monkeypatch):
    api = DummyAPI()
    notifier = DummyNotifier()
    ext_eval = DummyExtEvaluator()

    core = ScreenerCore(api, notifier, ext_eval)

    # 1) Forçar todos os símbolos a passarem no filtro de liquidez
    async def always_pass(self, symbols):
        return symbols
    monkeypatch.setattr(LiquidityFilter, "filter_by_liquidez", always_pass)

    # 2) Forçar SignalGenerator a aceitar o contexto e gerar gatilho
    monkeypatch.setattr(SignalGenerator, "check_context", lambda self, df: True)
    monkeypatch.setattr(SignalGenerator, "calculate_resistance_h1", lambda self, df: 1.25)
    monkeypatch.setattr(
        SignalGenerator,
        "check_trigger",
        lambda self, df, res: {
            "symbol": df["symbol"].iloc[-1],
            "entry_price": 1.23,
            "stop_loss": 1.15,
            "take_profit": 1.30,
            "indicators": {}
        }
    )

    # 3) Forçar IA a sempre sugerir ARPA_USDT
    monkeypatch.setattr(ai_suggester, "suggest_best_coin", lambda signals: "ARPA_USDT")

    # Executa o run()
    results = asyncio.run(core.run())

    # Verificações
    assert len(results) == 1, "Deve produzir um único sinal"
    assert len(notifier.sent) == 2, "Deve enviar duas mensagens (tech + IA)"

    trade_msg, ia_msg = notifier.sent
    assert "ARPA_USDT" in trade_msg, "Mensagem de trade deve conter o símbolo"
    assert ia_msg.startswith("🤖 <b>Sugestão da IA"), "Formato da mensagem da IA está incorreto"
