from fastapi import FastAPI, WebSocket
import asyncio
import json
import random

app = FastAPI()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    time = 0
    while True:
        time += 1
        data = json.dumps({"time": list(range(time)), "value": [random.uniform(20, 30) for _ in range(time)]})
        await websocket.send_text(data)
        await asyncio.sleep(1)  # Отправка данных каждую секунду

