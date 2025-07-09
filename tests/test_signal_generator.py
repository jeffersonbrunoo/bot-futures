import asyncio
import pytest
import pandas as pd
from typing import List, Dict

from screener.signal_generator import SignalGenerator, RESISTANCE_WINDOW
from screener.filter_engine import check_trigger

sg = SignalGenerator()

def make_df(close: List[float], volume: List[float]):
    df = pd.DataFrame({'close': close, 'high': close, 'volume': volume})
    return df

@pytest.mark.parametrize('n', [RESISTANCE_WINDOW-1, RESISTANCE_WINDOW])
def test_resistance_window(n):
    df = make_df(list(range(n)), [1]*n)
    if n < RESISTANCE_WINDOW:
        with pytest.raises(ValueError): sg.calculate_resistance_h1(df)
    else:
        assert sg.calculate_resistance_h1(df) == max(df['high'])

def test_macd_rsi_lengths():
    df = make_df(list(range(30)), [1]*30)
    rsi = sg.calculate_rsi(df)
    macd, sig = sg.calculate_macd(df)
    assert len(rsi)==len(df)
    assert len(macd)==len(df)
    assert len(sig)==len(df)

def test_check_trigger_conditions():
    # data where close < resistance, volume high, RSI<50, MACD below signal
    df = pd.DataFrame({
        'close':[1,0.9,0.8,0.7,0.6,0.5,0.4,0.3],
        'high':[1]*8,
        'ema_short':[0.5]*8,
        'ema_long':[1]*8,
        'rsi':[45]*8,
        'macd':[0.1]*8,
        'macd_signal':[0.2]*8,
        'volume':[1000]*8,
        'volume_ma':[500]*8
    })
    sig = check_trigger(df, resistance=1)
    assert isinstance(sig, dict)