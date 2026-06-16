import requests
import random
import logging
from config import (
    ML_SPORT_CATEGORIES, MIN_DISCOUNT_PERCENT, MIN_RATING,
    MIN_REVIEWS, MAX_PRICE, MIN_PRICE, PRODUCTS_PER_CATEGORY
)

logger = logging.getLogger(__name__)

ML_API_BASE = "https://api.mercadolibre.com"

# IDs já postados nesta sessão (evita repetir)
_posted_ids = set()


SEARCH_QUERIES = [
    "suplemento proteina",
    "whey protein",
    "creatina",
    "tenis corrida",
    "roupa academia",
    "ciclismo capacete",
    "bicicleta speed",
    "luva boxe",
    "colchonete yoga",
    "corda pular",
    "halteres",
    "kettlebell",
    "natacao oculos",
    "futebol chuteira",
]


def search_offers(category_id: str) -> list[dict]:
    """Busca produtos com desconto via query de texto (endpoint público)."""
    query = random.choice(SEARCH_QUERIES)
    try:
        url = f"{ML_API_BASE}/sites/MLB/search"
        params = {
            "q": query,
            "sort": "relevance",
            "condition": "new",
            "limit": 50,
        }
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return data.get("results", [])
    except Exception as e:
        logger.error(f"Erro ao buscar '{query}': {e}")
        return []


def get_product_details(item_id: str) -> dict | None:
    """Busca detalhes completos de um produto."""
    try:
        url = f"{ML_API_BASE}/items/{item_id}"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(f"Erro ao buscar produto {item_id}: {e}")
        return None


def calculate_discount(original_price: float, sale_price: float) -> int:
    """Calcula percentual de desconto."""
    if not original_price or original_price <= sale_price:
        return 0
    return int(((original_price - sale_price) / original_price) * 100)


def filter_product(item: dict) -> bool:
    """Retorna True se o produto passa nos filtros de qualidade."""
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

    rating = (item.get("seller_reputation") or {}).get("transactions", {})
    reviews = item.get("reviews", {})
    if reviews:
        if reviews.get("rating_average", 0) < MIN_RATING:
            return False
        if reviews.get("total", 0) < MIN_REVIEWS:
            return False

    return True


def get_best_offers() -> list[dict]:
    """Retorna os melhores produtos para postar hoje."""
    all_offers = []

    categories = ML_SPORT_CATEGORIES.copy()
    random.shuffle(categories)

    for category_id in categories:
        products = search_offers(category_id)
        good = [p for p in products if filter_product(p)]

        for product in good[:PRODUCTS_PER_CATEGORY]:
            details = get_product_details(product["id"])
            if details:
                details["_category_id"] = category_id
                all_offers.append(details)
                _posted_ids.add(product["id"])

    random.shuffle(all_offers)
    return all_offers


def format_price(price: float) -> str:
    """Formata preço no padrão brasileiro."""
    return f"R$ {price:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
