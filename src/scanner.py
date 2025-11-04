import asyncio
import struct
import sys
import json
import os
import structlog
import logging
from bleak import BleakScanner
from aiomqtt import Client

structlog.configure(wrapper_class=structlog.make_filtering_bound_logger(logging.INFO))
logger = structlog.get_logger(__name__)


class subscription:
    def __init__(self):
        self.queue = asyncio.Queue()

    def get(self):
        return self.queue.get()

    async def consume(self, callback, args=[], kwargs={}):
        while True:
            callback(await self.queue.get(), *args, **kwargs)


class topic:
    def __init__(self, name: str):
        self.name = name
        self.subscribers = []

    async def publish(self, message):
        """publish a message to this topic"""
        for subscriber in self.subscribers:
            await subscriber.queue.put(message)

    def subscribe(self) -> subscription:
        """return a subscription"""
        sub = subscription()
        self.subscribers.append(sub)
        return sub


# Tasks
async def ble_scanner(topic):
    """scan for ble advertisements and unpack the data"""

    structlog.contextvars.bind_contextvars(task=asyncio.current_task().get_name())

    stop = asyncio.Event()
    args = {
        "filters": {
            #'UUIDs': ['0000181a-0000-1000-8000-00805f9b34fb'],
            "Pattern": "A4:C1:38",
        }
    }

    logger.info("Starting BLE scan")
    async with BleakScanner(detection_callback=publish_data(topic), bluez=args) as _:
        await stop.wait()


async def mqtt_publisher(hostname: str, topic: topic):
    """connect to a mqtt server and publish received messages"""

    structlog.contextvars.bind_contextvars(
        hostname=hostname, task=asyncio.current_task().get_name()
    )
    subscription = topic.subscribe()

    logger.info("Connecting to MQTT")
    async with Client(hostname) as client:
        while True:
            message = await subscription.get()
            logger.debug("Publishing message")
            base_topic = f"LYWSD03MMC/{os.uname().nodename}/{message.local_name}"
            asyncio.gather(
                client.publish(f"{base_topic}/events", payload=message.json()),
                client.publish(
                    f"{base_topic}/temperatureC", payload=message.data.temperatureC
                ),
                client.publish(f"{base_topic}/humidity", payload=message.data.humidity),
                client.publish(
                    f"{base_topic}/batterymV", payload=message.data.batterymV
                ),
                client.publish(
                    f"{base_topic}/batteryLevel", payload=message.data.batteryLevel
                ),
            )


def publish_data(topic):
    """return a callback function that unpacks ble advertisement data and publish"""

    async def callback(device, advertisement_data):
        try:
            data = AdvertisementData(advertisement_data)
            logger.debug("Got data", data=str(data))
        except UnknownFormatException:
            logger.error("Unknown format")
            return

        logger.debug("Publish to topic", topic=topic.name)
        await topic.publish(data)

    return callback


class UnknownFormatException(Exception):
    pass


class AdvertisementData:
    def __init__(self, advertisement_data):
        service_data = advertisement_data.service_data.get(
            "0000181a-0000-1000-8000-00805f9b34fb", None
        )

        if service_data and len(service_data) == 15:
            data_format = PvvxFormat
        elif service_data and len(service_data) == 13:
            data_format = Atc1441Format
        else:
            raise UnknownFormatException()

        self.local_name = advertisement_data.local_name
        self.data = data_format(service_data)

    def __str__(self):
        return "{} {}".format(self.local_name, self.data)

    def json(self):
        return json.dumps(
            {
                "local_name": self.local_name,
                "payload_format": self.data.format,
                "address": self.data.address.upper(),
                "temperatureC": self.data.temperatureC,
                "humidity": self.data.humidity,
                "batterymV": self.data.batterymV,
                "batteryLevel": self.data.batteryLevel,
            }
        )


class PayloadFormat:
    def __str__(self):
        return f"Format {self.format}, {self.address.upper()}: {self.temperatureC}c, {self.humidity}% humidity, {self.batterymV}mV, {self.batteryLevel}% battery"


class PvvxFormat(PayloadFormat):
    def __init__(self, payload):
        self.payload = payload
        self.format = "pvvx"

    @property
    def address(self):
        return self.payload[0:6][::-1].hex()

    @property
    def temperatureC(self):
        return struct.unpack("h", self.payload[6:8])[0] * 0.01

    @property
    def humidity(self):
        return struct.unpack("H", self.payload[8:10])[0] * 0.01

    @property
    def batterymV(self):
        return struct.unpack("H", self.payload[10:12])[0]

    @property
    def batteryLevel(self):
        return struct.unpack("B", self.payload[12:13])[0]

    @property
    def counter(self):
        return struct.unpack("B", self.payload[13:14])[0]


class Atc1441Format(PayloadFormat):
    def __init__(self, payload):
        self.payload = payload
        self.format = "atc1441"

    @property
    def address(self):
        return self.payload[0:6].hex()

    @property
    def temperatureC(self):
        return struct.unpack(">h", self.payload[6:8])[0] / 10

    @property
    def humidity(self):
        return struct.unpack("B", self.payload[8:9])[0]

    @property
    def batterymV(self):
        return struct.unpack(">H", self.payload[10:12])[0]

    @property
    def batteryLevel(self):
        return struct.unpack("B", self.payload[9:10])[0]

    @property
    def counter(self):
        return struct.unpack("B", self.payload[12:13])[0]


async def main():
    mqtt_servers = sys.argv[1:]
    if len(mqtt_servers) < 1:
        logger.error("No servers given")

    measurements = topic("measurements")

    tasks = [
        ble_scanner(measurements),
    ]

    for mqtt_server in mqtt_servers:
        tasks.append(mqtt_publisher(mqtt_server, measurements))

    await asyncio.gather(*tasks)


def start():
    """script entrypoint"""
    asyncio.run(main())


if __name__ == "__main__":
    start()
