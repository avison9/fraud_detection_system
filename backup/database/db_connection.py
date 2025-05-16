import psycopg2
from psycopg2.extras import RealDictCursor
from pymongo import MongoClient

class DatabaseConnection:
    def __init__(self, postgres_config = None, mongo_uri = None, mongo_db_name = None):
        if not postgres_config and not mongo_uri:
            raise ValueError("Provide at least PostgreSQL or MongoDB configuration.")

        self.postgres_config = postgres_config
        self.mongo_uri = mongo_uri
        self.mongo_db_name = mongo_db_name

        self.pg_conn = None
        self.pg_cursor = None
        self.mongo_client = None
        self.mongo_db = None

        if self.postgres_config:
            self.connect_postgres()

        if self.mongo_uri and self.mongo_db_name:
            self.connect_mongo()

    def connect_postgres(self):
        try:
            self.pg_conn = psycopg2.connect(**self.postgres_config)
            self.pg_cursor = self.pg_conn.cursor(cursor_factory=RealDictCursor)
            print("[PostgreSQL] Connection established.")
        except Exception as e:
            print(f"[PostgreSQL] Connection error: {e}")

    def connect_mongo(self):
        try:
            self.mongo_client = MongoClient(self.mongo_uri)
            self.mongo_db = self.mongo_client[self.mongo_db_name]
            if self.mongo_db is not None: 
                print("[MongoDB] Connection established.")
            else:
                raise Exception("MongoDB connection failed. Database is None.")
        except Exception as e:
            print(f"[MongoDB] Connection error: {e}")


    def close_postgres(self):
        if self.pg_cursor:
            self.pg_cursor.close()
        if self.pg_conn:
            self.pg_conn.close()
        print("[PostgreSQL] Connection closed.")

    def close_mongo(self):
        if self.mongo_client is not None:
            self.mongo_client.close()
        print("[MongoDB] Connection closed.")

    def get_postgres_cursor(self):
        if not self.pg_cursor:
            raise RuntimeError("PostgreSQL is not initialized.")
        return self.pg_cursor

    def get_postgres_connection(self):
        if not self.pg_conn:
            raise RuntimeError("PostgreSQL is not initialized.")
        return self.pg_conn

    def get_mongo_collection(self, collection_name):
        if self.mongo_db is None:
            raise RuntimeError("MongoDB is not initialized.")
        return self.mongo_db[collection_name]

    def insert_postgres(self, query, values):
        if not self.pg_cursor or not self.pg_conn:
            raise RuntimeError("PostgreSQL is not initialized.")
        try:
            self.pg_cursor.execute(query, values)
            self.pg_conn.commit()
            print(f"[PostgreSQL] Inserted data: {values[0]} successfully into transactions table.")
        except Exception as e:
            self.pg_conn.rollback()
            print(f"[PostgreSQL] Insert failed: {e}")

    def insert_mongo(self, collection_name, document, training = False):
        if self.mongo_db is None:
            raise RuntimeError("MongoDB is not initialized.")
        if training:
            try:
                collection = self.get_mongo_collection(collection_name)
                result = collection.insert_one(document)
                print(f"[MongoDB] Inserted document successfully for initial training...")
            except Exception as e:
                print(f"[MongoDB] Insert failed: {e}")
        else:
            try:
                collection = self.get_mongo_collection(collection_name)
                result = collection.insert_one(document)
                print(f"[MongoDB] Inserted document sucessfully for subsequent training")
            except Exception as e:
                print(f"[MongoDB] Insert failed: {e}")
