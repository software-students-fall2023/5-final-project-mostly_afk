"""Module for Testing Python Functions"""
from unittest.mock import MagicMock, patch
import pytest
from bson import ObjectId
from werkzeug.security import generate_password_hash
from requests.exceptions import RequestException
from web_app.app import app


class Tests:
    """Test Functions for the Web App"""

    mock_user_id = str(ObjectId())

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

    def test_login_user_logged_in(self, client):
        """Test login route when user is logged in."""
        with client.session_transaction() as session:
            session["user_id"] = "some_user_id"

        response = client.get("/login")

        assert response.status_code == 302
        assert "/" in response.headers["Location"]

    def test_login_user_not_logged_in(self, client):
        """Test login route when user is not logged in."""
        with client.session_transaction() as session:
            session.pop("user_id", None)

        response = client.get("/login")

        assert response.status_code == 200
        assert b"login.html" in response.data

    def test_logout(self, client):
        """Test logout"""
        with client.session_transaction() as session:
            session["user_id"] = 123 

        response = client.get("/logout")

        with client.session_transaction() as session:
            assert "user_id" not in session

        assert response.status_code == 302  
    
    @patch('web_app.app.requests.post')
    def test_get_response_valid_data(self, mock_post, client):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "mocked response"}
        mock_post.return_value = mock_response

        with client.session_transaction() as session:
            session["user_id"] = self.mock_user_id

        response = client.post("/get_response", data={
            "user_input": "Hello",
            "personality": "Helpful Mom",
            "user_id": ObjectId(),
        })

        assert response.status_code == 200
        assert "response" in response.json
    
    def test_get_response_invalid_data(self, client):
        with client.session_transaction() as session:
            session["user_id"] = self.mock_user_id

        response = client.post("/get_response", data={})

        assert response.status_code == 500 
    
    @patch('web_app.app.requests.post')
    def test_get_response_timeout(self, mock_post, client):
        with client.session_transaction() as session:
            session["user_id"] = self.mock_user_id

        mock_post.side_effect = RequestException("Timeout occurred")
        response = client.post("/get_response", data={"user_input": "Hello"})

        assert response.status_code == 500
        assert "error" in response.json
    
    def test_load_chats_without_user_id(self, client):
        response = client.get("/load_chats")

        assert response.status_code == 400
        assert "error" in response.json
    
    @patch('web_app.app.collection.delete_many')
    def test_clear_chats_valid_user_id(self, mock_delete, client):
        mock_delete.return_value.deleted_count = 1
        response = client.post("/clear_chats", data={"user_id": self.mock_user_id})

        assert response.status_code == 200
        assert response.json.get("status") == "success"
    
    def test_clear_chats_without_user_id(self, client):
        response = client.post("/clear_chats")

        assert response.status_code == 400
        assert "error" in response.json
    
    def test_clear_session(self, client):
        with client.session_transaction() as session:
            session["user_id"] = self.mock_user_id

        response = client.post("/clear_session")

        assert response.status_code == 200
        assert "message" in response.json
        with client.session_transaction() as session:
            assert "user_id" not in session