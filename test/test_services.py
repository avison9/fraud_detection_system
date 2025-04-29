import unittest
from kafka import KafkaProducer, KafkaConsumer, KafkaError
from pymongo import MongoClient, errors as mongo_errors
import psycopg2
from psycopg2 import OperationalError
import os

broker1 = os.getenv('KAFKA_BROKER1')
broker2 = os.getenv('KAFKA_BROKER2')
broker3 = os.getenv('KAFKA_BROKER3')

mongo_host = os.getenv('MONGO_HOST')
mongo_port = os.getenv('MONGO_PORT')
mongo_password = os.getenv('MONGO_PASSWORD')
mongo_user = os.getenv('MONGO_USER')
mongo_db_name = os.getenv('MONGO_DB_NAME')
mongo_collection_name = os.getenv('MONGO_COLLECTION_NAME')

postgres_db = os.getenv('POSTGRES_DB_NAME')
postgres_user = os.getenv('POSTGRES_USER')
postgres_password = os.getenv('POSTGRES_PASSWORD')
postgres_host = os.getenv('POSTGRES_HOST')
postgres_port = os.getenv('POSTGRES_PORT')

class ServiceHealthCheckTest(unittest.TestCase):

    def test_kafka_producer_connection(self):
        try:
            producer = KafkaProducer(bootstrap_servers=[broker1,broker2,broker3])
            self.assertIsNotNone(producer)
            producer.close()
        except KafkaError as e:
            self.fail(f"Kafka Producer connection failed: {e}")

    def test_kafka_consumer_connection(self):
        try:
            consumer = KafkaConsumer(
                'trx',
                bootstrap_servers=[broker1,broker2,broker3],
                auto_offset_reset='earliest',
                group_id='healthcheck_group',
                consumer_timeout_ms=1000 
            )
            self.assertIsNotNone(consumer)
            consumer.close()
        except KafkaError as e:
            self.fail(f"Kafka Consumer connection failed: {e}")

    def test_mongodb_connection(self):
        try:
            client = MongoClient(f"mongodb://{mongo_user}:{mongo_password}@{mongo_host}:{mongo_port}/", serverSelectionTimeoutMS=2000)
            client.server_info()  
            self.assertTrue(True)
        except mongo_errors.ServerSelectionTimeoutError as e:
            self.fail(f"MongoDB connection failed: {e}")

    def test_postgres_connection(self):
        try:
            conn = psycopg2.connect(
                dbname=postgres_db,
                user=postgres_user,
                password=postgres_password,
                host=postgres_host,
                port=postgres_port,
                connect_timeout=2
            )
            self.assertTrue(conn is not None)
            conn.close()
        except OperationalError as e:
            self.fail(f"PostgreSQL connection failed: {e}")


if __name__ == '__main__':
    unittest.main()
