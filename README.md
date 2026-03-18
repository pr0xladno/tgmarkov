# tgmarkov

A Telegram bot that learns from a target user's messages and generates responses using Markov chains, somewhat similar to [vk-markovify-chatbot](https://github.com/monosans/vk-markovify-chatbot) but with extra steps. The bot collects messages from the specified user, builds a Markov model, and occasionally responds with generated text that mimics the user's style.

## Prerequisites

- Python 3.12 or higher
- Telegram Bot Token (obtain from [@BotFather](https://t.me/botfather))
- Target user's Telegram username

## Installation

### Option 1: Using Docker (Recommended)

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd tgmarkov
   ```

2. Create a `.env` file in the project root:
   ```
   BOT_TOKEN=your_telegram_bot_token_here
   TARGET_USERNAME=target_user_username_without_@
   TXT_PATH=messages.txt
   RESPONSE_CHANCE=0.15
   ```

3. Run with Docker Compose:
   ```bash
   docker-compose up -d
   ```

### Option 2: Local Python Environment

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd tgmarkov
   ```

2. Install dependencies using uv (recommended):
   ```bash
   pip install uv
   uv sync
   ```

   Or using pip:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the project root:
   ```
   BOT_TOKEN=your_telegram_bot_token_here
   TARGET_USERNAME=target_user_username_without_@
   TXT_PATH=messages.txt
   RESPONSE_CHANCE=0.15
   ```

4. Run the bot:
   ```bash
   python main.py
   ```

## Configuration

The bot requires the following environment variables:

- `BOT_TOKEN`: Your Telegram bot token from BotFather
- `TARGET_USERNAME`: The username of the user whose messages the bot will learn from (without @)
- `TXT_PATH`: Path to the initial text file for seeding the Markov model (default: messages.txt). Note that the project uses NewlineText(), so format the file firstly.
- `RESPONSE_CHANCE`: Probability of the bot responding to messages (default: 0.15 = 15%)

## How It Works

1. The bot monitors messages in chats it's added to
2. When the target user sends a message, it's added to the database and the Markov model is updated
3. With a configurable probability, the bot generates and sends a response

## Data Storage

- Messages are stored in `messages.db` (SQLite database)
- The `data/` directory is mounted as a volume in Docker for persistence
- Initial messages can be provided via the `TXT_PATH` file

## Development

The project uses:
- `aiogram` for Telegram Bot API
- `markovify` for Markov chain text generation
- `uv` for dependency management

## License

[MIT](LICENSE)