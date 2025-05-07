import os
import json
import time
import schedule
from pathlib import Path
import pandas as pd
from kafka import KafkaConsumer, KafkaProducer
from fraud_model import FraudDetector
from datetime import datetime
from data.load_training_data import create_offset, load_dataset
import threading
import warnings
from util.params import *

warnings.filterwarnings('always', category=UserWarning, message=".*compiled the loaded model.*")

CHUNK = 500
BASE = Path(__file__).resolve().parent.parent 
TRAINING_DIR = BASE / "data" / "training_data"

consumer = KafkaConsumer(
    TOPIC_IN,
    bootstrap_servers=KAFKA_BROKER,
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    auto_offset_reset='earliest',
    enable_auto_commit=False,
    group_id='fraud_detector_group',
    max_poll_records=50,  
    heartbeat_interval_ms=3000,
    session_timeout_ms=10000
)

producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER,
    value_serializer=lambda m: json.dumps(m).encode('utf-8'),
    acks='all',
    max_request_size=1048576
)

fraud_detector = FraudDetector()

def process_transaction(message):
    try:
        transaction = message.value
        prediction = fraud_detector.predict(transaction)
        target_topic = TOPIC_FRAUD if prediction == 1 else TOPIC_LEGIT
        transaction['is_fraud'] = prediction
        producer.send(target_topic, value=transaction)
        print(f"[{datetime.now()}] Sent transaction to {target_topic}")
        producer.send(TRAINING_TOPIC[0], transaction)
        print(f"[{datetime.now()}] Sent transaction to {TRAINING_TOPIC[0]} for model training")
    except Exception as e:
        print(f"Prediction error: {e}")

def load_latest_files(directory):

    load_dataset(create_offset(), CHUNK)

    files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
    
    files.sort(key=lambda f: os.path.getmtime(os.path.join(directory, f)), reverse=True)
    
    latest_files = files[:2]
    
    dataframes = []
    for file in latest_files:
        file_path = os.path.join(directory, file)
        df = pd.read_csv(file_path) 
        dataframes.append(df)
    
    combined_df = pd.concat(dataframes, ignore_index=True)
    
    return combined_df


def retrain_model():
    #will later implement this using airflow
    print(f"[{datetime.now()}] Starting model retraining...")
    try:
        df = load_latest_files(TRAINING_DIR)
        fraud_detector.train(df)
        print("Model retrained and saved.")
    except Exception as e:
        print(f"Training error: {e}")

def schedule_runner():
    # schedule.every().saturday.at("10:00").do(retrain_model)
    schedule.every(30).minutes.do(retrain_model)

    while True:
        try:
            schedule.run_pending()
        except Exception as e:
            print(f"Schedule error: {e}")
        time.sleep(2)  

retrain_model()

threading.Thread(target=schedule_runner, daemon=True).start()

print("Fraud detection agent is running...")

try:
    while True:
        raw_messages = consumer.poll(timeout_ms=1000)
        for tp, messages in raw_messages.items():
            for message in messages:
                process_transaction(message)
        consumer.commit()

        time.sleep(1)
except KeyboardInterrupt:
    print("Shutting down.")
finally:
    consumer.close()
    producer.close()


