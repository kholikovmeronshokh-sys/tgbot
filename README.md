# Message Writer Bot

Groq AI bilan ishlaydigan Telegram bot. Foydalanuvchi vaziyat yozadi, bot esa tayyor xabar variantlarini chiqaradi.

## Imkoniyatlar

- `Qizga yozish`
- `Ishga ariza`
- `Uzr so'rash`
- `Rasmiy yozuv`
- `Sotuv matni`
- `Erkin prompt`
- Inline keyboard orqali qayta ishlash:
  - `Iliqroq`
  - `Rasmiyroq`
  - `Qisqaroq`
  - `Emoji qo'sh`

## Lokal ishga tushirish

1. Virtual environment oching:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

2. Kutubxonalarni o'rnating:

```powershell
pip install -r requirements.txt
```

3. Environment variable'larni sozlang:

```powershell
$env:TELEGRAM_BOT_TOKEN="telegram-token"
$env:GROQ_API_KEY="groq-api-key"
$env:GROQ_MODEL="llama-3.3-70b-versatile"
```

4. Botni ishga tushiring:

```powershell
python -m app.main
```

## Fly.io deploy

1. `flyctl auth login`
2. `fly launch --no-deploy`
3. `fly secrets set TELEGRAM_BOT_TOKEN=... GROQ_API_KEY=...`
4. Agar kerak bo'lsa `fly.toml` ichidagi `app` nomini o'zgartiring
5. `fly deploy`

## Muhim

- API key'larni faylga yozib commit qilmang.
- Agar kalitni chatga yuborgan bo'lsangiz, uni almashtirib yuborish tavsiya qilinadi.
