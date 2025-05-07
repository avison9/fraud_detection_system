from kafka import KafkaAdminClient
import sys
import time
from params import *

def get_topic_count():
    while True:
        try:
            client = KafkaAdminClient(bootstrap_servers=KAFKA_BROKER, client_id='topic-counter')
            topics = client.list_topics()
            print(f"[Utility-Checks]: Found {len(topics)} topics: {topics}")
            sys.exit(int(len(topics)))
        except Exception as e:
            print(f"Kafka not ready yet: {e}")
        time.sleep(2)

if __name__ == "__main__":
    get_topic_count()

