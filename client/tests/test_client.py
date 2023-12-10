"""Module for Testing Python Functions"""
from unittest.mock import MagicMock, patch
import pytest
from .. import client


class Tests:
    """Test Functions for the Web App"""

    @pytest.fixture
    def example_fixture(self):
        """An example of a pytest fixture for"""
        yield

    # Test functions
    def test_sanity_check(self):
        """Run a simple test for the webapp side that always passes."""
        actual = True
        expected = True
        assert actual == expected, "Expected True to be equal to True!"