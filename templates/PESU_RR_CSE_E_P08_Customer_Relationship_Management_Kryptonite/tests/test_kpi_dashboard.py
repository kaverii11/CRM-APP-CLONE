import json
import pytest
from app import app
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta, timezone



# --- Tests for Epic 6: Dashboard & KPIs (Kavana) ---

def test_get_customer_kpis_success(client, mocker):
    """Test GET /api/customer-kpis - success"""
    mock_db = mocker.MagicMock()
    
    # --- Mock Data ---
    # Customer 1: Created 40 days ago
    mock_cust1 = mocker.MagicMock()
    mock_cust1.to_dict.return_value = {
        'createdAt': datetime.now(timezone.utc) - timedelta(days=40)
    }
    # Customer 2: Created 10 days ago
    mock_cust2 = mocker.MagicMock()
    mock_cust2.to_dict.return_value = {
        'createdAt': datetime.now(timezone.utc) - timedelta(days=10)
    }
    
    mock_db.collection.return_value.stream.return_value = [mock_cust1, mock_cust2]
    mocker.patch('app.get_db', return_value=mock_db)
    
    # --- Run Test ---
    response = client.get('/api/customer-kpis')
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['total_customers'] == 2
    assert data['new_customers_last_30_days'] == 1

def test_get_customer_kpis_db_failure(client, mocker):
    """Test GET /api/customer-kpis - failure (503)"""
    mocker.patch('app.get_db_or_raise', side_effect=RuntimeError("Database connection failed"))
    
    response = client.get('/api/customer-kpis')
    
    assert response.status_code == 503
    assert "Database connection failed" in response.get_json()['error']

def test_get_ticket_metrics_success(client, mocker):
    """Test GET /api/ticket-metrics - success"""
    mock_db = mocker.MagicMock()
    
    # --- Mock Data ---
    today = datetime.utcnow()
    # Ticket 1: Resolved in 24 hours (Week 1)
    mock_ticket1 = mocker.MagicMock()
    mock_ticket1.to_dict.return_value = {
        'status': 'Closed',
        'created_at': today - timedelta(days=2),
        'resolved_at': today - timedelta(days=1) # 24h resolution
    }
    # Ticket 2: Resolved in 48 hours (Week 2)
    mock_ticket2 = mocker.MagicMock()
    mock_ticket2.to_dict.return_value = {
        'status': 'Closed',
        'created_at': today - timedelta(days=10),
        'resolved_at': today - timedelta(days=8) # 48h resolution
    }
    
    mock_db.collection.return_value.stream.return_value = [mock_ticket1, mock_ticket2]
    mocker.patch('app.get_db', return_value=mock_db)

    # --- Run Test ---
    response = client.get('/api/ticket-metrics')
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['total_resolved'] == 2
    # Avg: (24 + 48) / 2 = 36 hours
    assert data['avg_resolution_hours'] == 36.0
    assert data['trend_labels'] == ['Week 1', 'Week 2', 'Week 3', 'Week 4']
    assert data['trend_values'] == [0, 0, 48.0, 24.0]

def test_get_ticket_metrics_db_failure(client, mocker):
    """Test GET /api/ticket-metrics - failure (503)"""
    mocker.patch('app.get_db_or_raise', side_effect=RuntimeError("Database connection failed"))
    
    response = client.get('/api/ticket-metrics')
    
    assert response.status_code == 503
    assert "Database connection failed" in response.get_json()['error']

# --- Tests for new HTML routes (Epic 6) ---

def test_sales_page_route(client):
    """Test that the /sales page loads."""
    response = client.get('/sales')
    assert response.status_code == 200
    assert response.content_type == 'text/html; charset=utf-8'

def test_kpi_report_page_route(client):
    """Test that the /report/kpis page loads."""
    response = client.get('/report/kpis')
    assert response.status_code == 200
    assert response.content_type == 'text/html; charset=utf-8'