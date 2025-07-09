# Tests for LiquidityFilter
# -----------------------

import asyncio
import pytest
import pandas as pd
from typing import List, Dict

# screener modules
from screener.liquidity_filter import LiquidityFilter

class DummyAPIVol:
    def __init__(self, data): self.data = data
    async def obter_liquidez(self, symbol): return self.data.get(symbol, (0,0))

@pytest.mark.asyncio
async def test_filter_by_liquidez_pass_fail(monkeypatch):
    from config import settings as s
    monkeypatch.setenv('MIN_VOLUME_24H_USD','50000')
    monkeypatch.setenv('MIN_OPEN_INTEREST_USD','10000')
    data = {'A':(60000,20000),'B':(40000,9000),'C':(50000,10000)}
    api = DummyAPIVol(data)
    lf = LiquidityFilter(api)
    res = await lf.filter_by_liquidez(['A','B','C'])
    assert 'A' in res and 'C' in res and 'B' not in res