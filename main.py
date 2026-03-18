import asyncio
import random
import markovify
import sqlite3
import os
import logging
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram import F

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("bot.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
TARGET_USERNAME = os.getenv("TARGET_USERNAME")
TXT_PATH = os.getenv("TXT_PATH")
RESPONSE_CHANCE = 0.15

if not BOT_TOKEN or not TARGET_USERNAME or not TXT_PATH:
    logger.error("Missing environment variables.")
    raise Exception("Missing environment variables")

logger.info(f"BOT_TOKEN: {BOT_TOKEN}")
logger.info(f"TARGET_USERNAME: {TARGET_USERNAME}")
logger.info(f"TXT_PATH: {TXT_PATH}")
logger.info(f"RESPONSE_CHANCE: {RESPONSE_CHANCE}")


class MarkovBot:
    def __init__(self, api_token, target_user_id, txt_path, response_chance):
        self.bot = Bot(token=api_token)
        self.dp = Dispatcher()
        self.target_user_id = target_user_id
        self.txt_path = txt_path
        self.response_chance = response_chance

        self.conn = sqlite3.connect("messages.db")
        self.cursor = self.conn.cursor()
        self._init_db()
        self.model = self._build_model()

        self.dp.message(F.chat.type.in_({"private", "group", "supergroup"}))(
            self.handle_message
        )

    def _init_db(self):
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL
            )
        """
        )
        self.conn.commit()
        self.cursor.execute("SELECT COUNT(*) FROM messages")
        if self.cursor.fetchone()[0] == 0 and os.path.exists(self.txt_path):
            with open(self.txt_path, "r") as f:
                lines = [line.strip() for line in f if line.strip()]
                self.cursor.executemany(
                    "INSERT INTO messages (text) VALUES (?)",
                    [(line,) for line in lines],
                )
                self.conn.commit()
            logger.info(
                f"Initialized database with {len(lines)} messages from {self.txt_path}"
            )
        else:
            logger.info("Database already initialized or no txt file found.")

    def add_message(self, text):
        self.cursor.execute("INSERT INTO messages (text) VALUES (?)", (text,))
        self.conn.commit()
        self.model = self._build_model()
        logger.debug(f"Added message: {text}")

    def _build_model(self):
        self.cursor.execute("SELECT text FROM messages")
        messages = self.cursor.fetchall()
        text = "\n".join([msg[0] for msg in messages])
        if text.strip():
            logger.info(f"Building Markov model with {len(messages)} messages")
            return markovify.NewlineText(text, state_size=1)
        logger.warning("No messages to build Markov model from")
        return markovify.NewlineText("", state_size=1)

    async def handle_message(self, message: types.Message):
        logger.info(
            f"Received message from @{message.from_user.username}: {message.text}"
        )
        if message.from_user.username == self.target_user_id:
            self.add_message(message.text)
            self.model = self._build_model()
        if random.random() < self.response_chance:
            sentence = await self.generate_sentence()
            if sentence:
                await self.send(message.chat.id, sentence)
                logger.info(f"Sent message to chat {message.chat.id}: {sentence}")

    async def send(self, chat_id, text):
        try:
            await self.bot.send_message(chat_id, text)
        except Exception as e:
            logger.error(f"Error sending message to chat {chat_id}: {e}")

    async def generate_sentence(self):
        return self.model.make_sentence()

    async def run(self):
        logger.info("Starting bot...")
        await self.dp.start_polling(self.bot)


if __name__ == "__main__":
    bot = MarkovBot(
        api_token=BOT_TOKEN,
        target_user_id=TARGET_USERNAME,
        txt_path=TXT_PATH,
        response_chance=RESPONSE_CHANCE,
    )
    try:
        asyncio.run(bot.run())
    except Exception as e:
        logger.error(f"Bot stopped with error: {e}")
