import pytest
import asyncio
from screener.screener_core import ScreenerCore
from notifier.telegram_notifier import TelegramNotifier

class DummyAPI:
    """
    Mock da API principal utilizada pelo ScreenerCore.
    Simula um único contrato e retorna candles suficientes para os filtros.
    """
    async def init(self): 
        return self

    async def get_futures_contracts(self):
        # Simula apenas 1 contrato futuro
        return [{"symbol": "ARPA_USDT"}]

    async def get_klines(self, sym, interval, start, end):
        # Sempre retorna 8 candles válidos para o símbolo solicitado
        return [
            {"open":1,"high":1.3,"low":1,"close":1.23,"volume":1000},
            {"open":1.23,"high":1.25,"low":1.2,"close":1.22,"volume":1100},
            {"open":1.22,"high":1.24,"low":1.21,"close":1.21,"volume":900},
            {"open":1.21,"high":1.23,"low":1.2,"close":1.22,"volume":950},
            {"open":1.22,"high":1.24,"low":1.2,"close":1.23,"volume":980},
            {"open":1.23,"high":1.26,"low":1.22,"close":1.25,"volume":990},
            {"open":1.25,"high":1.27,"low":1.24,"close":1.26,"volume":1010},
            {"open":1.26,"high":1.28,"low":1.25,"close":1.27,"volume":1020},
        ]

    def klines_to_dataframe(self, candles, sym):
        # Converte candles em DataFrame para compatibilidade com os filtros reais
        import pandas as pd
        return pd.DataFrame(candles)

    async def close(self): 
        pass

class DummyNotifier(TelegramNotifier):
    """
    Mock do notifier de Telegram. Apenas armazena as mensagens enviadas.
    """
    def __init__(self):
        self.sent = []
        self.is_configured = True

    async def send_message(self, msg):
        # Apenas salva a mensagem para posterior verificação
        self.sent.append(msg)

@pytest.mark.asyncio
async def test_screener_includes_suggestion(monkeypatch):
    """
    Teste de integração (mock) para validar o fluxo principal do ScreenerCore.
    Garante que:
        - O filtro de liquidez não bloqueia o símbolo.
        - Todos os filtros são forçados a aprovar o dado.
        - A IA retorna uma sugestão mockada.
        - O notifier recebe as mensagens corretas.
    """

    # Instancia os mocks para API e Notifier
    api = DummyAPI()
    notifier = DummyNotifier()
    core = ScreenerCore(api, notifier)

    # Força a função da IA a retornar um texto fixo (simulando sugestão)
    from ai.ai_suggester import suggest_best_coin
    monkeypatch.setattr("ai.ai_suggester.suggest_best_coin", lambda signals: "Minha sugestão de teste")

    # Monkeypatch para os filtros principais:
    #  - Todos aprovam o símbolo (ou criam um sinal fixo)
    async def always_pass_liquidity(api, syms):
        return syms
    monkeypatch.setattr("screener.screener_core.filter_by_liquidez", always_pass_liquidity)
    monkeypatch.setattr("screener.screener_core.check_context", lambda df: True)
    monkeypatch.setattr("screener.screener_core.calculate_resistance_h1", lambda df: 1.25)
    monkeypatch.setattr(
        "screener.screener_core.check_trigger",
        lambda df, resistance: {
            "symbol": "ARPA_USDT",
            "entry_price": 1.23,
            "stop_loss": 1.15,
            "take_profit": 1.30
        }
    )

    # Executa o fluxo principal do screener
    results = await core.run()

    # ---- Asserts para validar comportamento esperado ----
    # Deve retornar exatamente 1 sinal
    assert len(results) == 1
    # O notifier deve ter recebido 2 mensagens
    assert len(notifier.sent) == 2
    # A primeira mensagem deve conter a sugestão mockada da IA
    assert "🤖 *Sugestão da IA:*" in notifier.sent[0]
    assert "Minha sugestão de teste" in notifier.sent[0]
    # A segunda mensagem deve ser o relatório de reprovações
    assert notifier.sent[1].startswith("📊 *Resumo de reprovações:*")
