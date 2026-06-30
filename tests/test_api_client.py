import unittest
from unittest.mock import patch, MagicMock
from src.api_client import get_attendance_logs

class TestApiClient(unittest.TestCase):
    @patch('src.api_client.requests.post')
    def test_get_attendance_logs_success(self, mock_post):
        # Mock respuesta exitosa
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "result": True,
            "count": 14,
            "record": [
                {"enrollid": 52, "time": "2026-04-15 09:40:57"},
                {"enrollid": 52, "time": "2026-04-15 19:35:30"}
            ]
        }
        mock_post.return_value = mock_response

        records = get_attendance_logs(52, "2026-04-01", "2026-04-15")
        self.assertIsNotNone(records)
        self.assertEqual(len(records), 14)

    @patch('src.api_client.requests.post')
    def test_get_attendance_logs_failure(self, mock_post):
        mock_post.side_effect = Exception("Connection error")
        records = get_attendance_logs(52, "2026-04-01", "2026-04-15")
        self.assertIsNone(records)

if __name__ == '__main__':
    unittest.main()