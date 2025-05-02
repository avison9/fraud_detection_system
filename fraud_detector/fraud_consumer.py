import json
import uuid
import threading
import pandas as pd
from kafka import KafkaConsumer
from database.db_connection import DatabaseConnection

KAFKA_BROKER = ['broker1:29092','broker2:29093','broker3:29094']

POSTGRES_CONFIG = {
    'host': 'postgres',
    'port': 5432,
    'dbname': 'dev',
    'user': 'root',
    'password': 'password'
}

mongo_host = "mongodb"
mongo_port = 27017
mongo_password = "password"
mongo_user = "root"

MONGO_URI = f"mongodb://{mongo_user}:{mongo_password}@{mongo_host}:{mongo_port}/"
MONGO_DB = "transactions"
MONGO_COLLECTION = "raw_trx"


TOPIC_A = ['fraud', 'legit'] 
TOPIC_B = ['training_transactions']  

db = DatabaseConnection(POSTGRES_CONFIG, MONGO_URI, MONGO_DB)

db.connect_postgres()
db.connect_mongo()


def insert_into_postgres(data):
    query = """
    INSERT INTO transactions (
        transaction_id, timestamp, sender_wallet_id, receiver_wallet_id,
        amount, currency_id, gas_fee, is_smart_contract,
        location_id, device_type_id, is_fraud
    )
    VALUES (%s, %s, %s, %s, %s, 
            (SELECT currency_id FROM currencies WHERE currency_code = %s),
            %s, %s, 
            (SELECT location_id FROM locations WHERE country_name = %s),
            (SELECT device_type_id FROM device_types WHERE device_name = %s),
            %s
    )
    ON CONFLICT DO NOTHING;
    """
    txn = (
        data['transaction_id'],
        data['timestamp'],
        data['sender_wallet'],
        data['receiver_wallet'],
        data['amount'],
        data['currency'],
        data['gas_fee'],
        bool(data['is_smart_contract']),
        data['location'],
        data['device_type'],
        bool(data['is_fraud'])
    )
    db.insert_postgres(query,txn)




def insert_into_mongodb(data):
    db.insert_mongo(MONGO_COLLECTION, data)
    


def consume_postgres(topics):
    consumer = KafkaConsumer(
        *topics,
        bootstrap_servers=KAFKA_BROKER,
        group_id='postgres_group',
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        auto_offset_reset='earliest',
        enable_auto_commit=False,
        max_poll_records=50,  
        heartbeat_interval_ms=3000,
        session_timeout_ms=10000
    )

    print(f"[PostgreSQL Consumer] Listening to topics: {topics}")

    for message in consumer:
        try:
            data = message.value
            insert_into_postgres(data)
            print(f"[PostgreSQL Consumer] Inserted: {data['transaction_id']}")
        except Exception as e:
            print(f"[PostgreSQL Consumer] Error: {e}")


def consume_mongo(topics):
    consumer = KafkaConsumer(
        *topics,
        bootstrap_servers=KAFKA_BROKER,
        group_id='mongo_group',
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        auto_offset_reset='earliest',
        enable_auto_commit=False,
        max_poll_records=50,  
        heartbeat_interval_ms=3000,
        session_timeout_ms=10000
    )

    print(f"[MongoDB Consumer] Listening to topics: {topics}")

    for message in consumer:
        try:
            data = message.value
            insert_into_mongodb(data)
            print(f"[MongoDB Consumer] Inserted: {data['transaction_id']}")
        except Exception as e:
            print(f"[MongoDB Consumer] Error: {e}")



if __name__ == '__main__':
    t1 = threading.Thread(target=consume_postgres, args=(TOPIC_A,))
    t2 = threading.Thread(target=consume_mongo, args=(TOPIC_B,))
    t1.start()
    t2.start()
    t1.join()
    t2.join()


