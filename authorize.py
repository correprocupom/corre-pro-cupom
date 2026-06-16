"""
Execute este script UMA VEZ para autorizar o app ML e obter o refresh token.
Depois salve o token no Railway como ML_REFRESH_TOKEN.
"""
import requests
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from config import ML_APP_ID, ML_CLIENT_SECRET

AUTH_URL = (
    f"https://auth.mercadolivre.com.br/authorization"
    f"?response_type=code"
    f"&client_id={ML_APP_ID}"
    f"&redirect_uri=http://localhost:8888"
)

received_code = None


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        global received_code
        params = parse_qs(urlparse(self.path).query)
        received_code = params.get("code", [None])[0]
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"<h1>Autorizado! Pode fechar esta janela.</h1>")

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    print("\n=== Autorização Mercado Livre ===")
    print("Abrindo navegador para autorizar o app...")
    webbrowser.open(AUTH_URL)

    server = HTTPServer(("localhost", 8888), Handler)
    print("Aguardando autorização...")
    server.handle_request()

    if not received_code:
        print("Erro: código não recebido.")
        exit(1)

    resp = requests.post(
        "https://api.mercadolibre.com/oauth/token",
        data={
            "grant_type": "authorization_code",
            "client_id": ML_APP_ID,
            "client_secret": ML_CLIENT_SECRET,
            "code": received_code,
            "redirect_uri": "http://localhost:8888",
        },
    )

    data = resp.json()
    if "access_token" in data:
        print("\n✅ Autorização bem sucedida!")
        print(f"\nAccess Token:  {data['access_token']}")
        print(f"Refresh Token: {data['refresh_token']}")
        print("\n👉 Salve o REFRESH TOKEN no Railway como: ML_REFRESH_TOKEN")
    else:
        print(f"\n❌ Erro: {data}")
