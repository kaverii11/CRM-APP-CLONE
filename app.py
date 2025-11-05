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

@app.route('/customers')
def customers_page():
    """Renders the main customer list page."""
    return render_template('customers.html')

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

# --- API Route (NEW - Epic 3.1: Capture new leads) ---
@app.route('/api/lead', methods=['POST'])
def capture_lead():
    """Captures a new lead from a form submission and stores it."""
    try:
        db_conn = get_db()
        if db_conn is None:
            return jsonify({"success": False, "error": "Database connection failed"}), 500
        
        data = request.json
        name = data.get('name')
        email = data.get('email')
        source = data.get('source')
        
        if not name or not email or not source:
            return jsonify({'success': False, 'error': 'Name, email, and source are required'}), 400
        
        lead_data = {
            'name': name,
            'email': email,
            'source': source,
            'status': 'New', # Default status as per Story 3.4 context
            'assigned_to': None, # Placeholder for Story 3.3
            'createdAt': firestore.SERVER_TIMESTAMP # pylint: disable=no-member
        }
        # Store the lead in a separate 'leads' collection
        doc_ref = db_conn.collection('leads').document()
        doc_ref.set(lead_data)
        
        return jsonify({'success': True, 'id': doc_ref.id}), 201
        
    except Exception as e: # pylint: disable=broad-except
        return jsonify({'success': False, 'error': str(e)}), 500
# ... (Previous code including capture_lead function) ...

# --- API Route (NEW - Epic 3.2: Convert lead to opportunity) ---
@app.route('/api/lead/<string:lead_id>/convert', methods=['POST'])
def convert_lead_to_opportunity(lead_id):
    """Converts an existing lead into a sales opportunity."""
    try:
        db_conn = get_db()
        if db_conn is None:
            return jsonify({"success": False, "error": "Database connection failed"}), 500

        lead_ref = db_conn.collection('leads').document(lead_id)
        lead_doc = lead_ref.get()

        if not lead_doc.exists:
            return jsonify({"error": "Lead not found"}), 404
        
        lead_data = lead_doc.to_dict()

        # 1. Update Lead Status
        lead_ref.update({
            'status': 'Converted',
            'convertedAt': firestore.SERVER_TIMESTAMP # pylint: disable=no-member
        })

        # 2. Create Opportunity Record (for tracking pipeline)
        opportunity_data = {
            'lead_id': lead_id,
            'name': lead_data.get('name'),
            'email': lead_data.get('email'),
            'source': lead_data.get('source'),
            'stage': 'Qualification', # Initial stage
            'amount': 0.0, # Placeholder for potential deal size
            'createdAt': firestore.SERVER_TIMESTAMP # pylint: disable=no-member
        }
        opportunity_ref = db_conn.collection('opportunities').document()
        opportunity_ref.set(opportunity_data)

        return jsonify({
            "success": True, 
            "message": f"Lead {lead_id} converted to Opportunity.",
            "opportunity_id": opportunity_ref.id
        }), 200

    except Exception as e: # pylint: disable=broad-except
        return jsonify({'success': False, 'error': str(e)}), 500
# app.py (Modified capture_lead function)


@app.route('/api/lead/<string:lead_id>/assign', methods=['PUT'])
def assign_lead(lead_id):
    """Assigns an existing lead to a specified sales representative."""
    try:
        db_conn = get_db()
        if db_conn is None:
            return jsonify({"success": False, "error": "Database connection failed"}), 500

        data = request.json
        rep_id = data.get('rep_id')
        rep_name = data.get('rep_name', 'Unspecified')

        if not rep_id:
            return jsonify({"error": "Sales rep ID (rep_id) is required for assignment"}), 400

        lead_ref = db_conn.collection('leads').document(lead_id)
        
        # Check if the lead exists
        if not lead_ref.get().exists:
            return jsonify({"error": "Lead not found"}), 404
        
        # Update the lead document
        lead_ref.update({
            'assigned_to_id': rep_id,
            'assigned_to_name': rep_name,
            'assignedAt': firestore.SERVER_TIMESTAMP # pylint: disable=no-member
        })

        return jsonify({
            "success": True, 
            "message": f"Lead {lead_id} assigned to {rep_name} ({rep_id})"
        }), 200

    except Exception as e: # pylint: disable=broad-except
        print(f"Error in assign_lead: {e}") # Debugging line
        return jsonify({'success': False, 'error': str(e)}), 500
# --- API Route (NEW - Epic 3.4: Track opportunity status) ---
@app.route('/api/opportunity/<string:opportunity_id>/status', methods=['PUT'])
def update_opportunity_status(opportunity_id):
    """Updates the stage/status of an existing sales opportunity."""
    ALLOWED_STAGES = ['Qualification', 'Proposal', 'Negotiation', 'Won', 'Lost']

    try:
        db_conn = get_db()
        if db_conn is None:
            return jsonify({"success": False, "error": "Database connection failed"}), 500

        data = request.json
        new_stage = data.get('stage')

        if not new_stage:
            return jsonify({"error": "Stage is required in the request body"}), 400
        
        if new_stage not in ALLOWED_STAGES:
            return jsonify({
                "error": "Invalid stage provided.",
                "valid_stages": ALLOWED_STAGES
            }), 400

        opportunity_ref = db_conn.collection('opportunities').document(opportunity_id)
        
        # Check if the opportunity exists
        if not opportunity_ref.get().exists:
            return jsonify({"error": "Opportunity not found"}), 404
        
        # Update the stage
        update_data = {
            'stage': new_stage,
            'updatedAt': firestore.SERVER_TIMESTAMP # pylint: disable=no-member
        }
        
        # If the stage is 'Won' or 'Lost', record the completion timestamp
        if new_stage in ['Won', 'Lost']:
            update_data['closedAt'] = firestore.SERVER_TIMESTAMP # pylint: disable=no-member
        
        opportunity_ref.update(update_data)

        return jsonify({
            "success": True, 
            "message": f"Opportunity {opportunity_id} status updated to {new_stage}"
        }), 200

    except Exception as e: # pylint: disable=broad-except
        print(f"Error in update_opportunity_status: {e}") # Debugging line
        return jsonify({'success': False, 'error': str(e)}), 500
# ... (End of app.py) ...
# ... (after convert_lead_to_opportunity) ...
if __name__ == "__main__":
    app.run()
