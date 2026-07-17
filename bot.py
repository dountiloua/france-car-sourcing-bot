
import logging
import os
import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from datetime import datetime
import re

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "6997085553:AAELf17C6jHmuTkyRS13J0KoR4mhr238sTQ")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send welcome message."""
    await update.message.reply_text(
        "\U0001f697 Welcome to the France Car Sourcing Bot!\n\n"
        "Enter your maximum price in EUR to search for available cars:\n\n"
        "\U0001f50d Searching on: AutoScout24.fr & Leboncoin.fr\n"
        "\u26fd Fuel: Essence / Hybride only\n"
        "\U0001f4c5 Year: 2023+\n"
        "\U0001f6e0\ufe0f Condition: Non-accident\u00e9"
    )


def search_autoscout24(max_price: int) -> list:
    """Search AutoScout24.fr for matching listings."""
    results = []
    current_year = datetime.now().year

    autoscout_url = (
        f"https://www.autoscout24.fr/lst?"
        f"fuel=B%2CH&pricefrom=0&priceto={max_price}"
        f"&fregfrom=2023&fregto={current_year}"
        f"&desc=1&size=20&page=1&fc=0&cy=F"
        f"&damaged_listing=exclude&powertype=kw&sort=age"
    )

    try:
        response = requests.get(autoscout_url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(response.content, "html.parser")
        listings = soup.find_all("article")

        for listing in listings:
            try:
                model_tag = listing.find("h2")
                if not model_tag:
                    continue
                model_name = model_tag.text.strip()

                price_tag = listing.find("p", string=re.compile(r"\u20ac"))
                if not price_tag:
                    price_tag = listing.find(class_=re.compile(r"price", re.I))
                price_text = price_tag.text.strip() if price_tag else "N/A"

                data_text = listing.get_text("|", strip=True)
                year_match = re.search(r'(\d{2}/\d{4})', data_text)
                year = year_match.group(1).split('/')[-1] if year_match else "N/A"
                mileage_match = re.search(r'(\d+[\s\d]*)\s*km', data_text)
                mileage = mileage_match.group(1).strip() + " km" if mileage_match else "N/A"
                fuel = "Essence" if "essence" in data_text.lower() else ("Hybride" if "hybride" in data_text.lower() or "hybrid" in data_text.lower() else "N/A")

                location_tag = listing.find("span", class_=re.compile(r"SellerInfo_address", re.I))
                location = location_tag.text.strip() if location_tag else "France"

                link_tag = listing.find("a", href=re.compile(r"/offres/"))
                link = "https://www.autoscout24.fr" + link_tag["href"] if link_tag else "N/A"

                is_recent = False
                try:
                    if year != "N/A" and int(year) >= 2023:
                        is_recent = True
                except:
                    pass

                is_correct_fuel = fuel in ("Essence", "Hybride")

                if is_recent and is_correct_fuel:
                    results.append(
                        f"\U0001f697 {model_name} ({year})\n"
                        f"\U0001f4b0 Price: {price_text}\n"
                        f"\u26fd Fuel: {fuel}\n"
                        f"\U0001f6e3\ufe0f Mileage: {mileage}\n"
                        f"\U0001f4cd Location: {location}\n"
                        f"\U0001f517 Link: {link}\n"
                        f"\U0001f6e0\ufe0f Status: Non-accident\u00e9\n"
                        f"\U0001f4cc Source: AutoScout24"
                    )
            except Exception as e:
                logger.warning(f"Error parsing AutoScout24 listing: {e}")
    except Exception as e:
        logger.error(f"Error accessing AutoScout24: {e}")

    return results


def search_leboncoin(max_price: int) -> list:
    """Search Leboncoin.fr for matching listings."""
    results = []

    leboncoin_url = (
        f"https://www.leboncoin.fr/recherche?category=2&"
        f"fuel=1&price=min-{max_price}&"
        f"regdate=2023-max&"
        f"vehicle_damage=undamaged&"
        f"sort=time&order=desc"
    )

    try:
        response = requests.get(leboncoin_url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(response.content, "html.parser")

        # Try to find listing cards
        listing_cards = soup.find_all("a", href=re.compile(r"/ad/voitures/"))

        for card in listing_cards:
            try:
                title_tag = card.find("p") or card.find("span")
                model_name = title_tag.text.strip() if title_tag else "N/A"
                if model_name == "N/A":
                    continue

                price_tag = card.find(string=re.compile(r"\d+\s*\u20ac"))
                price_text = price_tag.strip() if price_tag else "N/A"

                href = card.get("href", "")
                link = f"https://www.leboncoin.fr{href}" if href.startswith("/") else href

                card_text = card.get_text("|", strip=True)
                year_match = re.search(r'20(2[3-9]|[3-9]\d)', card_text)
                year = year_match.group(0) if year_match else "2023+"
                mileage_match = re.search(r'(\d+[\s\d]*)\s*km', card_text)
                mileage = mileage_match.group(0).strip() if mileage_match else "N/A"

                location_match = re.search(r'(\d{5})', card_text)
                location = location_match.group(0) if location_match else "France"

                results.append(
                    f"\U0001f697 {model_name} ({year})\n"
                    f"\U0001f4b0 Price: {price_text}\n"
                    f"\u26fd Fuel: Essence\n"
                    f"\U0001f6e3\ufe0f Mileage: {mileage}\n"
                    f"\U0001f4cd Location: {location}\n"
                    f"\U0001f517 Link: {link}\n"
                    f"\U0001f6e0\ufe0f Status: Non-accident\u00e9\n"
                    f"\U0001f4cc Source: Leboncoin"
                )
            except Exception as e:
                logger.warning(f"Error parsing Leboncoin listing: {e}")
    except Exception as e:
        logger.error(f"Error accessing Leboncoin: {e}")

    return results


async def search_cars(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle price input and search for cars."""
    text = update.message.text.strip()

    price_match = re.search(r'\d+', text.replace(" ", "").replace(",", "").replace(".", ""))
    if not price_match:
        await update.message.reply_text("Please enter a valid price (number only). Example: 10000")
        return

    max_price = int(price_match.group())
    if max_price < 1000 or max_price > 100000:
        await update.message.reply_text("Please enter a price between 1,000\u20ac and 100,000\u20ac.")
        return

    await update.message.reply_text(
        f"\U0001f50d Searching for cars under {max_price:,}\u20ac...\n"
        f"\u26fd Essence/Hybride | \U0001f4c5 2023+ | \U0001f6e0\ufe0f Non-accident\u00e9\n"
        f"\U0001f310 Searching AutoScout24.fr & Leboncoin.fr...\n\n"
        f"Please wait..."
    )

    # Search both platforms
    results = []
    results.extend(search_autoscout24(max_price))
    results.extend(search_leboncoin(max_price))

    if results:
        count = min(len(results), 15)
        for result in results[:count]:
            await update.message.reply_text(result)
        if len(results) > count:
            await update.message.reply_text(
                f"\n\U0001f4ca Found {len(results)} total results. Showing top {count}.\n"
                f"Refine your search with a lower price for more specific results."
            )
        else:
            await update.message.reply_text(f"\n\U0001f4ca Found {len(results)} matching car(s).")
    else:
        await update.message.reply_text(
            "\u274c No matching cars found with the given criteria.\n\n"
            "This can happen because:\n"
            "\u2022 Websites may block automated access\n"
            "\u2022 No listings match at this price point\n\n"
            "\U0001f4a1 Try a higher price or check manually:\n"
            "\u2022 https://www.autoscout24.fr\n"
            "\u2022 https://www.leboncoin.fr/c/voitures"
        )


def main() -> None:
    """Start the bot."""
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_cars))
    logger.info("Bot started - searching AutoScout24.fr & Leboncoin.fr")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
