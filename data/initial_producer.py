from kafka import KafkaProducer
import json
import random
import uuid
import time
from datetime import datetime, timedelta
from wallet import CryptoWallet
from util.params import *

KAFKA_TOPIC = ''.join(TRAINING_TOPIC)

# Create Kafka producer
producer = KafkaProducer(bootstrap_servers=KAFKA_BROKER,
                         value_serializer=lambda v: json.dumps(v).encode('utf-8'))


def generate_random_timestamp(start_date, end_date):
    # Convert to datetime objects
    start = datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S")
    end = datetime.strptime(end_date, "%Y-%m-%d %H:%M:%S")

    delta = end - start
    random_seconds = random.randint(0, int(delta.total_seconds()))
    random_timestamp = start + timedelta(seconds=random_seconds)

    return random_timestamp.strftime("%Y-%m-%d %H:%M:%S")


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
        "is_fraud": None 
    }


def generate_initial_transactions(n_wallets=100, txns_per_wallet=random.randint(1,7)):
    data = []
    for _ in range(n_wallets):
        wallet = CryptoWallet()
        wallet_id = str(wallet.wallet_address)
        for _ in range(txns_per_wallet):
            rec_wallet = CryptoWallet()
            trx = {
                "transaction_id": str(uuid.uuid4()),
                "timestamp": generate_random_timestamp("2022-01-01 00:00:00", "2025-05-01 00:00:00"),
                "sender_wallet": wallet_id,
                "receiver_wallet": str(rec_wallet.wallet_address),
                "amount": round(random.uniform(0.0001, 10.0), 6),
                "currency": random.choice(["BTC", "ETH", "USDT"]),
                "gas_fee": round(random.uniform(0.00001, 0.005), 6),
                "is_smart_contract": random.choice([0, 1]),
                "location": random.choice(["USA", "Germany", "Nigeria", "India"]),
                "device_type": random.choice(["mobile", "desktop", "API"]),
                "is_fraud": random.choices([0, 1], weights=[0.90, 0.1])[0]
            }
            data.append(trx)
    return data
            

for data in generate_initial_transactions():
    # transaction = generate_transaction()
    producer.send(KAFKA_TOPIC, data)
    print(f"Sent transaction: {data}")
    time.sleep(0.2)   


