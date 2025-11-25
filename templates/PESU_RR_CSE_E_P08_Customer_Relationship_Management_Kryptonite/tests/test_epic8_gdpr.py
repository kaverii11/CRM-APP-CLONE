import json
import pytest
from app import app
from unittest.mock import MagicMock, patch


# --- Tests for Epic 8: GDPR/DPDP (Karthik) ---

def test_export_customer_data_success(client, mocker):
    """Test GET /api/gdpr/export/<id> - success"""
    mock_db = mocker.MagicMock()
    
    # --- Create separate mocks for each collection ---
    mock_coll_cust = mocker.MagicMock()
    mock_coll_tix = mocker.MagicMock()
    mock_coll_loyalty = mocker.MagicMock()

    # --- Set up the side_effect ---
    # This tells the mock to return the right collection based on the name
    def collection_side_effect(coll_name):
        if coll_name == 'customers':
            return mock_coll_cust
        if coll_name == 'tickets':
            return mock_coll_tix
        if coll_name == 'loyalty_profiles':
            return mock_coll_loyalty
        return mocker.MagicMock() # Default
    
    mock_db.collection.side_effect = collection_side_effect

    # --- Configure each collection mock ---
    mock_cust_doc = MagicMock(exists=True)
    mock_cust_doc.to_dict.return_value = {"name": "Test User", "email": "test@test.com"}
    mock_coll_cust.document.return_value.get.return_value = mock_cust_doc

    mock_ticket_doc = MagicMock()
    mock_ticket_doc.to_dict.return_value = {"issue": "It broke"}
    mock_coll_tix.where.return_value.stream.return_value = [mock_ticket_doc]
    
    mock_loyalty_doc = MagicMock(exists=True)
    mock_loyalty_doc.to_dict.return_value = {"points": 100, "tier": "Bronze"}
    mock_coll_loyalty.document.return_value.get.return_value = mock_loyalty_doc

    mocker.patch('app.get_db', return_value=mock_db)
    
    # --- Run Test ---
    response = client.get('/api/gdpr/export/cust-123')
    
    assert response.status_code == 200
    data = response.get_json()
    
    assert data['customer_details']['name'] == "Test User"
    assert len(data['support_tickets']) == 1
    assert data['loyalty_profile']['points'] == 100

def test_export_customer_data_not_found(client, mocker):
    """Test GET /api/gdpr/export/<id> - failure (404)"""
    mock_db = mocker.MagicMock()
    
    mock_cust_doc = MagicMock(exists=False) # Customer does not exist
    
    mock_db.collection('customers').document.return_value.get.return_value = mock_cust_doc
    
    mocker.patch('app.get_db', return_value=mock_db)
    
    response = client.get('/api/gdpr/export/cust-123')
    
    assert response.status_code == 404
    assert "Customer not found" in response.json['error']

def test_export_customer_data_db_failure(client, mocker):
    """Test GET /api/gdpr/export/<id> - failure (503)"""
    mocker.patch('app.get_db_or_raise', side_effect=RuntimeError("Database connection failed"))
    
    response = client.get('/api/gdpr/export/cust-123')
    
    assert response.status_code == 503
    assert "Database connection failed" in response.get_json()['error']