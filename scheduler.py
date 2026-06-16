import logging
import time
import random
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger
from ml_api import get_best_offers
from whatsapp_bot import send_offer, send_daily_intro
from config import POSTING_INTERVAL_MINUTES, START_HOUR, END_HOUR

logger = logging.getLogger(__name__)

scheduler = BlockingScheduler(timezone="America/Sao_Paulo")

# Fila de ofertas carregadas
_offer_queue: list[dict] = []


def is_within_posting_hours() -> bool:
    now = datetime.now()
    return START_HOUR <= now.hour < END_HOUR


def reload_offers() -> None:
    """Recarrega a fila de ofertas do Mercado Livre."""
    global _offer_queue
    logger.info("Buscando novas ofertas no Mercado Livre...")
    _offer_queue = get_best_offers()
    logger.info(f"{len(_offer_queue)} ofertas encontradas")


def post_next_offer() -> None:
    """Posta a próxima oferta da fila."""
    if not is_within_posting_hours():
        logger.info("Fora do horário de postagem, pulando...")
        return

    global _offer_queue
    if not _offer_queue:
        reload_offers()

    if not _offer_queue:
        logger.warning("Nenhuma oferta disponível no momento")
        return

    product = _offer_queue.pop(0)
    success = send_offer(product)

    if success:
        # Pequeno delay aleatório para parecer mais natural
        jitter = random.randint(0, 60)
        time.sleep(jitter)


def morning_routine() -> None:
    """Rotina matinal: mensagem de boas-vindas + carrega ofertas do dia."""
    send_daily_intro()
    reload_offers()


def start():
    logger.info("Iniciando agendador de ofertas...")

    # Carrega ofertas na inicialização
    reload_offers()

    # Posta a cada X minutos
    scheduler.add_job(
        post_next_offer,
        IntervalTrigger(minutes=POSTING_INTERVAL_MINUTES),
        id="post_offer",
        name="Postar oferta",
    )

    # Mensagem de bom dia + reload de ofertas todo dia às 8h
    scheduler.add_job(
        morning_routine,
        "cron",
        hour=START_HOUR,
        minute=0,
        id="morning",
        name="Rotina matinal",
    )

    # Recarrega ofertas ao meio-dia também
    scheduler.add_job(
        reload_offers,
        "cron",
        hour=12,
        minute=0,
        id="noon_reload",
        name="Reload meio-dia",
    )

    logger.info(f"Postando a cada {POSTING_INTERVAL_MINUTES} min entre {START_HOUR}h e {END_HOUR}h")
    scheduler.start()
