import logging
import time
import random
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger
from ml_api import get_best_offers, _mark_posted
from whatsapp_bot import send_offer, send_daily_intro
from config import POSTING_INTERVAL_MINUTES, START_HOUR, END_HOUR

logger = logging.getLogger(__name__)

scheduler = BlockingScheduler(timezone="America/Sao_Paulo")

_offer_queue: list[dict] = []
_posts_since_reload = 0
RELOAD_EVERY_N_POSTS = 10  # busca novos produtos a cada 10 postagens (~1h40 com intervalo de 10min)


def is_within_posting_hours() -> bool:
    now = datetime.now()
    return START_HOUR <= now.hour < END_HOUR


def reload_offers() -> None:
    """Recarrega a fila de ofertas."""
    global _offer_queue
    logger.info("Buscando novas ofertas no Mercado Livre...")
    _offer_queue = get_best_offers()
    logger.info(f"{len(_offer_queue)} ofertas encontradas")


def post_next_offer() -> None:
    global _offer_queue, _posts_since_reload

    if not is_within_posting_hours():
        logger.info("Fora do horário de postagem, pulando...")
        return

    # Recarrega a cada N postagens
    if _posts_since_reload >= RELOAD_EVERY_N_POSTS or not _offer_queue:
        reload_offers()
        _posts_since_reload = 0

    if not _offer_queue:
        logger.warning("Nenhuma oferta disponível")
        return

    product = _offer_queue.pop(0)
    success = send_offer(product)

    if success:
        _mark_posted(product["id"])
        _posts_since_reload += 1
        logger.info(f"Postagem {_posts_since_reload}/{RELOAD_EVERY_N_POSTS} antes do próximo reload")
        time.sleep(random.randint(5, 30))


def morning_routine() -> None:
    global _posts_since_reload
    _posts_since_reload = 0
    send_daily_intro()
    reload_offers()


def start():
    logger.info("Iniciando agendador de ofertas...")

    reload_offers()

    scheduler.add_job(
        post_next_offer,
        IntervalTrigger(minutes=POSTING_INTERVAL_MINUTES),
        id="post_offer",
        name="Postar oferta",
    )

    scheduler.add_job(
        morning_routine,
        "cron",
        hour=START_HOUR,
        minute=0,
        id="morning",
        name="Rotina matinal",
    )

    scheduler.add_job(
        reload_offers,
        "cron",
        hour=12,
        minute=0,
        id="noon_reload",
        name="Reload meio-dia",
    )

    logger.info(f"Postando a cada {POSTING_INTERVAL_MINUTES} min entre {START_HOUR}h e {END_HOUR}h")
    logger.info(f"Buscando novos produtos a cada {RELOAD_EVERY_N_POSTS} postagens")
    scheduler.start()
