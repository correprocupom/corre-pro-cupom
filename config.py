import os
from dotenv import load_dotenv

load_dotenv()

# === WHATSAPP (Evolution API) ===
EVOLUTION_API_URL = os.getenv("EVOLUTION_API_URL", "http://localhost:8080")
EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY", "")
EVOLUTION_INSTANCE = os.getenv("EVOLUTION_INSTANCE", "corre-pro-cupom")

# ID do Canal do WhatsApp (formato: 120363XXXXXXXXXX@newsletter)
WA_CHANNEL_ID = os.getenv("WA_CHANNEL_ID", "")

# IDs dos grupos separados por vírgula (formato: 5511999999999-XXXXXXXXXX@g.us)
_groups_raw = os.getenv("WA_GROUP_IDS", "")
WA_GROUP_IDS = [g.strip() for g in _groups_raw.split(",") if g.strip()]

ML_AFFILIATE_ID = os.getenv("ML_AFFILIATE_ID")
ML_APP_ID = os.getenv("ML_APP_ID")
ML_CLIENT_SECRET = os.getenv("ML_CLIENT_SECRET")
ML_ACCESS_TOKEN = os.getenv("ML_ACCESS_TOKEN")
POSTING_INTERVAL_MINUTES = int(os.getenv("POSTING_INTERVAL_MINUTES", 30))
START_HOUR = int(os.getenv("START_HOUR", 8))
END_HOUR = int(os.getenv("END_HOUR", 22))

# Categorias do Mercado Livre para nicho de esportes
# IDs oficiais das categorias ML Brasil
ML_SPORT_CATEGORIES = [
    "MLB1276",   # Esportes e Fitness
    "MLB1430",   # Suplementos e Vitaminas
    "MLB263535", # Musculação e Fitness
    "MLB1271",   # Corrida
    "MLB371",    # Ciclismo
    "MLB1245",   # Natação
    "MLB3498",   # Futebol
]

# Filtros de qualidade das ofertas
MIN_DISCOUNT_PERCENT = 20       # desconto mínimo para postar (%)
MIN_RATING = 4.0                # avaliação mínima do produto
MIN_REVIEWS = 5                 # número mínimo de avaliações
MAX_PRICE = 2000.0              # preço máximo em R$
MIN_PRICE = 15.0                # preço mínimo em R$ (evita lixo)

# Quantos produtos buscar por categoria a cada rodada
PRODUCTS_PER_CATEGORY = 5

# Emojis por categoria (para deixar as mensagens mais bonitas)
CATEGORY_EMOJIS = {
    "MLB1276": "🏋️",
    "MLB1430": "💊",
    "MLB263535": "💪",
    "MLB1271": "🏃",
    "MLB371": "🚴",
    "MLB1245": "🏊",
    "MLB3498": "⚽",
}

# Hashtags padrão para todas as postagens
DEFAULT_HASHTAGS = "#esporte #fitness #oferta #desconto #mercadolivre #suplementos #academia"
