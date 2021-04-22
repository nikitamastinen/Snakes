import logging
from typing import List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi_utils.tasks import repeat_every
from starlette.templating import Jinja2Templates

app = FastAPI()
templates = Jinja2Templates(directory="templates/")


class ConnectionManager:
    def __init__(self):
        self.HISTORY = []
        self.active_connections: List[(WebSocket, int)] = []

    async def connect(self, websocket: WebSocket, client_id: int):
        await websocket.accept()
        self.active_connections.append((websocket, client_id))

    def disconnect(self, websocket: WebSocket, client_id: int):
        self.active_connections.remove((websocket, client_id))

    async def broadcast(self, message: str):
        for connection, _ in self.active_connections:
            await connection.send_text(message)

    async def send_history(self, websocket: WebSocket):
        for i in range(len(field)):
            for j in range(len(field[i])):
                for id in field[i][j]:
                    await websocket.send_text(f'add {i * 10} {j * 10} {id}')


    # async def submit_coords(self, coords):
    #     for connection in self.active_connections:
    #         await connection.send_text(coords[0] + ' ' + coords[1])


manager = ConnectionManager()


@app.get("/")
async def get(request: Request):
    return templates.TemplateResponse('init_page.html', context={'request': request})


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    await manager.connect(websocket, client_id)
    print('success')
    try:
        await manager.send_history(websocket)
        while True:
            data = await websocket.receive_text()
            query = [i for i in data.split(' ')]
            if query[0] == 'pop':
                field[int(query[1]) // 10][int(query[2]) // 10].remove(int(query[3]))
            if query[0] == 'add':
                field[int(query[1]) // 10][int(query[2]) // 10].add(int(query[3]))
            await manager.broadcast(f"{data}")
            print(field)
    except WebSocketDisconnect:
        manager.disconnect(websocket, client_id)
        pass
    except Exception:
        pass
        #await manager.broadcast(f"Client #{client_id} left the chat")


counter = 0

field = [[set()] * 40 for _ in range(40)]


# @app.on_event("startup")
# @repeat_every(seconds=10, logger=logging.getLogger(__name__), wait_first=True)
# def periodic():
#     global counter
#     print('counter is', counter)
#     field[0][min(counter, 40)] += 1
#     #manager.submit_coords((0, min(counter, 40)))
#     counter += 1
