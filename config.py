import os
from dotenv import load_dotenv

load_dotenv()

# === WHATSAPP (Evolution API) ===
EVOLUTION_API_URL = os.getenv("EVOLUTION_API_URL", "http://localhost:8080")
EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY", "")
EVOLUTION_INSTANCE = os.getenv("EVOLUTION_INSTANCE", "corre-pro-cupom")
WA_CHANNEL_ID = os.getenv("WA_CHANNEL_ID", "")
_groups_raw = os.getenv("WA_GROUP_IDS", "")
WA_GROUP_IDS = [g.strip() for g in _groups_raw.split(",") if g.strip()]

# === AGENDAMENTO ===
POSTING_INTERVAL_MINUTES = int(os.getenv("POSTING_INTERVAL_MINUTES", 30))
START_HOUR = int(os.getenv("START_HOUR", 8))
END_HOUR = int(os.getenv("END_HOUR", 22))
OFFERS_PER_POST = int(os.getenv("OFFERS_PER_POST", 1))

# === FILTROS DE QUALIDADE ===
MIN_DISCOUNT_PERCENT = int(os.getenv("MIN_DISCOUNT_PERCENT", 20))
MIN_PRICE = float(os.getenv("MIN_PRICE", 15))
MAX_PRICE = float(os.getenv("MAX_PRICE", 2000))

# === PALAVRAS-CHAVE ===
_keywords_raw = os.getenv("SPORT_KEYWORDS", "esport,fitness,suplemento,whey,creatina,tenis,corrida,academia")
SPORT_KEYWORDS = [k.strip().lower() for k in _keywords_raw.split(",") if k.strip()]

# === AFILIADOS ===
ML_AFFILIATE_ID = os.getenv("ML_AFFILIATE_ID")
AMAZON_AFFILIATE_TAG = os.getenv("AMAZON_AFFILIATE_TAG", "")

# === MERCADO LIVRE ===
ML_APP_ID = os.getenv("ML_APP_ID")
ML_CLIENT_SECRET = os.getenv("ML_CLIENT_SECRET")
ML_ACCESS_TOKEN = os.getenv("ML_ACCESS_TOKEN")

# Categorias do ML (fixas)
ML_SPORT_CATEGORIES = [
    "MLB1276",   # Esportes e Fitness
    "MLB1430",   # Suplementos e Vitaminas
    "MLB263535", # Musculação e Fitness
    "MLB1271",   # Corrida
    "MLB371",    # Ciclismo
    "MLB1245",   # Natação
    "MLB3498",   # Futebol
]
PRODUCTS_PER_CATEGORY = 5

CATEGORY_EMOJIS = {
    "MLB1276": "🏋️",
    "MLB1430": "💊",
    "MLB263535": "💪",
    "MLB1271": "🏃",
    "MLB371": "🚴",
    "MLB1245": "🏊",
    "MLB3498": "⚽",
    "AMAZON": "📦",
}

DEFAULT_HASHTAGS = "#esporte #fitness #oferta #desconto #mercadolivre #suplementos #academia"
