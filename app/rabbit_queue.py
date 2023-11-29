import asyncio
import logging
import os

import aio_pika
import httpx

from app.message_storage import MESSAGE_STORAGE

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RabbitQueue:
    def __init__(self, queue_name) -> None:
        self._queue_name = queue_name

    async def run_message_receiver(self) -> None:
        try:
            connection = await self._connection_maker()

            async with connection:
                channel = await connection.channel()

                queue = await channel.declare_queue(
                    self._queue_name,
                    durable=True,
                )

                async def callback(message):
                    async with message.process():
                        body = message.body.decode("utf-8")
                        logger.info(msg=f"Received command from queue: {body}")
                        await self._actions_with_messages(body)

                await queue.consume(callback)

                logger.info(msg="Rabbit Queue started and waiting for messages.")
                while True:
                    await asyncio.sleep(1)
        except TypeError:
            logger.info(msg="Connection filed. Check provided credentials and try again.")
            return

    async def _connection_maker(self):
        try:
            connection = await aio_pika.connect_robust(
                login=os.getenv("AMQP_USER"),
                password=os.getenv("AMQP_PASSWORD"),
                host=os.getenv("AMQP_ADDRESS"),
                virtual_host=os.getenv("AMQP_VHOST"),
                port=int(os.getenv("AMQP_PORT")),
            )
            return connection
        except aio_pika.exceptions.AMQPConnectionError:
            return None

    async def _actions_with_messages(self, message) -> None:
        if message.lower() == "print":
            await self._print_last_message()

        elif message.lower() == "send":
            await self._send_message_to_external_api()

    async def _print_last_message(self) -> None:
        if MESSAGE_STORAGE.message:
            logger.info(msg=f"Last message: {MESSAGE_STORAGE.message}")
        else:
            self._print_no_messages()

    async def _send_message_to_external_api(self) -> None:
        if not os.getenv("EXTERNAL_API_URL"):
            logger.info(msg="External API URL is not set.")
            return

        if MESSAGE_STORAGE.message:
            data = {"last_message": MESSAGE_STORAGE.message}
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    os.getenv("EXTERNAL_API_URL"), json=data
                )
            logger.info(msg=f"POST request status: {response.status_code}")
        else:
            self._print_no_messages()

    @staticmethod
    def _print_no_messages() -> None:
        logger.info(msg="No message received yet.")

