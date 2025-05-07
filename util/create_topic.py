from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import TopicAlreadyExistsError
from kafka.errors import KafkaError
from params import *

def create_kafka_topics(bootstrap_servers, topic_list):
    admin_client = KafkaAdminClient(
        bootstrap_servers=bootstrap_servers,
        client_id='topic_creator'
    )

    topics_to_create = []
    topic_names = [t['name'] for t in topic_list]

    for topic in topic_list:
        topics_to_create.append(NewTopic(
            name=topic['name'],
            num_partitions=topic.get('num_partitions', 1),
            replication_factor=topic.get('replication_factor', 1)
        ))

    try:
        admin_client.create_topics(new_topics=topics_to_create, validate_only=False)
        print(f"Successfully created topics: {topic_names}")
    except TopicAlreadyExistsError as e:
        print(f"Topics already exist: {e}")
    except KafkaError as e:
        print(f"Failed to create topics due to KafkaError: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        admin_client.close()

if __name__ == '__main__':
    print("Creating Topics......")
    topics_to_create = [
        {'name': 'live_transactions', 'num_partitions': 7, 'replication_factor': 3},
        {'name': 'training_transactions', 'num_partitions': 5, 'replication_factor': 3},
        {'name': 'fraud', 'num_partitions': 6, 'replication_factor': 3},
        {'name': 'legit', 'num_partitions': 6, 'replication_factor': 3},
        {'name': 'alert', 'num_partitions': 4, 'replication_factor': 2}
    ]

    create_kafka_topics(KAFKA_BROKER, topics_to_create)



