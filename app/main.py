import asyncio
import html
import logging
import os
from typing import Final

from aiohttp import web
from groq import Groq
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ChatAction, ParseMode
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)


load_dotenv()

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
)
logger = logging.getLogger(__name__)


BOT_TOKEN: Final[str | None] = os.getenv("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY: Final[str | None] = os.getenv("GROQ_API_KEY")
GROQ_MODEL: Final[str] = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
PORT: Final[int] = int(os.getenv("PORT", "8080"))

MODE_LABELS: Final[dict[str, str]] = {
    "girl_text": "Qizga yozish",
    "job_apply": "Ishga ariza",
    "apology": "Uzr so'rash",
    "business": "Rasmiy yozuv",
    "sales": "Sotuv matni",
    "birthday": "Tabrik matni",
    "resume": "Resume/About me",
    "complaint": "Shikoyat matni",
    "invitation": "Taklifnoma",
    "telegram_post": "Telegram post",
    "free": "Erkin prompt",
}

MODE_PROMPTS: Final[dict[str, str]] = {
    "girl_text": (
        "Sen romantik va tabiiy yozuvchi assistantsan. O'zbek tilida, samimiy, "
        "hurmatli va sun'iy tuyulmaydigan xabar yoz."
    ),
    "job_apply": (
        "Sen professional career copywriter'san. O'zbek tilida qisqa, kuchli va "
        "ishonchli ishga ariza yoki murojaat matni yoz."
    ),
    "apology": (
        "Sen nozik vaziyatlarda yozuv tayyorlaydigan assistantsan. O'zbek tilida "
        "chin dildan, aybni tan oladigan va bosimsiz uzr matni yoz."
    ),
    "business": (
        "Sen rasmiy va ishonchli biznes yozuvlar muallifisan. O'zbek tilida "
        "aniq, odobli va professional matn yoz."
    ),
    "sales": (
        "Sen conversion copywriter'san. O'zbek tilida jalb qiluvchi, sodda va "
        "sotuvga ishlaydigan matn yoz."
    ),
    "birthday": (
        "Sen tabrik va tilak matnlari yozadigan assistantsan. O'zbek tilida "
        "samimiy, chiroyli va esda qoladigan tabrik yoz."
    ),
    "resume": (
        "Sen self-presentation va resume matnlari yozadigan assistantsan. "
        "O'zbek tilida kuchli, tartibli va ishonchli matn yoz."
    ),
    "complaint": (
        "Sen muammo va norozilik bo'yicha murojaatlar yozadigan assistantsan. "
        "O'zbek tilida aniq, muloyim va natijaga yo'naltirilgan shikoyat yoz."
    ),
    "invitation": (
        "Sen tadbir va uchrashuvlar uchun taklif matnlari yozadigan assistantsan. "
        "O'zbek tilida chiroyli, odobli va taklif qiluvchi matn yoz."
    ),
    "telegram_post": (
        "Sen ijtimoiy tarmoq va Telegram uchun post yozadigan assistantsan. "
        "O'zbek tilida qiziqarli, ushlab turuvchi va o'qishga yengil post yoz."
    ),
    "free": (
        "Sen kuchli message writer assistantsan. Foydalanuvchi maqsadiga qarab "
        "eng mos, tabiiy va sifatli o'zbekcha matn yoz."
    ),
}

MODE_HINTS: Final[dict[str, str]] = {
    "girl_text": "Masalan: 'birinchi marta salomlashish uchun yengil va samimiy text kerak'",
    "job_apply": "Masalan: 'HR ga python developer uchun qisqa ariza kerak'",
    "apology": "Masalan: 'do'stimdan kech qolganim uchun uzr so'rashim kerak'",
    "business": "Masalan: 'mijozga to'lov kechikishi haqida rasmiy xabar kerak'",
    "sales": "Masalan: 'SMM xizmati uchun sotuv matni yozib ber'",
    "birthday": "Masalan: 'akamga tug'ilgan kun uchun samimiy tabrik kerak'",
    "resume": "Masalan: 'o'zim haqimda junior python developer sifatida qisqa matn kerak'",
    "complaint": "Masalan: 'internet sifati yomonligi haqida provayderga shikoyat yozish kerak'",
    "invitation": "Masalan: 'do'stlarni to'yga chiroyli uslubda taklif qilish kerak'",
    "telegram_post": "Masalan: 'hozirgi vaqtni qadrlash haqida qisqa telegram post kerak'",
    "free": "Masalan: 'istalgan mavzuda kuchli va tabiiy matn yozib ber'",
}

STYLE_PROMPTS: Final[dict[str, str]] = {
    "warm": "Yana iliqroq va samimiyroq qayta yoz.",
    "formal": "Yana rasmiyroq va professionalroq qayta yoz.",
    "short": "Mazmunni saqlab, yanada qisqa variant qil.",
    "emoji": "Yengil va didli emoji bilan qayta yoz.",
}

LENGTH_LABELS: Final[dict[str, str]] = {
    "short": "Qisqa",
    "medium": "O'rta",
    "long": "Uzun",
}

VARIANT_LABELS: Final[dict[str, str]] = {
    "1": "1 ta",
    "2": "2 ta",
    "3": "3 ta",
}


def build_main_keyboard() -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton("Qizga yozish", callback_data="mode:girl_text"),
            InlineKeyboardButton("Ishga ariza", callback_data="mode:job_apply"),
        ],
        [
            InlineKeyboardButton("Uzr so'rash", callback_data="mode:apology"),
            InlineKeyboardButton("Rasmiy yozuv", callback_data="mode:business"),
        ],
        [
            InlineKeyboardButton("Sotuv matni", callback_data="mode:sales"),
            InlineKeyboardButton("Tabrik matni", callback_data="mode:birthday"),
        ],
        [
            InlineKeyboardButton("Resume/About me", callback_data="mode:resume"),
            InlineKeyboardButton("Shikoyat matni", callback_data="mode:complaint"),
        ],
        [
            InlineKeyboardButton("Taklifnoma", callback_data="mode:invitation"),
            InlineKeyboardButton("Telegram post", callback_data="mode:telegram_post"),
        ],
        [
            InlineKeyboardButton("Erkin prompt", callback_data="mode:free"),
        ],
    ]
    return InlineKeyboardMarkup(rows)


def build_settings_keyboard() -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton("Qisqa", callback_data="length:short"),
            InlineKeyboardButton("O'rta", callback_data="length:medium"),
            InlineKeyboardButton("Uzun", callback_data="length:long"),
        ],
        [
            InlineKeyboardButton("1 ta", callback_data="variants:1"),
            InlineKeyboardButton("2 ta", callback_data="variants:2"),
            InlineKeyboardButton("3 ta", callback_data="variants:3"),
        ],
    ]
    return InlineKeyboardMarkup(rows)


def build_refine_keyboard() -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton("Iliqroq", callback_data="style:warm"),
            InlineKeyboardButton("Rasmiyroq", callback_data="style:formal"),
        ],
        [
            InlineKeyboardButton("Qisqaroq", callback_data="style:short"),
            InlineKeyboardButton("Emoji qo'sh", callback_data="style:emoji"),
        ],
        [InlineKeyboardButton("Yangi matn", callback_data="action:reset")],
    ]
    return InlineKeyboardMarkup(rows)


def build_user_prompt(mode: str, details: str, length: str, variants: int) -> str:
    label = MODE_LABELS.get(mode, "Erkin prompt")
    length_map = {
        "short": "qisqa va lo'nda",
        "medium": "o'rta uzunlikdagi, muvozanatli",
        "long": "batafsilroq va boyroq",
    }
    selected_length = length_map.get(length, "o'rta uzunlikdagi, muvozanatli")
    return (
        f"Kategoriya: {label}\n"
        f"Vazifa tafsiloti: {details}\n\n"
        "Javobni faqat o'zbek tilida ber.\n"
        f"Har bir variant uslubi: {selected_length}.\n"
        f"Kerakli variantlar soni: {variants} ta.\n"
        "Natijani quyidagi formatda qaytar:\n"
        "1. Variant 1\n"
        "2. Variant 2\n"
        "3. Variant 3\n"
        "Oxirida: Qisqa tavsiya: bu matnni qachon ishlatish yaxshi.\n"
        f"Faqat {variants} ta variant yoz, undan ko'p emas.\n"
        "Matnlar copy-paste qilishga tayyor, tabiiy va ortiqcha AI uslubisiz bo'lsin."
    )


def render_response(text: str, mode: str) -> str:
    title = MODE_LABELS.get(mode, "Tayyor matn")
    escaped_text = html.escape(text)
    return (
        f"<b>{html.escape(title)}</b>\n\n"
        f"{escaped_text}\n\n"
        "<i>Kerak bo'lsa pastdagi tugmalar bilan qayta ishlatib beraman.</i>"
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data["mode"] = "free"
    context.user_data["length"] = "medium"
    context.user_data["variants"] = 3
    context.user_data.pop("last_request", None)
    context.user_data.pop("last_response", None)

    text = (
        "Salom, men <b>Message Writer Bot</b>man.\n\n"
        "Menga vaziyatni yozasiz, men sizga tayyor matn yozib beraman.\n"
        "Masalan:\n"
        "- qizga birinchi yozish\n"
        "- HR ga ishga ariza yuborish\n"
        "- kimdandir uzr so'rash\n\n"
        "Hozir menda 10 ta tayyor yo'nalish bor:\n"
        "qizga yozish, ishga ariza, uzr, rasmiy yozuv, sotuv matni,\n"
        "tabrik, resume/about me, shikoyat, taklifnoma, telegram post.\n\n"
        "Pastdagi sozlamalarda uzunlik va variant sonini ham tanlashingiz mumkin.\n\n"
        "Pastdan kategoriya tanlang yoki bevosita yozishni boshlang."
    )
    await update.effective_message.reply_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=build_main_keyboard(),
    )
    await update.effective_message.reply_text(
        "Sozlamalar: O'rta uzunlik, 3 ta variant.",
        reply_markup=build_settings_keyboard(),
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "/start - botni ishga tushiradi\n"
        "/new - yangi yozuv boshlaydi\n"
        "/help - yordam\n\n"
        "Ishlash tartibi juda oddiy:\n"
        "1. Kategoriya tanlaysiz\n"
        "2. Vaziyatni yozasiz\n"
        "3. Bot sizga bir necha tayyor variant beradi"
    )
    await update.effective_message.reply_text(text)


async def new_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data["mode"] = "free"
    context.user_data["length"] = "medium"
    context.user_data["variants"] = 3
    context.user_data.pop("last_request", None)
    context.user_data.pop("last_response", None)
    await update.effective_message.reply_text(
        "Yangi yozuv boshlandi. Kategoriyani tanlang yoki to'g'ridan-to'g'ri vaziyatni yozing.",
        reply_markup=build_main_keyboard(),
    )
    await update.effective_message.reply_text(
        "Sozlamalar: O'rta uzunlik, 3 ta variant.",
        reply_markup=build_settings_keyboard(),
    )


async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query is None:
        return

    await query.answer()
    data = query.data or ""

    if data.startswith("mode:"):
        mode = data.split(":", 1)[1]
        context.user_data["mode"] = mode
        await query.message.reply_text(
            f"Tanlandi: {MODE_LABELS.get(mode, 'Erkin prompt')}\n"
            f"Endi vaziyatni yozing. {MODE_HINTS.get(mode, MODE_HINTS['free'])}"
        )
        return

    if data.startswith("length:"):
        length = data.split(":", 1)[1]
        context.user_data["length"] = length
        variants = int(context.user_data.get("variants", 3))
        length_label = LENGTH_LABELS.get(length, "O'rta")
        await query.message.reply_text(
            f"Sozlama yangilandi: {length_label} uzunlik, {variants} ta variant."
        )
        return

    if data.startswith("variants:"):
        variants = data.split(":", 1)[1]
        context.user_data["variants"] = int(variants)
        length = context.user_data.get("length", "medium")
        length_label = LENGTH_LABELS.get(length, "O'rta")
        variant_label = VARIANT_LABELS.get(variants, "3 ta")
        await query.message.reply_text(
            f"Sozlama yangilandi: {length_label} uzunlik, {variant_label} variant."
        )
        return

    if data == "action:reset":
        context.user_data["mode"] = "free"
        context.user_data["length"] = "medium"
        context.user_data["variants"] = 3
        context.user_data.pop("last_request", None)
        context.user_data.pop("last_response", None)
        await query.message.reply_text(
            "Hammasi tozalandi. Yangi vaziyat yuboring.",
            reply_markup=build_main_keyboard(),
        )
        await query.message.reply_text(
            "Sozlamalar: O'rta uzunlik, 3 ta variant.",
            reply_markup=build_settings_keyboard(),
        )
        return

    if data.startswith("style:"):
        style = data.split(":", 1)[1]
        last_response = context.user_data.get("last_response")
        last_request = context.user_data.get("last_request")
        mode = context.user_data.get("mode", "free")
        length = context.user_data.get("length", "medium")
        variants = int(context.user_data.get("variants", 3))

        if not last_response or not last_request:
            await query.message.reply_text(
                "Avval biror vaziyat yuboring, keyin qayta ishlash tugmalaridan foydalanamiz."
            )
            return

        await query.message.chat.send_action(ChatAction.TYPING)
        refined = await generate_text(
            mode=mode,
            user_input=last_request,
            length=length,
            variants=variants,
            refinement=STYLE_PROMPTS.get(style, ""),
            previous_response=last_response,
        )
        context.user_data["last_response"] = refined
        await query.message.reply_text(
            render_response(refined, mode),
            parse_mode=ParseMode.HTML,
            reply_markup=build_refine_keyboard(),
        )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    if message is None or not message.text:
        return

    mode = context.user_data.get("mode", "free")
    length = context.user_data.get("length", "medium")
    variants = int(context.user_data.get("variants", 3))
    user_text = message.text.strip()
    context.user_data["last_request"] = user_text

    await message.chat.send_action(ChatAction.TYPING)
    result = await generate_text(
        mode=mode,
        user_input=user_text,
        length=length,
        variants=variants,
    )
    context.user_data["last_response"] = result

    await message.reply_text(
        render_response(result, mode),
        parse_mode=ParseMode.HTML,
        reply_markup=build_refine_keyboard(),
    )


async def generate_text(
    mode: str,
    user_input: str,
    length: str,
    variants: int,
    refinement: str = "",
    previous_response: str = "",
) -> str:
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY is not configured")

    system_prompt = MODE_PROMPTS.get(mode, MODE_PROMPTS["free"])
    user_prompt = build_user_prompt(mode, user_input, length, variants)

    if refinement and previous_response:
        user_prompt += (
            "\n\nOldingi javob:\n"
            f"{previous_response}\n\n"
            f"Qayta ishlash topshirig'i: {refinement}"
        )

    def _call_groq() -> str:
        client = Groq(api_key=GROQ_API_KEY)
        completion = client.chat.completions.create(
            model=GROQ_MODEL,
            temperature=0.9,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        content = completion.choices[0].message.content
        if not content:
            raise RuntimeError("Groq returned an empty response")
        return content.strip()

    return await asyncio.to_thread(_call_groq)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.exception("Unhandled error", exc_info=context.error)

    if isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text(
            "Kechirasiz, hozircha javob yozishda xatolik bo'ldi. Bir ozdan keyin yana urinib ko'ring."
        )


async def healthcheck(_: web.Request) -> web.Response:
    return web.json_response({"ok": True, "service": "message-writer-bot"})


async def start_health_server() -> web.AppRunner:
    app = web.Application()
    app.router.add_get("/", healthcheck)
    app.router.add_get("/health", healthcheck)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host="0.0.0.0", port=PORT)
    await site.start()
    logger.info("Health server started on port %s", PORT)
    return runner


async def post_init(application: Application) -> None:
    application.bot_data["health_runner"] = await start_health_server()
    logger.info("Bot is starting")


async def post_shutdown(application: Application) -> None:
    runner = application.bot_data.get("health_runner")
    if runner:
        await runner.cleanup()
        logger.info("Health server stopped")


def validate_env() -> None:
    missing = []
    if not BOT_TOKEN:
        missing.append("TELEGRAM_BOT_TOKEN")
    if not GROQ_API_KEY:
        missing.append("GROQ_API_KEY")

    if missing:
        raise RuntimeError(
            "Missing required environment variables: " + ", ".join(missing)
        )


def main() -> None:
    validate_env()

    # Python 3.14 no longer creates a default event loop for the main thread.
    asyncio.set_event_loop(asyncio.new_event_loop())

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("new", new_command))
    application.add_handler(CallbackQueryHandler(on_callback))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text)
    )
    application.add_error_handler(error_handler)

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
