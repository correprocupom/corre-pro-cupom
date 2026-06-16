import requests, re, json

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36",
    "Accept-Language": "pt-BR,pt;q=0.9",
}

r = requests.get("https://www.mercadolivre.com.br/ofertas", headers=headers, timeout=15)
html = r.text

match = re.search(r'_n\.ctx\.r\s*=\s*(\{.+)', html)
raw = match.group(1)

# Parseia o JSON (pode ter lixo no final, usa JSONDecoder incremental)
decoder = json.JSONDecoder()
try:
    data, _ = decoder.raw_decode(raw)
except Exception as e:
    print("Erro ao parsear JSON:", e)
    exit()

items = data.get("appProps", {}).get("pageProps", {}).get("data", {}).get("items", [])
print(f"Total de itens na pagina: {len(items)}")

def extract_product(item):
    card = item.get("card", {})
    meta = card.get("metadata", {})
    components = card.get("components", [])
    pictures_data = card.get("pictures", {})

    # URL
    url = meta.get("url", "")
    if url and not url.startswith("http"):
        url = "https://" + url
    url_params = meta.get("url_params", "")
    url_fragments = meta.get("url_fragments", "")

    # Titulo, preco da lista de componentes
    title = ""
    price = 0
    original_price = 0

    for comp in components:
        if comp.get("type") == "title":
            title = comp.get("title", {}).get("text", "")
        elif comp.get("type") == "price":
            p = comp.get("price", {})
            price = p.get("current_price", {}).get("value", 0)
            original_price = p.get("previous_price", {}).get("value", 0)

    # Imagem
    pics = pictures_data.get("pictures", [])
    image = ""
    if pics:
        pic_id = pics[0].get("id", "")
        if pic_id:
            image = f"https://http2.mlstatic.com/D_NQ_NP_{pic_id}-O.jpg"

    return {
        "title": title,
        "price": price,
        "original_price": original_price,
        "url": url,
        "image": image,
    }

print("\nPrimeiros 5 produtos:")
for item in items[:5]:
    p = extract_product(item)
    if p["price"] and p["title"]:
        discount = int(((p["original_price"] - p["price"]) / p["original_price"]) * 100) if p["original_price"] else 0
        print(f"  Titulo: {p['title'][:60]}")
        print(f"  Preco: R${p['price']} | Original: R${p['original_price']} | Desconto: {discount}%")
        print(f"  URL: {p['url'][:70]}")
        print(f"  Imagem: {p['image'][:70]}")
        print()
