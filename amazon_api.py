import requests
import re
import random
import logging
import os
from config import MIN_DISCOUNT_PERCENT, MAX_PRICE, MIN_PRICE

logger = logging.getLogger(__name__)

_posted_ids = set()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "pt-BR,pt;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

AMAZON_AFFILIATE_TAG = os.getenv("AMAZON_AFFILIATE_TAG", "")

SPORT_URLS = [
    "https://www.amazon.com.br/s?rh=n%3A16209740011&s=discount-rate-desc",
    "https://www.amazon.com.br/s?rh=n%3A16253587011&s=discount-rate-desc",
    "https://www.amazon.com.br/s?k=suplemento+esportivo&s=discount-rate-desc",
    "https://www.amazon.com.br/s?k=tenis+corrida&s=discount-rate-desc",
]

SPORT_KEYWORDS = [
    "esport", "fitness", "academia", "muscula", "suplemento", "whey", "creatina",
    "proteina", "tenis", "corrida", "bike", "bicicleta", "natacao", "futebol",
    "chuteira", "haltere", "kettlebell", "luva", "agasalho", "ciclismo",
    "adidas", "nike", "under armour", "puma", "speedo", "asics", "mochila",
    "figurinha", "copa", "esporte",
]


def _is_sport(text: str) -> bool:
    t = text.lower()
    return any(k in t for k in SPORT_KEYWORDS)


def _build_affiliate_url(asin: str) -> str:
    url = f"https://www.amazon.com.br/dp/{asin}"
    if AMAZON_AFFILIATE_TAG:
        return f"{url}?tag={AMAZON_AFFILIATE_TAG}"
    return url


def _parse_price(text: str) -> float:
    text = re.sub(r'[R$\s\xa0&;a-zA-Z]', '', text)
    text = text.replace('.', '').replace(',', '.')
    try:
        return float(text)
    except ValueError:
        return 0.0


def _fetch_amazon_deals(url: str) -> list[dict]:
    products = []
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            logger.warning(f"Amazon retornou {resp.status_code}")
            return []

        if "api-services-support@amazon.com" in resp.text:
            logger.warning("Amazon retornou CAPTCHA")
            return []

        html = resp.text

        # Divide em blocos por ASIN (cada resultado de busca)
        asin_positions = [(m.start(), m.group(1)) for m in re.finditer(r'data-asin="([A-Z0-9]{10})"', html)]
        logger.info(f"Amazon: {len(asin_positions)} produtos encontrados na pagina")

        for idx, (pos, asin) in enumerate(asin_positions):
            # Pega o bloco até o próximo ASIN ou 8000 chars
            end = asin_positions[idx + 1][0] if idx + 1 < len(asin_positions) else pos + 8000
            block = html[pos:min(end, pos + 8000)]

            item_id = f"amz-{asin}"
            if item_id in _posted_ids:
                continue

            # Título via h2
            title_match = re.search(r'<h2[^>]*>.*?<span[^>]*>([^<]{10,200})<', block, re.DOTALL)
            if not title_match:
                continue
            title = title_match.group(1).strip()

            # Preços via a-offscreen (mais confiável)
            price_texts = re.findall(r'<span class="a-offscreen">([^<]+)</span>', block)
            price = 0.0
            original_price = 0.0
            for pt in price_texts:
                if 'R$' in pt or 'R&#36;' in pt:
                    val = _parse_price(pt)
                    if val > 0 and price == 0:
                        price = val
                    elif val > price and original_price == 0:
                        original_price = val

            # Tenta também padrão direto
            if price == 0:
                p_match = re.search(r'<span class="a-price-whole">(\d+)', block)
                f_match = re.search(r'<span class="a-price-fraction">(\d+)', block)
                if p_match:
                    frac = f_match.group(1) if f_match else "00"
                    price = float(f"{p_match.group(1)}.{frac}")

            if price == 0:
                continue

            # Preço original via "De:"
            if original_price == 0:
                de_match = re.search(r'De:.*?R\$[^\d]*([\d.,]+)', block, re.DOTALL)
                if de_match:
                    original_price = _parse_price(de_match.group(1))

            # Imagem
            img_match = re.search(r'src="(https://m\.media-amazon\.com[^"]+)"', block)
            image = img_match.group(1) if img_match else ""

            permalink = _build_affiliate_url(asin)

            if price < MIN_PRICE or price > MAX_PRICE:
                continue

            if original_price and original_price > price:
                discount = int(((original_price - price) / original_price) * 100)
                if discount < MIN_DISCOUNT_PERCENT:
                    continue
            else:
                continue

            if not _is_sport(title):
                continue

            products.append({
                "id": item_id,
                "title": title,
                "price": price,
                "original_price": original_price,
                "permalink": permalink,
                "thumbnail": image,
                "pictures": [{"url": image}] if image else [],
                "shipping": {"free_shipping": False},
                "_category_id": "AMAZON",
                "_source": "amazon",
            })

    except Exception as e:
        logger.error(f"Erro ao buscar Amazon: {e}")

    logger.info(f"Amazon: {len(products)} produtos esportivos com desconto")
    return products


def get_amazon_offers() -> list[dict]:
    all_offers = []
    url = random.choice(SPORT_URLS)
    products = _fetch_amazon_deals(url)

    for p in products[:5]:
        if p["id"] not in _posted_ids:
            all_offers.append(p)
            _posted_ids.add(p["id"])

    logger.info(f"Amazon total: {len(all_offers)} ofertas")
    return all_offers
