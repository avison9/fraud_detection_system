#!/bin/bash

BOOTSTRAP_SERVERS="${BOOTSTRAP_SERVERS:-broker1:29092,broker2:29093,broker3:29094}"

(
  for i in {1..5}
  do
    echo "Waiting for Infrastructures to be up and running..."
    sleep 3
  done
) &

sleep 60

echo "Kafka is ready."

create_topic() {
  local topic=$1
  local partitions=$2
  local replication=$3

  kafka-topics --bootstrap-server "$BOOTSTRAP_SERVERS" \
    --create --if-not-exists \
    --replication-factor "$replication" \
    --partitions "$partitions" \
    --topic "$topic"

  echo "Created topic: $topic (partitions=$partitions, replication=$replication)"
}

create_topic "live_transactions" 7 2
create_topic "training_transactions" 4 2
create_topic "fraud" 5 2
create_topic "legit" 5 2
create_topic "alert" 4 3

echo "All topics created successfully."



kafka-topics --list --bootstrap-server $BOOTSTRAP_SERVER

