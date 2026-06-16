import requests
import logging
import time
from config import ML_APP_ID, ML_CLIENT_SECRET

logger = logging.getLogger(__name__)

_access_token = None
_token_expires_at = 0


def get_access_token() -> str | None:
    """Obtém token de acesso via Client Credentials (sem login do usuário)."""
    global _access_token, _token_expires_at

    if _access_token and time.time() < _token_expires_at - 60:
        return _access_token

    try:
        resp = requests.post(
            "https://api.mercadolibre.com/oauth/token",
            data={
                "grant_type": "client_credentials",
                "client_id": ML_APP_ID,
                "client_secret": ML_CLIENT_SECRET,
            },
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            _access_token = data.get("access_token")
            _token_expires_at = time.time() + data.get("expires_in", 21600)
            logger.info("Token ML obtido com sucesso")
            return _access_token
        logger.error(f"Erro ao obter token ML: {resp.text}")
    except Exception as e:
        logger.error(f"Falha na autenticação ML: {e}")
    return None
