"""Module for Testing Python Functions"""
from unittest.mock import MagicMock, patch
import pytest
from web_app.app import app


class Tests:
    """Test Functions for the Web App"""

    @pytest.fixture
    def example_fixture(self):
        """An example of a pytest fixture for"""
        yield

    @pytest.fixture
    def mocker(self):
        """Mocker fixture"""
        return MagicMock()

    # Test functions
    def test_sanity_check(self):
        """Run a simple test for the webapp side that always passes."""
        actual = True
        expected = True
        assert actual == expected, "Expected True to be equal to True!"

    @pytest.fixture
    def client(self):
        """Test client for web app"""
        app.config["TESTING"] = True
        with app.test_client() as test_client:
            yield test_client

    def test_index_route(self, client):
        """Test index route"""
        response = client.get("/")
        assert response.status_code == 200