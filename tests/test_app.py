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
    # We patch get_db to raise a generic Exception
    with patch('app.get_db', side_effect=Exception("Simulated database crash")):
        
        customer_data = {'name': 'Test User', 'email': 'test@example.com'}
        response = client.post('/api/customer', json=customer_data)
        
        assert response.status_code == 500
        assert "Simulated database crash" in response.json['error']

# Test 7: Test get_customers endpoint for 500 error
def test_get_customers_500_error(client):
    """Test the get_customers function for a generic 500 error."""
    # We patch get_db to raise a generic Exception
    with patch('app.get_db', side_effect=Exception("Simulated database crash")):
        
        response = client.get('/api/customers')
        
        assert response.status_code == 500
        assert "Simulated database crash" in response.json['error']

# Test 8: Test get_db for FileNotFoundError
def test_get_db_file_not_found_error(client):
    """Test the get_db function for a FileNotFoundError."""
    
    # We must reset the app.db global to None for this test
    # And mock the two firebase functions that will be called
    with patch('app.db', None), \
         patch('firebase_admin.credentials.Certificate', side_effect=FileNotFoundError("File not found")), \
         patch('firebase_admin.initialize_app'): # Mock initialize_app to do nothing

        # Make a request. The get_db() will be called, print an error,
        # but the app won't crash, and the 500 error handler will take over.
        response = client.get('/api/customers')
        
        assert response.status_code == 500