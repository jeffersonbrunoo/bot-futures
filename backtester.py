import asyncio
import pandas as pd
from datetime import datetime

from mexc.mexc_api import MexcApiAsync
from screener.filter_engine import (
    check_context,
    calculate_resistance_h1,
    check_trigger
)
from utils.logger import AppLogger

logger = AppLogger(__name__).get_logger()


class Backtester:
    def __init__(self, api: MexcApiAsync):
        self.api = api

    async def run_backtest(self, symbol: str, start_date: str, end_date: str, interval: str = "Min1"):
        logger.info(f"Iniciando backtest para {symbol} de {start_date} até {end_date}...")

        start_ts = int(datetime.strptime(start_date, "%Y-%m-%d").timestamp())
        end_ts = int(datetime.strptime(end_date, "%Y-%m-%d").timestamp())

        raw = await self.api.get_klines(symbol, interval=interval, start=start_ts, end=end_ts)
        if not raw:
            logger.warning(f"Sem dados de candle para {symbol}.")
            return []

        df = self.api.klines_to_dataframe(raw, symbol)
        if df.empty:
            logger.warning(f"Dataframe vazio para {symbol}.")
            return []

        return self.backtest_signals(df, symbol)

    def backtest_signals(self, df: pd.DataFrame, symbol: str):
        results = []

        for i in range(60, len(df) - 20):
            window = df.iloc[i - 60:i].copy()
            if not check_context(window):
                continue

            resistance = calculate_resistance_h1(window)
            signal = check_trigger(window, resistance)
            if not signal:
                continue

            entry = signal["entry_price"]
            stop = signal["stop_loss"]
            take_profit = signal["take_profit"]

            result = self.simulate_trade_window(df, i, entry, stop, take_profit)
            result["symbol"] = symbol
            result["entry_time"] = df.iloc[i + 1]["time"]
            result["entry"] = entry
            result["stop"] = stop
            result["take_profit"] = take_profit
            results.append(result)

        return results

    def simulate_trade_window(self, df: pd.DataFrame, i: int, entry, stop, take_profit, max_bars=20):
        for j in range(i + 1, min(i + 1 + max_bars, len(df))):
            high = df.iloc[j]["high"]
        low = df.iloc[j]["low"]

        if high >= stop:
            return {"result": "loss", "duration": j - i}
        if low <= take_profit:
            return {"result": "win", "duration": j - i}

        return {"result": "open", "duration": max_bars}



async def main():
    api = await MexcApiAsync().init()
    backtester = Backtester(api)

    symbols = ["DBR_USDT"]
    all_results = []
    for symbol in symbols:
        results = await backtester.run_backtest(
            symbol=symbol,
            start_date="2025-06-01",
            end_date="2025-06-13",
            interval="Min5"
        )
        all_results.extend(results)

    df = pd.DataFrame(all_results)
    df.to_csv("backtest_results.csv", index=False)
    logger.info(f"Backtest concluído. Resultados salvos em backtest_results.csv com {len(df)} entradas.")

    await api.close()


if __name__ == "__main__":
    asyncio.run(main())
