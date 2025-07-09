import os
import csv
import asyncio
from datetime import datetime, timedelta
import pandas as pd
from mexc.mexc_api import MexcApiAsync
from config.telegram_config import TelegramConfig
from telegram import Bot

LOG_FILE = "signals_log.csv"
REPORT_DIR = "reports/daily"
# garante pasta de relatórios diários
os.makedirs(REPORT_DIR, exist_ok=True)

async def _get_daily_candle(symbol: str, date_str: str) -> dict:
    """
    Busca o candle diário (interval=1d) para `symbol` na data YYYY-MM-DD.
    Retorna dict com keys 'high' e 'low'.
    """
    client = await MexcApiAsync().init()
    # converte date_str em timestamps de início e fim de dia em ms
    dt = datetime.fromisoformat(date_str)
    start_ts = int(dt.timestamp() * 1000)
    end_ts = int((dt + timedelta(days=1)).timestamp() * 1000)
    candles = await client.get_klines(
        symbol,
        interval="1d",
        start=start_ts,
        end=end_ts
    )
    await client.close()
    if candles:
        c = candles[0]
        return {"high": float(c.get("high", 0)), "low": float(c.get("low", 0))}
    return {"high": 0.0, "low": 0.0}


def log_signal(signal: dict, suggestion: list):
    """Append sinal no CSV de log."""
    ts = datetime.utcnow().isoformat()
    row = [
        ts,
        signal.get("symbol"),
        signal.get("entry_price"),
        signal.get("stop_loss"),
        signal.get("take_profit"),
        ";".join(suggestion or [])
    ]
    with open(LOG_FILE, "a", newline="") as f:
        csv.writer(f).writerow(row)


def generate_daily_report():
    """
    Lê o CSV de logs, avalia TP/SL/OPEN por candle diário,
    gera métricas e envia relatório no Telegram.
    """
    # 1) Carrega CSV
    if not os.path.isfile(LOG_FILE):
        return
    df = pd.read_csv(
        LOG_FILE,
        names=["timestamp","symbol","entry","stop_loss","take_profit","suggested"]
    )
    if df.empty:
        return

    # 2) Avalia resultados diários
    statuses = []
    for _, r in df.iterrows():
        date = r["timestamp"][0:10]
        daily = asyncio.run(_get_daily_candle(r["symbol"], date))
        high, low = daily["high"], daily["low"]
        if high >= r["take_profit"]:
            statuses.append("TP")
        elif low <= r["stop_loss"]:
            statuses.append("SL")
        else:
            statuses.append("OPEN")
    df["status"] = statuses

    # 3) Calcula métricas de performance
    total   = len(df)
    tp_hits = (df.status == "TP").sum()
    sl_hits = (df.status == "SL").sum()
    open_c  = (df.status == "OPEN").sum()
    win_rate = tp_hits / (tp_hits + sl_hits) * 100 if (tp_hits + sl_hits) > 0 else 0.0

    report_date = df.at[df.index[-1], "timestamp"][0:10]
    report = (
        f"📈 *Relatório Diário de Sinais* ({report_date})\n"
        f"Total: {total}\n"
        f"✅ TP: {tp_hits}\n"
        f"❌ SL: {sl_hits}\n"
        f"⏳ Open: {open_c}\n"
        f"🏆 Win-rate: {win_rate:.1f}%"
    )

    # 4) Envia por Telegram
    bot = Bot(token=TelegramConfig.BOT_TOKEN)
    bot.send_message(
        chat_id=TelegramConfig.CHAT_ID,
        text=report,
        parse_mode="Markdown"
    )

    # 5) Salva relatório em arquivo
    fname = os.path.join(REPORT_DIR, f"report_{report_date}.txt")
    with open(fname, "w") as f:
        f.write(report)
