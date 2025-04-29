from kafka import KafkaProducer
import json
import random
import uuid
import time
from datetime import datetime, timedelta
import os

broker1 = os.getenv('KAFKA_BROKER1')
broker2 = os.getenv('KAFKA_BROKER2')
broker3 = os.getenv('KAFKA_BROKER3')

KAFKA_TOPIC = "transactions"
KAFKA_BROKER = [broker1,broker2,broker3]

# Create Kafka producer
producer = KafkaProducer(bootstrap_servers=KAFKA_BROKER,
                         value_serializer=lambda v: json.dumps(v).encode('utf-8'))

def generate_random_timestamp(start_date, end_date):
    
    start = datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S")
    end = datetime.strptime(end_date, "%Y-%m-%d %H:%M:%S")

    delta = end - start
    random_seconds = random.randint(0, int(delta.total_seconds()))
    random_timestamp = start + timedelta(seconds=random_seconds)
    
    return random_timestamp.strftime("%Y-%m-%d %H:%M:%S")

def generate_initial_transactions(n_wallets=100, txns_per_wallet=random.randint(1,7)):
    data = []
    for _ in range(n_wallets):
        wallet_id = str(uuid.uuid4())
        for _ in range(txns_per_wallet):
            trxn = {
                "transaction_id": str(uuid.uuid4()),
                "timestamp": generate_random_timestamp("2022-01-01 00:00:00", "2025-01-01 00:00:00"),
                "sender_wallet": wallet_id,
                "receiver_wallet": str(uuid.uuid4()),
                "amount": round(random.uniform(0.0001, 10.0), 6),
                "currency": random.choice(["BTC", "ETH", "USDT"]),
                "gas_fee": round(random.uniform(0.00001, 0.005), 6),
                "is_smart_contract": random.choice([0, 1]),
                "location": random.choice(["US", "Germany", "Nigeria", "India"]),
                "device_type": random.choice(["mobile", "desktop", "API"]),
                "is_fraud": random.choices([0, 1], weights=[0.90, 0.1])[0]
            }
            data.append(trxn)
    return data
            

for data in generate_initial_transactions():
    # transaction = generate_transaction()
    producer.send(KAFKA_TOPIC, data)
    print(f"Sent transaction: {data}")
    time.sleep(1)]
print("Test data for training send to topic")
