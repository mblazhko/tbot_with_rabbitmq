import asyncio
import os

from app import RABBIT_QUEUE
from app import run_bot

from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')


async def main():
    task_bot = asyncio.create_task(run_bot(TOKEN))
    task_message_receiver = asyncio.create_task(
        RABBIT_QUEUE.run_message_receiver()
    )

    await asyncio.gather(task_bot, task_message_receiver)

if __name__ == '__main__':
    asyncio.run(main())
