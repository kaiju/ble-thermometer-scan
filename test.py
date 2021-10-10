import struct

payload = "1a18a4c13833a3ac00e130540b9412"

print(payload[16:20])

print(struct.unpack('>h', bytes.fromhex(payload[16:20]))[0] / 10)


