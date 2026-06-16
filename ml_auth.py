import requests
import logging
import time
from config import ML_APP_ID, ML_CLIENT_SECRET, ML_ACCESS_TOKEN

logger = logging.getLogger(__name__)

_access_token = ML_ACCESS_TOKEN
_token_expires_at = time.time() + 21600  # 6 horas


def get_access_token() -> str | None:
    global _access_token, _token_expires_at

    # Usa o token salvo enquanto válido
    if _access_token and time.time() < _token_expires_at - 300:
        return _access_token

    # Tenta renovar via client_credentials
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
            logger.info("Token ML renovado via client_credentials")
            return _access_token
    except Exception as e:
        logger.error(f"Erro ao renovar token: {e}")

    # Fallback: usa o token do env mesmo que próximo de expirar
    if _access_token:
        logger.warning("Usando token ML possivelmente expirado")
        return _access_token

    return None
