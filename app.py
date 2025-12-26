from flask import Flask, render_template, request, redirect, url_for
import sys
import os
import json
import db_connector
from db_connector import *
app = Flask(__name__)

# --- READ: List Assets & Fetch Categories for Dropdown ---
@app.route('/equipment')
def list_equipment():
    conn = db_connector.get_db_connection()
    items = []
    categories = []
    
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            
            # 1. Fetch Assets + Category Name (JOIN)
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
@app.route('/add_equipment', methods=['POST'])
def add_equipment():
    print("--- 🟢 STARTING ADD EQUIPMENT ---", flush=True)
    
    asset_id = request.form.get('asset_id')
    name = request.form.get('name')
    category_id = request.form.get('category_id') # Comes from the read-only box
    
    parent_asset_id = None 
    
    location_code = request.form.get('location_code')
    status = request.form.get('status')
    purchase_date = request.form.get('purchase_date')
    criticality = request.form.get('criticality')
    specifications = request.form.get('specifications') 

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

    return redirect(url_for('list_equipment'))

# --- EDIT ASSET ---
@app.route('/edit_equipment', methods=['POST'])
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
            
    return redirect(url_for('list_equipment'))

# --- NEW ROUTE: Get Next Category ID ---
@app.route('/get_next_category_id')
def get_next_category_id():
    conn = db_connector.get_db_connection()
    next_id = 1 
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(category_id) FROM asset_categories")
            result = cursor.fetchone()
            if result and result[0] is not None:
                next_id = result[0] + 1
        except Exception as e:
            print(f"❌ Error getting next ID: {e}", flush=True)
        finally:
            conn.close()
            
    return {'next_id': next_id}

# --- UPDATED: Add Category ---
@app.route('/add_category', methods=['POST'])
def add_category():
    print("--- 🟢 STARTING ADD CATEGORY ---", flush=True)
    
    category_id = request.form.get('category_id') 
    name = request.form.get('name')
    raw_schema = request.form.get('schema_definition') 

    schema_definition = "{}"
    
    if raw_schema and raw_schema.strip():
        try:
            json.loads(raw_schema)
            schema_definition = raw_schema
        except ValueError:
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
            
    return redirect(url_for('list_equipment'))


@app.route('/')
def index():
    work_orders, count_open, count_inprogress, count_completed = get_dashboard_data()
    return render_template(
        'index.html', 
        work_orders=work_orders, 
        count_open=count_open,
        count_inprogress=count_inprogress,
        count_completed=count_completed
    )
@app.route('/work-orders')
def work_orders_list():
    # Fetch all WOs from DB
    all_wos = get_all_work_orders()
    return render_template('work_orders_list.html', work_orders=all_wos)


@app.route('/work-order')
@app.route('/work-order/<wo_id>')
def work_order(wo_id='new'):
    # Retrieve details for specific WO
    wo, tasks, assets, users, total_cost = get_work_order_details(wo_id)
    return render_template(
        'work_order.html', 
        wo=wo, 
        tasks=tasks,
        assets=assets, 
        users=users,
        total_cost=total_cost,
        is_new=(wo_id == 'new')
    )
# @app.route('/work-order/add-cost', methods=['POST'])
# def add_cost_route():
#     wo_id = request.form.get('wo_id')
#     description = request.form.get('description')
#     category = request.form.get('category')
#     amount = request.form.get('amount')
#     vendor = request.form.get('vendor')
    
#     # Save to DB
#     add_maintenance_cost(wo_id, description, category, amount, vendor)
    
#     # Reload the page
#     return redirect(url_for('work_order', wo_id=wo_id))

@app.route('/work-order/save', methods=['POST'])
def save_work_order_route():
    wo_id = request.form.get('wo_id')
    status = request.form.get('status')
    priority = request.form.get('priority')
    assigned_user_id = request.form.get('assigned_user_id')
    total_cost = request.form.get('total_cost_hidden')
    # created_at = request.form.get('created_at')
    current_asset_id = request.form.get('current_asset_id')
    execution_data_json = request.form.get('execution_data_hidden') # Retrieve from hidden input
    if wo_id == 'NEW':
        create_work_order(current_asset_id, priority, assigned_user_id, status, execution_data_json, total_cost)
        return redirect(url_for('work_orders_list'))

    else:
        update_work_order(wo_id, status, priority, current_asset_id, assigned_user_id, total_cost, execution_data_json)
        return redirect(url_for('index'))
    
    




if __name__ == '__main__':
    app.run(debug=True)
