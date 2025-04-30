from kafka import KafkaProducer
import json
import random
import uuid
import time

KAFKA_TOPIC = "transactions"
KAFKA_BROKER = "kafka:9092"

# Create Kafka producer
producer = KafkaProducer(bootstrap_servers=[KAFKA_BROKER],
                         value_serializer=lambda v: json.dumps(v).encode('utf-8'))

def generate_transaction():
    return {
        "transaction_id": str(uuid.uuid4()),
        "timestamp": "2023-04-25 12:00:00",
        "sender_wallet": str(uuid.uuid4()),
        "receiver_wallet": str(uuid.uuid4()),
        "amount": round(random.uniform(0.0001, 10.0), 6),
        "currency": random.choice(["BTC", "ETH"]),
        "gas_fee": round(random.uniform(0.00001, 0.005), 6),
        "is_smart_contract": random.choice([0, 1]),
        "location": random.choice(["United States", "Canada", "Germany"]),
        "device_type": random.choice(["mobile", "desktop", "API"]),
        "is_fraud": random.choice([0, 1])  # Fraud label
    }

while True:
    transaction = generate_transaction()
    producer.send(KAFKA_TOPIC, transaction)
    print(f"Sent transaction: {transaction}")
    time.sleep(1)  # Simulate real-time transaction every 1 second
