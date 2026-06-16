import requests
import random
import logging
import re
import json
from config import MIN_DISCOUNT_PERCENT, MAX_PRICE, MIN_PRICE

logger = logging.getLogger(__name__)

_posted_ids = set()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36",
    "Accept-Language": "pt-BR,pt;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

SPORT_KEYWORDS = [
    "esport", "fitness", "academia", "muscula", "suplemento", "whey", "creatina",
    "proteina", "tenis", "corrida", "bike", "bicicleta", "natacao", "futebol",
    "chuteira", "haltere", "kettlebell", "luva", "agasalho", "ciclismo",
    "mochila esport", "garrafa term", "oculos natacao", "capacete", "adidas",
    "nike", "under armour", "puma", "speedo", "asics",
]

OFFER_URLS = [
    "https://www.mercadolivre.com.br/ofertas#nav-header",
    "https://www.mercadolivre.com.br/ofertas?page=2",
]


def _is_sport(text: str) -> bool:
    t = text.lower()
    return any(k in t for k in SPORT_KEYWORDS)


def _build_image_url(pic_id: str) -> str:
    return f"https://http2.mlstatic.com/D_NQ_NP_{pic_id}-O.jpg"


def _extract_items_from_page(url: str) -> list[dict]:
    """Busca e extrai produtos da página de ofertas do ML."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            logger.warning(f"ML retornou {resp.status_code} para {url}")
            return []

        if "suspicious" in resp.text:
            logger.warning("ML retornou página de CAPTCHA — IP bloqueado")
            return []

        match = re.search(r'_n\.ctx\.r\s*=\s*(\{.+)', resp.text)
        if not match:
            logger.warning("JSON de produtos não encontrado no HTML")
            return []

        data, _ = json.JSONDecoder().raw_decode(match.group(1))
        items = data.get("appProps", {}).get("pageProps", {}).get("data", {}).get("items", [])
        logger.info(f"Página {url}: {len(items)} itens encontrados")
        return items

    except Exception as e:
        logger.error(f"Erro ao buscar {url}: {e}")
        return []


def _parse_item(item: dict) -> dict | None:
    """Extrai e filtra dados de um produto."""
    try:
        card = item.get("card", {})
        meta = card.get("metadata", {})
        components = card.get("components", [])
        pictures_data = card.get("pictures", {})

        title = ""
        price = 0.0
        original_price = 0.0

        for comp in components:
            if comp.get("type") == "title":
                title = comp.get("title", {}).get("text", "")
            elif comp.get("type") == "price":
                p = comp.get("price", {})
                price = float(p.get("current_price", {}).get("value", 0))
                original_price = float(p.get("previous_price", {}).get("value", 0))

        if not title or not price:
            return None

        item_id = meta.get("id", "") or meta.get("product_id", "")
        if not item_id or item_id in _posted_ids:
            return None

        if price < MIN_PRICE or price > MAX_PRICE:
            return None

        if original_price and original_price > price:
            discount = int(((original_price - price) / original_price) * 100)
            if discount < MIN_DISCOUNT_PERCENT:
                return None
        else:
            return None

        url = meta.get("url", "")
        if url and not url.startswith("http"):
            url = "https://" + url

        pics = pictures_data.get("pictures", [])
        image = ""
        if pics:
            pic_id = pics[0].get("id", "")
            if pic_id:
                image = _build_image_url(pic_id)

        return {
            "id": item_id,
            "title": title,
            "price": price,
            "original_price": original_price,
            "permalink": url,
            "thumbnail": image,
            "pictures": [{"url": image}] if image else [],
            "shipping": {"free_shipping": False},
            "_category_id": "MLB1276",
            "_source": "ml_offers",
        }

    except Exception as e:
        logger.debug(f"Erro ao parsear item: {e}")
        return None


def get_best_offers() -> list[dict]:
    """Busca ofertas esportivas do ML e Amazon."""
    all_offers = []

    # Mercado Livre
    for page_url in OFFER_URLS:
        raw_items = _extract_items_from_page(page_url)
        for item in raw_items:
            product = _parse_item(item)
            if not product:
                continue
            if not _is_sport(product["title"]):
                continue
            all_offers.append(product)
            _posted_ids.add(product["id"])
            if len(all_offers) >= 10:
                break
        if len(all_offers) >= 10:
            break

    # Amazon
    try:
        from amazon_api import get_amazon_offers
        amazon_offers = get_amazon_offers()
        all_offers.extend(amazon_offers)
    except Exception as e:
        logger.warning(f"Amazon indisponível: {e}")

    random.shuffle(all_offers)
    logger.info(f"Total de ofertas (ML + Amazon): {len(all_offers)}")
    return all_offers


def calculate_discount(original_price: float, sale_price: float) -> int:
    if not original_price or original_price <= sale_price:
        return 0
    return int(((original_price - sale_price) / original_price) * 100)


def format_price(price: float) -> str:
    return f"R$ {price:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
