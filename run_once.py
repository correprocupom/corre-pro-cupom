"""Executado pelo GitHub Actions a cada 30 minutos."""
import logging
import sys
from datetime import datetime, timezone, timedelta

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

BRT = timezone(timedelta(hours=-3))

def main():
    now = datetime.now(BRT)
    hour = now.hour
    if hour < 8 or hour >= 22:
        logger.info(f"Fora do horário ({hour}h BRT) — nada a postar.")
        return

    logger.info(f"Iniciando postagem ({hour}h BRT)...")

    from ml_api import get_best_offers
    from whatsapp_bot import send_offer

    offers = get_best_offers()
    if not offers:
        logger.info("Nenhuma oferta encontrada.")
        return

    offer = offers[0]
    logger.info(f"Postando: {offer['title']}")
    send_offer(offer)
    logger.info("Postagem concluída.")

if __name__ == "__main__":
    main()
