import time
import schedule
import asyncio
from threading import Thread
from config.settings import SCHEDULER_INTERVAL_MINUTES
from screener.screener_core import ScreenerCore
from utils.logger import AppLogger

logger = AppLogger(__name__).get_logger()

def run_screener_job():
    """
    Executa o screener em uma thread isolada com seu próprio event loop.
    """
    def _run():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(run_screener_job_async())
        finally:
            loop.close()

    thread = Thread(target=_run)
    thread.start()


async def run_screener_job_async():
    """
    Executa o screener de forma assíncrona.
    """
    logger.info("Iniciando job do screener...")
    screener = await ScreenerCore.create()
    await screener.run()
    logger.info("Job do screener concluído.")


class JobScheduler:
    def __init__(self):
        self.interval_minutes = SCHEDULER_INTERVAL_MINUTES

    async def start(self):
        logger.info(f"Agendando screener para rodar a cada {self.interval_minutes} minutos...")
        schedule.every(self.interval_minutes).minutes.do(run_screener_job)

        run_screener_job()  # roda na inicialização

        self._run_continuously()

        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Scheduler parado pelo usuário.")

    def _run_continuously(self, interval=1):
        thread = Thread(target=self._schedule_loop, args=(interval,))
        thread.daemon = True
        thread.start()

    def _schedule_loop(self, interval):
        while True:
            schedule.run_pending()
            time.sleep(interval)
