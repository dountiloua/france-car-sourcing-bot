
import logging
import os
import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from datetime import datetime
import re

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = "6997085553:AAELf17C6jHmuTkyRS13J0KoR4mhr238sTQ"

async def start(update: Update, context) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        f"Hi {user.mention_html()}!\n🚗 Welcome to the France Car Sourcing Bot! Enter your maximum price in EUR to search for available cars:"
    )

async def search_cars(update: Update, context) -> None:
    """Search for cars based on the user's maximum price."""
    try:
        text = update.message.text.strip()
        max_price = int(re.sub(r'[^\d]', '', text))
        if max_price <= 0:
            await update.message.reply_text("Please enter a positive number for the maximum price.")
            return
    except ValueError:
        await update.message.reply_text("That doesn't look like a valid price. Please enter a number for the maximum price.")
        return

    await update.message.reply_text(f"Searching for cars with a maximum price of {max_price}€...")

    results = []
    current_year = datetime.now().year
    
    # AutoScout24.fr search URL with sorting by age (newest first)
    autoscout_url = f"https://www.autoscout24.fr/lst?fuel=B%2CH&pricefrom=0&priceto={max_price}&fregfrom=2023&fregto={current_year}&desc=1&size=20&page=1&fc=0&cy=F&damaged_listing=exclude&powertype=kw&sort=age"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(autoscout_url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.content, "html.parser")
        
        # AutoScout24 uses 'article' tags for listings
        listings = soup.find_all("article")

        for listing in listings:
            try:
                # Extract Model Name
                model_tag = listing.find("h2")
                if not model_tag: continue
                model_name = model_tag.text.strip()

                # Extract Price
                price_tag = listing.find("p", string=re.compile(r"€"))
                if not price_tag:
                    # Try finding by class if string match fails
                    price_tag = listing.find(class_=re.compile(r"price", re.I))
                
                price_text = price_tag.text.strip() if price_tag else "N/A"
                # Clean price text to just numbers
                price_val = re.sub(r'[^\d]', '', price_text)

                # Extract Year, Mileage, Fuel from the data list
                data_list = listing.find_all("span", class_=re.compile(r"DataVehicle", re.I))
                if not data_list:
                    # Fallback to looking for specific text patterns
                    data_text = listing.get_text("|", strip=True)
                    year_match = re.search(r'(\d{2}/\d{4})', data_text)
                    year = year_match.group(1).split('/')[-1] if year_match else "N/A"
                    
                    mileage_match = re.search(r'(\d+[\s\d]*)\s*km', data_text)
                    mileage = mileage_match.group(1).strip() if mileage_match else "N/A"
                    
                    fuel = "Essence" if "Essence" in data_text else ("Hybride" if "Hybride" in data_text else "N/A")
                else:
                    # Usually: 0: mileage, 1: year, 2: fuel, 3: power
                    mileage = data_list[0].text.strip() if len(data_list) > 0 else "N/A"
                    year_full = data_list[1].text.strip() if len(data_list) > 1 else "N/A"
                    year = year_full.split('/')[-1] if '/' in year_full else year_full
                    fuel = data_list[2].text.strip() if len(data_list) > 2 else "N/A"

                # Extract Location
                location_tag = listing.find("span", class_=re.compile(r"SellerInfo_address", re.I))
                location = location_tag.text.strip() if location_tag else "N/A"

                # Extract Link
                link_tag = listing.find("a", href=re.compile(r"/offres/"))
                link = "https://www.autoscout24.fr" + link_tag["href"] if link_tag else "N/A"

                # Filter: Must be 2023 or newer, and Gasoline/Hybrid
                is_recent = False
                try:
                    if year != "N/A" and int(year) >= 2023:
                        is_recent = True
                except: pass

                is_correct_fuel = False
                if fuel != "N/A" and ("essence" in fuel.lower() or "hybride" in fuel.lower() or "hybrid" in fuel.lower()):
                    is_correct_fuel = True

                if is_recent and is_correct_fuel:
                    results.append(
                        f"🚗 {model_name} ({year})\n"\
                        f"💰 Price: {price_text}\n"\
                        f"⛽ Fuel: {fuel}\n"\
                        f"🛣️ Mileage: {mileage}\n"\
                        f"📍 Location: {location}\n"\
                        f"🔗 Link: {link}\n"\
                        f"🛠️ Status: Non-accidenté\n"
                    )
            except Exception as e:
                logger.warning(f"Error parsing listing: {e}")

    except Exception as e:
        logger.error(f"Error accessing AutoScout24: {e}")

    if results:
        # Send top 10 results to avoid flooding
        for result in results[:10]:
            await update.message.reply_text(result)
        if len(results) > 10:
            await update.message.reply_text(f"Found {len(results)} total results. Showing the top 10.")
    else:
        await update.message.reply_text("No matching cars found on AutoScout24.fr with the given criteria. Please try a different price or check back later.")


def main() -> None:
    """Start the bot."""
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_cars))

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
