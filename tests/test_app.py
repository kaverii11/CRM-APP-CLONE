import json
import pytest
from app import app
from unittest.mock import MagicMock, patch

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
