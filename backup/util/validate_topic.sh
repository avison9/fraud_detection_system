#!/bin/bash

EXPECTED_TOPIC_COUNT=5
ACTUAL_TOPIC_COUNT=$(python util/check_topic.py)

echo "Expected topics: $EXPECTED_TOPIC_COUNT"
echo "Found topics: $ACTUAL_TOPIC_COUNT"

if [ "$ACTUAL_TOPIC_COUNT" -eq "$EXPECTED_TOPIC_COUNT" ]; then
    echo "All required topics are present. Starting app..."
    exit 0
else
    echo "Not all required topics found. Exiting."
    exit 1
fi
