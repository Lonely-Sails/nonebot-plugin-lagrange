import asyncio
import struct

class MinecraftProtocol:
    reader: asyncio.StreamReader = None
    writer: asyncio.StreamWriter = None

    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port

    async def connect(self):
        self.reader, self.writer = await asyncio.open_connection(self.host, self.port)

    async def send_packet(self, packet_id: bytes, data: bytes):
        packet_length = len(data) + len(packet_id)  # Include packet_id length
        packet = struct.pack('>I', packet_length) + packet_id + data
        self.writer.write(packet)
        await self.writer.drain()

    async def receive_packet(self) -> tuple[int, bytes]:
        packet_length = await self.read_varint()
        packet_id = await self.read_varint()
        data = await self.reader.read(packet_length - len(packet_id.to_bytes((packet_id.bit_length() + 7) // 8, 'big')))
        return packet_id, data

    async def read_varint(self) -> int:
        num_read = 0
        result = 0
        while True:
            byte = await self.reader.read(1)
            value = byte[0]
            result |= (value & 0x7F) << (7 * num_read)
            num_read += 1
            if num_read > 5:
                raise ValueError("VarInt is too big")
            if (value & 0x80) == 0:
                break
        return result

    async def handshake(self, next_state: int):
        packet_id = 0x00
        data = self.write_varint(767)  # Protocol version for Minecraft 1.21
        data += self.write_varint(len(self.host)) + self.host.encode('utf-8')
        data += struct.pack('>H', self.port)
        data += self.write_varint(next_state)
        await self.send_packet(packet_id.to_bytes(1, 'big'), data)

    def write_varint(self, value: int) -> bytes:
        buff = b''
        while True:
            temp = value & 0x7F
            value >>= 7
            if value != 0:
                temp |= 0x80
            buff += struct.pack('B', temp)
            if value == 0:
                break
        return buff

    async def login(self, username: str):
        packet_id = 0x00
        data = self.write_varint(len(username)) + username.encode('utf-8')
        await self.send_packet(packet_id.to_bytes(1, 'big'), data)

    async def close(self):
        self.writer.close()
        await self.writer.wait_closed()

async def main():
    mc_protocol = MinecraftProtocol('play.axiaoxiao.xyz', 25565)
    await mc_protocol.connect()
    await mc_protocol.handshake(2)  # 2 for login
    await mc_protocol.login('qwq')

    # 接收服务器响应
    packet_id, data = await mc_protocol.receive_packet()
    print(f"Received packet ID: {packet_id}")
    print(f"Received data: {data[2:].decode('utf-8')}")

    await mc_protocol.close()

if __name__ == "__main__":
    asyncio.run(main())
