import asyncio
import struct
import sys
from bleak import BleakScanner

def detection_callback(device, advertisement_data):
    if device.address.startswith("A4:C1:38"):
        print("{} ({})".format(device.address, advertisement_data.local_name))
        for sd in advertisement_data.service_data:
            payload = advertisement_data.service_data[sd]

            if sd.startswith("0000181a") and len(payload) == 15: # custom format?
                temp_c = struct.unpack('h', payload[6:8])[0] * 0.01
                humidity = struct.unpack('H', payload[8:10])[0] * 0.01
                battery_mv = struct.unpack('H', payload[10:12])[0]
                battery_level = struct.unpack('B', payload[12:13])[0]
                counter = struct.unpack('B', payload[13:14])[0]
                flags = payload[14:15]
                print("15 byte 0x181a payload: {} {} {} {} {} {}".format(temp_c, humidity, battery_mv, battery_level,
                    counter, flags))
            elif sd.startswith("0000181a") and len(payload) == 13: # atc1441??? 
                # first 5 bytes is address in correct order
                temp_c = struct.unpack('>h', payload[6:8])[0] / 10
                humidity = struct.unpack('B', payload[8:9])[0]
                battery_level = struct.unpack('B', payload[9:10])[0]
                battery_mv = struct.unpack('>H', payload[10:12])[0]
                counter = struct.unpack('B', payload[12:13])[0]
                print("13 byte 0x181a payload: {} {} {} {} {}".format(temp_c, humidity, battery_level,
                    battery_mv, counter))
            if sd.startswith("0000fe95"): # xaomi ble beacons?
                # TODO -- figure out how to decode these or if they have anything worthwhile
                pass

async def main():

    scanner = BleakScanner()
    scanner.register_detection_callback(detection_callback)
    await scanner.start()
    while True:
        await asyncio.sleep(1.0)

asyncio.run(main())

