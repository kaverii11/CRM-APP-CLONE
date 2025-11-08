"""Main Flask application for the CRM."""
import logging
import sys
from datetime import datetime, timedelta, timezone
import firebase_admin
from datetime import datetime, timedelta, timezone
from firebase_admin import credentials, firestore
from flask import Flask, request, jsonify, render_template

# --- Logging Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

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
            logger.info("Firebase Admin SDK initialized successfully.")
        except ValueError:
            logger.info("Firebase Admin SDK already initialized.")
        except FileNotFoundError:
            logger.error("FATAL ERROR: serviceAccountKey.json not found in runtime.")
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

# ... (all your existing imports like Flask, logger, datetime, firestore, etc.)
@app.route('/api/tickets', methods=['POST'])
def create_support_ticket():
    """
    Logs a new support ticket from a customer.
    Corresponds to Story CCRM-63.
    """
    try:
        db_conn = get_db()
        if db_conn is None:
            return jsonify({"error": "Database connection failed"}), 500
        data = request.get_json()

        # Basic validation
        if not data or 'customer_id' not in data or 'issue' not in data:
            customer_for_log = data.get('customer_id', 'Unknown') if isinstance(data, dict) else 'Unknown'
            logger.warning(
                "Failed ticket creation: Missing required fields. Customer: %s",
                customer_for_log
            )
            return jsonify({"error": "Missing required fields: customer_id, issue"}), 400

        now_utc = datetime.now(timezone.utc)
        ticket_data = {
            "customer_id": data['customer_id'],
            "issue": data['issue'],
            "status": "Open",
            "priority": data.get("priority", "Medium"), # Default priority
            "created_at": firestore.SERVER_TIMESTAMP, # Use Firestore server timestamp
            "sla_deadline": (now_utc + timedelta(hours=24)).isoformat() # Story CCRM-695
        }

        # Create ticket document
        ticket_ref = db_conn.collection('tickets').document()
        ticket_ref.set(ticket_data)

        logger.info(
            "New support ticket created. TicketID: %s, CustomerID: %s",
            ticket_ref.id,
            ticket_data['customer_id']
        )

        # Return ticket info including generated ID
        response_ticket = {
            "ticket_id": ticket_ref.id,
            "customer_id": ticket_data['customer_id'],
            "issue": ticket_data['issue'],
            "status": ticket_data['status'],
            "priority": ticket_data['priority'],
            "created_at": now_utc.isoformat(), # For immediate feedback; actual in DB is server timestamp
            "sla_deadline": ticket_data['sla_deadline']
        }
        return jsonify(response_ticket), 201
    except Exception as e: # pylint: disable=broad-except
        logger.error("Error creating support ticket: %s", str(e))
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run()