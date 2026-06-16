import requests
import random
import logging
import re
import json
import os
from datetime import datetime, timedelta
from config import MIN_DISCOUNT_PERCENT, MAX_PRICE, MIN_PRICE, SPORT_KEYWORDS

logger = logging.getLogger(__name__)

POSTED_IDS_FILE = os.path.join(os.path.dirname(__file__), "posted_ids.json")
POSTED_IDS_EXPIRE_DAYS = 7  # não repete o mesmo produto por 7 dias

def _load_posted_ids() -> dict:
    """Carrega IDs postados com timestamp do arquivo."""
    try:
        if os.path.exists(POSTED_IDS_FILE):
            with open(POSTED_IDS_FILE, "r") as f:
                return json.load(f)
    except Exception:
        pass
    return {}

def _save_posted_ids(data: dict) -> None:
    try:
        with open(POSTED_IDS_FILE, "w") as f:
            json.dump(data, f)
    except Exception as e:
        logger.warning(f"Erro ao salvar posted_ids: {e}")

def _clean_expired(data: dict) -> dict:
    """Remove IDs mais antigos que 7 dias."""
    cutoff = (datetime.now() - timedelta(days=POSTED_IDS_EXPIRE_DAYS)).isoformat()
    return {k: v for k, v in data.items() if v >= cutoff}

def _is_posted(item_id: str) -> bool:
    data = _load_posted_ids()
    return item_id in data

def _mark_posted(item_id: str) -> None:
    data = _load_posted_ids()
    data = _clean_expired(data)
    data[item_id] = datetime.now().isoformat()
    _save_posted_ids(data)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36",
    "Accept-Language": "pt-BR,pt;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

OFFER_URLS = [
    # Maior desconto
    "https://www.mercadolivre.com.br/ofertas#nav-header",
    "https://www.mercadolivre.com.br/ofertas?page=2",
    # Maior desconto por categoria
    "https://lista.mercadolivre.com.br/suplemento-esportivo_OrderId_PRICE*DESC_NoIndex_True",
    "https://lista.mercadolivre.com.br/whey-protein_OrderId_PRICE*DESC_NoIndex_True",
    "https://lista.mercadolivre.com.br/tenis-corrida_OrderId_PRICE*DESC_NoIndex_True",
    "https://lista.mercadolivre.com.br/creatina_OrderId_PRICE*DESC_NoIndex_True",
    "https://lista.mercadolivre.com.br/halteres-musculacao_OrderId_PRICE*DESC_NoIndex_True",
    "https://lista.mercadolivre.com.br/roupa-academia_OrderId_PRICE*DESC_NoIndex_True",
    # Menor preço por categoria
    "https://lista.mercadolivre.com.br/suplemento-esportivo_OrderId_PRICE*ASC_NoIndex_True",
    "https://lista.mercadolivre.com.br/whey-protein_OrderId_PRICE*ASC_NoIndex_True",
    "https://lista.mercadolivre.com.br/tenis-corrida_OrderId_PRICE*ASC_NoIndex_True",
    "https://lista.mercadolivre.com.br/kettlebell_OrderId_PRICE*ASC_NoIndex_True",
    "https://lista.mercadolivre.com.br/luva-boxe_OrderId_PRICE*ASC_NoIndex_True",
    "https://lista.mercadolivre.com.br/bicicleta-speed_OrderId_PRICE*ASC_NoIndex_True",
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

        # Tenta estrutura da página de ofertas (/_n.ctx.r)
        match = re.search(r'_n\.ctx\.r\s*=\s*(\{.+)', resp.text)
        if match:
            data, _ = json.JSONDecoder().raw_decode(match.group(1))
            items = data.get("appProps", {}).get("pageProps", {}).get("data", {}).get("items", [])
        else:
            # Tenta estrutura da página de busca (lista.mercadolivre)
            items = _parse_search_page(resp.text)

        if not items:
            logger.warning("Nenhum item encontrado no HTML")
            return []
        logger.info(f"Página {url}: {len(items)} itens encontrados")
        return items

    except Exception as e:
        logger.error(f"Erro ao buscar {url}: {e}")
        return []


def _parse_search_page(html: str) -> list[dict]:
    """Parser para páginas de busca do lista.mercadolivre.com.br."""
    items = []
    try:
        # Tenta extrair JSON do __PRELOADED_STATE__ ou similar
        match = re.search(r'window\.__PRELOADED_STATE__\s*=\s*(\{.+?);\s*</script>', html, re.DOTALL)
        if not match:
            match = re.search(r'"results"\s*:\s*(\[.+?\])\s*,\s*"paging"', html, re.DOTALL)
        if not match:
            return []
        raw = match.group(1)
        results = json.loads(raw) if raw.startswith('[') else json.loads(match.group(1)).get("results", [])
        for r in results:
            items.append({"card": {
                "metadata": {"id": r.get("id",""), "url": r.get("permalink","")},
                "components": [
                    {"type": "title", "title": {"text": r.get("title","")}},
                    {"type": "price", "price": {
                        "current_price": {"value": r.get("price", 0)},
                        "previous_price": {"value": r.get("original_price", 0)},
                    }},
                ],
                "pictures": {"pictures": [{"id": p.get("id","") for p in r.get("pictures", [])} if r.get("pictures") else {}]},
            }})
    except Exception as e:
        logger.debug(f"Erro ao parsear página de busca: {e}")
    return items


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
        if not item_id or _is_posted(item_id):
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
            if len(all_offers) >= 10:
                break
        if len(all_offers) >= 10:
            break

    # Amazon via Product Advertising API (habilitar quando tiver 3 vendas qualificadas)
    # from amazon_api import get_amazon_offers
    # all_offers.extend(get_amazon_offers())

    random.shuffle(all_offers)
    logger.info(f"Total de ofertas (ML + Amazon): {len(all_offers)}")
    return all_offers


def calculate_discount(original_price: float, sale_price: float) -> int:
    if not original_price or original_price <= sale_price:
        return 0
    return int(((original_price - sale_price) / original_price) * 100)


def format_price(price: float) -> str:
    return f"R$ {price:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
