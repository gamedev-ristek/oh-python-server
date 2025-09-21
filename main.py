from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import json
import asyncio
from game_executor import GameExecutor
from typing import Dict
import uuid
from functools import partial
import concurrent.futures

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.game_sessions: Dict[str, GameExecutor] = {}
        self.connection_lock = asyncio.Lock()
        self.thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=8)
    
    async def connect(self, websocket: WebSocket) -> str:
        await websocket.accept()
        async with self.connection_lock:
            session_id = str(uuid.uuid4())
            self.active_connections[session_id] = websocket
            self.game_sessions[session_id] = GameExecutor()
        return session_id
    
    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
        if session_id in self.game_sessions:
            del self.game_sessions[session_id]
    
    async def send_message(self, websocket: WebSocket, message: dict):
        await websocket.send_text(json.dumps(message))
    
    async def execute_code(self, session_id: str, code: str) -> dict:
        if session_id not in self.game_sessions:
            return {"success": False, "error": "session not found"}
        
        loop = asyncio.get_event_loop()
        try:
            result = await loop.run_in_executor(
                self.thread_pool,
                partial(self.game_sessions[session_id].execute_player_code, code)
            )
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    session_id = await manager.connect(websocket)
    
    try:
        await manager.send_message(websocket, {
            "type": "connected",
            "session_id": session_id
        })
        
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message["type"] == "execute_code":
                result = await manager.execute_code(session_id, message["code"])
                response = {
                    "type": "execution_result",
                    "data": result
                }
                await manager.send_message(websocket, response)
                
    except WebSocketDisconnect:
        manager.disconnect(session_id)
    except Exception as e:
        print(f"Error in websocket: {e}")
        manager.disconnect(session_id)

@app.get("/")
async def root():
    return {"message": "server is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000
    )
