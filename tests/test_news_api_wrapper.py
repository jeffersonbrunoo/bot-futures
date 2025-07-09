import asyncio
import pytest
import pandas as pd
from typing import List, Dict

from external_data.news_api_wrapper import NewsAPIWrapper

@pytest.mark.asyncio
async def test_news_wrapper(monkeypatch):
    wrapper = NewsAPIWrapper(api_key='key')
    class DummyResp:
        status_code=200
        def raise_for_status(self): pass
        def json(self): return {'articles':[{'title':'t','description':'d'}]}
    class DummyClient:
        async def __aenter__(self): return self
        async def __aexit__(self,*a): pass
        async def get(self,url,params): return DummyResp()
    monkeypatch.setattr('external_data.news_api_wrapper.httpx.AsyncClient', lambda **kwargs: DummyClient())
    arts = await wrapper.fetch_news('X')
    assert isinstance(arts,list)