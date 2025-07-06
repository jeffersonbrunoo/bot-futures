# screener/screener_core.py

import asyncio
import time
import html
from typing import List, Dict

from utils.logger import AppLogger
from mexc.mexc_api import MexcApiAsync
from screener.liquidity_filter import LiquidityFilter
from screener.signal_generator import SignalGenerator
from screener.external_factors_evaluator import ExternalFactorsEvaluator
from notifier.telegram_notifier import TelegramNotifier
from notifier.message_formatter import MessageFormatter
from telegram.constants import ParseMode
from config import settings

logger = AppLogger(__name__).get_logger()

# configurações de timeframe e candles
timeframe_trend = settings.TIMEFRAME_TREND
timeframe_entry = settings.TIMEFRAME_ENTRY
candle_limit   = settings.CANDLE_LIMIT
_periods       = settings._PERIODS

class ScreenerCore:
    def __init__(
        self,
        api: MexcApiAsync,
        notifier: TelegramNotifier,
        ext_evaluator: ExternalFactorsEvaluator
    ):
        self.api = api
        self.notifier = notifier
        self.ext_evaluator = ext_evaluator
        self.liquidity_filter = LiquidityFilter(api)
        self.signal_gen = SignalGenerator()

    @classmethod
    async def create(cls):
        api = await MexcApiAsync().init()
        notifier = TelegramNotifier()
        ext_evaluator = ExternalFactorsEvaluator()
        return cls(api, notifier, ext_evaluator)

    async def run(self) -> List[dict]:
        logger.info("Iniciando screener assíncrono…")
        now = int(time.time())

        interval_trend = _periods.get(timeframe_trend, _periods["Min60"])
        interval_entry = _periods.get(timeframe_entry, _periods["Min15"])
        trend_start = now - candle_limit * interval_trend
        entry_start = now - candle_limit * interval_entry
        trend_end = entry_end = now

        try:
            # 1) contratos
            contracts = await self.api.get_futures_contracts()
            symbols = [c["symbol"] for c in contracts if c.get("symbol")]
            logger.info(f"Total de {len(symbols)} símbolos encontrados.")

            # 2) liquidez
            liquid = await self.liquidity_filter.filter_by_liquidez(symbols)
            if not liquid and symbols:
                liquid = symbols.copy()
                logger.info("Nenhum símbolo passou no filtro de liquidez; aplicando todos.")
            logger.info(f"{len(liquid)} símbolos passarão nos filtros seguintes.")

            # 3) geração de sinais
            final_signals: List[dict] = []
            for sym in liquid:
                try:
                    # timeframe trend
                    trend_raw = await self.api.get_klines(
                        sym, interval=timeframe_trend,
                        start=trend_start, end=trend_end
                    )
                    if not trend_raw:
                        continue
                    trend_df = self.api.klines_to_dataframe(trend_raw, sym)
                    if not self.signal_gen.check_context(trend_df):
                        continue
                    resistance = self.signal_gen.calculate_resistance_h1(trend_df)

                    # timeframe entry
                    entry_raw = await self.api.get_klines(
                        sym, interval=timeframe_entry,
                        start=entry_start, end=entry_end
                    )
                    if not entry_raw:
                        continue
                    entry_df = self.api.klines_to_dataframe(entry_raw, sym)
                    signal = self.signal_gen.check_trigger(entry_df, resistance)
                    if not signal:
                        continue

                    # 3.3 fatores externos
                    factors = await self.ext_evaluator.evaluate_external_factors(sym, entry_df)
                    signal.update(factors)

                    # 3.4 volume médio e direção
                    vols = entry_df["volume"].tail(5).tolist()
                    avg_vol = sum(vols)/len(vols) if vols else 0
                    closes = entry_df["close"].tail(5).tolist()
                    trend_dir = "alta" if len(closes)>=2 and closes[-1]>closes[0] else "baixa"
                    signal.update({"avg_volume": avg_vol, "trend": trend_dir})

                    final_signals.append(signal)

                except Exception as e:
                    logger.warning(f"Erro processando {sym}: {e}")

            # 4) envia cada sinal no canal TECH
            for sig in final_signals:
                tech_msg = MessageFormatter.format_trade_signal(
                    symbol=sig["symbol"],
                    entry=sig["entry_price"],
                    stop_loss=sig["stop_loss"],
                    take_profit=sig["take_profit"],
                    indicators=sig.get("indicators", {})
                )
                await self.notifier.send_tech(tech_msg, parse_mode=ParseMode.HTML)

            # 5) sugestão IA no canal AI (mesmo formato do sinal TECH com prefixo)
            if final_signals:
                try:
                    from ai.ai_suggester import suggest_best_coin
                    best_symbol = suggest_best_coin(final_signals)
                    best_sig = next(s for s in final_signals if s["symbol"] == best_symbol)
                    ai_body = MessageFormatter.format_trade_signal(
                        symbol=best_sig["symbol"],
                        entry=best_sig["entry_price"],
                        stop_loss=best_sig["stop_loss"],
                        take_profit=best_sig["take_profit"],
                        indicators=best_sig.get("indicators", {})
                    )
                    ai_msg = "🤖 <b>Sugestão da IA:</b>\n" + ai_body
                    await self.notifier.send_ai(ai_msg, parse_mode=ParseMode.HTML)
                except Exception as e:
                    logger.warning(f"Erro ao obter/enviar sugestão da IA: {e}")

            logger.info(f"{len(final_signals)} sinais processados. Mensagens enviadas aos canais VIP.")
            return final_signals

        except Exception as e:
            logger.error(f"Erro no screener: {e}", exc_info=True)
            err = f"❌ <b>Erro no Screener:</b> {html.escape(str(e))}"
            await self.notifier.send_tech(err, parse_mode=ParseMode.HTML)
            return []

        finally:
            try:
                await self.api.close()
            except Exception as e:
                logger.warning(f"Erro fechando API: {e}")

    def run_screener(self) -> List[dict]:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            return asyncio.run_coroutine_threadsafe(self.run(), loop).result()
        else:
            return asyncio.new_event_loop().run_until_complete(self.run())

if __name__ == "__main__":
    asyncio.run(ScreenerCore.create().run())
