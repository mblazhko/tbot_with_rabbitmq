import logging

from aiogram import Dispatcher, types, Bot
from aiogram.enums import ParseMode

from app.rabbit_queue import RABBIT_QUEUE

from dotenv import load_dotenv

load_dotenv()

dp = Dispatcher()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dp.message()
async def echo_handler(
    message: types.Message,
) -> None:
    logger.info(msg=f"Received message from bot: {message.text}")
    await RABBIT_QUEUE.send_message_to_queue(message.text)


async def create_bot(token: str) -> Bot:
    return Bot(token, parse_mode=ParseMode.HTML)


async def run_bot(token: str) -> None:
    bot = await create_bot(token)
    logger.info(msg=f"Bot started")
    await dp.start_polling(bot)
