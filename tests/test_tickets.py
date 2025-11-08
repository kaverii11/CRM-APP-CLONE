import json
import pytest
from app import app


@pytest.fixture
def client():
    """Create a test client for the app."""
    with app.test_client() as client:
        yield client


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
