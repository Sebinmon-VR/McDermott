# import os
# import mysql.connector
# from mysql.connector import Error
# from dotenv import load_dotenv

# # Load variables from the .env file
# load_dotenv()

# def connect_to_db():
#     connection = None
#     try:
#         # Fetch credentials using os.getenv
#         connection = mysql.connector.connect(
#             host=os.getenv("DB_HOST"),
#             database=os.getenv("DB_NAME"),
#             user=os.getenv("DB_USER"),
#             password=os.getenv("DB_PASSWORD"),
#             port=int(os.getenv("DB_PORT", 3306)) # Default to 3306 if missing
#         )

#         if connection.is_connected():
#             print("✅ Successfully connected to the database using .env credentials!")
            
#             # Print database info to verify
#             db_info = connection.get_server_info()
#             print(f"   Connected to MySQL Server version: {db_info}")

#     except Error as e:
#         print(f"❌ Error while connecting: {e}")
        
#     finally:
#         if connection and connection.is_connected():
#             connection.close()
#             print("🔒 Connection closed")

# # if __name__ == '__main__':
# #     connect_to_db()

import os
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import json, uuid

# Load variables from the .env file
load_dotenv()

def get_db_connection():
    """Establishes a connection to the hosted MySQL database."""
    try:
        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            port=int(os.getenv("DB_PORT", 3306))
        )
        return connection
    except Error as e:
        print(f"❌ Error while connecting to MySQL: {e}")
        return None

def get_all_work_orders():
    """Retrieves full details for the Work Orders List page."""
    conn = get_db_connection()
    if conn is None: return []
    
    cursor = conn.cursor(dictionary=True)
    
    query = """
        SELECT 
            w.wo_id,
            w.status,
            w.priority,
            w.created_at,
            w.completed_at,
            -- Asset Details
            COALESCE(a.asset_id, 'N/A') AS unit_number,
            COALESCE(a.name, 'General Maintenance') AS asset_name,
            -- Assignee Details
            COALESCE(u.full_name, 'Unassigned') AS assignee_name
        FROM work_orders w
        LEFT JOIN assets a ON w.current_asset_id = a.asset_id
        LEFT JOIN users u ON w.assigned_user_id = u.user_id
        ORDER BY w.created_at DESC
    """
    
    try:
        cursor.execute(query)
        work_orders = cursor.fetchall()
        return work_orders
    except Error as e:
        print(f"❌ Query Error: {e}")
        return []
    finally:
        if conn.is_connected(): cursor.close(); conn.close()

def add_maintenance_cost(wo_id, description, category, amount, vendor=None):
    conn = get_db_connection()
    if conn is None: return False
    try:
        cursor = conn.cursor()
        query = "INSERT INTO maintenance_costs (wo_id, description, cost_category, cost_amount, vendor_name) VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(query, (wo_id, description, category, amount, vendor))
        conn.commit(); return True
    except Error as e: return False
    finally: 
        if conn.is_connected(): cursor.close(); conn.close()

def get_dashboard_data():
    """
    Retrieves work orders and calculates counts for Open, In Progress, and Completed.
    """
    conn = get_db_connection()
    if conn is None: return [], 0, 0, 0
    
    cursor = conn.cursor(dictionary=True)
    
    query = """
        SELECT 
            w.wo_id,
            a.asset_id AS unit_number, 
            a.name AS asset_name,
            w.status,
            w.priority,
            COALESCE(tt.name, 'General') AS wo_type
        FROM work_orders w
        LEFT JOIN assets a ON w.current_asset_id = a.asset_id
        LEFT JOIN preventive_maintenance_schedules pms ON w.schedule_id = pms.schedule_id
        LEFT JOIN task_templates tt ON pms.template_id = tt.template_id
        WHERE w.status != 'Closed'
        ORDER BY w.created_at DESC
    """
    
    try:
        cursor.execute(query)
        work_orders = cursor.fetchall()
        
        # Calculate counts for the chart
        count_open = sum(1 for wo in work_orders if wo['status'] == 'Open')
        count_inprogress = sum(1 for wo in work_orders if wo['status'] == 'In_Progress')
        count_completed = sum(1 for wo in work_orders if wo['status'] == 'Completed')
        
        return work_orders, count_open, count_inprogress, count_completed
        
    except Error as e:
        print(f"❌ Query Error: {e}")
        return [], 0, 0, 0
    finally:
        if conn.is_connected(): cursor.close(); conn.close()


def get_work_order_details(wo_id):
    conn = get_db_connection()
    if conn is None: return None, [], [], [], 0.0

    cursor = conn.cursor(dictionary=True)
    
    # 1. Fetch Dropdowns
    cursor.execute("SELECT asset_id, name FROM assets WHERE status != 'Retired'")
    assets = cursor.fetchall()
    cursor.execute("SELECT user_id, full_name FROM users WHERE is_active = 1")
    users = cursor.fetchall()

    if wo_id == 'new':
        conn.close()
        return None, [], assets, users, 0.0

    try:
        query_wo = """
            SELECT 
                w.*, 
                a.name as asset_name, 
                u.full_name as assignee_name
            FROM work_orders w
            LEFT JOIN assets a ON w.current_asset_id = a.asset_id
            LEFT JOIN users u ON w.assigned_user_id = u.user_id
            WHERE w.wo_id = %s
        """
        cursor.execute(query_wo, (wo_id,))
        wo = cursor.fetchone()

        # 2. Parse Execution Data (Reused for Maintenance Log)
        tasks = []
        if wo and wo['execution_data']:
            try:
                raw_data = wo['execution_data']
                # Handle double-serialization if DB has it stored as string-in-string
                tasks = json.loads(raw_data) if isinstance(raw_data, str) else raw_data
            except Exception as e:
                print(f"JSON Parse Error: {e}")
                tasks = []

        # Calculate total from JSON data
        total_cost = sum(float(t.get('amount', 0)) for t in tasks)
        
        return wo, tasks, assets, users, total_cost
        
    except Error as e:
        print(f"❌ Query Error: {e}")
        return None, [], [], [], 0.0
    finally:
        if conn.is_connected(): cursor.close(); conn.close()

def create_work_order(asset_id, priority, assigned_user_id, status, execution_data_json, total_cost):
    """Inserts new WO with JSON data in execution_data column."""
    conn = get_db_connection()
    if conn is None: return None

    
    try:
        cursor = conn.cursor()
        query = """
            INSERT INTO work_orders 
            ( current_asset_id, priority, assigned_user_id, status, 
             snapshot_asset_name, snapshot_asset_loc, technician_name_log, execution_data, total_cost)
            SELECT 
                 %s, %s, %s, %s,
                a.name, a.location_code, u.full_name, %s, %s
            FROM assets a, users u
            WHERE a.asset_id = %s AND u.user_id = %s
        """
        cursor.execute(query, (asset_id, priority, assigned_user_id, status, 
                               execution_data_json, total_cost, asset_id, assigned_user_id))
        conn.commit()
        return True
    except Error as e:
        print(f"❌ Create WO Error: {e}")
        return False
    finally:
        if conn.is_connected(): cursor.close(); conn.close()

def update_work_order(wo_id, status, priority, assigned_user_id, current_asset_id, total_cost, execution_data_json):
    """Updates WO including the execution_data column."""
    conn = get_db_connection()
    if conn is None: return False
    
    try:
        cursor = conn.cursor()
        query = """
            UPDATE work_orders 
            SET status = %s, priority = %s, assigned_user_id = %s, current_asset_id = %s, total_cost = %s, execution_data = %s
            WHERE wo_id = %s
        """
        cursor.execute(query, (status, priority, assigned_user_id, current_asset_id, total_cost, execution_data_json, wo_id))
        conn.commit()
        return True
    except Error as e:
        print(f"❌ Update WO Error: {e}")
        return False
    finally:
        if conn.is_connected(): cursor.close(); conn.close()