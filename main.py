import socket
import eel
import asyncio
import back.host
from threading import Thread

eel.init("front")

def run_async_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(back.host.start_data_stream())

if __name__ == '__main__':
    thread = Thread(target=run_async_loop, daemon=True)
    thread.start()
    print(socket.gethostbyname(socket.gethostname()))
    eel.start("index.html", size=(1300, 720), mode="chrome", host=socket.gethostbyname(socket.gethostname()), port=8080, suppress_error=True, block=True, )