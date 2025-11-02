"""Main Flask application for the CRM."""
import firebase_admin
from firebase_admin import credentials, firestore
from flask import Flask, request, jsonify, render_template

# Initialize Flask App
app = Flask(__name__)

# Initialize Firebase Admin SDK
try:
    cred = credentials.Certificate('serviceAccountKey.json')
    firebase_admin.initialize_app(cred)
    print("Firebase Admin SDK initialized successfully.")
except ValueError:
    print("Firebase Admin SDK already initialized.")
except FileNotFoundError:
    print("FATAL ERROR: serviceAccountKey.json not found.")

# Get the firestore client.
db = firestore.client()


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
        data = request.json
        if not data.get('name') or not data.get('email'):
            return jsonify({"error": "Name and email are required"}), 400

        customer_ref = db.collection('customers').document()
        customer_ref.set({
            'name': data.get('name'),
            'email': data.get('email'),
            'phone': data.get('phone', ''),
            'company': data.get('company', ''),
            # This line fixes the E1101 error
            'createdAt': firestore.SERVER_TIMESTAMP # pylint: disable=no-member
        })

        return jsonify({"success": True, "id": customer_ref.id}), 201

    # This line fixes the W0718 error
    except Exception as e: # pylint: disable=broad-except
        return jsonify({"error": str(e)}), 500

@app.route('/api/customers', methods=['GET'])
def get_customers():
    """Gets all customers for dropdowns."""
    try:
        customers = []
        docs = db.collection('customers').stream()
        for doc in docs:
            customer = doc.to_dict()
            customer['id'] = doc.id
            customers.append(customer)
        return jsonify(customers), 200
    # This line fixes the W0718 error
    except Exception as e: # pylint: disable=broad-except
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
