import json
import os
from kafka import KafkaConsumer
from pymongo import MongoClient
from datetime import datetime


mongo_host = os.getenv('MONGO_HOST')
mongo_port = os.getenv('MONGO_PORT')
mongo_password = os.getenv('MONGO_PASSWORD')
mongo_user = os.getenv('MONGO_USER')
mongo_db_name = os.getenv('MONGO_DB_NAME')
mongo_collection_name = os.getenv('MONGO_COLLECTION_NAME')

broker1 = os.getenv('KAFKA_BROKER1')
broker2 = os.getenv('KAFKA_BROKER2')
broker3 = os.getenv('KAFKA_BROKER3')


kafka_brokers = [broker1,broker2,broker3]
kafka_topic = 'transactions'

client = MongoClient(f"mongodb://{mongo_user}:{mongo_password}@{mongo_host}:{mongo_port}/")
db = client[mongo_db_name]
collection = db[mongo_collection_name]

print("Connected to MongoDB")


consumer = KafkaConsumer(
    kafka_topic,
    bootstrap_servers=kafka_brokers,
    auto_offset_reset='earliest',
    enable_auto_commit=True,
    group_id='fraud_detection_group'
)

print(f"Connected to Kafka's {len(kafka_brokers)} brokers")

INACTIVITY_TIMEOUT_SECONDS = 60 
last_message_time = datetime.now()

def process_and_insert_data(message):
    global last_message_time
    try:
        data = json.loads(message.value.decode('utf-8'))

        document = {
            'transaction_id': data['transaction_id'],
            'timestamp': datetime.strptime(data['timestamp'], '%Y-%m-%d %H:%M:%S'),
            'sender_wallet': data['sender_wallet'],
            'receiver_wallet': data['receiver_wallet'],
            'amount': data['amount'],
            'currency': data['currency'],
            'gas_fee': data['gas_fee'],
            'is_smart_contract': data['is_smart_contract'],
            'location': data['location'],
            'device_type': data['device_type'],
            'is_fraud': data['is_fraud']
        }

        collection.insert_one(document)
        print(f"Inserted transaction with ID: {data['transaction_id']} into MongoDB")
        last_message_time = datetime.now()
    
    except Exception as e:
        print(f"Error processing message: {e}")


try:
    while True:
        message_pack = consumer.poll(timeout_ms=1000)  
        if message_pack:
            for tp, messages in message_pack.items():
                for message in messages:
                    process_and_insert_data(message)
        else:
            if datetime.now() - last_message_time > timedelta(seconds=INACTIVITY_TIMEOUT_SECONDS):
                print(f"No new messages for {INACTIVITY_TIMEOUT_SECONDS} seconds. Shutting down consumer.")
                break

except KeyboardInterrupt:
    print("Stopping Kafka consumer manually.")

finally:
    consumer.close()
    print("Kafka consumer closed.")
