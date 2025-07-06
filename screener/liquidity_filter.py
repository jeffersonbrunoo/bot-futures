import asyncio
from typing import List, Optional

from config.settings import (
    MIN_VOLUME_24H_USD,
    MIN_OPEN_INTEREST_USD
)
from mexc.mexc_api import MexcApiAsync
from utils.logger import AppLogger

logger = AppLogger(__name__).get_logger()

class LiquidityFilter:
    def __init__(self, api: MexcApiAsync):
        self.api = api

    async def filter_by_liquidez(self, symbols: List[str], max_concurrent: int = 5) -> List[str]:
        sem = asyncio.Semaphore(max_concurrent)
        failed_syms: List[str] = []

        async def _check(sym: str) -> Optional[str]:
            async with sem:
                try:
                    vol, oi = await self.api.obter_liquidez(sym)
                    logger.debug(f"{sym} - Vol: {vol}, OI: {oi}")
                    if vol >= MIN_VOLUME_24H_USD and oi >= MIN_OPEN_INTEREST_USD:
                        return sym
                    # mark as failed
                    failed_syms.append(sym)
                    return None
                except Exception as e:
                    failed_syms.append(sym)
                    logger.debug(f"Erro ao obter liquidez para {sym}: {e}")
                    return None

        tasks = [asyncio.create_task(_check(s)) for s in symbols]
        results = await asyncio.gather(*tasks)
        passed = [r for r in results if r]

        # Inform only count
        logger.info(f"{len(passed)} símbolos passaram no filtro de liquidez.")
        # Detailed failures kept at debug level
        if failed_syms:
            logger.debug(f"Símbolos excluídos por liquidez insuficiente ou erro: {failed_syms}")

        return passed
