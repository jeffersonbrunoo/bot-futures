import asyncio
from config.settings import SCHEDULER_INTERVAL_MINUTES
from screener.screener_core import ScreenerCore
from utils.logger import AppLogger

logger = AppLogger(__name__).get_logger()

async def run_screener_job_async():
    """
    Executa o screener de forma assíncrona.
    """
    try:
        logger.info("Iniciando execução do Screener...")
        screener = await ScreenerCore.create()
        await screener.run()
        logger.info("Execução do Screener concluída.")
    except Exception as e:
        logger.error(f"Erro durante o Screener agendado: {e}", exc_info=True)

class JobScheduler:
    """
    Scheduler que executa o Screener periodicamente utilizando apenas asyncio.
    """
    def __init__(self):
        self.interval_minutes = SCHEDULER_INTERVAL_MINUTES
        self._stop = False

    async def start(self):
        """
        Inicia o loop de agendamento: executa imediatamente e depois a cada intervalo.
        """
        logger.info(f"Agendando Screener a cada {self.interval_minutes} minutos...")
        # execução imediata
        await run_screener_job_async()

        # loop periódico
        while not self._stop:
            await asyncio.sleep(self.interval_minutes * 60)
            await run_screener_job_async()

    def stop(self):
        """
        Sinaliza para parar o agendamento após a iteração atual.
        """
        self._stop = True
