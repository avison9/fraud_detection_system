from db_connection import DatabaseConnection
import os

script_dir = os.path.dirname(__file__)
schema_path = os.path.join(script_dir, 'schema.sql')

def execute_sql_file(sql_file_path, db_config):
    db = None
    try:
        with open(sql_file_path, 'r') as file:
            sql_commands = file.read()

        db = DatabaseConnection(postgres_config=db_config)
        cursor = db.get_postgres_cursor()

        for command in sql_commands.strip().split(';'):
            if command.strip():
                cursor.execute(command + ';')

        db.get_postgres_connection().commit()
        print("[PostgreSQL] SQL script executed successfully.")

    except Exception as e:
        if db:
            db.get_postgres_connection().rollback()
        print(f"[PostgreSQL] Error executing SQL script: {e}")
    
    finally:
        if db:
            db.close_postgres()


db_config = {
    'host': 'postgres',
    'port': 5432,
    'database': 'dev',
    'user': 'root',
    'password': 'password'
}


execute_sql_file(schema_path, db_config)
