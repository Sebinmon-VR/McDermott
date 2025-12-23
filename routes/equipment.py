from flask import Blueprint, render_template, request, redirect, url_for
import sys
import os

# Path fix
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import db_connector

equipment_bp = Blueprint('equipment_bp', __name__)

# --- READ ---
# --- READ: List Assets & Fetch Categories for Dropdown ---
# --- READ: List Assets (Now with Category Name JOIN) ---
@equipment_bp.route('/equipment')
def list_equipment():
    conn = db_connector.get_db_connection()
    items = []
    categories = []
    
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            
            # 1. Fetch Assets + Category Name (JOIN)
            # We select all asset info, PLUS the category name aliased as 'category_name'
            query = """
                SELECT 
                    assets.*, 
                    asset_categories.name AS category_name 
                FROM assets
                LEFT JOIN asset_categories ON assets.category_id = asset_categories.category_id
            """
            cursor.execute(query)
            items = cursor.fetchall()
            
            # 2. Fetch Categories (for the Dropdowns)
            cursor.execute("SELECT category_id, name FROM asset_categories")
            categories = cursor.fetchall()
            
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"❌ Error fetching data: {e}", flush=True)
            
    return render_template('equipment.html', equipment_list=items, category_list=categories)

# --- CREATE ASSET ---
@equipment_bp.route('/add_equipment', methods=['POST'])
def add_equipment():
    print("--- 🟢 STARTING ADD EQUIPMENT ---", flush=True)
    
    asset_id = request.form.get('asset_id')
    name = request.form.get('name')
    category_id = request.form.get('category_id') # Comes from the read-only box
    
    # REMOVED: Parent Asset ID input is gone, so we force it to None
    parent_asset_id = None 
    
    location_code = request.form.get('location_code')
    status = request.form.get('status')
    purchase_date = request.form.get('purchase_date')
    criticality = request.form.get('criticality')
    specifications = request.form.get('specifications') 

    # Data Cleaning
    if not purchase_date or purchase_date.strip() == "":
        purchase_date = None

    print(f"📝 Received Data: ID={asset_id}, CatID={category_id}", flush=True)

    conn = db_connector.get_db_connection()
    if conn:
        cursor = conn.cursor()
        query = """
            INSERT INTO assets 
            (asset_id, name, category_id, parent_asset_id, location_code, status, purchase_date, criticality, specifications)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        values = (asset_id, name, category_id, parent_asset_id, location_code, status, purchase_date, criticality, specifications)
        
        try:
            cursor.execute(query, values)
            conn.commit()
            print(f"✅ SUCCESS: Added Asset {asset_id}", flush=True)
        except Exception as e:
            print(f"❌ SQL ERROR: {e}", flush=True)
        finally:
            conn.close()

    return redirect(url_for('equipment_bp.list_equipment'))

# --- EDIT ASSET ---
@equipment_bp.route('/edit_equipment', methods=['POST'])
def edit_equipment():
    print("--- 🟢 STARTING EDIT ---", flush=True)
    asset_id = request.form.get('asset_id')
    name = request.form.get('name')
    location_code = request.form.get('location_code')
    status = request.form.get('status')
    criticality = request.form.get('criticality')
    specifications = request.form.get('specifications')
    
    conn = db_connector.get_db_connection()
    if conn:
        cursor = conn.cursor()
        query = """
            UPDATE assets 
            SET name=%s, location_code=%s, status=%s, criticality=%s, specifications=%s
            WHERE asset_id=%s
        """
        values = (name, location_code, status, criticality, specifications, asset_id)
        
        try:
            cursor.execute(query, values)
            conn.commit()
            print(f"✅ Updated Asset: {asset_id}", flush=True)
        except Exception as e:
            print(f"❌ Update Error: {e}", flush=True)
        finally:
            conn.close()
            
    return redirect(url_for('equipment_bp.list_equipment'))

# --- ADD CATEGORY ---
import json # Import json at the top of the file

# ... (Keep existing imports and equipment_bp definition)

# --- NEW ROUTE: Get Next Category ID ---
@equipment_bp.route('/get_next_category_id')
def get_next_category_id():
    conn = db_connector.get_db_connection()
    next_id = 1 # Default if table is empty
    if conn:
        try:
            cursor = conn.cursor()
            # Find the highest number currently used
            cursor.execute("SELECT MAX(category_id) FROM asset_categories")
            result = cursor.fetchone()
            if result and result[0] is not None:
                next_id = result[0] + 1
        except Exception as e:
            print(f"❌ Error getting next ID: {e}", flush=True)
        finally:
            conn.close()
            
    # Return the number as simple JSON
    return {'next_id': next_id}

# --- UPDATED: Add Category ---
@equipment_bp.route('/add_category', methods=['POST'])
def add_category():
    print("--- 🟢 STARTING ADD CATEGORY ---", flush=True)
    
    # 1. Get Data
    # Note: We still get category_id from the form, but it's readonly for the user
    category_id = request.form.get('category_id') 
    name = request.form.get('name')
    raw_schema = request.form.get('schema_definition') 

    # 2. Fix JSON for 'jsonb' column
    # The DB requires valid JSON. If the user types plain text, we wrap it.
    schema_definition = "{}" # Default empty JSON
    
    if raw_schema and raw_schema.strip():
        try:
            # Try to see if it's already valid JSON (e.g. {"key": "val"})
            json.loads(raw_schema)
            schema_definition = raw_schema
        except ValueError:
            # If not valid JSON, wrap it as a description string
            schema_definition = json.dumps({"description": raw_schema})

    conn = db_connector.get_db_connection()
    if conn:
        cursor = conn.cursor()
        query = "INSERT INTO asset_categories (category_id, name, schema_definition) VALUES (%s, %s, %s)"
        
        try:
            cursor.execute(query, (category_id, name, schema_definition))
            conn.commit()
            print(f"✅ Added Category: {category_id}", flush=True)
        except Exception as e:
            print(f"❌ Category Error: {e}", flush=True)
        finally:
            conn.close()
            
    return redirect(url_for('equipment_bp.list_equipment'))