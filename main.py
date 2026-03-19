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
RESPONSE_CHANCE = float(os.getenv("RESPONSE_CHANCE", "0.15"))

if not BOT_TOKEN or not TARGET_USERNAME or not TXT_PATH:
    logger.error("Missing environment variables.")
    raise Exception("Missing environment variables")

logger.info(f"BOT_TOKEN: {BOT_TOKEN}")
logger.info(f"TARGET_USERNAME: {TARGET_USERNAME}")
logger.info(f"TXT_PATH: {TXT_PATH}")
logger.info(f"RESPONSE_CHANCE: {RESPONSE_CHANCE}")


class MarkovBot:
    def __init__(self, api_token, target_username, txt_path, response_chance: float):
        self.bot = Bot(token=api_token)
        self.dp = Dispatcher()
        self.target_username = target_username
        self.txt_path = txt_path
        self.response_chance = response_chance

        self.conn = sqlite3.connect("./data/messages.db")
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

        if os.path.exists(self.txt_path):
            self.cursor.execute("SELECT COUNT(*) FROM messages")
            if self.cursor.fetchone()[0] == 0:
                with open(self.txt_path, "r") as f:
                    lines = [(line.strip(),) for line in f if line.strip()]
                if lines:
                    self.cursor.executemany(
                        "INSERT INTO messages (text) VALUES (?)", lines
                    )
                    self.conn.commit()
                    logger.info(
                        f"Initialized database with {len(lines)} messages from {self.txt_path}"
                    )
                    return
        logger.info("Database already initialized or no txt file found.")

    def add_message(self, text: str):
        """Adds a new message to the database and rebuilds the Markov model

        Args:
            text (str): Message text to add to the database
        """
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
        else:
            logger.warning("No messages to build Markov model from")
        return markovify.NewlineText(text, state_size=1)

    async def handle_message(self, message: types.Message):
        """Handles incoming messages, decides whether to reply, and generates a response if needed"""
        logger.info(
            f"Received message from @{message.from_user.username}: {message.text}"
        )

        if message.from_user.username == self.target_username and message.text:
            self.add_message(message.text)

        reply_to = message.reply_to_message

        should_reply = (
            reply_to
            and reply_to.from_user.id == self.bot.id
            and message.from_user.id != self.bot.id
        ) or random.random() < self.response_chance

        if not should_reply:
            return

        sentence = await self.generate_sentence()
        if not sentence:
            return

        if sentence:
            await self.send(
                message.chat.id,
                sentence,
                reply_to_message_id=message.message_id if reply_to else None,
            )
            logger.info(f"Sent message to chat {message.chat.id}: {sentence}")

    async def send(self, chat_id: int, text: str, reply_to_message_id: int = None):
        """Sends message to a chat

        Args:
            chat_id (int): Chat ID to send the message to
            text (str): Message text to send
            reply_to_message_id (int, optional): Message ID to reply to. Defaults to None.
        """
        try:
            await self.bot.send_message(
                chat_id, text, reply_to_message_id=reply_to_message_id
            )
        except Exception as e:
            logger.error(f"Error sending message to chat {chat_id}: {e}")

    async def generate_sentence(self):
        """Generates a sentence using the Markov model"""
        sentence = None
        while not sentence:
            sentence = self.model.make_short_sentence(
                random.randint(1, 100), tries=100
            )
        return sentence

    async def periodic_sender(
        self, chat_id: int, min_delay: int = 3600, max_delay: int = 3600 * 4
    ):  # TODO: target chat_ids instead of TARGET_USERNAME
        """Periodically sends a message to a chat with a random delay between messages

        Args:
            chat_id (int): _description_
            min_delay (int, optional): Minimum delay (in seconds). Defaults to 3600.
            max_delay (int, optional): Maximum delay (in seconds). Defaults to 3600*4.
        """
        while True:
            random_delay = random.randint(min_delay, max_delay)
            await asyncio.sleep(random_delay)  # Send a message every 2-4 hours
            sentence = await self.generate_sentence()
            if sentence:
                await self.send(TARGET_USERNAME, sentence)
                logger.info(f"Sent periodic message to @{TARGET_USERNAME}: {sentence}")

    async def run(self):
        logger.info("Starting bot...")
        await self.dp.start_polling(self.bot)


if __name__ == "__main__":
    bot = MarkovBot(
        api_token=BOT_TOKEN,
        target_username=TARGET_USERNAME,
        txt_path=TXT_PATH,
        response_chance=RESPONSE_CHANCE,
    )
    try:
        asyncio.run(bot.run())
    except Exception as e:
        logger.error(f"Bot stopped with error: {e}")
