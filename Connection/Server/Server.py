# server.py
# uvicorn Server:app --host 0.0.0.0 --port 8000 --reload

import asyncio
import json
from typing import List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# serve a static folder if you want CSS or JS files separate
app.mount("/static", StaticFiles(directory="static"), name="static")

class ConnectionManager:
    def __init__(self):
        self.dashboards: List[WebSocket] = []   # browser dashboards (receive only)
        self.clients: List[WebSocket] = []      # system-reporting clients (senders)

    async def connect(self, websocket: WebSocket, role: str):
        await websocket.accept()
        if role == "dashboard":
            self.dashboards.append(websocket)
            print("Dashboard connected:", websocket.client)
        else:
            self.clients.append(websocket)
            print("Client reporter connected:", websocket.client)

    def disconnect(self, websocket: WebSocket, role: str):
        if role == "dashboard":
            try:
                self.dashboards.remove(websocket)
            except ValueError:
                pass
            print("Dashboard disconnected:", websocket.client)
        else:
            try:
                self.clients.remove(websocket)
            except ValueError:
                pass
            print("Client reporter disconnected:", websocket.client)

    async def broadcast_to_dashboards(self, message: str):
        # broadcast to all dashboards; remove stale connections
        to_remove = []
        for ws in self.dashboards:
            try:
                await ws.send_text(message)
            except Exception:
                to_remove.append(ws)
        for ws in to_remove:
            try:
                self.dashboards.remove(ws)
            except ValueError:
                pass

manager = ConnectionManager()

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/cpu", response_class=HTMLResponse)
async def cpu_page(request: Request):
    return templates.TemplateResponse("cpu.html", {"request": request})

@app.get("/mem", response_class=HTMLResponse)
async def mem_page(request: Request):
    return templates.TemplateResponse("mem.html", {"request": request})

@app.get("/net", response_class=HTMLResponse)
async def net_page(request: Request):
    return templates.TemplateResponse("net.html", {"request": request})
@app.get("/cup", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("cpu.html", {"request": request})

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint used by both:
      - Client reporters (role=client) - they send JSON snapshots
      - Dashboards (role=dashboard) - they receive snapshots
    Role is provided as query param: /ws?role=client  or /ws?role=dashboard
    """
    role = websocket.query_params.get("role", "client")
    await manager.connect(websocket, role)
    try:
        if role == "client":
            # receive messages from client and broadcast to dashboards
            while True:
                data = await websocket.receive_text()
                # Optionally validate/transform here
                # broadcast to dashboards
                await manager.broadcast_to_dashboards(data)
        else:  # dashboard: keep connection open, maybe accept commands later
            while True:
                # dashboards might send ping/commands, handle if needed
                msg = await websocket.receive_text()
                # For now, ignore or print
                print("Received from dashboard:", msg)
    except WebSocketDisconnect:
        manager.disconnect(websocket, role)
    except Exception as e:
        # catch other exceptions and disconnect
        print("WebSocket error:", e)
        manager.disconnect(websocket, role)


