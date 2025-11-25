import json
import pytest
from app import app



def test_create_support_ticket_success(client, mocker):
    """
    Test successfully creating a new support ticket (Story CCRM-63).
    Now mocks database persistence.
    """
    mock_db = mocker.MagicMock()
    mock_ticket_ref = mocker.MagicMock()
    mock_ticket_ref.id = "ABC-FIRESTORE-ID-123"

    mock_db.collection.return_value.document.return_value = mock_ticket_ref
    mocker.patch('app.get_db', return_value=mock_db)

    ticket_data = {
        "customer_id": "CUST-12345",
        "issue": "Cannot log in to the portal."
    }
    response = client.post('/api/tickets', data=json.dumps(ticket_data), content_type='application/json')

    assert response.status_code == 201
    data = response.get_json()
    assert data['status'] == "Open"
    assert data['customer_id'] == "CUST-12345"
    assert data['ticket_id'] == "ABC-FIRESTORE-ID-123"
    assert "sla_deadline" in data

    mock_db.collection.assert_called_with('tickets')
    mock_ticket_ref.set.assert_called_once()


def test_create_support_ticket_fail_no_data(client, mocker):
    """
    Test failure case when no data or required fields are missing.
    """
    mock_db = mocker.MagicMock()
    mocker.patch('app.get_db', return_value=mock_db)

    ticket_data = {
        "issue": "This request is missing the customer_id"
    }
    response = client.post('/api/tickets', data=json.dumps(ticket_data), content_type='application/json')

    assert response.status_code == 400
    data = response.get_json()
    assert "Missing required fields" in data['error']


def test_get_tickets_success(client, mocker):
    """
    Test fetching recent tickets via the GET branch.
    """
    mock_db = mocker.MagicMock()

    mock_ticket_doc = mocker.MagicMock()
    mock_ticket_doc.id = "TICKET-1"
    mock_ticket_doc.to_dict.return_value = {'status': 'Open', 'priority': 'High'}

    mock_query = mocker.MagicMock()
    mock_query.stream.return_value = [mock_ticket_doc]

    mock_collection = mocker.MagicMock()
    mock_collection.order_by.return_value.limit.return_value = mock_query
    mock_db.collection.return_value = mock_collection

    mocker.patch('app.get_db', return_value=mock_db)

    response = client.get('/api/tickets')
    assert response.status_code == 200
    data = response.get_json()
    assert data[0]['id'] == "TICKET-1"
    assert data[0]['status'] == 'Open'


def test_create_support_ticket_invalid_body(client, mocker):
    """
    Posting without JSON should trigger the invalid body path.
    """
    mock_db = mocker.MagicMock()
    mocker.patch('app.get_db', return_value=mock_db)

    response = client.post('/api/tickets')
    assert response.status_code == 400
    assert "Invalid JSON body" in response.get_json()['error']


def test_close_ticket_happy_path(client, mocker):
    """
    Happy path for closing a ticket: ensure 200 and correct Firestore update payload.
    """
    # Mock ticket doc to exist
    mock_ticket_doc = mocker.MagicMock()
    mock_ticket_doc.exists = True
    mock_ticket_doc.to_dict.return_value = {
        "customer_id": "cust-123",
        "issue": "Device broken",
        "status": "Resolved"
    }
    # Spy the update call
    update_spy = mocker.MagicMock()

    mock_doc_ref = mocker.MagicMock()
    mock_doc_ref.get.return_value = mock_ticket_doc
    mock_doc_ref.update = update_spy

    mock_db = mocker.MagicMock()
    mock_db.collection.return_value.document.return_value = mock_doc_ref
    mocker.patch('app.get_db_or_raise', return_value=mock_db)

    response = client.put('/api/ticket/T-12345/close')
    assert response.status_code == 200
    body = response.get_json()
    assert body["success"] is True
    assert body["message"] == "Ticket closed"

    # Validate update payload
    assert update_spy.call_count == 1
    args, _ = update_spy.call_args
    assert isinstance(args, tuple) and len(args) == 1
    payload = args[0]
    assert payload["status"] == "Closed"
    assert "resolved_at" in payload and "updated_at" in payload


def test_check_sla_breaches_escalates_ticket(client, mocker):
    """
    Ensures check_sla_breaches finds a past-deadline ticket and escalates it.
    """
    # Build a fake document with a reference that can be updated
    mock_doc_ref = mocker.MagicMock()
    mock_ticket_doc = mocker.MagicMock()
    mock_ticket_doc.reference = mock_doc_ref

    # Create a chainable where().where().stream() that returns [mock_ticket_doc]
    mock_query = mocker.MagicMock()
    mock_query.where.return_value = mock_query
    mock_query.stream.return_value = [mock_ticket_doc]

    mock_collection = mocker.MagicMock()
    mock_collection.where.return_value = mock_query

    # Mock batch with update + commit
    mock_batch = mocker.MagicMock()

    # Mock DB
    mock_db = mocker.MagicMock()
    mock_db.collection.return_value = mock_collection
    mock_db.batch.return_value = mock_batch
    mocker.patch('app.get_db_or_raise', return_value=mock_db)

    # Call the route
    response = client.post('/api/tickets/check-sla')
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["tickets_escalated"] == 1

    # Batch should have been used to escalate
    assert mock_batch.update.call_count == 1
    update_args, _ = mock_batch.update.call_args
    # First arg is the document reference
    assert update_args[0] is mock_doc_ref
    # Second arg includes the escalated payload
    escal_payload = update_args[1]
    assert escal_payload["status"] == "Escalated"
    assert escal_payload["priority"] == "High"
