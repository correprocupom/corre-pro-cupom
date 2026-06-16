import requests, re

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "pt-BR,pt;q=0.9",
}

resp = requests.get("https://www.amazon.com.br/s?rh=n%3A16209740011&s=discount-rate-desc", headers=headers, timeout=15)
print("Status:", resp.status_code)
print("CAPTCHA:", "api-services-support" in resp.text)

with open("amazon_page.html", "w", encoding="utf-8") as f:
    f.write(resp.text)
print("HTML salvo, tamanho:", len(resp.text))

# Testa varios padroes de titulo
for pattern in [
    'a-size-base-plus a-color-base a-text-normal',
    'a-size-medium a-color-base a-text-normal',
    'a-size-base a-color-base a-text-normal',
    'a-text-normal',
]:
    found = resp.text.count(pattern)
    print(f"  '{pattern}': {found} ocorrencias")

prices = re.findall(r'class="a-price-whole">(\d+)<', resp.text)
print("Precos encontrados:", prices[:5])
