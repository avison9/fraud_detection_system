from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from kafka import KafkaConsumer
import threading
import json
import asyncio
import redis
import time
from params import KAFKA_BROKER, PREDICTION_TOPIC
from rebalancer import RebalanceListener

time.sleep(80)
app = FastAPI()
clients = []
message_queue = asyncio.Queue()
buffer = []

# Redis connection
redis_client = redis.Redis(host="redis", port=6379, db=0)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.append(websocket)
    try:
        while True:
            if websocket.client_state.name != "CONNECTED":
                break
            await asyncio.sleep(10)
    except Exception:
        pass
    finally:
        clients.remove(websocket)

@app.get("/latest")
def get_latest_messages(limit: int = 50):
    messages = redis_client.lrange("tx_cache", 0, limit - 1)
    return [json.loads(msg) for msg in messages]

async def websocket_broadcaster():
    while True:
        data = await message_queue.get()
        await send_to_clients(data)  


async def send_to_clients(data):
    serialized = json.dumps(data)
    for ws in clients.copy():
        try:
            await ws.send_text(serialized)
        except Exception:
            clients.remove(ws)  

def broadcast_to_clients(data_list):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.get_event_loop()
    
    for data in data_list:
        try:
            asyncio.run_coroutine_threadsafe(send_to_clients(data), loop)  
        except Exception as e:
            print(f"[Broadcast] Failed to schedule coroutine: {e}")

def kafka_consumer_thread():
    consumer = KafkaConsumer(
        bootstrap_servers=KAFKA_BROKER,
        group_id='streaming-dashboard',
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        auto_offset_reset='earliest',
        enable_auto_commit=False,
        max_poll_records=50,
        heartbeat_interval_ms=3000,
        session_timeout_ms=10000
    )

    listener = RebalanceListener(consumer, buffer, broadcast_to_clients)  
    consumer.subscribe(PREDICTION_TOPIC, listener=listener)

    print("[KAFKA] Consumer started...")
    while True:
        try:
            records = consumer.poll(timeout_ms=1000)
            for _, messages in records.items():
                for message in messages:
                    if not message:
                        print(f'[WEB-API]- No messages in topic {message.topic} partition {message.partition}!')
                        continue
                    data = message.value
                    redis_client.lpush("tx_cache", json.dumps(data))
                    redis_client.ltrim("tx_cache", 0, 499)
                    asyncio.run_coroutine_threadsafe(message_queue.put(data), loop)
            consumer.commit()
        except Exception as e:
            print(f"[KAFKA ERROR] {e}")
            time.sleep(5)

# Launch background threads/tasks
@app.on_event("startup")
async def startup_event():
    global loop
    loop = asyncio.get_running_loop()
    threading.Thread(target=kafka_consumer_thread, daemon=True).start()
    asyncio.create_task(websocket_broadcaster())


