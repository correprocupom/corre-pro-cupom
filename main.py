import logging
import sys
from whatsapp_bot import test_connection
from config import EVOLUTION_API_URL, EVOLUTION_API_KEY, EVOLUTION_INSTANCE, ML_AFFILIATE_ID

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("ofertas.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


def check_config() -> bool:
    """Verifica se todas as variáveis de ambiente estão configuradas."""
    missing = []

    if not EVOLUTION_API_URL:
        missing.append("EVOLUTION_API_URL")

    if not EVOLUTION_API_KEY:
        missing.append("EVOLUTION_API_KEY")

    if not EVOLUTION_INSTANCE:
        missing.append("EVOLUTION_INSTANCE")

    if not ML_AFFILIATE_ID:
        missing.append("ML_AFFILIATE_ID (opcional, mas sem ele você não ganha comissão)")

    if missing:
        print("\n❌ Configuração incompleta. Preencha no arquivo .env:")
        for item in missing:
            print(f"   - {item}")
        print("\nConsulte o README.md para instruções detalhadas.\n")
        return False

    return True


def main():
    print("\n🏆 Bot de Ofertas Esportivas")
    print("=" * 40)

    if not check_config():
        if "TELEGRAM_BOT_TOKEN" in str(check_config):
            sys.exit(1)

    if not test_connection():
        print("\n❌ Falha na conexão com WhatsApp (Evolution API). Verifique as variáveis no .env\n")
        sys.exit(1)

    print("✅ Configuração OK — iniciando bot...\n")

    from scheduler import start
    start()


if __name__ == "__main__":
    main()
