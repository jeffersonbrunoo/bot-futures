import asyncio
import pytest
import pandas as pd
from typing import List, Dict

from external_data.nlp_sentiment_analyzer import NLPSentimentAnalyzer

def test_sentiment_empty():
    an = NLPSentimentAnalyzer()
    assert an.get_overall_sentiment([])=='neutro'

def test_sentiment_polarity(monkeypatch):
    an = NLPSentimentAnalyzer()
    monkeypatch.setattr(an, 'analyze_sentiment', lambda t: {'polarity':-0.7})
    assert an.get_overall_sentiment([{'title':'x'}])=='negativo'