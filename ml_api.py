import requests
import random
import logging
import re
import xml.etree.ElementTree as ET
from config import MIN_DISCOUNT_PERCENT, MAX_PRICE, MIN_PRICE

logger = logging.getLogger(__name__)

_posted_ids = set()

PROMOBIT_FEEDS = [
    "https://www.promobit.com.br/oferta/esporte-e-fitness/feed/",
    "https://www.promobit.com.br/oferta/suplementos/feed/",
    "https://www.promobit.com.br/feed/",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36",
    "Accept": "application/rss+xml,application/xml,text/xml,*/*",
    "Accept-Language": "pt-BR,pt;q=0.9",
}

SPORT_KEYWORDS = [
    "esport", "fitness", "academia", "muscula", "suplemento", "whey", "creatina",
    "proteina", "tenis", "corrida", "bike", "bicicleta", "natacao", "futebol",
    "chuteira", "haltere", "kettlebell", "luva", "mochila", "ciclismo",
]


def _is_sport(text: str) -> bool:
    t = text.lower()
    return any(k in t for k in SPORT_KEYWORDS)


def _extract_price(text: str) -> float:
    match = re.search(r'R\$\s*([\d.,]+)', text)
    if match:
        return float(match.group(1).replace('.', '').replace(',', '.'))
    match = re.search(r'([\d]+),([\d]{2})', text)
    if match:
        return float(f"{match.group(1)}.{match.group(2)}")
    return 0.0


def _extract_original_price(text: str) -> float:
    matches = re.findall(r'R\$\s*([\d.,]+)', text)
    if len(matches) >= 2:
        prices = [float(m.replace('.', '').replace(',', '.')) for m in matches]
        prices.sort(reverse=True)
        return prices[0]
    return 0.0


def _fetch_promobit_feed(url: str) -> list[dict]:
    """Busca e parseia RSS do Promobit."""
    products = []
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        logger.info(f"Promobit {url}: status {resp.status_code}")
        if resp.status_code != 200:
            return []

        root = ET.fromstring(resp.content)
        ns = {'media': 'http://search.yahoo.com/mrss/'}
        channel = root.find('channel')
        if channel is None:
            return []

        items = channel.findall('item')
        logger.info(f"Promobit: {len(items)} itens no feed")

        for item in items:
            try:
                title = item.findtext('title', '')
                link = item.findtext('link', '')
                description = item.findtext('description', '') or ''
                guid = item.findtext('guid', link)

                if not _is_sport(title + ' ' + description):
                    continue

                full_text = title + ' ' + description
                price = _extract_price(full_text)
                original_price = _extract_original_price(full_text)

                if price <= 0:
                    continue
                if price < MIN_PRICE or price > MAX_PRICE:
                    continue

                if original_price > price:
                    discount = int(((original_price - price) / original_price) * 100)
                    if discount < MIN_DISCOUNT_PERCENT:
                        continue
                else:
                    original_price = price * 1.3  # assume 30% off se não tiver preço original

                item_id = re.sub(r'[^a-z0-9]', '-', (guid or link).lower())[:60]
                if item_id in _posted_ids:
                    continue

                image = ''
                media_content = item.find('media:content', ns)
                if media_content is not None:
                    image = media_content.get('url', '')
                if not image:
                    enclosure = item.find('enclosure')
                    if enclosure is not None:
                        image = enclosure.get('url', '')
                if not image:
                    img_match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', description)
                    if img_match:
                        image = img_match.group(1)

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
                    "_source": "promobit",
                })
            except Exception as e:
                logger.debug(f"Erro ao processar item: {e}")
                continue

    except Exception as e:
        logger.error(f"Erro ao buscar feed {url}: {e}")

    return products


def get_best_offers() -> list[dict]:
    """Busca ofertas esportivas via Promobit RSS."""
    all_offers = []

    for feed_url in PROMOBIT_FEEDS:
        products = _fetch_promobit_feed(feed_url)
        for p in products[:5]:
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
