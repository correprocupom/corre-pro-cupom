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
    """
    Encurta o link usando o serviço gratuito TinyURL.
    Links curtos ficam melhor nas mensagens do Telegram.
    """
    try:
        resp = requests.get(
            f"https://tinyurl.com/api-create.php?url={url}",
            timeout=5
        )
        if resp.status_code == 200:
            return resp.text.strip()
    except Exception as e:
        logger.warning(f"Falha ao encurtar URL: {e}")
    return url


def get_affiliate_link(product_url: str, shorten: bool = True) -> str:
    """Gera link de afiliado (e encurta opcionalmente)."""
    link = build_affiliate_link(product_url)
    if shorten:
        link = shorten_url(link)
    return link
