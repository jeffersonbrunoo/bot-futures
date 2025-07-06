import sys
import os
import asyncio

# Adiciona caminho do projeto
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configura o logger ANTES de qualquer outro import que use bibliotecas verbosas (httpx, aiohttp, etc.)
from utils.logger import AppLogger
logger = AppLogger(__name__).get_logger()

# Imports principais só após configurar o logger
from screener.screener_core import ScreenerCore
from scheduler.job_scheduler import JobScheduler

async def run_screener_once():
    logger.info("Executando screener em modo de execução única...")
    try:
        screener = await ScreenerCore.create()
        results = await screener.run()

        if not results:
            logger.info("Nenhum resultado encontrado no screener.")
            return

        logger.info("Execução única do screener concluída.")

    except Exception:
        logger.error("Erro ao executar screener", exc_info=True)

async def run_scheduler():
    scheduler = JobScheduler()
    await scheduler.start()

async def cli():
    if len(sys.argv) < 2:
        logger.info("Uso: python main.py [screener|scheduler]")
        return

    command = sys.argv[1].lower()

    if command == "screener":
        await run_screener_once()
    elif command == "scheduler":
        await run_scheduler()
    else:
        logger.error(f"Comando desconhecido: {command}")

if __name__ == "__main__":
    try:
        # Se já há um loop rodando, agendamos a execução
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        asyncio.ensure_future(cli())
    else:
        asyncio.run(cli())
