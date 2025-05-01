#!/bin/bash


source /app/venv/bin/activate
(
  for i in {1..5}
  do
    echo "Waiting for Infrastructures to be up and running..."
    sleep 10
  done
) &

sleep 70

echo "Running producer script..."
python data/producer.py 

echo "Running consumer script..."
python data/consumer.py


echo "Running fraud detection script..."
python fraud_detector/fraud_producer.py &

python fraud_detector/compro.py

