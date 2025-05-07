import pandas as pd
from pymongo import MongoClient
from datetime import datetime
import os
from pathlib import Path
from util.params import *


mongo_db_name = MONGO_DB_CONFIG['database']
mongo_collection_name = MONGO_DB_CONFIG['collection']


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

    client = MongoClient(MONGO_URI)
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






