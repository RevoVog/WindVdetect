from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import uvicorn

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Store clients
clients = {}

# ======================
# Dashboard Routes
# ======================
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "clients": list(clients.keys())})

@app.get("/client/{client_id}", response_class=HTMLResponse)
async def client_page(request: Request, client_id: str):
    return templates.TemplateResponse("client.html", {"request": request, "client_id": client_id})

# ======================
# WebSocket for Clients
# ======================
@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await websocket.accept()
    clients[client_id] = websocket
    print(f"[CONNECTED] {client_id}")
    try:
        while True:
            data = await websocket.receive_text()
            print(f"[FROM {client_id}] {data}")
            # Echo back to sender (or broadcast)
            await websocket.send_text(f"Server: Received '{data}'")
    except WebSocketDisconnect:
        del clients[client_id]
        print(f"[DISCONNECTED] {client_id}")

# ======================
# Send message to a client (from web dashboard)
# ======================
@app.websocket("/ws_server/{client_id}")
async def server_to_client(websocket: WebSocket, client_id: str):
    await websocket.accept()
    try:
        while True:
            msg = await websocket.receive_text()
            if client_id in clients:
                await clients[client_id].send_text(f"Server says: {msg}")
    except WebSocketDisconnect:
        pass

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
