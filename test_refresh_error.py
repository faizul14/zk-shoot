import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# Mock environment variables before importing app
os.environ["BASE_API_URL"] = "https://example.com"
os.environ["BASE_CIAM_URL"] = "https://example.com"
os.environ["BASIC_AUTH"] = "dGVzdDp0ZXN0"
os.environ["UA"] = "test-agent"

# Add parent directory to sys.path to allow imports
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from app.client.engsel import get_new_token

class TestTokenRefresh(unittest.TestCase):
    @patch('app.client.engsel.requests.post')
    def test_get_new_token_400_error(self, mock_post):
        # Mock a 400 Bad Request response
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "error": "invalid_grant",
            "error_description": "Token is invalid or expired"
        }
        mock_post.return_value = mock_response

        # Call the function
        result = get_new_token("fake_refresh_token")

        # Verify that the result is None (as expected for 400 errors now)
        self.assertIsNone(result)
        # Verify that raise_for_status was NOT called for 400
        mock_response.raise_for_status.assert_not_called()

    @patch('app.client.engsel.requests.post')
    def test_get_new_token_200_success(self, mock_post):
        # Mock a 200 OK response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "new_access_token",
            "refresh_token": "new_refresh_token",
            "id_token": "new_id_token"
        }
        mock_post.return_value = mock_response

        # Call the function
        result = get_new_token("fake_refresh_token")

        # Verify that the result is corrected
        self.assertEqual(result["access_token"], "new_access_token")
        # Verify that raise_for_status was called (implicitly by the code logic)
        mock_response.raise_for_status.assert_called_once()

if __name__ == '__main__':
    unittest.main()
