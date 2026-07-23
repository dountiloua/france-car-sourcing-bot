# 🚗 CARDZSCRAP

**France Auto Export Sourcing Agent** — A Telegram bot that instantly generates pre-filtered search links for used cars in France, ready for export.

## Features

- **Instant Results**: Enter a max price and get direct links to matching listings
- **Multi-Platform**: Searches across AutoScout24.fr, Leboncoin.fr & LaCentrale.fr
- **Pre-Filtered**: All links come with filters already applied (fuel, year, condition)
- **Export Ready**: Focused on non-accidenté vehicles suitable for export
- **Criteria**: Gasoline/Hybrid only, 2023+, non-damaged

## How It Works

1. User sends `/start` to the bot
2. User enters their maximum budget in EUR
3. Bot generates direct search links with all filters pre-applied
4. User clicks links to view all matching listings instantly

## Setup & Installation

1. **Clone the repository**:
    ```bash
    git clone https://github.com/dountiloua/france-car-sourcing-bot.git
    cd france-car-sourcing-bot
    ```

2. **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3. **Set your Telegram Bot Token**:
    ```bash
    export TELEGRAM_BOT_TOKEN=your_token_here
    ```

4. **Run the bot**:
    ```bash
    python3 bot.py
    ```


## Search Platforms

| Platform | Coverage |
|----------|----------|
| AutoScout24.fr | Professional & private sellers |
| Leboncoin.fr | Private listings & dealers |
| LaCentrale.fr | Certified dealers |

## License

MIT License — Free to use and modify.

---

**Powered by ALI DOUNTILOU** 🚗

