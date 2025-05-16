from kafka import KafkaProducer
import json
import random
import uuid
import time
from datetime import datetime, timedelta
import signal
from data.wallet import CryptoWallet
from util.params import *

KAFKA_TOPIC = TOPIC_IN
RUNNING = True
START_DATE, END_DATE = "2022-01-01 00:00:00", "2025-01-01 00:00:00"


def signal_handler(sig, frame):
    global RUNNING
    print("\n[INFO] Interrupt received, shutting down gracefully...")
    RUNNING = False

signal.signal(signal.SIGINT, signal_handler)

 
producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER,
    client_id=f'producer-{uuid.uuid4()}',
    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
    acks='all',
    max_request_size=1048576,
    # linger_ms=5,
    # batch_size=32 * 1024,  
    # compression_type='lz4'
    )

def generate_random_timestamp(start_date, end_date):

    start = datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S")
    end = datetime.strptime(end_date, "%Y-%m-%d %H:%M:%S")

    delta = end - start
    random_seconds = random.randint(0, int(delta.total_seconds()))
    random_timestamp = start + timedelta(seconds=random_seconds)
    
    return random_timestamp.strftime("%Y-%m-%d %H:%M:%S")


def generate_transaction():

    sender = CryptoWallet()
    receiver = CryptoWallet()
    return {
        "transaction_id": str(uuid.uuid4()),
        "timestamp": generate_random_timestamp(START_DATE, END_DATE),
        "sender_wallet": str(sender.wallet_address),
        "receiver_wallet": str(receiver.wallet_address),
        "amount": round(random.uniform(0.0001, 10.0), 6),
        "currency": random.choice(["BTC", "ETH","PI"]),
        "gas_fee": round(random.uniform(0.00001, 0.005), 6),
        "is_smart_contract": random.choice([0, 1]),
        "location": random.choice(["United States", "Canada", "Germany"]),
        "device_type": random.choice(["mobile", "desktop", "API"]),
        "is_fraud": None 
    }


print("[INFO] Kafka producer started. Press Ctrl+C to exit.")

try:
    count = 0
    while RUNNING:
        txn = generate_transaction()
        future = producer.send(KAFKA_TOPIC, value=txn)
        print(f'live transaction {count} sent to {KAFKA_TOPIC} topic')
        future.add_callback(lambda metadata: print(f"[INFO] Sent to {metadata.topic} [{metadata.partition()}]"))
        future.add_errback(lambda exc: print(f"[ERROR] Failed to send message: {exc}"))
        count += 1
        time.sleep(1)

except Exception as e:
    print(f"[ERROR] Unexpected error: {e}")

finally:
    print("[INFO] Flushing and closing Kafka producer...")
    producer.flush()
    producer.close()
    print("[INFO] Kafka producer exited cleanly.")

