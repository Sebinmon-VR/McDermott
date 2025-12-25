import mysql.connector
import os
from dotenv import load_dotenv

# Load variables
load_dotenv()

def get_db_connection():
    try:
        # 1. Open the connection
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME')
        )
        
        # 2. Return it OPEN (Do not close it here!)
        return connection
        
    except mysql.connector.Error as err:
        print(f"❌ DATABASE ERROR: {err}", flush=True)
        return None