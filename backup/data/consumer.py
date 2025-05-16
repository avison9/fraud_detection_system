import json
from kafka import KafkaConsumer
from datetime import datetime, timedelta
from database.db_connection import DatabaseConnection
from util.params import *

# Kafka Consumer Configuration
kafka_brokers = KAFKA_BROKER
kafka_topic = ''.join(TRAINING_TOPIC)

mongo_db_name = MONGO_DB_CONFIG['database']
mongo_collection_name = MONGO_DB_CONFIG['collection']


db = DatabaseConnection(None,MONGO_URI, mongo_db_name)

db.connect_mongo()

print("Connected to MongoDB")

consumer = KafkaConsumer(
    kafka_topic,
    bootstrap_servers=kafka_brokers,
    auto_offset_reset='earliest',
    enable_auto_commit=True,
    group_id='fraud_detection_group'
)

print(f"Connected to Kafka's {len(kafka_brokers)} brokers")

INACTIVITY_TIMEOUT_SECONDS = 30 
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

        db.insert_mongo(mongo_collection_name,document, True)
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

