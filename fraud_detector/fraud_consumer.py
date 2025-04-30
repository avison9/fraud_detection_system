from kafka import KafkaConsumer
import json
import pickle
from fraud_detector import FraudDetector

KAFKA_TOPIC = "transactions"
KAFKA_BROKER = "kafka:9092"

# Create Kafka consumer
consumer = KafkaConsumer(KAFKA_TOPIC, bootstrap_servers=[KAFKA_BROKER],
                         value_deserializer=lambda m: json.loads(m.decode('utf-8')))

# Load the trained model
with open('fraud_detection_model.pkl', 'rb') as f:
    model = pickle.load(f)

# Initialize FraudDetector
fraud_detector = FraudDetector()
fraud_detector.model = model

for message in consumer:
    transaction = message.value
    prediction = fraud_detector.predict(transaction)
    print(f"Transaction ID: {transaction['transaction_id']} - {'Fraud' if prediction == 1 else 'Legit'}")
