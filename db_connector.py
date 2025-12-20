import os
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

# Load variables from the .env file
load_dotenv()

def connect_to_db():
    connection = None
    try:
        # Fetch credentials using os.getenv
        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            port=int(os.getenv("DB_PORT", 3306)) # Default to 3306 if missing
        )

        if connection.is_connected():
            print("✅ Successfully connected to the database using .env credentials!")
            
            # Print database info to verify
            db_info = connection.get_server_info()
            print(f"   Connected to MySQL Server version: {db_info}")

    except Error as e:
        print(f"❌ Error while connecting: {e}")
        
    finally:
        if connection and connection.is_connected():
            connection.close()
            print("🔒 Connection closed")

# if __name__ == '__main__':
#     connect_to_db()