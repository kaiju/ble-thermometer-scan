import struct
from bluepy.btle import Scanner, DefaultDelegate, BTLEDisconnectError 

class ScannerDelegate(DefaultDelegate):
    def __init__(self):
        DefaultDelegate.__init__(self)

    def handleDiscovery(self, scanEntry, isNewDev, isNewData):
        if scanEntry.getValueText(22) is not None:
          payload = scanEntry.getValueText(22)
          bytes_length = len(bytes.fromhex(payload))
          uid = bytes.fromhex(payload[0:4])[::-1]

          if uid == b'\x18\x1a' and bytes_length == 17:
            temp_c = round(struct.unpack('h', bytes.fromhex(payload[16:20]))[0] * 0.01, 1)
            humidity = round(struct.unpack('H', bytes.fromhex(payload[20:24]))[0] * 0.01, 1)
            battery_mv = struct.unpack('H', bytes.fromhex(payload[24:28]))[0]
            battery_level = struct.unpack('B', bytes.fromhex(payload[28:30]))[0]
            counter = struct.unpack('B', bytes.fromhex(payload[30:32]))[0]
            flags = bytes.fromhex(payload[32:34])

            print("{} ({}) {} #{} Temp: {}c, Humidity: {}%, battery mV: {}, Battery: {}%".format(
                    scanEntry.getValueText(9),
                    scanEntry.addr,
                    scanEntry.rssi,
                    counter,
                    temp_c,
                    humidity,
                    battery_mv,
                    battery_level,
                    ))

          if uid == b'\x18\x1a' and bytes_length == 15: # atc1411 style
            temp_c = round(struct.unpack('>h', bytes.fromhex(payload[16:20]))[0] / 10, 1)
            humidity = round(struct.unpack('B', bytes.fromhex(payload[20:22]))[0], 1)
            battery_level = struct.unpack('B', bytes.fromhex(payload[22:24]))[0] 
            battery_mv = struct.unpack('>H', bytes.fromhex(payload[24:28]))[0]
            counter = struct.unpack('B', bytes.fromhex(payload[28:30]))[0]

            print("{} ({}) {} #{} Temp: {}c, Humidity: {}%, battery mV: {}, Battery: {}%".format(
                    scanEntry.getValueText(9),
                    scanEntry.addr,
                    scanEntry.rssi,
                    counter,
                    temp_c,
                    humidity,
                    battery_mv,
                    battery_level,
                    ))

scanner = Scanner().withDelegate(ScannerDelegate())
print("Scanning...")

while True:
    try:
        scanner.scan(30)
    except BTLEDisconnectError:
        continue

