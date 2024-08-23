import base64
import hashlib
import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

from src.iracingdataapi.client import irDataClient


class TestIrDataClient(unittest.TestCase):
    def setUp(self):
        self.client = irDataClient(username="test_user", password="test_password")

    def test_encode_password(self):
        expected_password = base64.b64encode(
            hashlib.sha256(
                ("test_password" + "test_user".lower()).encode("utf-8")
            ).digest()
        ).decode("utf-8")
        encoded_password = self.client._encode_password("test_user", "test_password")
        self.assertEqual(encoded_password, expected_password)

    @patch("requests.Session.post")
    def test_login_successful(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"authcode": "mock_authcode"}
        mock_post.return_value = mock_response

        self.client._login()
        self.assertTrue(self.client.authenticated)

    @patch("requests.Session.post")
    def test_login_rate_limited(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.headers = {"x-ratelimit-reset": datetime.now().timestamp() + 1}
        mock_post.side_effect = [
            mock_response,
            MagicMock(status_code=200, json=lambda: {"authcode": "mock_authcode"}),
        ]

        self.client._login()
        self.assertTrue(self.client.authenticated)

    @patch("requests.Session.post")
    def test_login_failure(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"error": "invalid_credentials"}
        mock_post.return_value = mock_response

        with self.assertRaises(RuntimeError):
            self.client._login()

    def test_build_url(self):
        endpoint = "/test/endpoint"
        expected_url = self.client.base_url + endpoint
        self.assertEqual(self.client._build_url(endpoint), expected_url)

    @patch("requests.Session.get")
    @patch("requests.Session.post")
    def test_get_resource_or_link_not_authenticated(self, mock_post, mock_get):
        self.client.authenticated = False

        mock_post.return_value = MagicMock(
            status_code=200, json=lambda: {"authcode": "someauthcode"}
        )
        mock_get.return_value = MagicMock(
            status_code=200, json=lambda: {"key": "value"}
        )

        response = self.client._get_resource_or_link(self.client.base_url)
        self.assertTrue(self.client.authenticated)
        self.assertEqual(response, [{"key": "value"}, False])

    @patch("requests.Session.get")
    @patch.object(irDataClient, "_login", return_value=None)
    def test_get_resource_or_link_successful(self, mock_login, mock_get):
        self.client.authenticated = True

        mock_get.return_value = MagicMock(
            status_code=200, json=lambda: {"key": "value"}
        )
        response = self.client._get_resource_or_link(self.client.base_url)
        self.assertEqual(response, [{"key": "value"}, False])

    @patch("requests.Session.get")
    @patch.object(irDataClient, "_login", return_value=None)
    def test_get_resource_or_link_link(self, mock_login, mock_get):
        self.client.authenticated = True
        mock_get.return_value = MagicMock(
            status_code=200, json=lambda: {"link": "some_link"}
        )
        response = self.client._get_resource_or_link(self.client.base_url)
        self.assertEqual(response, ["some_link", True])

    @patch("requests.Session.get")
    @patch("requests.Session.post")
    def test_get_resource_or_link_handles_401(self, mock_post, mock_get):
        self.client.authenticated = True
        mock_get.return_value = ["a link", True]
        mock_get.side_effect = [
            MagicMock(status_code=401),
            MagicMock(
                status_code=200,
                json=lambda: {"key": "value"},
                headers={"Content-Type": "application/json"},
            ),
        ]

        mock_post.return_value = MagicMock(
            status_code=200, json=lambda: {"authcode": "someauthcode"}
        )

        response = self.client._get_resource_or_link(self.client.base_url)
        self.assertEqual(response, [{"key": "value"}, False])

    @patch("requests.Session.get")
    def test_get_resource_or_link_handles_429(self, mock_get):
        self.client.authenticated = True
        mock_get.side_effect = [
            MagicMock(status_code=429),
            MagicMock(
                status_code=200,
                json=lambda: {"key": "value"},
                headers={"Content-Type": "application/json"},
            ),
        ]

        response = self.client._get_resource_or_link(self.client.base_url)
        self.assertEqual(response, [{"key": "value"}, False])

    @patch("requests.Session.get")
    @patch.object(irDataClient, "_get_resource_or_link")
    def test_get_resource_handles_401(self, mock_resource_or_link, mock_get):
        self.client.authenticated = True

        mock_resource_or_link.return_value = ["a link", True]
        mock_get.side_effect = [
            MagicMock(status_code=401),
            MagicMock(
                status_code=200,
                json=lambda: {"key": "value"},
                headers={"Content-Type": "application/json"},
            ),
        ]

        with patch.object(self.client, "_login", return_value=None) as mock_login:
            self.client.authenticated = True
            response = self.client._get_resource("/test/endpoint")
            mock_login.assert_called_once()
            self.assertEqual(mock_get.call_count, 2)
            self.assertEqual(response, {"key": "value"})

    @patch("requests.Session.get")
    @patch.object(irDataClient, "_get_resource_or_link")
    def test_get_resource_handles_429(self, mock_resource_or_link, mock_get):
        self.client.authenticated = True
        mock_resource_or_link.return_value = ["a link", True]
        mock_get.side_effect = [
            MagicMock(status_code=429),
            MagicMock(
                status_code=200,
                json=lambda: ["a link", True],
                headers={"Content-Type": "application/json"},
            ),
        ]

        response = self.client._get_resource("/test/endpoint")
        self.assertEqual(response, ["a link", True])

    @patch("requests.Session.get")
    @patch.object(irDataClient, "_get_resource_or_link")
    def test_get_chunks(self, mock_get_resource_or_link, mock_get):
        mock_get_resource_or_link.return_value = [
            {"data_url": "http://example.com/chunk"},
            False,
        ]
        mock_get.return_value = MagicMock(
            status_code=200, json=lambda: [{"chunked": "data"}]
        )

        chunks = self.client._get_chunks(
            {"base_download_url": "http://example.com/", "chunk_file_names": ["chunk"]}
        )

        self.assertEqual(chunks, [{"chunked": "data"}])

    def test_add_assets(self):
        objects = [{"id": 1}, {"id": 2}]
        assets = {"1": {"logo": "logo1"}, "2": {"logo": "logo2"}}
        id_key = "id"
        expected_result = [{"id": 1, "logo": "logo1"}, {"id": 2, "logo": "logo2"}]

        result = self.client._add_assets(objects, assets, id_key)
        self.assertEqual(result, expected_result)

    @patch.object(irDataClient, "_get_resource")
    def test_result_with_parameters(self, mock_get_resource):
        client = irDataClient(username="test_user", password="test_password")
        mock_get_resource.return_value = {"result": "some data"}

        subsession_id = 12345
        include_licenses = True
        response = client.result(
            subsession_id=subsession_id, include_licenses=include_licenses
        )

        mock_get_resource.assert_called_once_with(
            "/data/results/get",
            payload={
                "subsession_id": subsession_id,
                "include_licenses": include_licenses,
            },
        )
        self.assertEqual(response, {"result": "some data"})

    @patch.object(irDataClient, "_get_resource")
    def test_result_without_optional_parameters(self, mock_get_resource):
        client = irDataClient(username="test_user", password="test_password")
        mock_get_resource.return_value = {"result": "some data"}

        subsession_id = 12345
        response = client.result(subsession_id=subsession_id)

        mock_get_resource.assert_called_once_with(
            "/data/results/get",
            payload={"subsession_id": subsession_id, "include_licenses": False},
        )
        self.assertEqual(response, {"result": "some data"})

    def test_result_missing_subsession_id(self):
        client = irDataClient(username="test_user", password="test_password")

        with self.assertRaises(TypeError) as context:
            client.result()
        self.assertIn(
            "irDataClient.result() missing 1 required positional argument: 'subsession_id'",
            str(context.exception),
        )

    @patch.object(irDataClient, "_get_resource")
    def test_season_spectator_subsessionids_with_default_event_types(
        self, mock_get_resource
    ):

        client = irDataClient(username="test_user", password="test_password")
        mock_get_resource.return_value = {"subsession_ids": [1, 2, 3, 4]}

        response = client.season_spectator_subsessionids()

        mock_get_resource.assert_called_once_with(
            "/data/season/spectator_subsessionids", payload={"event_types": "2,3,4,5"}
        )
        self.assertEqual(response, [1, 2, 3, 4])

    @patch.object(irDataClient, "_get_resource")
    def test_season_spectator_subsessionids_with_specific_event_types(
        self, mock_get_resource
    ):

        client = irDataClient(username="test_user", password="test_password")
        mock_get_resource.return_value = {"subsession_ids": [5, 6, 7]}

        event_types = [3, 5]
        response = client.season_spectator_subsessionids(event_types=event_types)

        mock_get_resource.assert_called_once_with(
            "/data/season/spectator_subsessionids", payload={"event_types": "3,5"}
        )
        self.assertEqual(response, [5, 6, 7])

    @patch.object(irDataClient, "_get_resource")
    def test_season_spectator_subsessionids_with_empty_response(
        self, mock_get_resource
    ):

        client = irDataClient(username="test_user", password="test_password")
        mock_get_resource.return_value = {"subsession_ids": []}

        response = client.season_spectator_subsessionids()

        mock_get_resource.assert_called_once_with(
            "/data/season/spectator_subsessionids", payload={"event_types": "2,3,4,5"}
        )
        self.assertEqual(response, [])

    @patch.object(irDataClient, "_get_resource")
    def test_hosted_combined_sessions_with_package_id(self, mock_get_resource):
        client = irDataClient(username="test_user", password="test_password")
        mock_get_resource.return_value = {"sessions": ["session1", "session2"]}

        package_id = 456
        response = client.hosted_combined_sessions(package_id=package_id)

        mock_get_resource.assert_called_once_with(
            "/data/hosted/combined_sessions", payload={"package_id": package_id}
        )
        self.assertEqual(response, {"sessions": ["session1", "session2"]})

    @patch.object(irDataClient, "_get_resource")
    def test_hosted_combined_sessions_without_package_id(self, mock_get_resource):
        client = irDataClient(username="test_user", password="test_password")
        mock_get_resource.return_value = {"sessions": ["session1", "session2"]}

        response = client.hosted_combined_sessions()

        mock_get_resource.assert_called_once_with(
            "/data/hosted/combined_sessions", payload={}
        )
        self.assertEqual(response, {"sessions": ["session1", "session2"]})

    @patch.object(irDataClient, "_get_resource")
    def test_hosted_combined_sessions_with_empty_response(self, mock_get_resource):
        client = irDataClient(username="test_user", password="test_password")
        mock_get_resource.return_value = {}

        response = client.hosted_combined_sessions()

        mock_get_resource.assert_called_once_with(
            "/data/hosted/combined_sessions", payload={}
        )
        self.assertEqual(response, {})

    @patch.object(irDataClient, "_get_chunks")
    @patch.object(irDataClient, "_get_resource")
    def test_result_search_series_with_required_parameters(
        self, mock_get_resource, mock_get_chunks
    ):
        client = irDataClient(username="test_user", password="test_password")
        mock_get_resource.return_value = {"data": {"chunk_info": "chunk_data"}}
        mock_get_chunks.return_value = ["result1", "result2"]

        season_year = 2021
        season_quarter = 2
        response = client.result_search_series(
            season_year=season_year, season_quarter=season_quarter
        )

        mock_get_resource.assert_called_once_with(
            "/data/results/search_series",
            payload={
                "season_year": season_year,
                "season_quarter": season_quarter,
                "official_only": True,
            },
        )
        mock_get_chunks.assert_called_once_with("chunk_data")
        self.assertEqual(response, ["result1", "result2"])

    @patch.object(irDataClient, "_get_chunks")
    @patch.object(irDataClient, "_get_resource")
    def test_result_search_series_with_all_parameters(
        self, mock_get_resource, mock_get_chunks
    ):
        client = irDataClient(username="test_user", password="test_password")
        mock_get_resource.return_value = {"data": {"chunk_info": "chunk_data"}}
        mock_get_chunks.return_value = ["result1", "result2"]

        season_year = 2021
        season_quarter = 2
        start_range_begin = "2021-01-01T00:00Z"
        start_range_end = "2021-01-31T23:59Z"
        finish_range_begin = "2021-01-01T00:00Z"
        finish_range_end = "2021-01-31T23:59Z"
        cust_id = 12345
        series_id = 67890
        race_week_num = 3
        official_only = True
        event_types = [2, 3]
        category_ids = [1, 2]

        response = client.result_search_series(
            season_year=season_year,
            season_quarter=season_quarter,
            start_range_begin=start_range_begin,
            start_range_end=start_range_end,
            finish_range_begin=finish_range_begin,
            finish_range_end=finish_range_end,
            cust_id=cust_id,
            series_id=series_id,
            race_week_num=race_week_num,
            official_only=official_only,
            event_types=event_types,
            category_ids=category_ids,
        )

        mock_get_resource.assert_called_once_with(
            "/data/results/search_series",
            payload={
                "season_year": season_year,
                "season_quarter": season_quarter,
                "start_range_begin": start_range_begin,
                "start_range_end": start_range_end,
                "finish_range_begin": finish_range_begin,
                "finish_range_end": finish_range_end,
                "cust_id": cust_id,
                "series_id": series_id,
                "race_week_num": race_week_num,
                "official_only": official_only,
                "event_types": event_types,
                "category_ids": category_ids,
            },
        )
        mock_get_chunks.assert_called_once_with("chunk_data")
        self.assertEqual(response, ["result1", "result2"])

    @patch.object(irDataClient, "_get_chunks")
    @patch.object(irDataClient, "_get_resource")
    def test_result_search_series_with_partial_parameters(
        self, mock_get_resource, mock_get_chunks
    ):
        client = irDataClient(username="test_user", password="test_password")
        mock_get_resource.return_value = {"data": {"chunk_info": "chunk_data"}}
        mock_get_chunks.return_value = ["result1", "result2"]

        start_range_begin = "2021-01-01T00:00Z"
        finish_range_begin = "2021-01-01T00:00Z"
        cust_id = 12345

        response = client.result_search_series(
            start_range_begin=start_range_begin,
            finish_range_begin=finish_range_begin,
            cust_id=cust_id,
        )

        mock_get_resource.assert_called_once_with(
            "/data/results/search_series",
            payload={
                "start_range_begin": "2021-01-01T00:00Z",
                "finish_range_begin": "2021-01-01T00:00Z",
                "cust_id": 12345,
                "official_only": True,
            },
        )
        mock_get_chunks.assert_called_once_with("chunk_data")
        self.assertEqual(response, ["result1", "result2"])

    @patch.object(irDataClient, "_get_chunks")
    @patch.object(irDataClient, "_get_resource")
    def test_result_search_series_raises_without_required_parameters(
        self, mock_get_resource, mock_get_chunks
    ):
        client = irDataClient(username="test_user", password="test_password")

        with self.assertRaises(RuntimeError) as context:
            client.result_search_series()
        self.assertIn(
            "Please supply Season Year and Season Quarter or a date range",
            str(context.exception),
        )
        mock_get_resource.assert_not_called()
        mock_get_chunks.assert_not_called()

    @patch.object(irDataClient, "_get_resource")
    def test_member_with_required_parameters(self, mock_get_resource):
        client = irDataClient(username="test_user", password="test_password")
        mock_get_resource.return_value = {"members": [{"cust_id": 12345}]}

        cust_id = 12345
        response = client.member(cust_id=cust_id)

        mock_get_resource.assert_called_once_with(
            "/data/member/get", payload={"cust_ids": cust_id, "include_licenses": False}
        )
        self.assertEqual(response, {"members": [{"cust_id": cust_id}]})

    @patch.object(irDataClient, "_get_resource")
    def test_member_with_all_parameters(self, mock_get_resource):
        client = irDataClient(username="test_user", password="test_password")
        mock_get_resource.return_value = {
            "members": [{"cust_id": 12345, "licenses": ["license1", "license2"]}]
        }

        cust_id = 12345
        include_licenses = True
        response = client.member(cust_id=cust_id, include_licenses=include_licenses)

        mock_get_resource.assert_called_once_with(
            "/data/member/get",
            payload={"cust_ids": cust_id, "include_licenses": include_licenses},
        )
        self.assertEqual(
            response,
            {"members": [{"cust_id": cust_id, "licenses": ["license1", "license2"]}]},
        )

    @patch.object(irDataClient, "_get_resource")
    def test_member_with_multiple_cust_ids(self, mock_get_resource):
        client = irDataClient(username="test_user", password="test_password")
        mock_get_resource.return_value = {"members": [{"cust_id": "12345,67890"}]}

        cust_ids = "12345,67890"
        response = client.member(cust_id=cust_ids)

        mock_get_resource.assert_called_once_with(
            "/data/member/get",
            payload={"cust_ids": cust_ids, "include_licenses": False},
        )
        self.assertEqual(response, {"members": [{"cust_id": cust_ids}]})

    def test_member_missing_cust_id(self):
        client = irDataClient(username="test_user", password="test_password")

        with self.assertRaises(TypeError) as context:
            client.member()
        self.assertIn(
            "irDataClient.member() missing 1 required positional argument: 'cust_id'",
            str(context.exception),
        )


if __name__ == "__main__":
    unittest.main()
