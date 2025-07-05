import socket
import time
import asyncio
import argparse
import random
from bleak import BleakScanner
import json

async def run_client(server_host: str, server_port: int, substation: str):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((server_host, server_port))
        print(f"[CLIENT] Connected to {server_host}:{server_port}")
        counter = 0
        try:
            while True:
                counter += 1
                devices = await BleakScanner.discover(timeout=5)
                device_list = []
                for d in devices:
                    v:float = random.uniform(6, 8)
                    if d.details[0] is not None:
                        device_list.append({
                            'device_name': str(d.name),
                            'device_address': str(d.address),
                            'temperature': v * random.uniform(3.5, 4.9),
                            'voltage': v * random.uniform(2.5, 2.9),
                            'current': v * random.uniform(1.5, 2.9),
                            'charge': v * random.uniform(0.5, 1.5),
                            'substation': substation
                            })
                data = json.dumps(device_list).encode('utf-8')
                sock.sendall(len(data).to_bytes(4, 'big') + data)
                print(f"[CLIENT] Sent ping {counter}")

        except KeyboardInterrupt:
            print("\n[CLIENT] Stopped by user")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simple TCP client with periodic messages")
    parser.add_argument("host", help="Server host or IP")
    parser.add_argument("port", type=int, help="Server port")
    parser.add_argument("substation", type=str, help="Substation name")
    args = parser.parse_args()
    while True:
        try:
            asyncio.run(run_client(args.host, args.port, args.substation))
        except:
            print("attempt to connect")