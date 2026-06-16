import requests
import logging
from ml_api import calculate_discount, format_price
from affiliate import get_affiliate_link
from config import (
    EVOLUTION_API_URL, EVOLUTION_API_KEY, EVOLUTION_INSTANCE,
    WA_CHANNEL_ID, WA_GROUP_IDS,
    CATEGORY_EMOJIS, DEFAULT_HASHTAGS
)

logger = logging.getLogger(__name__)


def _headers() -> dict:
    return {
        "apikey": EVOLUTION_API_KEY,
        "Content-Type": "application/json",
    }


TITLE_EMOJIS = [
    (["corrida", "runner", "correr", "run ", "atletismo", "maratona"], "🏃"),
    (["musculacao", "musculação", "haltere", "halter", "peso", "barra", "anilha", "supino", "agachamento"], "🏋️"),
    (["bike", "biciclet", "ciclis", "mountain bike", "mtb", "spinning"], "🚴"),
    (["futebol", "chuteira", "bola de futebol", "campo", "society"], "⚽"),
    (["tenis", "tênis", "calçado esport", "sapatilha"], "👟"),
    (["natacao", "natação", "nado", "piscina", "oculos de natacao", "touca"], "🏊"),
    (["whey", "proteina", "proteína", "suplemento", "creatina", "bcaa", "pre-treino", "pre treino", "colageno", "colágeno", "vitamina"], "💊"),
    (["yoga", "pilates", "meditacao", "meditação", "tapete"], "🧘"),
    (["boxe", "muay thai", "mma", "luta", "luva", "saco de pancada"], "🥊"),
    (["crossfit", "funcional", "kettlebell", "corda de pular", "speed rope"], "💪"),
    (["agasalho", "camiseta", "bermuda", "short", "legging", "roupa", "uniforme", "moletom"], "👕"),
    (["mochila", "bolsa esport", "bag esport"], "🎒"),
    (["garrafa", "squeeze", "coqueteleira", "shaker"], "🥤"),
    (["smartwatch", "relogio", "relógio", "monitor cardiaco", "gps esport"], "⌚"),
    (["futebol americano", "basquete", "basquetebol", "volei", "vôlei", "handball"], "🏀"),
    (["skate", "patins", "patinete"], "🛹"),
    (["natacao", "surf", "stand up", "sup "], "🏄"),
    (["tiro", "arco", "flecha"], "🎯"),
]


def _get_emoji(title: str) -> str:
    t = title.lower()
    for keywords, emoji in TITLE_EMOJIS:
        if any(k in t for k in keywords):
            return emoji
    return "🏷️"


def build_message(product: dict) -> str:
    """Monta o texto da mensagem no estilo dos grupos de oferta."""
    title = product.get("title", "Produto")
    price = product.get("price", 0)
    original_price = product.get("original_price") or 0
    discount = calculate_discount(original_price, price)
    emoji = _get_emoji(title)

    url = product.get("permalink", "")
    affiliate_link = get_affiliate_link(url)

    lines = [f"{emoji} *{title}*\n"]

    if original_price and discount > 0:
        lines.append(f"~De {format_price(original_price)}~ por *{format_price(price)}*")
        lines.append(f"🔥 *{discount}% OFF*\n")
    else:
        lines.append(f"💰 *{format_price(price)}*\n")

    free_shipping = product.get("shipping", {}).get("free_shipping", False)
    if free_shipping:
        lines.append("✅ Frete grátis\n")

    lines.append(f"🛒 {affiliate_link}\n")
    lines.append(DEFAULT_HASHTAGS)

    return "\n".join(lines)


def _send_text(chat_id: str, text: str) -> bool:
    """Envia mensagem de texto para um chat (canal ou grupo)."""
    try:
        url = f"{EVOLUTION_API_URL}/message/sendText/{EVOLUTION_INSTANCE}"
        resp = requests.post(
            url,
            headers=_headers(),
            json={"number": chat_id, "text": text},
            timeout=15,
        )
        return resp.status_code in (200, 201)
    except Exception as e:
        logger.error(f"Erro ao enviar texto para {chat_id}: {e}")
        return False


def _send_media(chat_id: str, image_url: str, caption: str) -> bool:
    """Envia imagem com legenda para um chat."""
    try:
        url = f"{EVOLUTION_API_URL}/message/sendMedia/{EVOLUTION_INSTANCE}"
        resp = requests.post(
            url,
            headers=_headers(),
            json={
                "number": chat_id,
                "mediatype": "image",
                "media": image_url,
                "caption": caption,
            },
            timeout=20,
        )
        return resp.status_code in (200, 201)
    except Exception as e:
        logger.error(f"Erro ao enviar mídia para {chat_id}: {e}")
        return False


def get_product_image_url(product: dict) -> str | None:
    pictures = product.get("pictures", [])
    if pictures:
        return pictures[0].get("secure_url") or pictures[0].get("url")
    thumbnail = product.get("thumbnail", "")
    return thumbnail.replace("I.jpg", "O.jpg") if thumbnail else None


def _post_to_chat(chat_id: str, product: dict) -> bool:
    """Posta uma oferta em um chat específico."""
    message = build_message(product)
    image_url = get_product_image_url(product)

    if image_url:
        return _send_media(chat_id, image_url, message)
    return _send_text(chat_id, message)


def send_offer(product: dict) -> bool:
    """Posta a oferta no Canal e em todos os Grupos configurados."""
    success_count = 0
    targets = []

    if WA_CHANNEL_ID:
        targets.append(("Canal", WA_CHANNEL_ID))

    for group_id in WA_GROUP_IDS:
        targets.append(("Grupo", group_id))

    for target_type, chat_id in targets:
        ok = _post_to_chat(chat_id, product)
        if ok:
            success_count += 1
            logger.info(f"Postado no {target_type}: {product.get('title', '')[:40]}")
        else:
            logger.warning(f"Falhou no {target_type} {chat_id}")

    return success_count > 0


def send_daily_intro() -> None:
    """Envia mensagem de boas-vindas no início do dia."""
    message = (
        "🏆 *Bom dia, atletas!*\n\n"
        "As melhores ofertas de esporte e fitness do dia chegaram! "
        "Fique ligado que vem muito mais por aí 👇\n\n"
        "#esporte #fitness #ofertas"
    )
    targets = []
    if WA_CHANNEL_ID:
        targets.append(WA_CHANNEL_ID)
    targets.extend(WA_GROUP_IDS)

    for chat_id in targets:
        _send_text(chat_id, message)


def test_connection() -> bool:
    """Verifica se a Evolution API está online e a instância conectada."""
    try:
        url = f"{EVOLUTION_API_URL}/instance/connectionState/{EVOLUTION_INSTANCE}"
        resp = requests.get(url, headers=_headers(), timeout=5)
        if resp.status_code == 200:
            state = resp.json().get("instance", {}).get("state", "")
            if state == "open":
                logger.info("WhatsApp conectado!")
                return True
            logger.error(f"WhatsApp não conectado. Estado: {state}")
            logger.error("Escaneie o QR code em: GET /instance/connect/{instance}")
            return False
        return False
    except Exception as e:
        logger.error(f"Evolution API offline: {e}")
        return False


def get_qr_code() -> str | None:
    """Retorna o QR code para conectar o WhatsApp (use no primeiro setup)."""
    try:
        url = f"{EVOLUTION_API_URL}/instance/connect/{EVOLUTION_INSTANCE}"
        resp = requests.get(url, headers=_headers(), timeout=10)
        if resp.status_code == 200:
            return resp.json().get("qrcode", {}).get("base64")
    except Exception as e:
        logger.error(f"Erro ao buscar QR code: {e}")
    return None
