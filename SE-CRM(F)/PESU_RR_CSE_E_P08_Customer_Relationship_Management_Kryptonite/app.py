"""Main Flask application for the CRM."""
import logging
import sys
from datetime import datetime, timedelta, timezone
import random
import string
from functools import lru_cache
import firebase_admin
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


@lru_cache(maxsize=1)
def get_db():
    """
    Returns a Firestore client, initializing the app if necessary.
    """
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
    return firestore.client()


def generate_referral_code(name=""):
    """Generates a simple, human-readable referral code."""
    prefix = name.upper().replace(" ", "")[:5] or "CRM"
    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"{prefix}-{suffix}"

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
    """Creates a new customer AND their loyalty profile."""
    try:
        db_conn = get_db()
        if db_conn is None:
            return jsonify({"error": "Database connection failed"}), 500
        data = request.json
        if not data.get('name') or not data.get('email'):
            return jsonify({"error": "Name and email are required"}), 400

        customer_ref = db_conn.collection('customers').document()
        customer_data = {
            'name': data.get('name'),
            'email': data.get('email'),
            'phone': data.get('phone', ''),
            'company': data.get('company', ''),
            'createdAt': firestore.SERVER_TIMESTAMP # pylint: disable=no-member
        }
        customer_ref.set(customer_data)

        referral_code = generate_referral_code(customer_data['name'])
        loyalty_ref = db_conn.collection('loyalty_profiles').document(customer_ref.id)
        loyalty_ref.set({
            'customer_id': customer_ref.id,
            'points': 0,
            'tier': 'Bronze',
            'referral_code': referral_code,
            'createdAt': firestore.SERVER_TIMESTAMP # pylint: disable=no-member
        })

        customer_ref.update({'loyalty_profile_id': loyalty_ref.id})

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

        if not lead_ref.get().exists:
            return jsonify({"error": "Lead not found"}), 404

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
        logger.exception("Error in assign_lead: %s", e)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/opportunity/<string:opportunity_id>/status', methods=['PUT'])
def update_opportunity_status(opportunity_id):
    """Updates the stage/status of an existing sales opportunity."""
    allowed_stages = ['Qualification', 'Proposal', 'Negotiation', 'Won', 'Lost']

    try:
        db_conn = get_db()
        if db_conn is None:
            return jsonify({"success": False, "error": "Database connection failed"}), 500

        data = request.json
        new_stage = data.get('stage')

        if not new_stage:
            return jsonify({"error": "Stage is required in the request body"}), 400

        if new_stage not in allowed_stages:
            return jsonify({
                "error": "Invalid stage provided.",
                "valid_stages": allowed_stages
            }), 400

        opportunity_ref = db_conn.collection('opportunities').document(opportunity_id)

        if not opportunity_ref.get().exists:
            return jsonify({"error": "Opportunity not found"}), 404

        update_data = {
            'stage': new_stage,
            'updatedAt': firestore.SERVER_TIMESTAMP # pylint: disable=no-member
        }

        if new_stage in ['Won', 'Lost']:
            update_data['closedAt'] = firestore.SERVER_TIMESTAMP # pylint: disable=no-member

        opportunity_ref.update(update_data)

        return jsonify({
            "success": True,
            "message": f"Opportunity {opportunity_id} status updated to {new_stage}"
        }), 200

    except Exception as e: # pylint: disable=broad-except
        logger.exception("Error in update_opportunity_status: %s", e)
        return jsonify({'success': False, 'error': str(e)}), 500


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
            customer_for_log = 'Unknown'
            if isinstance(data, dict):
                customer_for_log = data.get('customer_id', 'Unknown')
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
            "created_at": firestore.SERVER_TIMESTAMP, # Use Firestore server timestamp  # pylint: disable=no-member
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
            "created_at": now_utc.isoformat(), # Immediate feedback; DB stores server timestamp
            "sla_deadline": ticket_data['sla_deadline']
        }
        return jsonify(response_ticket), 201
    except Exception as e: # pylint: disable=broad-except
        logger.error("Error creating support ticket: %s", str(e))
        return jsonify({"error": str(e)}), 500


# --- API Routes (NEW - Epic 5: Loyalty Program) ---
TIER_LEVELS = {
    "Bronze": 0,
    "Silver": 500,
    "Gold": 2000
}


@app.route('/api/loyalty/<string:customer_id>', methods=['GET'])
def get_loyalty_profile(customer_id):
    """Gets the loyalty profile for a specific customer."""
    try:
        db_conn = get_db()
        if db_conn is None:
            return jsonify({"error": "Database connection failed"}), 500

        loyalty_ref = db_conn.collection('loyalty_profiles').document(customer_id)
        profile_doc = loyalty_ref.get()

        if not profile_doc.exists:
            return jsonify({"error": "Loyalty profile not found"}), 404

        return jsonify(profile_doc.to_dict()), 200

    except Exception as e: # pylint: disable=broad-except
        return jsonify({"error": str(e)}), 500


@app.route('/api/loyalty/<string:customer_id>/redeem', methods=['POST'])
def redeem_points(customer_id):
    """
    Redeems points for a reward.
    Assumes request body: { "points_to_redeem": 100 }
    """
    try:
        db_conn = get_db()
        if db_conn is None:
            return jsonify({"error": "Database connection failed"}), 500

        data = request.json
        points_to_redeem = data.get('points_to_redeem')

        if not isinstance(points_to_redeem, int) or points_to_redeem <= 0:
            return jsonify({"error": "Invalid points_to_redeem"}), 400

        loyalty_ref = db_conn.collection('loyalty_profiles').document(customer_id)
        profile_doc = loyalty_ref.get()

        if not profile_doc.exists:
            return jsonify({"error": "Profile not found"}), 404

        current_points = profile_doc.to_dict().get('points', 0)

        if current_points < points_to_redeem:
            return jsonify({"error": "Not enough points"}), 400

        loyalty_ref.update({
            'points': firestore.Increment(-points_to_redeem) # pylint: disable=no-member
        })

        return jsonify({
            "message": "Redemption successful",
            "new_points_balance": current_points - points_to_redeem
        }), 200

    except Exception as e: # pylint: disable=broad-except
        return jsonify({"error": str(e)}), 500


@app.route('/api/loyalty/<string:customer_id>/use-referral', methods=['POST'])
def use_referral_code(customer_id):
    """
    Applies a referral code for a new customer.
    The customer_id in the URL is the *new user* using the code.
    The referrer (code owner) gets points.

    Assumes request body: { "referral_code": "KAVERI-A4B8" }
    """
    try:
        db_conn = get_db()
        if db_conn is None:
            return jsonify({"error": "Database connection failed"}), 500

        data = request.json
        code_used = data.get('referral_code')
        if not code_used:
            return jsonify({"error": "Referral code required"}), 400

        query = (
            db_conn.collection('loyalty_profiles')
            .where('referral_code', '==', code_used)
            .limit(1)
        )
        referrers = list(query.stream())

        if not referrers:
            return jsonify({"error": "Invalid referral code"}), 404

        referrer_doc = referrers[0]
        referrer_id = referrer_doc.id

        if referrer_id == customer_id:
            return jsonify({"error": "Cannot refer yourself"}), 400

        referral_bonus = 100

        referrer_ref = db_conn.collection('loyalty_profiles').document(referrer_id)
        referrer_ref.update({
            'points': firestore.Increment(referral_bonus) # pylint: disable=no-member
        })

        return jsonify({
            "message": f"Referral successful! User {referrer_id} earned {referral_bonus} points."
        }), 200

    except Exception as e: # pylint: disable=broad-except
        return jsonify({"error": str(e)}), 500


def add_points_on_purchase(db_conn, customer_id, purchase_amount):
    """
    Service function to add points and check for tier upgrades.
    Called by the Payment service.
    """
    try:
        loyalty_ref = db_conn.collection('loyalty_profiles').document(customer_id)

        points_earned = int(purchase_amount)

        loyalty_ref.update({
            'points': firestore.Increment(points_earned) # pylint: disable=no-member
        })

        profile_doc = loyalty_ref.get()
        if not profile_doc.exists:
            return None

        profile_data = profile_doc.to_dict()
        current_points = profile_data.get('points', 0)
        current_tier = profile_data.get('tier', 'Bronze')
        new_tier = current_tier

        if current_points >= TIER_LEVELS["Gold"]:
            new_tier = "Gold"
        elif current_points >= TIER_LEVELS["Silver"]:
            new_tier = "Silver"

        if new_tier != current_tier:
            loyalty_ref.update({'tier': new_tier})
            logger.info("Tier Upgrade! Customer %s is now %s.", customer_id, new_tier)

        return {"points_earned": points_earned, "new_tier": new_tier}

    except Exception as e: # pylint: disable=broad-except
        logger.error("Error in add_points_on_purchase for %s: %s", customer_id, e)
        return None

if __name__ == "__main__":
    app.run()
