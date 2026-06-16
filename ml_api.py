import requests
import random
import logging
from config import MIN_DISCOUNT_PERCENT, MAX_PRICE, MIN_PRICE, ML_AFFILIATE_ID

logger = logging.getLogger(__name__)

ML_API_BASE = "https://api.mercadolibre.com"

_posted_ids = set()

SEARCH_QUERIES = [
    "suplemento proteina",
    "whey protein",
    "creatina",
    "tenis corrida",
    "roupa academia",
    "bicicleta",
    "luva boxe",
    "colchonete yoga",
    "corda pular",
    "halteres",
    "kettlebell",
    "futebol chuteira",
    "mochila esporte",
    "garrafa termica",
]


def search_offers_lomadee() -> list[dict]:
    """
    Busca ofertas via Lomadee — plataforma de afiliados BR
    que agrega ofertas do ML com desconto, sem precisar de OAuth.
    """
    try:
        url = "https://api.lomadee.com/v3/BR/offer/_search"
        params = {
            "sourceId": "28571273",
            "token": "6296B1AA4BB2D2E6C57E",
            "keyword": random.choice(SEARCH_QUERIES),
            "categoryId": "6424",
            "size": 20,
        }
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            offers = data.get("offers", [])
            return [_normalize_lomadee(o) for o in offers if _filter_lomadee(o)]
    except Exception as e:
        logger.error(f"Erro Lomadee: {e}")
    return []


def _normalize_lomadee(offer: dict) -> dict:
    """Converte formato Lomadee para o formato interno do bot."""
    return {
        "id": str(offer.get("id", "")),
        "title": offer.get("name", ""),
        "price": float(offer.get("price", 0)),
        "original_price": float(offer.get("priceFrom") or offer.get("price", 0)),
        "permalink": offer.get("link", ""),
        "thumbnail": offer.get("thumbnail", ""),
        "pictures": [{"url": offer.get("thumbnail", "")}],
        "shipping": {"free_shipping": offer.get("freeShipping", False)},
        "_category_id": "MLB1276",
        "_source": "lomadee",
    }


def _filter_lomadee(offer: dict) -> bool:
    price = float(offer.get("price", 0))
    price_from = float(offer.get("priceFrom") or 0)
    if price < MIN_PRICE or price > MAX_PRICE:
        return False
    if price_from and price_from > price:
        discount = int(((price_from - price) / price_from) * 100)
        if discount < MIN_DISCOUNT_PERCENT:
            return False
    return True


def search_offers_ml_direct(query: str) -> list[dict]:
    """Busca direta na API pública do ML (sem OAuth)."""
    try:
        url = f"{ML_API_BASE}/sites/MLB/search"
        params = {"q": query, "sort": "relevance", "condition": "new", "limit": 50}
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code == 200:
            return resp.json().get("results", [])
    except Exception as e:
        logger.error(f"Erro ML direto '{query}': {e}")
    return []


def get_product_details(item_id: str) -> dict | None:
    try:
        resp = requests.get(f"{ML_API_BASE}/items/{item_id}", timeout=10)
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        logger.error(f"Erro ao buscar produto {item_id}: {e}")
    return None


def calculate_discount(original_price: float, sale_price: float) -> int:
    if not original_price or original_price <= sale_price:
        return 0
    return int(((original_price - sale_price) / original_price) * 100)


def filter_product(item: dict) -> bool:
    item_id = item.get("id")
    if item_id in _posted_ids:
        return False
    price = item.get("price", 0)
    if price < MIN_PRICE or price > MAX_PRICE:
        return False
    original_price = item.get("original_price") or 0
    discount = calculate_discount(original_price, price)
    if discount < MIN_DISCOUNT_PERCENT:
        return False
    return True


def get_best_offers() -> list[dict]:
    """Tenta Lomadee primeiro, cai para ML direto se falhar."""
    all_offers = []

    # Tenta Lomadee
    lomadee = search_offers_lomadee()
    if lomadee:
        logger.info(f"Lomadee: {len(lomadee)} ofertas")
        all_offers.extend(lomadee)

    # Complementa com ML direto
    if len(all_offers) < 5:
        for query in random.sample(SEARCH_QUERIES, 3):
            products = search_offers_ml_direct(query)
            good = [p for p in products if filter_product(p)]
            for product in good[:3]:
                details = get_product_details(product["id"])
                if details:
                    details["_category_id"] = "MLB1276"
                    all_offers.append(details)
                    _posted_ids.add(product["id"])

    random.shuffle(all_offers)
    logger.info(f"Total de ofertas: {len(all_offers)}")
    return all_offers


def format_price(price: float) -> str:
    return f"R$ {price:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
