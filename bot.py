import logging
import os
import requests
from bs4 import BeautifulSoup
from telegram import Update, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from datetime import datetime
import re
import tempfile

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable is not set!")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send welcome message."""
    await update.message.reply_text(
        "🚗 Welcome to the France Car Sourcing Bot!\n\n"
        "Enter your maximum price in EUR to search for available cars:\n\n"
        "🔍 Searching on: AutoScout24.fr & Leboncoin.fr\n"
        "⛽ Fuel: Essence / Hybride only\n"
        "📅 Year: 2023+\n"
        "🛠️ Condition: Non-accidenté"
    )


def search_autoscout24(max_price: int) -> list:
    """Search AutoScout24.fr for matching listings."""
    results = []
    current_year = datetime.now().year

    # Search multiple pages for better coverage
    for page in range(1, 3):
        autoscout_url = (
            f"https://www.autoscout24.fr/lst?"
            f"fuel=B%2CH&pricefrom=0&priceto={max_price}"
            f"&fregfrom=2023&fregto={current_year}"
            f"&desc=1&size=20&page={page}&fc=0&cy=F"
            f"&damaged_listing=exclude&powertype=kw&sort=age"
        )

        try:
            response = requests.get(autoscout_url, headers=HEADERS, timeout=20)
            if response.status_code != 200:
                logger.warning(f"AutoScout24 returned status {response.status_code}")
                continue

            soup = BeautifulSoup(response.content, "html.parser")

            # Find all listing links - AutoScout24 uses links with /offres/ in href
            all_links = soup.find_all("a", href=re.compile(r"/offres/[a-z]"))

            seen_urls = set()
            for link_tag in all_links:
                try:
                    href = link_tag.get("href", "")
                    if not href or href in seen_urls:
                        continue

                    full_link = "https://www.autoscout24.fr" + href if href.startswith("/") else href
                    seen_urls.add(href)

                    # Get the parent article or container
                    container = link_tag.find_parent("article") or link_tag.find_parent("div", class_=re.compile(r"list"))
                    if not container:
                        container = link_tag

                    container_text = container.get_text("|", strip=True)

                    # Extract model name from h2 or first significant text
                    model_tag = container.find("h2") or container.find("a")
                    model_name = model_tag.text.strip() if model_tag else "Unknown"
                    # Clean up model name
                    if len(model_name) > 80:
                        model_name = model_name[:80]

                    # Extract price
                    price_match = re.search(r'([\d\s\.]+)\s*€', container_text)
                    if price_match:
                        price_text = price_match.group(0).strip()
                    else:
                        price_text = "N/A"

                    # Extract year
                    year_match = re.search(r'(\d{2})/(\d{4})', container_text)
                    if year_match:
                        year = year_match.group(2)
                    else:
                        year_match2 = re.search(r'(202[3-9]|20[3-9]\d)', container_text)
                        year = year_match2.group(0) if year_match2 else "N/A"

                    # Extract mileage
                    mileage_match = re.search(r'([\d\s\.]+)\s*km', container_text)
                    mileage = mileage_match.group(0).strip() if mileage_match else "N/A"

                    # Determine fuel type
                    text_lower = container_text.lower()
                    if "hybride" in text_lower or "hybrid" in text_lower:
                        fuel = "Hybride"
                    elif "essence" in text_lower:
                        fuel = "Essence"
                    else:
                        fuel = "Essence"

                    # Extract location
                    location_tag = container.find("span", class_=re.compile(r"SellerInfo|address|location", re.I))
                    if location_tag:
                        location = location_tag.text.strip()
                    else:
                        loc_match = re.search(r'(\d{5})\s*([A-Za-zÀ-ÿ\s\-]+)', container_text)
                        location = f"{loc_match.group(2).strip()} ({loc_match.group(1)})" if loc_match else "France"

                    # Filter: year must be 2023+
                    is_recent = False
                    try:
                        if year != "N/A" and int(year) >= 2023:
                            is_recent = True
                    except:
                        pass

                    if is_recent and model_name != "Unknown":
                        results.append({
                            "model": model_name,
                            "year": year,
                            "price": price_text,
                            "fuel": fuel,
                            "mileage": mileage,
                            "location": location,
                            "link": full_link,
                            "source": "AutoScout24"
                        })
                except Exception as e:
                    logger.warning(f"Error parsing AutoScout24 listing: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error accessing AutoScout24 page {page}: {e}")

    # Remove duplicates based on link
    seen = set()
    unique_results = []
    for r in results:
        if r["link"] not in seen:
            seen.add(r["link"])
            unique_results.append(r)

    return unique_results


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
        response = requests.get(leboncoin_url, headers=HEADERS, timeout=20)
        soup = BeautifulSoup(response.content, "html.parser")

        # Find listing links
        listing_links = soup.find_all("a", href=re.compile(r"/ad/voitures/\d+"))

        seen_urls = set()
        for card in listing_links:
            try:
                href = card.get("href", "")
                if not href or href in seen_urls:
                    continue
                seen_urls.add(href)

                link = f"https://www.leboncoin.fr{href}" if href.startswith("/") else href

                card_text = card.get_text("|", strip=True)

                # Extract title/model
                title_tag = card.find("p") or card.find("span")
                model_name = title_tag.text.strip() if title_tag else "N/A"
                if model_name == "N/A" or len(model_name) < 3:
                    continue

                # Extract price
                price_match = re.search(r'([\d\s\.]+)\s*€', card_text)
                price_text = price_match.group(0).strip() if price_match else "N/A"

                # Extract year
                year_match = re.search(r'(202[3-9]|20[3-9]\d)', card_text)
                year = year_match.group(0) if year_match else "2023+"

                # Extract mileage
                mileage_match = re.search(r'([\d\s\.]+)\s*km', card_text)
                mileage = mileage_match.group(0).strip() if mileage_match else "N/A"

                # Location
                loc_match = re.search(r'(\d{5})', card_text)
                location = loc_match.group(0) if loc_match else "France"

                results.append({
                    "model": model_name,
                    "year": year,
                    "price": price_text,
                    "fuel": "Essence",
                    "mileage": mileage,
                    "location": location,
                    "link": link,
                    "source": "Leboncoin"
                })
            except Exception as e:
                logger.warning(f"Error parsing Leboncoin listing: {e}")
    except Exception as e:
        logger.error(f"Error accessing Leboncoin: {e}")

    return results


def format_result(car: dict) -> str:
    """Format a single car result for Telegram."""
    return (
        f"🚗 {car['model']} ({car['year']})\n"
        f"💰 Price: {car['price']}\n"
        f"⛽ Fuel: {car['fuel']}\n"
        f"🛣️ Mileage: {car['mileage']}\n"
        f"📍 Location: {car['location']}\n"
        f"🔗 Link: {car['link']}\n"
        f"🛠️ Status: Non-accidenté\n"
        f"📌 Source: {car['source']}"
    )


def generate_pdf_report(results: list, max_price: int) -> str:
    """Generate a text report file with all results."""
    report_lines = []
    report_lines.append("=" * 60)
    report_lines.append("  FRANCE CAR SOURCING REPORT")
    report_lines.append(f"  Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    report_lines.append(f"  Max Price: {max_price:,}€")
    report_lines.append(f"  Criteria: Essence/Hybride | 2023+ | Non-accidenté")
    report_lines.append(f"  Sources: AutoScout24.fr & Leboncoin.fr")
    report_lines.append(f"  Total Results: {len(results)}")
    report_lines.append("=" * 60)
    report_lines.append("")

    for i, car in enumerate(results, 1):
        report_lines.append(f"--- Car #{i} ---")
        report_lines.append(f"Model:    {car['model']} ({car['year']})")
        report_lines.append(f"Price:    {car['price']}")
        report_lines.append(f"Fuel:     {car['fuel']}")
        report_lines.append(f"Mileage:  {car['mileage']}")
        report_lines.append(f"Location: {car['location']}")
        report_lines.append(f"Link:     {car['link']}")
        report_lines.append(f"Status:   Non-accidenté")
        report_lines.append(f"Source:   {car['source']}")
        report_lines.append("")

    report_lines.append("=" * 60)
    report_lines.append("  Generated by France Car Sourcing Bot")
    report_lines.append("=" * 60)

    # Save to temp file
    tmp_file = tempfile.NamedTemporaryFile(
        mode='w', suffix='.txt', prefix='car_report_',
        delete=False, encoding='utf-8'
    )
    tmp_file.write("\n".join(report_lines))
    tmp_file.close()
    return tmp_file.name


async def search_cars(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle price input and search for cars."""
    text = update.message.text.strip()

    price_match = re.search(r'\d+', text.replace(" ", "").replace(",", "").replace(".", ""))
    if not price_match:
        await update.message.reply_text("Please enter a valid price (number only). Example: 10000")
        return

    max_price = int(price_match.group())
    if max_price < 1000 or max_price > 100000:
        await update.message.reply_text("Please enter a price between 1,000€ and 100,000€.")
        return

    await update.message.reply_text(
        f"🔍 Searching for cars under {max_price:,}€...\n"
        f"⛽ Essence/Hybride | 📅 2023+ | 🛠️ Non-accidenté\n"
        f"🌐 Searching AutoScout24.fr & Leboncoin.fr...\n\n"
        f"Please wait..."
    )

    # Search both platforms
    results = []
    results.extend(search_autoscout24(max_price))
    results.extend(search_leboncoin(max_price))

    if results:
        # Send individual results (max 15)
        count = min(len(results), 15)
        for car in results[:count]:
            await update.message.reply_text(format_result(car))

        if len(results) > count:
            await update.message.reply_text(
                f"\n📊 Found {len(results)} total results. Showing top {count}."
            )
        else:
            await update.message.reply_text(f"\n📊 Found {len(results)} matching car(s).")

        # Generate and send report file
        try:
            report_path = generate_pdf_report(results, max_price)
            with open(report_path, 'rb') as f:
                await update.message.reply_document(
                    document=InputFile(f, filename=f"car_report_{max_price}EUR_{datetime.now().strftime('%Y%m%d')}.txt"),
                    caption="📄 Full report with all listings and links attached above."
                )
            os.unlink(report_path)
        except Exception as e:
            logger.error(f"Error generating report: {e}")
    else:
        await update.message.reply_text(
            "❌ No matching cars found with the given criteria.\n\n"
            "This can happen because:\n"
            "• Websites may block automated access\n"
            "• No listings match at this price point\n\n"
            "💡 Try a higher price or check manually:\n"
            "• https://www.autoscout24.fr\n"
            "• https://www.leboncoin.fr/c/voitures"
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
