import asyncio
import logging
import os

import aio_pika
from aio_pika import DeliveryMode, Message
import httpx

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RabbitQueue:
    def __init__(self, queue_name) -> None:
        self._queue_name = queue_name
        self._last_message = None

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
                        await self._actions_with_messages(message=body)

                await queue.consume(callback)

                logger.info(
                    msg="Rabbit Queue started and waiting for messages."
                )
                while True:
                    await asyncio.sleep(1)
        except TypeError:
            logger.info(
                msg="Connection filed. Check provided credentials and try again."
            )
            return

    async def send_message_to_queue(self, message_text) -> None:
        connection = await self._connection_maker()
        async with connection:
            channel = await connection.channel()
            queue = await channel.declare_queue(
                self._queue_name,
                durable=True,
            )

            message = Message(
                message_text.encode("utf-8"),
                delivery_mode=DeliveryMode.PERSISTENT,
            )

            await channel.default_exchange.publish(
                message, routing_key=queue.name
            )

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
            logger.info(msg=f"Received 'print' command. Printing last message")
            await self._print_last_message()

        elif message.lower() == "send":
            logger.info(
                msg=f"Received 'send' command. Sending last message to external API"
            )
            await self._send_message_to_external_api()

        else:
            self._last_message = message

    async def _print_last_message(self) -> None:
        if self._last_message:
            logger.info(msg=f"Last message: {self._last_message}")
        else:
            self._print_no_messages()

    async def _send_message_to_external_api(self) -> None:
        if not os.getenv("EXTERNAL_API_URL"):
            logger.info(msg="External API URL is not set.")
            return

        if self._last_message:
            data = {"last_message": self._last_message}
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


RABBIT_QUEUE = RabbitQueue("0")
