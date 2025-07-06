# mexc/mexc_api.py

import asyncio
import hashlib
import hmac
import json
import time
from urllib.parse import quote_plus

import aiohttp
import pandas as pd
import websockets

from config.settings import (
    MEXC_API_KEY,
    MEXC_SECRET_KEY,
    MEXC_BASE_URL,
    MEXC_WS_URL
 )
from mexc.mexc_endpoints import MexcEndpoints
from utils.logger import AppLogger

logger = AppLogger(__name__).get_logger()

class MexcApiAsync:
    def __init__(self):
        self.api_key = MEXC_API_KEY
        self.secret_key = MEXC_SECRET_KEY
        self.base_url = MEXC_BASE_URL
        self.ws_url = MEXC_WS_URL
        self.http = None
        self.ws = None

    async def init(self ):
        if not self.http:
            self.http = aiohttp.ClientSession( )
        return self

    @staticmethod
    def klines_to_dataframe(data: dict, symbol: str) -> pd.DataFrame:
        df = pd.DataFrame({
            "time": data.get("time", []),
            "open": data.get("open", []),
            "high": data.get("high", []),
            "low": data.get("low", []),
            "close": data.get("close", []),
            "volume": data.get("vol", []),
            "amount": data.get("amount", []),
        })
        df["time"] = pd.to_datetime(df["time"], unit="s")
        df["symbol"] = symbol
        return df

    async def close(self):
        if self.ws:
            await self.ws.close()
        if self.http:
            await self.http.close( )

    def _get_signature(self, timestamp: int, params: dict) -> str:
        param_str = "&".join(
            f"{k}={quote_plus(str(v))}" for k, v in sorted(params.items())
        ) if params else ""
        payload = f"{self.api_key}{timestamp}{param_str}"
        return hmac.new(
            self.secret_key.encode(), payload.encode(), hashlib.sha256
        ).hexdigest()

    async def _make_request(self, method: str, endpoint: str, params: dict = None, signed: bool = False) -> dict | list | None:
        params = params or {}
        headers = {"Accept": "application/json"}

        if signed:
            if not self.api_key or not self.secret_key:
                logger.error("API key não configurada para requisição assinada.")
                return None
            timestamp = int(time.time() * 1000)
            signature = self._get_signature(timestamp, params)
            headers.update({
                "ApiKey": self.api_key,
                "Request-Time": str(timestamp),
                "Signature": signature,
                "Content-Type": "application/json",
            })

        url = f"{self.base_url}{endpoint}"
        for attempt in range(3):
            try:
                async with self.http.request(
                    method=method.upper( ),
                    url=url,
                    params=params if method.upper() == "GET" else None,
                    json=params if method.upper() == "POST" else None,
                    headers=headers,
                ) as resp:
                    resp.raise_for_status()
                    if "application/json" in resp.headers.get("Content-Type", ""):
                        return await resp.json()
                    return None
            except Exception as e:
                if attempt == 2:
                    logger.error(f"Falha ao acessar {endpoint} após 3 tentativas: {e}")
                else:
                    logger.debug(f"Tentativa {attempt+1}/3 falhou para {endpoint}: {e}")
                await asyncio.sleep(0.5 * (attempt + 1))
        return None

    async def get_futures_contracts(self) -> list:
        data = await self._make_request("GET", MexcEndpoints.FUTURES_CONTRACTS)
        if not isinstance(data, dict) or "data" not in data:
            logger.warning("Resposta inesperada ao obter contratos futuros.")
            return []
        contracts = data["data"]
        filtered = [
            d for d in contracts
            if d.get("quoteCoin", "").upper() == "USDT"
            and int(d.get("futureType", 0)) == 1
        ]
        logger.info(f"{len(filtered)} contratos ativos (USDT).")
        return filtered

    async def get_klines(self, symbol: str, interval: str, start: int | None = None, end: int | None = None) -> dict | None:
        valid = {"Min1","Min5","Min15","Min30","Min60","Hour4","Hour8","Day1","Week1","Month1"}
        if interval not in valid:
            logger.warning(f"Intervalo inválido: {interval}.")
            return None
        params = {"interval": interval}
        if start is not None: params["start"] = start
        if end is not None:   params["end"] = end
        endpoint = f"{MexcEndpoints.KLINES}/{symbol}"
        resp = await self._make_request("GET", endpoint, params=params)
        if isinstance(resp, dict) and "data" in resp:
            return resp["data"]
        logger.warning(f"Formato inesperado de klines para {symbol}.")
        return None

    async def get_ticker(self, symbol: str) -> dict | None:
        return await self._make_request(
            "GET", MexcEndpoints.TICKER, params={"symbol": symbol}
        )

    async def obter_liquidez(self, symbol: str) -> tuple[float, float]:
        try:
            resp = await self.get_ticker(symbol)
            if not resp or not resp.get("success"):
                logger.debug(f"Ticker inválido ou ausente: {symbol}")
                return 0.0, 0.0
            data = resp.get("data", {})
            vol = float(data.get("volume24", data.get("amount24", 0)))
            oi = float(data.get("holdVol", data.get("hold_vol", 0)))
            return vol, oi
        except Exception as e:
            logger.debug(f"Erro ao obter liquidez para {symbol}: {e}")
            return 0.0, 0.0

    async def subscribe_kline(self, symbol: str, interval: str, callback: callable):
        if not self.ws:
            self.ws = await websockets.connect(self.ws_url)
        sub = json.dumps({"method":"sub.kline","param":{"symbol":symbol,"interval":interval}})
        await self.ws.send(sub)
        async for msg in self.ws:
            data = json.loads(msg)
            await callback(data)

    async def subscribe_ticker(self, symbol: str, callback: callable):
        if not self.ws:
            self.ws = await websockets.connect(self.ws_url)
        sub = json.dumps({"method":"sub.ticker","param":{"symbol":symbol}})
        await self.ws.send(sub)
        async for msg in self.ws:
            data = json.loads(msg)
            await callback(data)


