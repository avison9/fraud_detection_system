from kafka import KafkaAdminClient
import sys
import time

BOOTSTRAP_SERVERS = ['broker1:29092', 'broker2:29092', 'broker3:29092']

def get_topic_count():
    while True:
        try:
            client = KafkaAdminClient(bootstrap_servers=BOOTSTRAP_SERVERS, client_id='topic-counter')
            topics = client.list_topics()
            print(f"[Utility-Checks]: Found {len(topics)} topics: {topics}")
            sys.exit(len(topics))
        except Exception as e:
            print(f"Kafka not ready yet: {e}")
        time.sleep(2)

if __name__ == "__main__":
    get_topic_count()

