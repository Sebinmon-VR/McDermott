# from flask import Flask, render_template

# # Import the Blueprint from the routes folder
# from routes.equipment import equipment_bp

# app = Flask(__name__)

# # Register the Blueprint so the app knows about the equipment routes
# app.register_blueprint(equipment_bp)

# # The Homepage route stays here
# @app.route('/')
# def index():
#     return render_template('index.html')

# if __name__ == '__main__':
#     app.run(debug=True)


from flask import Flask, render_template, redirect, url_for # <-- Added imports
from routes.equipment import equipment_bp

app = Flask(__name__)
app.register_blueprint(equipment_bp)

@app.route('/')
def index():
    # DIRECTLY SEND USER TO EQUIPMENT PAGE
    return redirect(url_for('equipment_bp.list_equipment'))

if __name__ == '__main__':
    app.run(debug=True)