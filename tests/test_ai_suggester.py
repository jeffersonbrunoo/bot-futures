import asyncio
import pytest
import pandas as pd
from typing import List, Dict

import ai.ai_suggester as ai_suggester

def test_build_prompt_includes_fields():
    signals = [{
        'symbol':'A','entry_price':1,'stop_loss':2,'take_profit':3,
        'anomalous_volume':True,'anomalous_volume_z':2.5,
        'sentiment':'negativo','news_count':3
    }]
    prompt = ai_suggester.build_technical_prompt(signals)
    assert 'A: Entrada' in prompt and 'Volume Anômalo: True' in prompt

@pytest.mark.asyncio
async def test_suggest_best_coins_local(monkeypatch):
    # Força provider local
    monkeypatch.setenv('AI_PROVIDER', 'local')
    # Define sinais dummy para o teste
    signals = [{
        'symbol':'A',
        'entry_price':1,
        'stop_loss':2,
        'take_profit':3,
        'anomalous_volume':True,
        'anomalous_volume_z':2.5,
        'sentiment':'negativo',
        'news_count':3
    }]
    from ai.ai_suggester import suggest_best_coins
    # Monkeypatch do gerador local para retornar texto previsível
    monkeypatch.setattr(ai_suggester, '_gen', lambda prompt, **kwargs: [{ 'generated_text': prompt + ',X,Y' }])
    res = suggest_best_coins(signals)
    assert len(res) == 2