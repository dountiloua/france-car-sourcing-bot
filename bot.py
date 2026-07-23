import logging
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from datetime import datetime
import re
from urllib.parse import quote

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable is not set!")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send welcome message."""
    await update.message.reply_text(
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🚗  CARDZSCRAP  🚗\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "France Auto Export Sourcing Agent\n\n"
        "Enter your maximum price in EUR:\n\n"
        "🔍 Sources: AutoScout24.fr & Leboncoin.fr\n"
        "⛽ Fuel: Essence / Hybride only\n"
        "📅 Year: 2023+\n"
        "🛠️ Condition: Non-accidenté\n"
        "📦 Export Ready\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━"
    )


def generate_autoscout24_link(max_price: int) -> str:
    """Generate a direct AutoScout24.fr search link with all filters applied."""
    current_year = datetime.now().year
    url = (
        f"https://www.autoscout24.fr/lst?"
        f"fuel=B%2CH"
        f"&pricefrom=0&priceto={max_price}"
        f"&fregfrom=2023&fregto={current_year}"
        f"&desc=1&size=20&page=1&fc=0&cy=F"
        f"&damaged_listing=exclude"
        f"&powertype=kw&sort=age"
    )
    return url


def generate_leboncoin_link(max_price: int) -> str:
    """Generate a direct Leboncoin.fr search link with all filters applied."""
    url = (
        f"https://www.leboncoin.fr/recherche?category=2"
        f"&fuel=1"
        f"&price=min-{max_price}"
        f"&regdate=2023-max"
        f"&vehicle_damage=undamaged"
        f"&sort=time&order=desc"
    )
    return url


def generate_lacentrale_link(max_price: int) -> str:
    """Generate a direct LaCentrale.fr search link with filters."""
    url = (
        f"https://www.lacentrale.fr/listing?"
        f"makesModelsCommercialNames="
        f"&priceMax={max_price}"
        f"&yearMin=2023"
        f"&energies=essence%2Chybride"
        f"&damaged=non"
    )
    return url


async def search_cars(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle price input and generate direct search links."""
    text = update.message.text.strip()

    price_match = re.search(r'\d+', text.replace(" ", "").replace(",", "").replace(".", ""))
    if not price_match:
        await update.message.reply_text("Please enter a valid price (number only). Example: 10000")
        return

    max_price = int(price_match.group())
    if max_price < 1000 or max_price > 100000:
        await update.message.reply_text("Please enter a price between 1,000€ and 100,000€.")
        return

    # Generate filtered links
    autoscout_link = generate_autoscout24_link(max_price)
    leboncoin_link = generate_leboncoin_link(max_price)
    lacentrale_link = generate_lacentrale_link(max_price)

    today = datetime.now().strftime("%d/%m/%Y")

    response_text = (
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🚗  CARDZSCRAP RESULTS  🚗\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📅 Date: {today}\n"
        f"💰 Max Price: {max_price:,}€\n"
        f"⛽ Fuel: Essence / Hybride\n"
        f"📅 Year: 2023 → {datetime.now().year}\n"
        f"🛠️ Condition: Non-accidenté\n"
        f"📦 Export Ready\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "🔗 CLICK TO VIEW LISTINGS:\n\n"
        f"1️⃣ AutoScout24.fr:\n{autoscout_link}\n\n"
        f"2️⃣ Leboncoin.fr:\n{leboncoin_link}\n\n"
        f"3️⃣ LaCentrale.fr:\n{lacentrale_link}\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "✅ All filters pre-applied!\n"
        "Just click the links above to see\n"
        "all matching cars instantly.\n\n"
        "💡 Tip: Bookmark these links to\n"
        "check for new listings daily.\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "Powered by CARDZSCRAP 🚗"
    )

    await update.message.reply_text(response_text, disable_web_page_preview=True)


def main() -> None:
    """Start the bot."""
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_cars))
    logger.info("CARDZSCRAP Bot started - AutoScout24.fr & Leboncoin.fr & LaCentrale.fr")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
