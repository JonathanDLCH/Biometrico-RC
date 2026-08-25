import unittest
from unittest.mock import MagicMock, patch

from src.api_client import build_api_url, get_attendance_logs, get_user_list


class TestApiClient(unittest.TestCase):
    def test_build_api_url_from_ip(self):
        self.assertEqual(build_api_url("10.0.0.2"), "http://10.0.0.2:80/api")

    @patch("src.api_client.requests.post")
    def test_get_attendance_logs_uses_device_url(self, mock_post):
        response = MagicMock()
        response.json.return_value = {"result": True, "record": [{"time": "2026-08-18 09:00:00"}]}
        mock_post.return_value = response

        records = get_attendance_logs(52, "2026-08-18", "2026-08-18", "http://10.0.0.2:80/api", "secret")

        self.assertEqual(len(records), 1)
        self.assertEqual(mock_post.call_args.args[0], "http://10.0.0.2:80/api")
        self.assertEqual(mock_post.call_args.kwargs["json"]["password"], "secret")

    @patch("src.api_client.requests.post", side_effect=Exception("Connection error"))
    def test_get_user_list_returns_none_on_failure(self, mock_post):
        self.assertIsNone(get_user_list("http://10.0.0.2:80/api", "secret"))


if __name__ == "__main__":
    unittest.main()
