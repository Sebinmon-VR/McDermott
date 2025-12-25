# from flask import Flask, render_template

# app = Flask(__name__)

# @app.route('/')
# def index():
#     return render_template('index.html')

# @app.route('/work-order')
# def work_order():   
#     return render_template('work_order.html')


# if __name__ == '__main__':
#     app.run(debug=True)
    
from flask import Flask, render_template, request, redirect, url_for
from db_connector import get_dashboard_data, get_work_order_details, add_maintenance_cost, update_work_order, get_all_work_orders, create_work_order

app = Flask(__name__)

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