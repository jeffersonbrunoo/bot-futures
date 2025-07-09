import asyncio
import pytest
import pandas as pd
from typing import List, Dict

from screener.external_factors_evaluator import ExternalFactorsEvaluator

class DummyNewsClient:
    def __init__(self, articles): self.articles = articles
    async def fetch_news(self, query, days_back, page_size): return self.articles

class DummySentimentAnalyzer:
    def analyze_sentiment(self, text): return {'polarity': 0.8}

@pytest.mark.asyncio
async def test_external_factors(monkeypatch):
    evalr = ExternalFactorsEvaluator()
    # stub NewsAPI and Sentiment
    monkeypatch.setattr(evalr, 'news_wrapper', DummyNewsClient([{'title':'t','description':'d'}]))
    monkeypatch.setattr(evalr, 'sentiment_analyzer', DummySentimentAnalyzer())
    df = pd.DataFrame({'volume':[1,2,3,100]})
    res = await evalr.evaluate_external_factors('SYM', df)
    assert res['news_count']==1
    assert res['sentiment']=='positivo'
    assert isinstance(res['anomalous_volume_z'], float)