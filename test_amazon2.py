import re

with open("amazon_page.html", encoding="utf-8") as f:
    html = f.read()

# Busca contexto ao redor do ASIN B0GH7YZB7B
idx = html.find('B0GH7YZB7B')
block = html[idx:idx+5000]

# Busca titulo
print("=== BUSCANDO TITULO ===")
for pattern in [
    r'aria-label="([^"]{15,200})"',
    r'"a-size-base-plus[^"]*"[^>]*>([^<]{15,200})<',
    r'<h2[^>]*>.*?<span[^>]*>([^<]{15,200})<',
    r'<span[^>]*>([A-Z][a-zA-Z\s]{15,150})<\/span>',
]:
    m = re.search(pattern, block)
    if m:
        print(f"Padrao '{pattern[:40]}': {m.group(1)[:80]}")

print("\n=== PRECOS ===")
prices = re.findall(r'R\$[^\d]*([\d.,]+)', block)
print("Precos encontrados:", prices[:5])

print("\n=== IMAGENS ===")
imgs = re.findall(r'src="(https://[^"]+\.jpg[^"]*)"', block)
print("Imagens:", imgs[:2])

print("\n=== PRIMEIROS 1000 CHARS ===")
print(block[:1000])
