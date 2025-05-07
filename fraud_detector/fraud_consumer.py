import json
import uuid
import threading
import pandas as pd
from kafka import KafkaConsumer
from database.db_connection import DatabaseConnection
from util.logger_conf import ConsumerLogger
from util.rebalancer import RebalanceListener
import os
from util.params import *

logger = ConsumerLogger(os.path.basename(__file__)).get_logger()

MONGO_DB = MONGO_DB_CONFIG['database']
MONGO_COLLECTION = MONGO_DB_CONFIG['collection']

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
    buffer = []
    consumer = KafkaConsumer(
        bootstrap_servers=KAFKA_BROKER,
        group_id='postgres_group',
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        auto_offset_reset='earliest',
        enable_auto_commit=False,
        max_poll_records=50,  
        heartbeat_interval_ms=3000,
        session_timeout_ms=10000
    )

    listener = RebalanceListener(consumer, buffer, insert_into_postgres)
    consumer.subscribe(topics, listener=listener)

    print(f"[PostgreSQL Consumer] Listening to topics: {topics}")

    try:
        logger.info("Consumer starting to consume data")
        while True:
            try:
                messages = consumer.poll(timeout_ms=1000)
                if not messages:
                    continue
                for topic_partition, records in messages.items():
                    if not records:
                        print('[PostgrSQL] No new message in Topic {topic_partition.topic} Partition {topic_partition.partition}')
                        continue
                    for record in records:
                        try:
                            insert_into_postgres(record.value)
                            buffer.append(record.value)
                            listener.update_last_used()
                        except Exception as e:
                            print(f"[PostgreSQL Consumer] Error: {e}")
                consumer.commit()
            except Exception as e:
                logger.error(f"Error during polling or processing: {e}", exc_info=True)
    except KeyboardInterrupt:
        logger.info("Consumer interrupted by user")
    finally:
        consumer.close()
        listener.stop()
        logger.info("Kafka consumer closed")


def consume_mongo(topics):
    buffer = []
    consumer = KafkaConsumer(
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

    listener = RebalanceListener(consumer, buffer, insert_into_mongodb)
    consumer.subscribe(topics, listener=listener)

    try:
        logger.info("Consumer starting to consume data")
        while True:
            try:
                messages = consumer.poll(timeout_ms=1000)
                if not messages:
                    continue
                for topic_partition, records in messages.items():
                    if not records:
                        print('[MongoDB] No new message in Topic {topic_partition.topic} Partition {topic_partition.partition}')
                        continue
                    for record in records:
                        try:
                            insert_into_mongodb(record.value)
                            buffer.append(record.value)
                            listener.update_last_used()
                        except Exception as e:
                            print(f"[MongoBD Consumer] Error: {e}")
                consumer.commit()
            except Exception as e:
                logger.error(f"Error during polling or processing: {e}", exc_info=True)
    except KeyboardInterrupt:
        logger.info("Consumer interrupted by user")
    finally:
        consumer.close()
        listener.stop()
        logger.info("Kafka consumer closed")



if __name__ == '__main__':
    t1 = threading.Thread(target=consume_postgres, args=(PREDICTION_TOPIC,))
    t2 = threading.Thread(target=consume_mongo, args=(TRAINING_TOPIC,))
    t1.start()
    t2.start()
    t1.join()
    t2.join()




