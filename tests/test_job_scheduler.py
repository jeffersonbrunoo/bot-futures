import asyncio
import pytest
import pandas as pd
from typing import List, Dict

from scheduler.job_scheduler import run_screener_job_sync

def test_run_screener_job_sync(monkeypatch):
    class DummyCore:
        @staticmethod
        async def create(): return DummyCore()
        def run_screener(self): return ['x']
    monkeypatch.setattr('screener.screener_core.ScreenerCore', DummyCore)
    res = run_screener_job_sync()
    assert res==['x']