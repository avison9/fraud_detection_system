import pandas as pd
from pymongo import MongoClient
from datetime import datetime
import os
from pathlib import Path

mongo_host = "mongodb"
mongo_port = 27017
mongo_password = "password"
mongo_user = "root"
mongo_db_name = "transactions"
mongo_collection_name = "raw_trx"

mongo_uri = f"mongodb://{mongo_user}:{mongo_password}@{mongo_host}:{mongo_port}/"

skip_file = "data/skip_offset.txt"

def create_offset():
    if os.path.exists(skip_file):
        with open(skip_file, "r") as f:
            skip = int(f.read().strip())
    else:
        skip = 0

    return skip

def update_offset(skip, chunk_size):
    skip += chunk_size
    with open(skip_file, "w") as f:
        f.write(str(skip))



def load_dataset(skip, chunk_size):

    create_offset()

    client = MongoClient(mongo_uri)
    db = client[mongo_db_name]
    collection = db[mongo_collection_name]

    data = list(collection.find().skip(skip).limit(chunk_size))

    if data:
        for item in data:
            item.pop('_id', None)

        df = pd.DataFrame(data)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = Path(f"data/training_data/training_data_{timestamp}.csv")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)

        print(f"[{timestamp}] Fetched and saved {len(df)} training data.")
    else:
        print(f"[{datetime.now()}] No more data to fetch.")

    update_offset(skip, chunk_size)
