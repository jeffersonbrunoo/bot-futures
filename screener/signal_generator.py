import pandas as pd
from typing import Optional, Tuple, Dict, Any

from config.settings import (
    EMA_SHORT_PERIOD,
    EMA_LONG_PERIOD,
    RSI_PERIOD,
    MACD_FAST_PERIOD,
    MACD_SLOW_PERIOD,
    MACD_SIGNAL_PERIOD,
    VOLUME_MA_PERIOD
)
from utils.logger import AppLogger

logger = AppLogger(__name__).get_logger()

# Buffers e parâmetros de risco para operações de SHORT
ENTRY_BUFFER = 0.001      # entry 0.1% abaixo do close
STOP_BUFFER = 0.002       # SL 0.2% acima da resistência
RESISTANCE_BUFFER = 0.995 # considera resistência 0.5% abaixo do topo
RR_TARGET = 1.5           # target de reward:risk
RESISTANCE_WINDOW = 8     # candles para calcular resistência
VOLUME_THRESHOLD_MULTIPLIER = 0.8  # volume >= 80% da média

class SignalGenerator:
    def __init__(self):
        pass

    def calculate_resistance_h1(self, df: pd.DataFrame) -> float:
        if len(df) < RESISTANCE_WINDOW:
            raise ValueError(f"DataFrame precisa de ao menos {RESISTANCE_WINDOW} candles para resistência.")
        # Garante ordenação por timestamp ascendente
        df_sorted = df.sort_index()
        return df_sorted['high'].rolling(window=RESISTANCE_WINDOW).max().iloc[-1]

    def calculate_rsi(self, df: pd.DataFrame) -> pd.Series:
        delta = df['close'].diff()
        gain = delta.clip(lower=0).ewm(alpha=1/RSI_PERIOD, adjust=False).mean()
        loss = -delta.clip(upper=0).ewm(alpha=1/RSI_PERIOD, adjust=False).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    def calculate_macd(self, df: pd.DataFrame) -> Tuple[pd.Series, pd.Series]:
        ema_fast = df['close'].ewm(span=MACD_FAST_PERIOD, adjust=False).mean()
        ema_slow = df['close'].ewm(span=MACD_SLOW_PERIOD, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal = macd_line.ewm(span=MACD_SIGNAL_PERIOD, adjust=False).mean()
        return macd_line, signal

    def check_context(self, df: pd.DataFrame) -> bool:
        """
        Tendência de baixa para SHORT: EMA_SHORT abaixo de EMA_LONG e RSI abaixo de 50.
        """
        ema_short = df['close'].ewm(span=EMA_SHORT_PERIOD, adjust=False).mean().iloc[-1]
        ema_long = df['close'].ewm(span=EMA_LONG_PERIOD, adjust=False).mean().iloc[-1]
        rsi_val = self.calculate_rsi(df).iloc[-1]
        logger.debug(f"Contexto: EMA_SHORT={ema_short:.4f}, EMA_LONG={ema_long:.4f}, RSI={rsi_val:.2f}")
        return (ema_short < ema_long) and (rsi_val < 50)

    def check_trigger(
        self,
        df: pd.DataFrame,
        resistance: float
    ) -> Optional[dict]:
        indicators: dict = {}
        try:
            # valida tendência de baixa antes dos gatilhos
            if not self.check_context(df):
                logger.debug("Rejeitado no contexto de baixa antes do gatilho.")
                return None

            # janela mínima considerando todos os indicadores
            min_bars = max(EMA_LONG_PERIOD, RSI_PERIOD, MACD_SLOW_PERIOD,
                           VOLUME_MA_PERIOD, RESISTANCE_WINDOW)
            if df.empty or len(df) < min_bars:
                raise ValueError(f"DataFrame insuficiente: precisa de ao menos {min_bars} barras.")

            close = df['close'].iloc[-1]
            indicators['resistance_raw'] = resistance
            buf_res = resistance * RESISTANCE_BUFFER
            indicators['resistance_buffered'] = buf_res
            # Verifica resistência: para SHORT, close deve estar abaixo do nível bufferizado
            if close > buf_res:
                logger.debug(f"Rejeitado por resistência: close={close:.4f} > buf_res={buf_res:.4f}")
                return None

            # Volume
            vol = df['volume'].iloc[-1]
            vol_ma = df['volume'].rolling(window=VOLUME_MA_PERIOD).mean().iloc[-1]
            indicators['volume'] = vol
            indicators['volume_ma'] = vol_ma
            if vol < vol_ma * VOLUME_THRESHOLD_MULTIPLIER:
                logger.debug(f"Rejeitado por volume: vol={vol:.2f} < {vol_ma * VOLUME_THRESHOLD_MULTIPLIER:.2f}")
                return None

            # RSI
            rsi_val = self.calculate_rsi(df).iloc[-1]
            indicators['rsi'] = rsi_val
            if rsi_val >= 50:
                logger.debug(f"Rejeitado por RSI: {rsi_val:.2f} >= 50")
                return None

            # MACD
            macd_line, signal = self.calculate_macd(df)
            macd_val = macd_line.iloc[-1]
            sig_val = signal.iloc[-1]
            indicators['macd'] = macd_val
            indicators['macd_signal'] = sig_val
            if macd_val >= sig_val:
                logger.debug(f"Rejeitado por MACD: macd={macd_val:.4f} >= signal={sig_val:.4f}")
                return None

            # Cálculo de preços para SHORT
            entry_price = close * (1 - ENTRY_BUFFER)
            stop_loss = resistance * (1 + STOP_BUFFER)
            risk = stop_loss - entry_price
            take_profit = entry_price - risk * RR_TARGET

            return {
                'symbol': df['symbol'].iloc[-1] if 'symbol' in df.columns else '',
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'indicators': indicators
            }

        except Exception as e:
            logger.error(f"Erro ao calcular gatilhos de short: {e}")
            return None


