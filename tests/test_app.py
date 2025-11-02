import json
import pytest
from app import app
from unittest.mock import MagicMock, patch

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

# Test for Epic 2: Create Customer (Success)
def test_create_customer_success(client):
    with patch('app.db') as mock_db:
        mock_ref = MagicMock()
        mock_ref.id = "new-cust-123"
        mock_db.collection.return_value.document.return_value = mock_ref
        
        customer_data = {'name': 'Test User', 'email': 'test@example.com'}
        response = client.post('/api/customer', json=customer_data)
        
        assert response.status_code == 201
        assert response.json['success'] is True
        assert response.json['id'] == "new-cust-123"

# Test for Epic 2: Create Customer (Failure)
def test_create_customer_missing_name(client):
    customer_data = {'email': 'test@example.com'}
    response = client.post('/api/customer', json=customer_data)
    
    assert response.status_code == 400
    assert 'Name and email are required' in response.json['error']

# Test for Epic 2: Get Customers
def test_get_customers_success(client):
    with patch('app.db') as mock_db:
        mock_doc1 = MagicMock()
        mock_doc1.id = "cust_1"
        mock_doc1.to_dict.return_value = {'name': 'Customer A'}
        
        mock_doc2 = MagicMock()
        mock_doc2.id = "cust_2"
        mock_doc2.to_dict.return_value = {'name': 'Customer B'}

        mock_stream = [mock_doc1, mock_doc2]
        mock_db.collection.return_value.stream.return_value = mock_stream
        
        response = client.get('/api/customers')
        
        assert response.status_code == 200
        assert len(response.json) == 2
        assert response.json[0]['name'] == 'Customer A'