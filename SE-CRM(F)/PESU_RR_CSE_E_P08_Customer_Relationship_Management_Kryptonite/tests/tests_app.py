import json
import pytest
from app import app
from unittest.mock import MagicMock, patch
from firebase_admin import firestore
# Initialize Flask App
@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

# Test 1: Test customer creation SUCCESS
def test_create_customer_success(client):
    """Test the create_customer function succeeds."""
    mock_db = MagicMock()
    mock_ref = MagicMock()
    mock_ref.id = "new-cust-123"
    mock_db.collection.return_value.document.return_value = mock_ref
    
    with patch('app.get_db', return_value=mock_db):
        customer_data = {'name': 'Test User', 'email': 'test@example.com'}
        response = client.post('/api/customer', json=customer_data)
        
        assert response.status_code == 201
        assert response.json['success'] is True
        assert response.json['id'] == "new-cust-123"

# Test 2: Test customer creation FAILURE (missing name)
def test_create_customer_missing_name(client):
    """Test the create_customer function fails validation."""
    mock_db = MagicMock()
    with patch('app.get_db', return_value=mock_db):
        customer_data = {'email': 'test@example.com'}
        response = client.post('/api/customer', json=customer_data)
    
        assert response.status_code == 400
        assert 'Name and email are required' in response.json['error']

# Test 3: Test get_customers SUCCESS
def test_get_customers_success(client):
    """Test the get_customers function succeeds."""
    mock_db = MagicMock()
    mock_doc1 = MagicMock()
    mock_doc1.id = "cust_1"
    mock_doc1.to_dict.return_value = {'name': 'Customer A'}
    mock_doc2 = MagicMock()
    mock_doc2.id = "cust_2"
    mock_doc2.to_dict.return_value = {'name': 'Customer B'}
    mock_stream = [mock_doc1, mock_doc2]
    mock_db.collection.return_value.stream.return_value = mock_stream

    with patch('app.get_db', return_value=mock_db):
        response = client.get('/api/customers')
        
        assert response.status_code == 200
        assert len(response.json) == 2
        assert response.json[0]['name'] == 'Customer A'

# Test 4: Test the dashboard route (/)
def test_dashboard_route(client):
    """Test that the dashboard page loads."""
    response = client.get('/')
    assert response.status_code == 200
    assert response.content_type == 'text/html; charset=utf-8'

# Test 5: Test the login route (/login)
def test_login_route(client):
    """Test that the login page loads."""
    response = client.get('/login')
    assert response.status_code == 200
    assert response.content_type == 'text/html; charset=utf-8'

# Test 6: Test create_customer endpoint for 500 error
def test_create_customer_500_error(client):
    """Test the create_customer function for a generic 500 error."""
    # This is where the bug was. customer_data must be defined.
    customer_data = {'name': 'Test User', 'email': 'test@example.com'}
    
    with patch('app.get_db', side_effect=Exception("Simulated database crash")):
        
        response = client.post('/api/customer', json=customer_data)
        
        assert response.status_code == 500
        assert "Simulated database crash" in response.json['error']

# Test 7: Test get_customers endpoint for 500 error
def test_get_customers_500_error(client):
    """Test the get_customers function for a generic 500 error."""
    with patch('app.get_db', side_effect=Exception("Simulated database crash")):
        
        response = client.get('/api/customers')
        
        assert response.status_code == 500
        assert "Simulated database crash" in response.json['error']

# Test 8: Test get_db for FileNotFoundError
def test_get_db_file_not_found_error(client):
    """Test the get_db function for a FileNotFoundError."""
    
    # We mock get_db to return None, which is what our app.py now does
    with patch('app.get_db', return_value=None):
        
        response = client.get('/api/customers')
        
        # The app should now correctly return a 500 error
        assert response.status_code == 500
        assert "Database connection failed" in response.json['error']

# Add these new tests to the end of tests/test_app.py

def test_get_customer_details_success(client):
    """Test getting a single customer's details."""
    mock_db = MagicMock()
    mock_doc = MagicMock()
    mock_doc.exists = True
    mock_doc.to_dict.return_value = {"name": "Test User", "email": "test@example.com"}
    
    # This line mocks the .get() call
    mock_db.collection.return_value.document.return_value.get.return_value = mock_doc
    
    with patch('app.get_db', return_value=mock_db):
        response = client.get('/api/customer/some-id')
        
        assert response.status_code == 200
        assert response.json['name'] == "Test User"

def test_get_customer_details_not_found(client):
    """Test getting a customer that does not exist."""
    mock_db = MagicMock()
    mock_doc = MagicMock()
    mock_doc.exists = False # Simulate a customer not being found
    
    mock_db.collection.return_value.document.return_value.get.return_value = mock_doc
    
    with patch('app.get_db', return_value=mock_db):
        response = client.get('/api/customer/some-id')
        
        assert response.status_code == 404
        assert "Customer not found" in response.json['error']
        
# Add these new tests to the end of tests/test_app.py

def test_update_customer_success(client):
    """Test updating a customer's details."""
    mock_db = MagicMock()
    mock_doc = MagicMock()
    mock_doc.exists = True # Make the document exist
    
    # Mock the .get() call
    mock_db.collection.return_value.document.return_value.get.return_value = mock_doc
    
    with patch('app.get_db', return_value=mock_db):
        update_data = {"name": "New Name", "phone": "123456"}
        response = client.put('/api/customer/some-id', json=update_data)
        
        assert response.status_code == 200
        assert response.json['success'] is True

def test_update_customer_not_found(client):
    """Test updating a customer that does not exist."""
    mock_db = MagicMock()
    mock_doc = MagicMock()
    mock_doc.exists = False # Make the document NOT exist
    
    mock_db.collection.return_value.document.return_value.get.return_value = mock_doc
    
    with patch('app.get_db', return_value=mock_db):
        update_data = {"name": "New Name"}
        response = client.put('/api/customer/some-id', json=update_data)
        
        assert response.status_code == 404
        assert "Customer not found" in response.json['error']

def test_update_customer_bad_request(client):
    """Test updating a customer with no data."""
    mock_db = MagicMock() # This test shouldn't even reach the db
    
    with patch('app.get_db', return_value=mock_db):
        # Send an empty JSON object
        response = client.put('/api/customer/some-id', json={})
        
        assert response.status_code == 400
        assert "No update data provided" in response.json['error']

# Add these new tests to the end of tests/test_app.py

def test_delete_customer_success(client):
    """Test deleting a customer successfully."""
    mock_db = MagicMock()
    mock_doc = MagicMock()
    mock_doc.exists = True # Make the document exist
    
    # Mock the .get() call
    mock_db.collection.return_value.document.return_value.get.return_value = mock_doc
    
    with patch('app.get_db', return_value=mock_db):
        response = client.delete('/api/customer/some-id')
        
        assert response.status_code == 200
        assert response.json['success'] is True

def test_delete_customer_not_found(client):
    """Test deleting a customer that does not exist."""
    mock_db = MagicMock()
    mock_doc = MagicMock()
    mock_doc.exists = False # Make the document NOT exist
    
    mock_db.collection.return_value.document.return_value.get.return_value = mock_doc
    
    with patch('app.get_db', return_value=mock_db):
        response = client.delete('/api/customer/some-id')
        
        assert response.status_code == 404
        assert "Customer not found" in response.json['error']
# --- Tests for Epic 3.1: Capture new leads ---

def test_capture_lead_success(client):
    """Test the capture_lead function succeeds."""
    mock_db = MagicMock()
    mock_ref = MagicMock()
    mock_ref.id = "new-lead-456"
    # Note: Use document().set() in app.py, so we mock the doc reference
    mock_db.collection.return_value.document.return_value = mock_ref 

    with patch('app.get_db', return_value=mock_db):
        lead_data = {'name': 'Test Lead', 'email': 'lead@example.com', 'source': 'Web Form'}
        response = client.post('/api/lead', json=lead_data)

        assert response.status_code == 201
        assert response.json['success'] is True
        assert response.json['id'] == "new-lead-456"
        
def test_capture_lead_missing_data(client):
    """Test the capture_lead function fails validation."""
    mock_db = MagicMock()
    with patch('app.get_db', return_value=mock_db):
        # Missing 'source'
        lead_data = {'name': 'Test Lead', 'email': 'lead@example.com'}
        response = client.post('/api/lead', json=lead_data)
    
        assert response.status_code == 400
        assert 'Name, email, and source are required' in response.json['error']

def test_capture_lead_500_error(client):
    """Test the capture_lead function for a generic 500 error."""
    lead_data = {'name': 'Test Lead', 'email': 'lead@example.com', 'source': 'Web Form'}
    
    with patch('app.get_db', side_effect=Exception("Simulated lead database crash")):
        
        response = client.post('/api/lead', json=lead_data)
        
        assert response.status_code == 500
        assert "Simulated lead database crash" in response.json['error']
# --- Tests for Epic 3.2: Convert lead to opportunity ---

def test_convert_lead_success(client):
    """Test the convert_lead_to_opportunity function succeeds."""
    # Use from unittest.mock import MagicMock, patch if needed here, but it's already imported at the top
    mock_db = MagicMock()

    # Mock the existing lead document
    mock_lead_doc = MagicMock()
    mock_lead_doc.exists = True
    mock_lead_doc.to_dict.return_value = {
        'name': 'Convert Lead',
        'email': 'convert@example.com',
        'source': 'Web Form',
        'status': 'New'
    }

    # Mock Firestore document references
    lead_ref_mock = MagicMock(id='lead-to-convert', get=lambda: mock_lead_doc, update=MagicMock())
    opp_ref_mock = MagicMock(id='new-opp-789', set=MagicMock())

    # Simulate multiple .document() calls dynamically
    def document_side_effect(doc_id=None):
        if doc_id == 'lead-to-convert':
            return lead_ref_mock
        else:
            return opp_ref_mock

    mock_db.collection.return_value.document.side_effect = document_side_effect

    with patch('app.get_db', return_value=mock_db):
        response = client.post('/api/lead/lead-to-convert/convert')

        assert response.status_code == 200
        assert response.json['success'] is True
        assert "converted" in response.json['message']
        assert response.json['opportunity_id'] == "new-opp-789"

        # Verify the lead was updated with the correct fields
        lead_ref_mock.update.assert_called_once_with({
            'status': 'Converted',
            'convertedAt': firestore.SERVER_TIMESTAMP 
        })
        opp_ref_mock.set.assert_called_once()


def test_convert_lead_not_found(client):
    """Test the convert_lead_to_opportunity function fails if lead is missing."""
    mock_db = MagicMock()
    mock_lead_doc = MagicMock()
    mock_lead_doc.exists = False
    mock_db.collection.return_value.document.return_value.get.return_value = mock_lead_doc
    
    with patch('app.get_db', return_value=mock_db):
        response = client.post('/api/lead/non-existent-lead/convert')
        
        assert response.status_code == 404
        assert 'Lead not found' in response.json['error']

def test_convert_lead_500_error(client):
    """Test the convert_lead_to_opportunity function for a generic 500 error."""
    with patch('app.get_db', side_effect=Exception("Simulated conversion crash")):
        response = client.post('/api/lead/any-id/convert')
        
        assert response.status_code == 500
        assert "Simulated conversion crash" in response.json['error']
# --- Tests for Epic 3.3: Assign lead to sales rep ---

def test_assign_lead_success(client):
    """Test the assign_lead function succeeds."""
    mock_db = MagicMock()
    mock_lead_doc = MagicMock()
    mock_lead_doc.exists = True
    mock_db.collection.return_value.document.return_value.get.return_value = mock_lead_doc
    
    with patch('app.get_db', return_value=mock_db):
        assignment_data = {'rep_id': 'sales-rep-1', 'rep_name': 'Alice Smith'}
        response = client.put('/api/lead/lead-to-assign/assign', json=assignment_data)
        
        assert response.status_code == 200
        assert response.json['success'] is True
        assert "assigned to Alice Smith" in response.json['message']
        
        # Verify the lead was updated with the correct data
        mock_db.collection.return_value.document.return_value.update.assert_called_once_with({
            'assigned_to_id': 'sales-rep-1',
            'assigned_to_name': 'Alice Smith',
            'assignedAt': firestore.SERVER_TIMESTAMP 
        })
        
def test_assign_lead_missing_rep_id(client):
    """Test the assign_lead function fails if rep_id is missing."""
    mock_db = MagicMock()
    
    with patch('app.get_db', return_value=mock_db):
        assignment_data = {'rep_name': 'Alice Smith'} 
        response = client.put('/api/lead/lead-to-assign/assign', json=assignment_data)
    
        assert response.status_code == 400
        assert 'Sales rep ID (rep_id) is required' in response.json['error']

def test_assign_lead_not_found(client):
    """Test the assign_lead function fails if lead is missing."""
    mock_db = MagicMock()
    mock_lead_doc = MagicMock()
    mock_lead_doc.exists = False
    mock_db.collection.return_value.document.return_value.get.return_value = mock_lead_doc
    
    with patch('app.get_db', return_value=mock_db):
        assignment_data = {'rep_id': 'sales-rep-1'}
        response = client.put('/api/lead/non-existent-lead/assign', json=assignment_data)
        
        assert response.status_code == 404
        assert 'Lead not found' in response.json['error']
# --- Tests for Epic 3.4: Track opportunity status (Open, Won, Lost) ---

def test_update_opportunity_status_success(client):
    """Test updating the status of an opportunity to a valid stage."""
    mock_db = MagicMock()
    mock_opp_doc = MagicMock()
    mock_opp_doc.exists = True
    mock_db.collection.return_value.document.return_value.get.return_value = mock_opp_doc
    
    with patch('app.get_db', return_value=mock_db):
        update_data = {'stage': 'Negotiation'}
        response = client.put('/api/opportunity/opp-123/status', json=update_data)
        
        assert response.status_code == 200
        assert response.json['success'] is True
        assert "Negotiation" in response.json['message']
        
        # Verify the update call includes the stage and updated timestamp
        mock_db.collection.return_value.document.return_value.update.assert_called_once_with({
            'stage': 'Negotiation',
            'updatedAt': firestore.SERVER_TIMESTAMP 
        })

def test_update_opportunity_status_won_closure(client):
    """Test updating the status to 'Won' includes the closedAt timestamp."""
    mock_db = MagicMock()
    mock_opp_doc = MagicMock()
    mock_opp_doc.exists = True
    mock_db.collection.return_value.document.return_value.get.return_value = mock_opp_doc
    
    with patch('app.get_db', return_value=mock_db):
        update_data = {'stage': 'Won'}
        client.put('/api/opportunity/opp-123/status', json=update_data)
        
        # Verify the update call includes both the stage and closedAt timestamp
        mock_db.collection.return_value.document.return_value.update.assert_called_once_with({
            'stage': 'Won',
            'updatedAt': firestore.SERVER_TIMESTAMP,
            'closedAt': firestore.SERVER_TIMESTAMP 
        })

def test_update_opportunity_status_invalid(client):
    """Test updating the status with an invalid stage fails with 400."""
    mock_db = MagicMock() 
    
    with patch('app.get_db', return_value=mock_db):
        update_data = {'stage': 'Black Hole'}
        response = client.put('/api/opportunity/opp-123/status', json=update_data)
        
        assert response.status_code == 400
        assert 'Invalid stage provided' in response.json['error']

def test_update_opportunity_status_not_found(client):
    """Test updating the status fails if the opportunity is missing."""
    mock_db = MagicMock()
    mock_opp_doc = MagicMock()
    mock_opp_doc.exists = False
    mock_db.collection.return_value.document.return_value.get.return_value = mock_opp_doc
    
    with patch('app.get_db', return_value=mock_db):
        update_data = {'stage': 'Lost'}
        response = client.put('/api/opportunity/non-existent-opp/status', json=update_data)
        
        assert response.status_code == 404
        assert 'Opportunity not found' in response.json['error']