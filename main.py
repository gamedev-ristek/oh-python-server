from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import json
import asyncio
from game_executor import GameExecutor
from typing import Dict
import uuid

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
    
    async def connect(self, websocket: WebSocket) -> str:
        await websocket.accept()
        session_id = str(uuid.uuid4())
        self.active_connections[session_id] = websocket
        self.game_sessions[session_id] = GameExecutor()

        print(f"new session created: {session_id}")
        return session_id
    
    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
        if session_id in self.game_sessions:
            del self.game_sessions[session_id]
    
    async def send_message(self, session_id: str, message: dict):
        if session_id in self.active_connections:
            websocket = self.active_connections[session_id]
            await websocket.send_text(json.dumps(message))

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    session_id = await manager.connect(websocket)
    
    try:
        await manager.send_message(session_id, {
            "type": "connected",
            "session_id": session_id
        })
        
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            print(f"received message: {message}")
            
            if message["type"] == "execute_code":
                print(f"executing code for session {session_id}")
                executor = manager.game_sessions[session_id]
                result = await executor.execute_player_code(message["code"])
                print(f"execution result: {result}")
                
                response = {
                    "type": "execution_result",
                    "data": result
                }
                await manager.send_message(session_id, response)
                
    except WebSocketDisconnect:
        print(f"session {session_id} disconnected")
        manager.disconnect(session_id)

@app.get("/")
async def root():
    return {"message": "backend is running, nunggu instance to connect."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)