
KAFKA_BROKER = ['broker1:29092','broker2:29093','broker3:29094']

POSTGRES_CONFIG = {
    'host': 'postgres',
    'port': 5432,
    'dbname': 'dev',
    'user': 'root',
    'password': 'password'
}

MONGO_DB_CONFIG = {
	'host' : 'mongodb',
	'port' : 27017,
	'user' : 'root',
	'password' : 'password',
	'collection' : 'raw_trx',
	'database' : 'transactions'
}

MONGO_URI = f"mongodb://{MONGO_DB_CONFIG['user']}:{MONGO_DB_CONFIG['password']}@{MONGO_DB_CONFIG['host']}:{MONGO_DB_CONFIG['port']}/"

PREDICTION_TOPIC = ['fraud', 'legit']

TRAINING_TOPIC = ['training_transactions'] 

TOPIC_IN = 'live_transactions'

TOPIC_FRAUD = 'fraud'


TOPIC_LEGIT = 'legit'
