import html
from typing import List, Union, Dict, Any

class MessageFormatter:
    @staticmethod
    def format_trade_signal(
        symbol: str,
        entry: float,
        stop_loss: float,
        take_profit: float,
        indicators: Dict[str, Any]
    ) -> str:
        # Escapa texto para HTML
        sym     = html.escape(symbol)
        ent     = html.escape(f"{entry:.4f}")
        sl      = html.escape(f"{stop_loss:.4f}")
        tp      = html.escape(f"{take_profit:.4f}")
        ema_s   = html.escape(f"{indicators.get('ema_short', 0):.4f}")
        ema_l   = html.escape(f"{indicators.get('ema_long', 0):.4f}")
        rsi     = html.escape(f"{indicators.get('rsi', 0):.2f}")
        macd    = html.escape(f"{indicators.get('macd', 0):.4f}")
        macd_s  = html.escape(f"{indicators.get('macd_signal', 0):.4f}")
        vol     = html.escape(f"{indicators.get('volume', 0):.2f}")
        vol_ma  = html.escape(f"{indicators.get('volume_ma', 0):.2f}")

        return (
            "🚨 <b>SINAL DE VENDA IDENTIFICADO</b> 🚨\n\n"
            f"<b>Símbolo:</b> <code>{sym}</code>\n"
            f"<b>Entrada:</b> <code>{ent}</code>\n"
            f"<b>Stop Loss:</b> <code>{sl}</code> ❌\n"
            f"<b>Take Profit:</b> <code>{tp}</code> ✅\n\n"
            "📊 <b>Indicadores Técnicos:</b>\n"
            f"• EMA Curta: <code>{ema_s}</code>\n"
            f"• EMA Longa: <code>{ema_l}</code>\n"
            f"• RSI(14): <code>{rsi}</code>\n"
            f"• MACD: <code>{macd}</code> vs Signal: <code>{macd_s}</code>\n"
            f"• Volume: <code>{vol}</code> > MA({vol_ma})\n\n"
            "Lembre-se de gerenciar o risco adequadamente! 🛡️"
        )

    @staticmethod
    def format_screener_results(
        results: List[Union[Dict[str, Any], tuple]],
        suggestion: str = None
    ) -> str:
        parts: List[str] = []

        if not results:
            parts.append("🤖 Screener executado: nenhuma oportunidade encontrada.")
        else:
            for item in results:
                if isinstance(item, dict):
                    symbol = item.get("symbol")
                    entry  = item.get("entry") or item.get("entry_price") or item.get("price")
                    sl     = item.get("stop_loss")
                    tp     = item.get("take_profit")
                    ind    = item.get("indicators", {})
                else:
                    try:
                        symbol, entry, sl, tp, ind = item
                    except Exception:
                        continue

                if None in (symbol, entry, sl, tp):
                    continue

                parts.append(
                    MessageFormatter.format_trade_signal(
                        symbol=symbol,
                        entry=float(entry),
                        stop_loss=float(sl),
                        take_profit=float(tp),
                        indicators=ind or {}
                    )
                )

        # Sugestão da IA
        if suggestion:
            sug = html.escape(suggestion)
            parts.append(f"🤖 <b>Sugestão da IA:</b>\n<code>{sug}</code>")

        return "\n\n".join(parts)
