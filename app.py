"""Main Flask application for the CRM."""
import firebase_admin
from firebase_admin import credentials, firestore
from flask import Flask, request, jsonify, render_template

# Initialize Flask App
app = Flask(__name__)

# --- Firebase Initialization ---
db = None

def get_db():
    """
    Returns a Firestore client, initializing the app if necessary.
    """
    global db
    if db is None:
        try:
            cred = credentials.Certificate('serviceAccountKey.json')
            firebase_admin.initialize_app(cred)
            print("Firebase Admin SDK initialized successfully.")
        except ValueError:
            print("Firebase Admin SDK already initialized.")
        except FileNotFoundError:
            print("FATAL ERROR: serviceAccountKey.json not found in runtime.")
            # Return None to signal a failure
            return None
        db = firestore.client()
    return db

# --- HTML Rendering Routes ---
@app.route('/')
def dashboard():
    """Renders the main dashboard page."""
    return render_template('index.html')

@app.route('/login')
def login_page():
    """Renders the login page."""
    return render_template('login.html')

# --- API Routes (Epic 2: Customer CRUD) ---
@app.route('/api/customer', methods=['POST'])
def create_customer():
    """Creates a new customer in the database."""
    try:
        db_conn = get_db()
        if db_conn is None:
            return jsonify({"error": "Database connection failed"}), 500
        data = request.json
        if not data.get('name') or not data.get('email'):
            return jsonify({"error": "Name and email are required"}), 400

        customer_ref = db_conn.collection('customers').document()
        customer_ref.set({
            'name': data.get('name'),
            'email': data.get('email'),
            'phone': data.get('phone', ''),
            'company': data.get('company', ''),
            'createdAt': firestore.SERVER_TIMESTAMP # pylint: disable=no-member
        })

        return jsonify({"success": True, "id": customer_ref.id}), 201

    except Exception as e: # pylint: disable=broad-except
        return jsonify({"error": str(e)}), 500

@app.route('/api/customers', methods=['GET'])
def get_customers():
    """Gets all customers for dropdowns."""
    try:
        db_conn = get_db()
        if db_conn is None:
            return jsonify({"error": "Database connection failed"}), 500
        customers = []
        docs = db_conn.collection('customers').stream()
        for doc in docs:
            customer = doc.to_dict()
            customer['id'] = doc.id
            customers.append(customer)
        return jsonify(customers), 200
    except Exception as e: # pylint: disable=broad-except
        return jsonify({"error": str(e)}), 500
# Add this new route to app.py

@app.route('/api/customer/<string:customer_id>', methods=['GET'])
def get_customer_details(customer_id):
    """Gets a single customer's details by their ID."""
    try:
        db_conn = get_db()
        if db_conn is None:
            return jsonify({"error": "Database connection failed"}), 500
        customer_ref = db_conn.collection('customers').document(customer_id)
        customer = customer_ref.get()
        if not customer.exists:
            return jsonify({"error": "Customer not found"}), 404
        return jsonify(customer.to_dict()), 200

    except Exception as e: # pylint: disable=broad-except
        return jsonify({"error": str(e)}), 500
    
# Add this new route to app.py

@app.route('/api/customer/<string:customer_id>', methods=['PUT'])
def update_customer_details(customer_id):
    """Updates a customer's details by their ID."""
    try:
        db_conn = get_db()
        if db_conn is None:
            return jsonify({"error": "Database connection failed"}), 500

        data = request.json
        # Basic validation: ensure they are sending at least one field to update
        if not data or ('name' not in data and 'email' not in data and 'phone' not in data):
            return jsonify({"error": "No update data provided"}), 400

        customer_ref = db_conn.collection('customers').document(customer_id)
        # Check if customer exists before trying to update
        if not customer_ref.get().exists:
            return jsonify({"error": "Customer not found"}), 404
        
        # Update the customer document
        # 'merge=True' ensures we only update fields that are sent
        customer_ref.set(data, merge=True)
        
        return jsonify({"success": True, "id": customer_id}), 200

    except Exception as e: # pylint: disable=broad-except
        return jsonify({"error": str(e)}), 500
    
# Add this new route to app.py

@app.route('/api/customer/<string:customer_id>', methods=['DELETE'])
def delete_customer(customer_id):
    """Deletes a customer by their ID."""
    try:
        db_conn = get_db()
        if db_conn is None:
            return jsonify({"error": "Database connection failed"}), 500

        customer_ref = db_conn.collection('customers').document(customer_id)
        # Check if customer exists before trying to delete
        if not customer_ref.get().exists:
            return jsonify({"error": "Customer not found"}), 404
        # Delete the customer document
        customer_ref.delete()
        return jsonify({"success": True, "id": customer_id}), 200

    except Exception as e: # pylint: disable=broad-except
        return jsonify({"error": str(e)}), 500
if __name__ == '__main__':
    app.run()
