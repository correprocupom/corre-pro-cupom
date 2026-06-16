import requests
import random
import logging
from ml_auth import get_access_token
from config import MIN_DISCOUNT_PERCENT, MAX_PRICE, MIN_PRICE

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
    "garrafa termica esporte",
]

ML_SPORT_CATEGORIES = [
    "MLB1276",
    "MLB263535",
    "MLB1271",
    "MLB371",
    "MLB1245",
    "MLB3498",
]


def _auth_headers() -> dict:
    token = get_access_token()
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


def search_offers(query: str) -> list[dict]:
    """Busca produtos via query com autenticação."""
    try:
        resp = requests.get(
            f"{ML_API_BASE}/sites/MLB/search",
            params={"q": query, "sort": "relevance", "condition": "new", "limit": 50},
            headers=_auth_headers(),
            timeout=10,
        )
        if resp.status_code == 200:
            return resp.json().get("results", [])
        logger.error(f"Erro {resp.status_code} ao buscar '{query}'")
    except Exception as e:
        logger.error(f"Erro ao buscar '{query}': {e}")
    return []


def search_by_category(category_id: str) -> list[dict]:
    """Busca produtos por categoria com autenticação."""
    try:
        resp = requests.get(
            f"{ML_API_BASE}/sites/MLB/search",
            params={"category": category_id, "sort": "relevance", "condition": "new", "limit": 50},
            headers=_auth_headers(),
            timeout=10,
        )
        if resp.status_code == 200:
            return resp.json().get("results", [])
    except Exception as e:
        logger.error(f"Erro categoria {category_id}: {e}")
    return []


def get_product_details(item_id: str) -> dict | None:
    try:
        resp = requests.get(
            f"{ML_API_BASE}/items/{item_id}",
            headers=_auth_headers(),
            timeout=10,
        )
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        logger.error(f"Erro produto {item_id}: {e}")
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
    """Busca as melhores ofertas por query e categoria."""
    all_offers = []

    queries = random.sample(SEARCH_QUERIES, 5)
    for query in queries:
        products = search_offers(query)
        good = [p for p in products if filter_product(p)]
        for product in good[:3]:
            details = get_product_details(product["id"])
            if details:
                details["_category_id"] = "MLB1276"
                all_offers.append(details)
                _posted_ids.add(product["id"])

    categories = random.sample(ML_SPORT_CATEGORIES, 3)
    for cat in categories:
        products = search_by_category(cat)
        good = [p for p in products if filter_product(p)]
        for product in good[:2]:
            details = get_product_details(product["id"])
            if details:
                details["_category_id"] = cat
                all_offers.append(details)
                _posted_ids.add(product["id"])

    random.shuffle(all_offers)
    logger.info(f"Total de ofertas encontradas: {len(all_offers)}")
    return all_offers


def format_price(price: float) -> str:
    return f"R$ {price:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
