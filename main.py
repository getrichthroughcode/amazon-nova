import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(name)s | %(levelname)s | %(message)s")

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

load_dotenv()

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

STATIC_DIR = Path(__file__).parent / "static"


@app.get("/")
async def index():
    return HTMLResponse((STATIC_DIR / "index.html").read_text())


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            if message.get("type") != "prompt":
                continue

            prompt = message.get("prompt", "").strip()
            model = message.get("model", "groq/llama-3.3-70b-versatile").strip()
            if not prompt:
                continue

            from agent import stream_diagram

            await websocket.send_text(json.dumps({"type": "start"}))

            try:
                async for element in stream_diagram(prompt, model):
                    await websocket.send_text(
                        json.dumps({"type": "element", "data": element})
                    )
                await websocket.send_text(json.dumps({"type": "done"}))
            except Exception as e:
                await websocket.send_text(
                    json.dumps({"type": "error", "message": str(e)})
                )

    except WebSocketDisconnect:
        pass


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
