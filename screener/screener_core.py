import asyncio
import time
import html
from typing import List, Dict
from utils.logger import AppLogger
from mexc.mexc_api import MexcApiAsync
from screener.filter_engine import (
    filter_by_liquidez,
    check_context,
    calculate_resistance_h1,
    check_trigger
)
from notifier.telegram_notifier import TelegramNotifier
from notifier.message_formatter import MessageFormatter
from telegram.constants import ParseMode
from config import settings

logger = AppLogger(__name__).get_logger()

# Configurações multi‐timeframe
TIMEFRAME_TREND = settings.TIMEFRAME_TREND    # ex: "Min60"
TIMEFRAME_ENTRY = settings.TIMEFRAME_ENTRY    # ex: "Min15"
CANDLE_LIMIT   = settings.CANDLE_LIMIT        # nº de candles a buscar
_PERIODS       = settings._PERIODS            # mapeamento de segundos por timeframe

class ScreenerCore:
    def __init__(self, api: MexcApiAsync, notifier: TelegramNotifier):
        self.api = api
        self.notifier = notifier

    @classmethod
    async def create(cls):
        api = await MexcApiAsync().init()
        notifier = TelegramNotifier()
        return cls(api, notifier)

    async def run(self) -> List[dict]:
        logger.info("Iniciando screener assíncrono…")
        now = int(time.time())

        # calcula timestamps para cada timeframe
        interval_trend = _PERIODS.get(TIMEFRAME_TREND, _PERIODS["Min60"])
        interval_entry = _PERIODS.get(TIMEFRAME_ENTRY, _PERIODS["Min15"])
        trend_start = now - CANDLE_LIMIT * interval_trend
        entry_start = now - CANDLE_LIMIT * interval_entry
        trend_end = entry_end = now

        try:
            # 1) Recupera contratos
            contracts = await self.api.get_futures_contracts()
            symbols = [c["symbol"] for c in contracts if c.get("symbol")]
            logger.info(f"Total de {len(symbols)} símbolos encontrados.")

            # 2) Filtra por liquidez
            liquid = await filter_by_liquidez(self.api, symbols)
            if not liquid and symbols:
                liquid = symbols.copy()
                logger.info("Nenhum símbolo passou no filtro de liquidez; aplicando todos.")
            logger.info(f"{len(liquid)} símbolos passarão nos filtros seguintes.")

            # 3) Gera sinais (trend + entry)
            final_signals: List[dict] = []
            for sym in liquid:
                try:
                    # 3.1) Trend
                    trend_klines = await self.api.get_klines(
                        sym, interval=TIMEFRAME_TREND,
                        start=trend_start, end=trend_end
                    )
                    if not trend_klines:
                        continue
                    trend_df = self.api.klines_to_dataframe(trend_klines, sym)
                    if trend_df.empty or not check_context(trend_df):
                        continue
                    resistance = calculate_resistance_h1(trend_df)

                    # 3.2) Entry
                    entry_klines = await self.api.get_klines(
                        sym, interval=TIMEFRAME_ENTRY,
                        start=entry_start, end=entry_end
                    )
                    if not entry_klines:
                        continue
                    entry_df = self.api.klines_to_dataframe(entry_klines, sym)
                    if entry_df.empty:
                        continue

                    signal = check_trigger(entry_df, resistance)
                    if not signal:
                        continue

                    # enriquecer com volume e tendência
                    vols = entry_df["volume"].tail(5).tolist()
                    avg_vol = sum(vols) / len(vols) if vols else 0
                    closes = entry_df["close"].tail(5).tolist()
                    trend_dir = "alta" if len(closes)>=2 and closes[-1]>closes[0] else "baixa"

                    signal.update({
                        "volume": avg_vol,
                        "liquidity": "alta",
                        "trend": trend_dir
                    })
                    final_signals.append(signal)

                except Exception as e:
                    logger.warning(f"Erro processando {sym}: {e}")

            # 4) Envia cada sinal separadamente (HTML)
            for sig in final_signals:
                html_msg = MessageFormatter.format_trade_signal(
                    symbol=sig["symbol"],
                    entry=sig["entry_price"],
                    stop_loss=sig["stop_loss"],
                    take_profit=sig["take_profit"],
                    indicators=sig.get("indicators", {})
                )
                await self.notifier.send_message(html_msg, parse_mode=ParseMode.HTML)

            # 5) Sugestão da IA (se houver sinais)
            if final_signals:
                try:
                    from ai.ai_suggester import suggest_best_coin
                    best = suggest_best_coin(final_signals)
                    sug_html = (
                        "🤖 <b>Sugestão da IA:</b>\n"
                        f"<code>{html.escape(best)}</code>"
                    )
                    await self.notifier.send_message(sug_html, parse_mode=ParseMode.HTML)
                except Exception as e:
                    logger.warning(f"Erro ao obter sugestão da IA: {e}")

            logger.info(f"{len(final_signals)} sinais enviados ao Telegram.")
            return final_signals

        except Exception as e:
            logger.error(f"Erro no screener: {e}", exc_info=True)
            err = f"❌ <b>Erro no Screener:</b> {html.escape(str(e))}"
            await self.notifier.send_message(err, parse_mode=ParseMode.HTML)
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
            fut = asyncio.run_coroutine_threadsafe(self.run(), loop)
            return fut.result()
        else:
            new_loop = asyncio.new_event_loop()
            try:
                return new_loop.run_until_complete(self.run())
            finally:
                new_loop.close()


if __name__ == "__main__":
    asyncio.run(ScreenerCore.create().then(lambda c: c.run()))
