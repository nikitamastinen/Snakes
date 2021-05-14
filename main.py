import logging
from random import randint
from typing import List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi_utils.tasks import repeat_every
from starlette.templating import Jinja2Templates

app = FastAPI()
templates = Jinja2Templates(directory="templates/")

field = [[set() for _ in range(61)] for _ in range(61)]
usernames = {}
food = set()


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[(WebSocket, int)] = []

    async def connect(self, websocket: WebSocket, client_id: int):
        await websocket.accept()
        self.active_connections.append((websocket, client_id))

    async def send_food(self):
        x = randint(1, 60)
        y = randint(1, 60)
        await self.send_food_item(x, y)

    async def send_food_item(self, x, y):
        if (x, y) not in food:
            food.add((x, y))
            await self.broadcast(f'food {x} {y}')

    async def disconnect(self, websocket: WebSocket, client_id: int):
        if (websocket, client_id) in self.active_connections:
            self.active_connections.remove((websocket, client_id))
        usernames.pop(client_id)
        for i in range(len(field)):
            for j in range(len(field[i])):
                if client_id in field[i][j]:
                    field[i][j].remove(client_id)
        for connection, _ in self.active_connections:
            try:
                await connection.send_text(f'delete {client_id}')
            except Exception:
                pass

    async def broadcast(self, message: str):
        for connection, _ in self.active_connections:
            try:
                await connection.send_text(message)
            except RuntimeError:
                pass

    async def send_history(self, websocket: WebSocket):
        for i in range(len(field)):
            for j in range(len(field[i])):
                for client_id in field[i][j]:
                    try:
                        await websocket.send_text(f'add {i * 10} {j * 10} {client_id} {usernames[client_id]}')
                    except RuntimeError:
                        pass
        for (x, y) in food:
            try:
                await websocket.send_text(f'food {x} {y}')
            except:
                pass


manager = ConnectionManager()


@app.get("/")
async def get(request: Request):
    # TODO address = 'hungry-snakes.herokuapp.com'
    address = '93.175.2.219'
    return templates.TemplateResponse('game.html', context={'request': request, 'address': address})


@app.websocket("/ws/{client_id}/{username}")
@app.websocket("/ws/{client_id}/")
async def websocket_endpoint(websocket: WebSocket, client_id: int, username: str = ''):
    await manager.connect(websocket, client_id)
    usernames[client_id] = username
    try:
        await manager.send_history(websocket)
        fl = False
        while True:
            data = await websocket.receive_text()
            print(data)
            if not fl:
                await manager.send_history(websocket)
                fl = True
            query = [i for i in data.split(' ')]
            if query[0] == 'pop' and int(query[3]) in field[int(query[1])][int(query[2])]:
                field[int(query[1])][int(query[2])].remove(int(query[3]))
            elif query[0] == 'add':
                if len(field[int(query[1])][int(query[2])]) != 0:
                    if len(field[int(query[1])][int(query[2])]) != 0:
                        print("deleted: " + str(client_id))
                        current_food = []
                        for i in range(len(field)):
                            for j in range(len(field[i])):
                                print("TRY: " + str(client_id) + ' ' + str(field[i][j]))
                                if client_id in field[i][j]:
                                    field[i][j].remove(int(query[3]))
                                    print("kkk")
                                    current_food.append((i, j))
                        for (connection, ind) in manager.active_connections:
                            if ind == int(query[3]):
                                manager.active_connections.remove((connection, ind))
                                break
                        for x, y in current_food:
                            await manager.send_food_item(x, y)
                else:
                    field[int(query[1])][int(query[2])].add(int(query[3]))
            elif query[0] == 'delete':
                for (connection, ind) in manager.active_connections:
                    if ind == int(query[1]):
                        manager.active_connections.remove((connection, ind))
                        break
                for i in field:
                    for j in i:
                        if int(query[1]) in j:
                            j.remove(int(query[1]))
                            continue
            elif query[0] == 'popadd':
                if len(field[int(query[1])][int(query[2])]) != 0:
                    print("deleted: " + str(client_id))

                    current_food = []
                    for i in range(len(field)):
                        for j in range(len(field[i])):
                            print("TRY: " + str(client_id) + ' ' + str(field[i][j]))
                            if client_id in field[i][j]:
                                field[i][j].remove(int(query[3]))
                                print("kkk")
                                current_food.append((i, j))
                        print()
                    for (connection, ind) in manager.active_connections:
                        if ind == int(query[3]):
                            manager.active_connections.remove((connection, ind))
                            break
                    for x, y in current_food:
                        await manager.send_food_item(x, y)
                    data = f'delete {int(query[3])}'
                else:
                    field[int(query[1])][int(query[2])].add(int(query[3]))
                    if int(query[3]) in field[int(query[4])][int(query[5])]:
                        field[int(query[4])][int(query[5])].remove(int(query[3]))
            elif query[0] == 'popfood':
                if (int(query[1]), int(query[2])) in food:
                    food.remove((int(query[1]), int(query[2])))
            await manager.broadcast(f"{data}")
    except WebSocketDisconnect:
        await manager.disconnect(websocket, client_id)
    except IndexError:
        await manager.disconnect(websocket, client_id)


@app.on_event("startup")
@repeat_every(seconds=10, logger=logging.getLogger(__name__), wait_first=True)
async def periodic():
    await manager.send_food()
    for i in field:
        for j in i:
            bad = []
            for k in j:
                if k not in [i for _, i in manager.active_connections]:
                    bad.append(k)
            for b in bad:
                j.remove(b)
                try:
                    await manager.broadcast(f'delete {b}')
                except Exception:
                    pass
