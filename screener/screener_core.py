import asyncio
import time
import html
from typing import List, Dict, Union

from utils.logger import AppLogger
from mexc.mexc_api import MexcApiAsync
from screener.liquidity_filter import LiquidityFilter
from screener.signal_generator import SignalGenerator
from screener.external_factors_evaluator import ExternalFactorsEvaluator
from notifier.telegram_notifier import TelegramNotifier
from notifier.message_formatter import MessageFormatter
from telegram.constants import ParseMode
from config import settings

# Import do sugeridor da IA
from ai.ai_suggester import suggest_best_coin
from reports.performance import log_signal

logger = AppLogger(__name__).get_logger()

# Configurações multi‐timeframe
TIMEFRAME_TREND = settings.TIMEFRAME_TREND
TIMEFRAME_ENTRY = settings.TIMEFRAME_ENTRY
CANDLE_LIMIT   = settings.CANDLE_LIMIT
_PERIODS       = settings._PERIODS


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

        # calcula timestamps para cada timeframe
        interval_trend = _PERIODS.get(TIMEFRAME_TREND, _PERIODS["Min60"])
        interval_entry = _PERIODS.get(TIMEFRAME_ENTRY, _PERIODS["Min15"])
        trend_start = now - CANDLE_LIMIT * interval_trend
        entry_start = now - CANDLE_LIMIT * interval_entry
        trend_end = entry_end = now

        try:
            # 1) Recupera contratos futuros USDT
            contracts = await self.api.get_futures_contracts()
            symbols = [c["symbol"] for c in contracts if c.get("symbol")]
            logger.info(f"Total de {len(symbols)} símbolos encontrados.")

            # 2) Filtra por liquidez
            liquid = await self.liquidity_filter.filter_by_liquidez(symbols)
            if not liquid and symbols:
                liquid = symbols.copy()
                logger.info("Nenhum símbolo passou no filtro de liquidez; aplicando todos.")
            logger.info(f"{len(liquid)} símbolos passarão nos filtros seguintes.")

            # 3) Geração de sinais
            final_signals: List[dict] = []
            for sym in liquid:
                try:
                    # 3.1) Timeframe trend
                    trend_raw = await self.api.get_klines(
                        sym, interval=TIMEFRAME_TREND,
                        start=trend_start, end=trend_end
                    )
                    if not trend_raw:
                        continue
                    trend_df = self.api.klines_to_dataframe(trend_raw, sym)
                    if trend_df.empty or not self.signal_gen.check_context(trend_df):
                        continue
                    resistance = self.signal_gen.calculate_resistance_h1(trend_df)

                    # 3.2) Timeframe entry
                    entry_raw = await self.api.get_klines(
                        sym, interval=TIMEFRAME_ENTRY,
                        start=entry_start, end=entry_end
                    )
                    if not entry_raw:
                        continue
                    entry_df = self.api.klines_to_dataframe(entry_raw, sym)
                    if entry_df.empty:
                        continue

                    # 3.3) Gatilho técnico
                    signal = self.signal_gen.check_trigger(entry_df, resistance)
                    if not signal:
                        continue

                    # 3.4) Avalia fatores externos (para uso da IA)
                    factors = await self.ext_evaluator.evaluate_external_factors(sym, entry_df)
                    signal.update(factors)

                    # 3.5) Enriquecer sinal com volume médio e tendência
                    recent_vols = entry_df['volume'].tail(5).tolist()
                    avg_vol = sum(recent_vols) / len(recent_vols) if recent_vols else 0
                    recent_closes = entry_df['close'].tail(5).tolist()
                    trend_dir = (
                        "alta" if len(recent_closes) >= 2 and recent_closes[-1] > recent_closes[0]
                        else "baixa"
                    )
                    signal.update({"avg_volume": avg_vol, "trend": trend_dir})

                    final_signals.append(signal)

                except Exception as e:
                    logger.warning(f"Erro processando {sym}: {e}")

            # 4) Envia cada sinal individualmente no canal TECH
            for sig in final_signals:
                tech_msg = MessageFormatter.format_trade_signal(
                    symbol=sig["symbol"],
                    entry=sig["entry_price"],
                    stop_loss=sig["stop_loss"],
                    take_profit=sig["take_profit"],
                    indicators=sig.get("indicators", {})
                )
                await self.notifier.send_tech(tech_msg, parse_mode=ParseMode.HTML)

            # 5) Sugestões da IA (escolha de até dois ativos)
            if final_signals:
                tickers = []
                try:
                    response = suggest_best_coin(final_signals)
                    # Se a IA retornar lista, usá-la diretamente; se for string, dividir por vírgula
                    if isinstance(response, list):
                        tickers = response[:2]
                    else:
                        tickers = [t.strip() for t in response.split(",") if t.strip()][:2]

                    if tickers:
                        ai_msg = "🤖 <b>Sugestões da IA:</b>\n"
                        for tick in tickers:
                            sig = next((s for s in final_signals if s["symbol"] == tick), None)
                            if sig:
                                body = MessageFormatter.format_trade_signal(
                                    symbol=sig["symbol"],
                                    entry=sig["entry_price"],
                                    stop_loss=sig["stop_loss"],
                                    take_profit=sig["take_profit"],
                                    indicators=sig.get("indicators", {})
                                )
                                ai_msg += body + "\n"
                        await self.notifier.send_ai(ai_msg, parse_mode=ParseMode.HTML)
                except Exception:
                    logger.warning("Erro ao obter/enviar sugestão da IA:", exc_info=True)

                # 6) Log de performance dos sinais (timestamp, symbol, entry, SL, TP e sugestão)
                for sig in final_signals:
                    log_signal(sig, tickers)

            logger.info(f"{len(final_signals)} sinais processados. Mensagens enviadas aos canais VIP.")
            return final_signals

        except Exception as e:
            logger.error(f"Erro no screener: {e}", exc_info=True)
            err_msg = f"❌ <b>Erro no Screener:</b> {html.escape(str(e))}"
            await self.notifier.send_tech(err_msg, parse_mode=ParseMode.HTML)
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
    asyncio.run(ScreenerCore.create().run())
