import requests
import logging
from io import BytesIO
from ml_api import calculate_discount, format_price
from affiliate import get_affiliate_link
from config import (
    TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID,
    CATEGORY_EMOJIS, DEFAULT_HASHTAGS
)

logger = logging.getLogger(__name__)

TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"


def build_message(product: dict) -> str:
    """Monta o texto da mensagem no estilo dos grupos de oferta."""
    title = product.get("title", "Produto")
    price = product.get("price", 0)
    original_price = product.get("original_price") or 0
    discount = calculate_discount(original_price, price)
    category_id = product.get("_category_id", "")
    emoji = CATEGORY_EMOJIS.get(category_id, "🏷️")

    url = product.get("permalink", "")
    affiliate_link = get_affiliate_link(url)

    lines = [f"{emoji} *{title}*\n"]

    if original_price and discount > 0:
        lines.append(f"~~De {format_price(original_price)}~~ por *{format_price(price)}*")
        lines.append(f"🔥 *{discount}% OFF*\n")
    else:
        lines.append(f"💰 *{format_price(price)}*\n")

    free_shipping = product.get("shipping", {}).get("free_shipping", False)
    if free_shipping:
        lines.append("✅ Frete grátis\n")

    lines.append(f"🛒 [Comprar agora]({affiliate_link})\n")
    lines.append(DEFAULT_HASHTAGS)

    return "\n".join(lines)


def get_product_image_url(product: dict) -> str | None:
    """Pega a URL da imagem principal do produto."""
    pictures = product.get("pictures", [])
    if pictures:
        return pictures[0].get("url") or pictures[0].get("secure_url")
    thumbnail = product.get("thumbnail", "")
    return thumbnail.replace("I.jpg", "O.jpg") if thumbnail else None


def send_offer(product: dict) -> bool:
    """Envia uma oferta para o canal Telegram."""
    try:
        message = build_message(product)
        image_url = get_product_image_url(product)

        if image_url:
            resp = requests.post(
                f"{TELEGRAM_API}/sendPhoto",
                json={
                    "chat_id": TELEGRAM_CHANNEL_ID,
                    "photo": image_url,
                    "caption": message,
                    "parse_mode": "Markdown",
                },
                timeout=15,
            )
        else:
            resp = requests.post(
                f"{TELEGRAM_API}/sendMessage",
                json={
                    "chat_id": TELEGRAM_CHANNEL_ID,
                    "text": message,
                    "parse_mode": "Markdown",
                    "disable_web_page_preview": False,
                },
                timeout=15,
            )

        if resp.status_code == 200:
            logger.info(f"Postado: {product.get('title', '')[:50]}")
            return True
        else:
            logger.error(f"Telegram erro {resp.status_code}: {resp.text}")
            return False

    except Exception as e:
        logger.error(f"Erro ao enviar oferta: {e}")
        return False


def send_daily_intro() -> None:
    """Envia mensagem de boas-vindas no início do dia."""
    message = (
        "🏆 *Bom dia, atletas!*\n\n"
        "As melhores ofertas de esporte e fitness do dia chegaram! "
        "Fique ligado que vem muito mais por aí 👇\n\n"
        "#esporte #fitness #ofertas"
    )
    requests.post(
        f"{TELEGRAM_API}/sendMessage",
        json={
            "chat_id": TELEGRAM_CHANNEL_ID,
            "text": message,
            "parse_mode": "Markdown",
        },
        timeout=10,
    )


def test_connection() -> bool:
    """Testa se o bot está configurado corretamente."""
    try:
        resp = requests.get(f"{TELEGRAM_API}/getMe", timeout=5)
        if resp.status_code == 200:
            bot_info = resp.json().get("result", {})
            logger.info(f"Bot conectado: @{bot_info.get('username')}")
            return True
        logger.error(f"Token inválido: {resp.text}")
        return False
    except Exception as e:
        logger.error(f"Sem conexão com Telegram: {e}")
        return False
