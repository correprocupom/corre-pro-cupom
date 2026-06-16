import requests
import logging
from config import ML_AFFILIATE_ID

logger = logging.getLogger(__name__)


def build_affiliate_link(product_url: str) -> str:
    """
    Adiciona o parâmetro matid ao link do produto.
    Formato oficial do ML Afiliados: ?matid=wkXXXXXXXXXXXXXX
    """
    if not ML_AFFILIATE_ID:
        logger.warning("ML_AFFILIATE_ID não configurado — usando link sem afiliado")
        return product_url

    separator = "&" if "?" in product_url else "?"
    return f"{product_url}{separator}matid={ML_AFFILIATE_ID}"


def shorten_url(url: str) -> str:
    """Encurta o link usando is.gd (gratuito, sem página de preview)."""
    try:
        resp = requests.get(
            "https://is.gd/create.php",
            params={"format": "simple", "url": url},
            timeout=5
        )
        if resp.status_code == 200 and resp.text.startswith("https://"):
            return resp.text.strip()
    except Exception as e:
        logger.warning(f"Falha ao encurtar URL: {e}")
    return url


def get_affiliate_link(product_url: str, shorten: bool = False) -> str:
    """Gera link de afiliado."""
    return build_affiliate_link(product_url)
