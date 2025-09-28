import asyncio
import websockets

async def client_program(client_id):
    uri = f"ws://<server_ip>:8000/ws/{client_id}"
    async with websockets.connect(uri) as websocket:
        while True:
            msg = input("You: ")
            await websocket.send(msg)
            response = await websocket.recv()
            print(response)

if __name__ == "__main__":
    client_id = input("Enter client ID: ")
    asyncio.run(client_program(client_id))
