import json
import pytest
from app import app


@pytest.fixture
def client():
    """Create a test client for the app."""
    with app.test_client() as client:
        yield client


def test_create_support_ticket_success(client):
    """
    Test successfully creating a new support ticket (Story CCRM-63).
    """
    ticket_data = {
        "customer_id": "CUST-12345",
        "issue": "Cannot log in to the portal."
    }
    response = client.post('/api/tickets', data=json.dumps(ticket_data), content_type='application/json')

    assert response.status_code == 201
    data = response.get_json()
    assert data['status'] == "Open"
    assert data['customer_id'] == "CUST-12345"
    assert "ticket_id" in data
    assert "sla_deadline" in data  # Test for Story CCRM-695


def test_create_support_ticket_fail_no_data(client):
    """
    Test failure case when no data or required fields are missing.
    """
    ticket_data = {
        "issue": "This request is missing the customer_id"
    }
    response = client.post('/api/tickets', data=json.dumps(ticket_data), content_type='application/json')

    assert response.status_code == 400
    data = response.get_json()
    assert "Missing required fields" in data['error']
