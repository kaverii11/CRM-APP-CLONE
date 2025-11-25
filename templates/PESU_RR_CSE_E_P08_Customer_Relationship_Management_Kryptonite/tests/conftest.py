import pytest
from app import app

@pytest.fixture
def client():
    """
    Global Test Fixture.
    Sets TESTING=True so app.py knows to disable the security guard.
    """
    app.config['TESTING'] = True
    
    with app.test_client() as client:
        yield client