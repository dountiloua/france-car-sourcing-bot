# France Car Sourcing Bot

This Telegram bot helps users search for car listings on French websites based on their specified maximum price. The bot focuses on gasoline or hybrid cars, registered from June 1, 2023, to the current date, with a 'non-accidenté' (no accidents) condition.

## Features

- **`/start` command**: Greets the user and prompts for a maximum price.
- **Price-based search**: Users can enter a maximum price in EUR, and the bot will search for matching car listings.
- **Criteria**: Searches for Gasoline or Hybrid cars, registered from 01/06/2023 to today, with a 'non-accidenté' condition.
- **Websites**: Searches on AutoScout24.fr & Leboncoin.fr simultaneously.
- **Formatted results**: Returns car listings with details such as model, year, price, fuel type, mileage, location, link, and status.

## Setup and Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/dountiloua/france-car-sourcing-bot.git
    cd france-car-sourcing-bot
    ```

2.  **Create a virtual environment** (recommended):
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure your Telegram Bot Token**:
    Create a `.env` file in the project root with your Telegram bot token:
    ```
    TELEGRAM_BOT_TOKEN=your_token_here
    ```
    (You can get your bot token from BotFather on Telegram).

## How to Run

To run the bot, execute the `bot.py` script:

```bash
python3 bot.py
```

For running in the background (e.g., on a server):

```bash
nohup python3 bot.py > bot.log 2>&1 &
```

## Usage

1.  Start a chat with your bot on Telegram.
2.  Send the `/start` command.
3.  Enter your desired maximum price in EUR when prompted.
4.  The bot will return matching car listings from AutoScout24.fr & Leboncoin.fr.

## Contributing

Feel free to fork the repository, make improvements, and submit pull requests.

## License

This project is open-source and available under the MIT License.
