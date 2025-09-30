

import asyncio
import datetime
from flask import json
import websockets


SERVER_WS = "ws://localhost:8000/ws?role=client"


def collect_system_snapshot():
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try :
        snapshot = {
                "Timestamp": now
        }
        return snapshot
    except Exception:
        return {"Timestamp": now, "error": "failed collecting snapshot"}


async def send():
    async with websockets.connect(SERVER_WS, max_size=2**25) as ws:
        print("Connected to server", SERVER_WS)
        try:
            while True:
                snap = collect_system_snapshot()
                payload = json.dumps(snap, default=str)
                await ws.send(payload)
                await asyncio.sleep(1)
        except Exception as e:
            print("Client send loop error:", e)
            raise


if __name__ == "__main__":
    print("System reporter client starting. Server:", SERVER_WS)
    try:
        asyncio.run(send())
    except KeyboardInterrupt:
        print("Stopped by user")
    except Exception as e:
        print("Client error:", e)