# Bot de Ofertas Esportivas — Telegram

Bot que busca automaticamente ofertas de esporte no Mercado Livre e posta no seu canal Telegram com link de afiliado.

## Configuração em 4 passos

### 1. Instalar Python
- Baixe em: https://python.org/downloads
- Durante a instalação, marque **"Add Python to PATH"**

### 2. Criar o bot no Telegram
1. Abra o Telegram e procure por **@BotFather**
2. Envie `/newbot`
3. Escolha um nome (ex: "Ofertas Esporte") e um username (ex: `ofertasesportebot`)
4. O BotFather vai te dar um **token** (parece com: `123456789:ABCdefGHI...`)
5. Copie esse token

### 3. Criar seu canal Telegram
1. No Telegram, crie um novo Canal
2. Adicione seu bot como **administrador** do canal com permissão de postar mensagens
3. O ID do canal pode ser o @username (ex: `@ofertasesporte`) ou o ID numérico

### 4. Configurar o .env
```
# Copie o arquivo .env.example para .env
copy .env.example .env

# Abra o .env e preencha:
TELEGRAM_BOT_TOKEN=token_que_o_botfather_te_deu
TELEGRAM_CHANNEL_ID=@seu_canal
ML_AFFILIATE_ID=seu_id_do_ml_afiliados
```

## Instalação e execução

```bash
# Instale as dependências (só na primeira vez)
pip install -r requirements.txt

# Rode o bot
python main.py
```

## Como pegar seu ID de afiliado no ML

1. Acesse https://afiliados.mercadolivre.com.br
2. Após aprovação, vá em **Ferramentas > Links**
3. Gere um link de qualquer produto — o seu ID aparece no parâmetro `partner_id` da URL

## Hospedagem (para rodar 24/7)

Para rodar sem precisar deixar o PC ligado, use um servidor na nuvem:
- **Railway.app** — gratuito para começar (recomendado)
- **Render.com** — plano gratuito disponível
- **VPS** (DigitalOcean, Contabo) — mais controle, ~R$30/mês

## Personalização

Edite o `config.py` para:
- Mudar categorias de produto
- Ajustar desconto mínimo
- Mudar horários de postagem
- Editar hashtags
