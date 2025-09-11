"""Tests for irRateLimit class."""

import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from src.iracingdataapi.client import irDataClient
from src.iracingdataapi.rate_limit import irRateLimit

class TestIrRateLimit(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures with mock responses and client instance."""
        self.client = irDataClient(username="test_user", password="test_password")
        
        # Create common test fixtures
        self.mock_response_with_all_headers = TestIrRateLimit._create_mock_response(
            {'x-ratelimit-limit': '1000', 'x-ratelimit-remaining': '999', 'x-ratelimit-reset': '1640995200'})
        self.mock_response_partial_headers = TestIrRateLimit._create_mock_response(
            {'x-ratelimit-limit': '1000', 'x-ratelimit-remaining': '999'})  # Missing reset
        self.mock_response_no_headers = TestIrRateLimit._create_mock_response({})
        self.mock_response_invalid_headers = TestIrRateLimit._create_mock_response(
            {'x-ratelimit-limit': 'invalid', 'x-ratelimit-remaining': '999', 'x-ratelimit-reset': '1640995200'})
        self.mock_response_zero_remaining = TestIrRateLimit._create_mock_response(
            {'x-ratelimit-limit': '1000', 'x-ratelimit-remaining': '0', 'x-ratelimit-reset': '1640995200'})
        self.updated_rate_limit_headers = TestIrRateLimit._create_mock_response(
            {'x-ratelimit-limit': '1000', 'x-ratelimit-remaining': '998', 'x-ratelimit-reset': '1640995300'})
        
        # Time-based fixtures
        future_timestamp = int((datetime.now() + timedelta(minutes=5)).timestamp())
        past_timestamp = int((datetime.now() - timedelta(minutes=5)).timestamp())
        self.mock_response_future_reset = TestIrRateLimit._create_mock_response(
            {'x-ratelimit-limit': '1000', 'x-ratelimit-remaining': '999', 'x-ratelimit-reset': str(future_timestamp)})
        self.mock_response_past_reset = TestIrRateLimit._create_mock_response(
            {'x-ratelimit-limit': '1000', 'x-ratelimit-remaining': '999', 'x-ratelimit-reset': str(past_timestamp)})

    @staticmethod
    def _create_mock_response(headers):
        """Helper method to create mock HTTP responses with specified headers."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = headers
        mock_response.json.return_value = {"test": "data"}
        return mock_response


    def test_rate_limit_initialization(self):
        """Test that rate limit is initialized with defaults"""
        client = irDataClient(username="test_user", password="test_password")
        self.assertIsNotNone(client.rate_limit)
        self.assertFalse(client.rate_limit.has_data)  # Should have no data initially
        self.assertEqual(client.rate_limit.limit, 0)  # Default values
        self.assertEqual(client.rate_limit.remaining, 0)
        self.assertEqual(client.rate_limit.reset, 0)

    @patch.object(irDataClient, "_get_resource")
    def test_rate_limit_object_creation(self, _mock_get_resource):
        """Test that rate limit object is created from successful responses"""
        # Set authenticated to bypass login
        self.client.authenticated = True
        
        # Mock the session.get to return our response
        with patch.object(self.client.session, 'get', return_value=self.mock_response_with_all_headers):
            self.client._get_resource_or_link("http://test.com")
        
        # Verify rate limit object was created with correct values
        self.assertIsNotNone(self.client.rate_limit)
        self.assertEqual(self.client.rate_limit.limit, 1000)
        self.assertEqual(self.client.rate_limit.remaining, 999)
        self.assertEqual(self.client.rate_limit.reset, 1640995200)

    @patch.object(irDataClient, "_get_resource")
    def test_rate_limit_partial_headers_not_updated(self, _mock_get_resource):
        """Test that rate limit object is not updated with partial headers"""
        # Set authenticated to bypass login
        self.client.authenticated = True
        
        with patch.object(self.client.session, 'get', return_value=self.mock_response_partial_headers):
            self.client._get_resource_or_link("http://test.com")
        
        # Rate limit object should exist but not have data due to partial headers
        self.assertIsNotNone(self.client.rate_limit)
        self.assertFalse(self.client.rate_limit.has_data)  # Should not have data

    def test_rate_limit_properties_and_defaults(self):
        """Test rate limit properties with and without data"""
        # Test default values when no data
        self.assertIsNotNone(self.client.rate_limit)
        self.assertFalse(self.client.rate_limit.has_data)
        self.assertEqual(self.client.rate_limit.limit, 0)
        self.assertEqual(self.client.rate_limit.remaining, 0)
        self.assertEqual(self.client.rate_limit.reset, 0)
        
        # Test properties after updating with response data
        rate_limit = irRateLimit()
        rate_limit.update_from_response(self.mock_response_with_all_headers)
        self.client.rate_limit = rate_limit
        
        self.assertTrue(self.client.rate_limit.has_data)
        self.assertEqual(self.client.rate_limit.limit, 1000)
        self.assertEqual(self.client.rate_limit.remaining, 999)
        self.assertEqual(self.client.rate_limit.reset, 1640995200)

    def test_rate_limit_reset_time_property(self):
        """Test rate_limit.reset_time property"""
        rate_limit = irRateLimit()
        rate_limit.update_from_response(self.mock_response_with_all_headers)
        self.client.rate_limit = rate_limit
        
        expected_time = datetime.fromtimestamp(1640995200, tz=timezone.utc)
        self.assertEqual(self.client.rate_limit.reset_time, expected_time)

    def test_seconds_until_reset_property(self):
        """Test rate_limit.seconds_until_reset property"""
        # Test with future timestamp
        rate_limit_future = irRateLimit()
        rate_limit_future.update_from_response(self.mock_response_future_reset)
        self.client.rate_limit = rate_limit_future
        
        seconds = self.client.rate_limit.seconds_until_reset
        self.assertIsNotNone(seconds)
        self.assertGreater(seconds, 0)
        self.assertLess(seconds, 301)  # Should be less than 5 minutes + 1 second
        
        # Test with past timestamp (should return 0)
        rate_limit_past = irRateLimit()
        rate_limit_past.update_from_response(self.mock_response_past_reset)
        self.client.rate_limit = rate_limit_past
        
        seconds = self.client.rate_limit.seconds_until_reset
        self.assertEqual(seconds, 0)

    def test_rate_limit_update_method(self):
        """Test that existing rate limit object can be updated with new response"""
        # Create initial rate limit object
        rate_limit = irRateLimit()
        rate_limit.update_from_response(self.mock_response_with_all_headers)
        self.client.rate_limit = rate_limit
        
        # Update with new values (all headers present)
        result = self.client.rate_limit.update_from_response(self.updated_rate_limit_headers)
        
        # Verify values were updated and method returned True
        self.assertTrue(result)
        self.assertEqual(self.client.rate_limit.limit, 1000)
        self.assertEqual(self.client.rate_limit.remaining, 998)
        self.assertEqual(self.client.rate_limit.reset, 1640995300)

    def test_rate_limit_update_scenarios(self):
        """Test update method with various header scenarios"""
        rate_limit = irRateLimit()
        
        # Test with missing headers - should return False and not update
        result = rate_limit.update_from_response(self.mock_response_partial_headers)
        self.assertFalse(result)
        self.assertFalse(rate_limit.has_data)
        
        # Test with no headers at all - should return False and not update
        result = rate_limit.update_from_response(self.mock_response_no_headers)
        self.assertFalse(result)
        self.assertFalse(rate_limit.has_data)
        
        # Test with all headers present - should return True and update
        result = rate_limit.update_from_response(self.mock_response_with_all_headers)
        self.assertTrue(result)
        self.assertTrue(rate_limit.has_data)
        self.assertEqual(rate_limit.limit, 1000)
        self.assertEqual(rate_limit.remaining, 999)
        self.assertEqual(rate_limit.reset, 1640995200)

    def test_update_method_preserves_data_with_incomplete_headers(self):
        """Test that update method preserves existing data when headers are incomplete or invalid"""
        
        # Create initial rate limit object and populate with data
        rate_limit = irRateLimit()
        rate_limit.update_from_response(self.mock_response_with_all_headers)
        self.assertTrue(rate_limit.has_data)
        
        # Test with partial headers - should preserve original data
        result = rate_limit.update_from_response(self.mock_response_partial_headers)
        self.assertFalse(result)
        self.assertTrue(rate_limit.has_data)
        self.assertEqual(rate_limit.limit, 1000)
        self.assertEqual(rate_limit.remaining, 999)
        self.assertEqual(rate_limit.reset, 1640995200)
        
        # Test with invalid headers - should also preserve original data
        result = rate_limit.update_from_response(self.mock_response_invalid_headers)
        self.assertFalse(result)
        self.assertTrue(rate_limit.has_data)
        self.assertEqual(rate_limit.limit, 1000)
        self.assertEqual(rate_limit.remaining, 999)
        self.assertEqual(rate_limit.reset, 1640995200)

    def test_update_method_updates_with_complete_headers(self):
        """Test that update method updates data when all headers are present"""
        
        # Create initial rate limit object and populate with data
        rate_limit = irRateLimit()
        rate_limit.update_from_response(self.mock_response_with_all_headers)
        self.assertTrue(rate_limit.has_data)
        
        # Update with complete response - should update data
        result = rate_limit.update_from_response(self.updated_rate_limit_headers)
        
        # Should return True indicating update succeeded
        self.assertTrue(result)
        
        # Data should be updated
        self.assertTrue(rate_limit.has_data)
        self.assertEqual(rate_limit.limit, 1000)
        self.assertEqual(rate_limit.remaining, 998)
        self.assertEqual(rate_limit.reset, 1640995300)

    def test_invalid_rate_limit_headers_return_false(self):
        """Test that invalid rate limit headers return False without data"""
        rate_limit = irRateLimit()
        
        # Should return False when trying to update with invalid headers
        result = rate_limit.update_from_response(self.mock_response_invalid_headers)
        
        # Should return False and not have data
        self.assertFalse(result)
        self.assertFalse(rate_limit.has_data)

    def test_is_rate_limited_property(self):
        """Test is_rate_limited property in various scenarios"""
        rate_limit = irRateLimit()
        
        # Should return False when no data is available
        self.assertFalse(rate_limit.is_rate_limited)
        
        # Should return False when requests are remaining (999 > 0)
        rate_limit.update_from_response(self.mock_response_with_all_headers)
        self.assertFalse(rate_limit.is_rate_limited)
        
        # Should return True when no requests are remaining and we have data
        rate_limit.update_from_response(self.mock_response_zero_remaining)
        self.assertTrue(rate_limit.is_rate_limited)
        self.assertTrue(rate_limit.has_data)
        self.assertEqual(rate_limit.remaining, 0)


if __name__ == "__main__":
    unittest.main()