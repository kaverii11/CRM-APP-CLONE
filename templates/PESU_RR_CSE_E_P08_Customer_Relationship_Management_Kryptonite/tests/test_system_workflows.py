import json
import pytest
from app import app
from unittest.mock import MagicMock, patch


# --- System Test 1: Customer & Ticket Workflow (Epic 2 -> Epic 4) ---

def test_system_customer_to_ticket_workflow(client, mocker):
    """
    Tests creating a customer (Epic 2) and then creating a ticket (Epic 4) for them.
    This is a true System Test.
    """
    mock_db = mocker.MagicMock()
    mocker.patch('app.get_db', return_value=mock_db)
    
    # --- Mocking for Step 1: Create Customer (and Loyalty Profile) ---
    mock_cust_ref = mocker.MagicMock()
    mock_cust_ref.id = "new-cust-system-test"
    
    mock_loyalty_ref = mocker.MagicMock()
    mock_loyalty_ref.id = "loyalty-system-test"

    # Mock the two document() calls in create_customer
    def doc_side_effect(path=None):
        if path == "new-cust-system-test":
            return mock_cust_ref
        return mock_loyalty_ref if path is None else mock_cust_ref

    mock_db.collection('customers').document.return_value = mock_cust_ref
    mock_db.batch.return_value = mocker.MagicMock() # Mock the batch
    
    # === STEP 1: CREATE A NEW CUSTOMER (from Epic 2) ===
    customer_data = {'name': 'System Test User', 'email': 'system@test.com'}
    response_cust = client.post('/api/customer', json=customer_data)
    
    assert response_cust.status_code == 201
    new_customer_id = response_cust.json['id']
    assert new_customer_id == "new-cust-system-test"

    # --- Mocking for Step 2: Create Ticket ---
    mock_ticket_ref = mocker.MagicMock()
    mock_ticket_ref.id = "new-ticket-system-test"
    # We must reset the side_effect for the new mock
    mock_db.collection.return_value.document = mocker.MagicMock(return_value=mock_ticket_ref)

    # === STEP 2: CREATE A TICKET FOR THAT CUSTOMER (from Epic 4) ===
    ticket_data = {"customer_id": new_customer_id, "issue": "System Test Issue"}
    response_ticket = client.post('/api/tickets', json=ticket_data)
    
    assert response_ticket.status_code == 201
    assert response_ticket.json['ticket_id'] == "new-ticket-system-test"
    assert response_ticket.json['customer_id'] == new_customer_id

# Add this new test to tests/test_system_workflows.py

def test_system_lead_to_kpi_workflow(client, mocker):
    """
    Tests creating a lead, converting it, marking it as 'Won' (Epic 3),
    and then verifying the Sales KPI dashboard (Epic 6) is updated.
    """
    mock_db = mocker.MagicMock()
    mocker.patch('app.get_db', return_value=mock_db)
    mocker.patch('app.get_db_or_raise', return_value=mock_db)

    # --- Mocking Data ---
    mock_lead_ref = mocker.MagicMock()
    mock_lead_ref.id = "lead-123"
    mock_lead_doc = mocker.MagicMock(exists=True)
    mock_lead_doc.to_dict.return_value = {'name': 'Big Lead', 'email': 'lead@test.com', 'source': 'Web'}
    mock_lead_ref.get.return_value = mock_lead_doc

    mock_opp_ref = mocker.MagicMock()
    mock_opp_ref.id = "opp-456"
    mock_opp_doc = mocker.MagicMock(exists=True)
    mock_opp_ref.get.return_value = mock_opp_doc

    # Mock the various document() calls
    def doc_side_effect(path=None):
        if path == "lead-123":
            return mock_lead_ref
        if path == "opp-456":
            return mock_opp_ref
        return mocker.MagicMock(id="new-doc-id") # Default mock for new docs

    mock_db.collection.return_value.document = doc_side_effect

    # === STEP 1: Convert the Lead (from Epic 3) ===
    response_convert = client.post('/api/lead/lead-123/convert')
    assert response_convert.status_code == 200

    # === STEP 2: Update Opportunity to 'Won' (from Epic 3) ===
    update_data = {'stage': 'Won', 'amount': 5000}
    response_update = client.put('/api/opportunity/opp-456/status', json=update_data)
    assert response_update.status_code == 200

    # --- Mocking for Step 3: Check Sales KPI ---
    # Mock the stream() call for the KPI endpoint
    mock_won_opp = mocker.MagicMock()
    mock_won_opp.to_dict.return_value = {"stage": "Won", "amount": 5000}
    mock_db.collection.return_value.stream.return_value = [mock_won_opp]

    # === STEP 3: Check Sales KPI (from Epic 6) ===
    response_kpi = client.get('/api/sales-kpis')

    assert response_kpi.status_code == 200
    assert response_kpi.json['total_opportunities'] == 1
    assert response_kpi.json['won_opportunities'] == 1
    assert response_kpi.json['total_revenue_won'] == 5000.0