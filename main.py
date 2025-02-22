from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import json
import random
import time
import asyncio
from datetime import datetime
import uuid
from typing import Dict, List
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    asyncio.create_task(generate_data_periodically())
    yield
    # Shutdown
    pass

app = FastAPI(lifespan=lifespan)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static 파일 서빙
app.mount("/static", StaticFiles(directory="static"), name="static")

class StompWebSocket:
    def __init__(self, websocket: WebSocket):
        self.websocket = websocket
        self.subscriptions: Dict[str, str] = {}
        
    async def send_message(self, destination: str, message: str):
        try:
            stomp_frame = {
                "command": "MESSAGE",
                "headers": {
                    "destination": destination,
                    "content-type": "application/json",
                    "message-id": str(uuid.uuid4()),
                    "subscription": "sub-" + destination.split('/')[-1]
                },
                "body": message
            }
            await self.websocket.send_json(stomp_frame)
        except Exception as e:
            print(f"Error sending message: {e}")

# 클라이언트 관리
stomp_clients: List[StompWebSocket] = []

def generate_random_data():
    """랜덤 모니터링 데이터 생성"""
    transaction_id = f"txn_{uuid.uuid4().hex[:12]}"
    current_time = time.time()
    
    # Request 데이터
    request_data = {
        "transaction_id": transaction_id,
        "type": "request",
        "timestamp": current_time,
        "data": {
            "method": random.choice(["GET", "POST", "PUT", "DELETE"]),
            "url": f"http://localhost:8080/{random.choice(['api', 'users', 'products', 'orders'])}",
            "headers": {"user-agent": "curl/7.68.0"},
            "body": "",
            "client_ip": f"192.168.1.{random.randint(1, 255)}",
            "start_time": current_time
        }
    }
    
    # Process 시작 데이터
    process_start_data = {
        "transaction_id": transaction_id,
        "type": "process",
        "timestamp": current_time + 0.01,
        "data": {
            "class_name": "ApiHandler",
            "function_name": random.choice(["get_user", "create_order", "update_product"]),
            "file_name": "handlers.py",
            "line_number": random.randint(1, 100),
            "parameters": {},
            "start_time": current_time + 0.01,
            "status": "started"
        }
    }
    
    # Process 완료 데이터
    process_end_data = {
        "transaction_id": transaction_id,
        "type": "process",
        "timestamp": current_time + 0.02,
        "data": {
            **process_start_data["data"],
            "duration": 0.01,
            "return_value": json.dumps({"status": "success"}),
            "status": "completed"
        }
    }
    
    # Response 데이터
    response_data = {
        "transaction_id": transaction_id,
        "type": "response",
        "timestamp": current_time + 0.03,
        "data": {
            "status_code": random.choice([200, 201, 400, 401, 403, 404, 500]),
            "headers": {"content-type": "application/json"},
            "body": json.dumps({"status": "success"}),
            "duration": 0.03,
            "error": None
        }
    }
    
    # Transaction 데이터
    transaction_data = {
        "transaction_id": transaction_id,
        "type": "transaction",
        "timestamp": current_time + 0.04,
        "data": {
            "duration": 0.04,
            "status": "success",
            "error": None
        }
    }
    
    return [request_data, process_start_data, process_end_data, response_data, transaction_data]

async def handle_stomp_message(client: StompWebSocket, message: dict):
    try:
        command = message.get("command")
        headers = message.get("headers", {})
        
        if command == "CONNECT":
            await client.websocket.send_json({
                "command": "CONNECTED",
                "headers": {"version": "1.2"}
            })
        
        elif command == "SUBSCRIBE":
            destination = headers.get("destination")
            subscription_id = headers.get("id")
            if destination and subscription_id:
                client.subscriptions[destination] = subscription_id
                print(f"Client subscribed to {destination} with id {subscription_id}")
        
        elif command == "SEND":
            destination = headers.get("destination")
            if destination:
                # 수신된 메시지를 구독 중인 모든 클라이언트에게 전달
                for other_client in stomp_clients:
                    if destination in other_client.subscriptions:
                        await other_client.send_message(destination, message.get("body", ""))
    
    except Exception as e:
        print(f"Error handling STOMP message: {e}")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    client = StompWebSocket(websocket)
    stomp_clients.append(client)
    print("New client connected")
    
    try:
        while True:
            message = await websocket.receive_json()
            await handle_stomp_message(client, message)
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        if client in stomp_clients:
            stomp_clients.remove(client)
        print("Client disconnected")

async def generate_data_periodically():
    while True:
        try:
            data_list = generate_random_data()
            for data in data_list:
                message = json.dumps(data)
                destination = f"/topic/{data['type']}"
                
                for client in stomp_clients:
                    if destination in client.subscriptions:
                        await client.send_message(destination, message)
            
            await asyncio.sleep(1)
        except Exception as e:
            print(f"Error in data generation: {e}")
            await asyncio.sleep(1)

@app.get("/topicServer")
async def get_html():
    with open("static/topicServer.html") as f:
        return HTMLResponse(f.read())
    
@app.get("/monitor")
async def get_html():
    with open("static/monitor.html") as f:
        return HTMLResponse(f.read())    

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080) 