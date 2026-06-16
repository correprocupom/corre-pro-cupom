import requests
import random
import logging
import re
import json
from config import MIN_DISCOUNT_PERCENT, MAX_PRICE, MIN_PRICE

logger = logging.getLogger(__name__)

_posted_ids = set()

SEARCH_QUERIES = [
    "whey-protein",
    "creatina",
    "suplemento-esportivo",
    "tenis-corrida",
    "roupa-academia",
    "bicicleta-speed",
    "luva-boxe",
    "halteres",
    "kettlebell",
    "chuteira-futebol",
    "mochila-esporte",
    "garrafa-termica",
    "oculos-natacao",
    "capacete-ciclismo",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "pt-BR,pt;q=0.9",
}


def search_ml_site(query: str) -> list[dict]:
    """Faz scraping do site do ML para buscar produtos com desconto."""
    try:
        url = f"https://lista.mercadolivre.com.br/{query}"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            logger.warning(f"ML site retornou {resp.status_code} para {query}")
            return []

        # Extrai JSON embutido na página (__PRELOADED_STATE__ ou similar)
        products = _parse_ml_html(resp.text, query)
        logger.info(f"'{query}': {len(products)} produtos encontrados")
        return products

    except Exception as e:
        logger.error(f"Erro ao buscar '{query}': {e}")
        return []


def _parse_ml_html(html: str, query: str) -> list[dict]:
    """Extrai produtos do HTML do ML."""
    products = []

    # Tenta extrair do JSON embutido
    pattern = r'"price":\s*(\d+(?:\.\d+)?)'
    prices = re.findall(pattern, html)

    # Extrai títulos
    title_pattern = r'"title":\s*"([^"]{10,100})"'
    titles = re.findall(title_pattern, html)

    # Extrai links de produtos
    link_pattern = r'"permalink":\s*"(https://www\.mercadolivre\.com\.br/[^"]+)"'
    links = re.findall(link_pattern, html)

    # Extrai imagens
    img_pattern = r'"thumbnail":\s*"(https://[^"]+\.jpg[^"]*)"'
    images = re.findall(img_pattern, html)

    # Extrai preços originais
    orig_pattern = r'"original_price":\s*(\d+(?:\.\d+)?)'
    orig_prices = re.findall(orig_pattern, html)

    # Combina os dados
    max_items = min(len(titles), len(prices), len(links), 10)
    for i in range(max_items):
        try:
            price = float(prices[i])
            original_price = float(orig_prices[i]) if i < len(orig_prices) else 0
            title = titles[i]
            link = links[i] if i < len(links) else ""
            image = images[i] if i < len(images) else ""

            item_id = f"{query}-{i}-{int(price)}"

            if item_id in _posted_ids:
                continue
            if price < MIN_PRICE or price > MAX_PRICE:
                continue
            if original_price and original_price > price:
                discount = int(((original_price - price) / original_price) * 100)
                if discount < MIN_DISCOUNT_PERCENT:
                    continue
            elif not original_price:
                continue  # sem desconto visível, pula

            products.append({
                "id": item_id,
                "title": title,
                "price": price,
                "original_price": original_price,
                "permalink": link,
                "thumbnail": image,
                "pictures": [{"url": image}] if image else [],
                "shipping": {"free_shipping": False},
                "_category_id": "MLB1276",
                "_source": "ml_site",
            })
        except (IndexError, ValueError):
            continue

    return products


def get_best_offers() -> list[dict]:
    """Busca as melhores ofertas via scraping do site ML."""
    all_offers = []
    queries = random.sample(SEARCH_QUERIES, 5)

    for query in queries:
        products = search_ml_site(query)
        for p in products[:3]:
            if p["id"] not in _posted_ids:
                all_offers.append(p)
                _posted_ids.add(p["id"])

    random.shuffle(all_offers)
    logger.info(f"Total de ofertas: {len(all_offers)}")
    return all_offers


def calculate_discount(original_price: float, sale_price: float) -> int:
    if not original_price or original_price <= sale_price:
        return 0
    return int(((original_price - sale_price) / original_price) * 100)


def format_price(price: float) -> str:
    return f"R$ {price:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
