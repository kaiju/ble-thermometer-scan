import asyncio
import struct
import sys
import json
import os
from bleak import BleakScanner
from asyncio_mqtt import Client, ProtocolVersion

class MQTTPayload():
    def __init__(self, advertisement_data, payload):
        self.advertisement_data = advertisement_data
        self.payload = payload

    def __str__(self):
        return "{} {}".format(self.advertisement_data, self.payload)

    # todo, add hostname as 'listener'
    def json(self):
        return json.dumps({
            "local_name": self.advertisement_data.local_name,
            "payload_format": self.payload.format,
            "address": self.payload.address.upper(),
            "temperatureC": self.payload.temperatureC,
            "humidity": self.payload.humidity,
            "batterymV": self.payload.batterymV,
            "batteryLevel": self.payload.batteryLevel
            })

class PayloadFormat():
    def __str__(self):
        return f'Format {self.format}, {self.address.upper()}: {self.temperatureC}c, {self.humidity}% humidity, {self.batterymV}mV, {self.batteryLevel}% battery'

class PvvxFormat(PayloadFormat):
    def __init__(self, payload):
        self.payload = payload
        self.format = 'pvvx'

    @property
    def address(self):
        return self.payload[0:6][::-1].hex()

    @property
    def temperatureC(self):
        return struct.unpack('h', self.payload[6:8])[0] * 0.01

    @property
    def humidity(self):
        return struct.unpack('H', self.payload[8:10])[0] * 0.01

    @property
    def batterymV(self):
        return struct.unpack('H', self.payload[10:12])[0]

    @property
    def batteryLevel(self):
        return struct.unpack('B', self.payload[12:13])[0]

    @property
    def counter(self):
        return struct.unpack('B', self.payload[13:14])[0]


class Atc1441Format(PayloadFormat):
    def __init__(self, payload):
        self.payload = payload
        self.format = 'atc1441'

    @property
    def address(self):
        return self.payload[0:6].hex()

    @property
    def temperatureC(self):
        return struct.unpack('>h', self.payload[6:8])[0] / 10

    @property
    def humidity(self):
        return struct.unpack('B', self.payload[8:9])[0]

    @property
    def batterymV(self):
        return struct.unpack('>H', self.payload[10:12])[0]

    @property
    def batteryLevel(self):
        return struct.unpack('B', self.payload[9:10])[0]

    @property
    def counter(self):
        return struct.unpack('B', payload[12:13])[0]


def device_detection_callback(device, advertisement_data, messages):

    if device.address.startswith("A4:C1:38"):

        # TODO -- see about decoding xaomi (0xfe95) payloads and if they have anything interesting
        payload = advertisement_data.service_data.get('0000181a-0000-1000-8000-00805f9b34fb', None)

        if payload and len(payload) == 15: # pvvx format
            payload_format = PvvxFormat 
        elif payload and len(payload) == 13: # atc1441 format
            payload_format = Atc1441Format
        else:
           return 

        async def publish():
            await messages.put(MQTTPayload(advertisement_data, payload_format(payload)))

        asyncio.create_task(publish())

async def main():

    messages = asyncio.Queue()

    def discovery_wrapper(device, advertisement_data):
      device_detection_callback(device, advertisement_data, messages)

    mqtt_client = Client("mqtt.mast.haus", protocol=ProtocolVersion.V31)
    scanner = BleakScanner()
    scanner.register_detection_callback(discovery_wrapper)
    await scanner.start()

    # TODO make mqtt configurable
    async with Client("mqtt.mast.haus") as client:
        while True:
            m = await messages.get()
            base_topic = f'LYWSD03MMC/{os.uname().nodename}/{m.advertisement_data.local_name}'
            await client.publish(f'{base_topic}/events', payload=m.json())
            await client.publish(f'{base_topic}/temperatureC',
                    payload=m.payload.temperatureC)
            await client.publish(f'{base_topic}/humidity', payload=m.payload.humidity)
            await client.publish(f'{base_topic}/batterymV', payload=m.payload.batterymV)
            await client.publish(f'{base_topic}/batteryLevel', payload=m.payload.batteryLevel)
            

asyncio.run(main())

