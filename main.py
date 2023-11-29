import asyncio
import os

from app import RabbitQueue
from app import run_bot

from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')


async def main():
    rabbit_queue = RabbitQueue("0")

    task_bot = asyncio.create_task(run_bot(TOKEN))
    task_message_receiver = asyncio.create_task(
        rabbit_queue.run_message_receiver()
    )

    await asyncio.gather(task_bot, task_message_receiver)

if __name__ == '__main__':
    asyncio.run(main())
