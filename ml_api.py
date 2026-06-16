import json
import random
import logging
import os
from config import MIN_DISCOUNT_PERCENT, MAX_PRICE, MIN_PRICE

logger = logging.getLogger(__name__)

_posted_ids = set()

_PRODUCTS_FILE = os.path.join(os.path.dirname(__file__), "products.json")


def _load_products() -> list[dict]:
    with open(_PRODUCTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def get_best_offers() -> list[dict]:
    """Retorna ofertas da lista curada com link de afiliado."""
    try:
        products = _load_products()
    except Exception as e:
        logger.error(f"Erro ao carregar products.json: {e}")
        return []

    eligible = []
    for p in products:
        if p["id"] in _posted_ids:
            continue
        price = p.get("price", 0)
        original = p.get("original_price", 0)
        if price < MIN_PRICE or price > MAX_PRICE:
            continue
        if original > price:
            discount = int(((original - price) / original) * 100)
            if discount < MIN_DISCOUNT_PERCENT:
                continue
        eligible.append({
            "id": p["id"],
            "title": p["title"],
            "price": price,
            "original_price": original,
            "permalink": p["permalink"],
            "thumbnail": p.get("thumbnail", ""),
            "pictures": [{"url": p["thumbnail"]}] if p.get("thumbnail") else [],
            "shipping": {"free_shipping": False},
            "_category_id": "MLB1276",
            "_source": "curated",
        })

    random.shuffle(eligible)
    offers = eligible[:3]

    for o in offers:
        _posted_ids.add(o["id"])

    # Reseta quando todos foram postados
    if len(_posted_ids) >= len(products):
        logger.info("Todos os produtos postados — reiniciando ciclo.")
        _posted_ids.clear()

    logger.info(f"Total de ofertas: {len(offers)}")
    return offers


def calculate_discount(original_price: float, sale_price: float) -> int:
    if not original_price or original_price <= sale_price:
        return 0
    return int(((original_price - sale_price) / original_price) * 100)


def format_price(price: float) -> str:
    return f"R$ {price:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
