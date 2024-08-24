import base64
import hashlib
import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

import requests

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
    def test_get_resource_or_link_unhandled_error(self, mock_get):
        self.client.authenticated = True
        mock_get.side_effect = [
            MagicMock(status_code=410),
            MagicMock(
                status_code=200,
                json=lambda: {"key": "value"},
                headers={"Content-Type": "application/json"},
            ),
        ]

        with self.assertRaises(RuntimeError) as context:
            self.client._get_resource_or_link(self.client.base_url)

        self.assertIn("Unhandled Non-200 response", str(context.exception))

    @patch.object(irDataClient, "_get_resource_or_link")
    @patch("requests.Session.get")
    def test_get_resource_unhandled_error(self, mock_get, mock_resource_or_link):
        self.client.authenticated = True
        mock_resource_or_link.return_value = [{"key": "value"}, False]
        mock_get.side_effect = [
            MagicMock(
                status_code=200,
                json=lambda: {"key": "value"},
                headers={"Content-Type": "application/json"},
            ),
        ]

        response = self.client._get_resource("/test/endpoint")
        self.assertEqual(response, {"key": "value"})

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

    @patch("requests.Session.post")
    def test_login_timeout(self, mock_post):
        mock_post.side_effect = requests.Timeout()
        with self.assertRaises(RuntimeError) as context:
            self.client._login()
        self.assertIn("Login timed out", str(context.exception))

    @patch("requests.Session.post")
    def test_login_connection_error(self, mock_post):
        mock_post.side_effect = requests.ConnectionError()
        with self.assertRaises(RuntimeError) as context:
            self.client._login()
        self.assertIn("Connection error", str(context.exception))

    def test_parse_csv_response_valid(self):
        # Test with well-formed CSV data
        csv_text = "Name,Age,Location\nAlice,30,NY\nBob,25,CA"
        expected_output = [
            {"name": "Alice", "age": "30", "location": "NY"},
            {"name": "Bob", "age": "25", "location": "CA"},
        ]

        result = self.client._parse_csv_response(csv_text)
        self.assertEqual(result, expected_output)

    @patch("builtins.print")
    def test_parse_csv_response_mismatch(self, mock_print):
        # Test with row length mismatch
        csv_text = "Name,Age,Location\nAlice,30,NY\nBob,25"
        expected_output = [{"name": "Alice", "age": "30", "location": "NY"}]

        result = self.client._parse_csv_response(csv_text)
        self.assertEqual(result, expected_output)
        self.assertTrue(mock_print.called)
        self.assertTrue(
            mock_print.called_with("Warning: Row length does not match headers length")
        )

    @patch.object(irDataClient, "get_cars")
    @patch.object(irDataClient, "get_cars_assets")
    @patch.object(irDataClient, "_add_assets")
    def test_cars_property(self, mock_add_assets, mock_get_cars_assets, mock_get_cars):
        # Setup mock return values
        mock_get_cars.return_value = [
            {"car_id": 1, "name": "Car One"},
            {"car_id": 2, "name": "Car Two"},
        ]
        mock_get_cars_assets.return_value = {
            "1": {"image": "image1_url"},
            "2": {"image": "image2_url"},
        }

        # Expected result after assets are added
        expected_cars_with_assets = [
            {"car_id": 1, "name": "Car One", "image": "image1_url"},
            {"car_id": 2, "name": "Car Two", "image": "image2_url"},
        ]

        # Mock _add_assets to return the expected result
        mock_add_assets.return_value = expected_cars_with_assets

        # Access the property to trigger the chain of method calls
        cars_with_assets = self.client.cars

        # Assertions to ensure cars property includes assets
        mock_get_cars.assert_called_once()
        mock_get_cars_assets.assert_called_once()
        mock_add_assets.assert_called_once_with(
            mock_get_cars.return_value, mock_get_cars_assets.return_value, "car_id"
        )

        self.assertEqual(cars_with_assets, expected_cars_with_assets)

    @patch.object(irDataClient, "get_cars")
    @patch.object(irDataClient, "get_cars_assets")
    @patch.object(irDataClient, "_add_assets")
    def test_cars_property(self, mock_add_assets, mock_get_cars_assets, mock_get_cars):
        # Setup mock return values
        mock_get_cars.return_value = [
            {"car_id": 1, "name": "Car One"},
            {"car_id": 2, "name": "Car Two"},
        ]
        mock_get_cars_assets.return_value = {
            "1": {"image": "image1_url"},
            "2": {"image": "image2_url"},
        }

        # Expected result after assets are added
        expected_cars_with_assets = [
            {"car_id": 1, "name": "Car One", "image": "image1_url"},
            {"car_id": 2, "name": "Car Two", "image": "image2_url"},
        ]

        # Mock _add_assets to return the expected result
        mock_add_assets.return_value = expected_cars_with_assets

        # Access the property to trigger the chain of method calls
        cars_with_assets = self.client.cars

        # Assertions to ensure cars property includes assets
        mock_get_cars.assert_called_once()
        mock_get_cars_assets.assert_called_once()
        mock_add_assets.assert_called_once_with(
            mock_get_cars.return_value, mock_get_cars_assets.return_value, "car_id"
        )

        self.assertEqual(cars_with_assets, expected_cars_with_assets)

    @patch.object(irDataClient, "get_tracks")
    @patch.object(irDataClient, "get_tracks_assets")
    @patch.object(irDataClient, "_add_assets")
    def test_tracks_property(
        self, mock_add_assets, mock_get_tracks_assets, mock_get_tracks
    ):
        # Setup mock return values
        mock_get_tracks.return_value = [
            {"track_id": 1, "name": "Track One"},
            {"track_id": 2, "name": "Track Two"},
        ]
        mock_get_tracks_assets.return_value = {
            "1": {"image": "image1_url"},
            "2": {"image": "image2_url"},
        }

        # Expected result after assets are added
        expected_tracks_with_assets = [
            {"track_id": 1, "name": "Track One", "image": "image1_url"},
            {"track_id": 2, "name": "Track Two", "image": "image2_url"},
        ]

        # Mock _add_assets to return the expected result
        mock_add_assets.return_value = expected_tracks_with_assets

        # Access the property to trigger the chain of method calls
        tracks_with_assets = self.client.tracks

        # Assertions to ensure tracks property includes assets
        mock_get_tracks.assert_called_once()
        mock_get_tracks_assets.assert_called_once()
        mock_add_assets.assert_called_once_with(
            mock_get_tracks.return_value,
            mock_get_tracks_assets.return_value,
            "track_id",
        )

        self.assertEqual(tracks_with_assets, expected_tracks_with_assets)

    @patch.object(irDataClient, "get_series")
    @patch.object(irDataClient, "get_series_assets")
    @patch.object(irDataClient, "_add_assets")
    def test_series_property(
        self, mock_add_assets, mock_get_series_assets, mock_get_series
    ):
        # Setup mock return values
        mock_get_series.return_value = [
            {"series_id": 1, "name": "Series One"},
            {"series_id": 2, "name": "Series Two"},
        ]
        mock_get_series_assets.return_value = {
            "1": {"logo": "logo1_url"},
            "2": {"logo": "logo2_url"},
        }

        # Expected result after assets are added
        expected_series_with_assets = [
            {"series_id": 1, "name": "Series One", "logo": "logo1_url"},
            {"series_id": 2, "name": "Series Two", "logo": "logo2_url"},
        ]

        # Mock _add_assets to return the expected result
        mock_add_assets.return_value = expected_series_with_assets

        # Access the property to trigger the chain of method calls
        series_with_assets = self.client.series

        # Assertions to ensure series property includes assets
        mock_get_series.assert_called_once()
        mock_get_series_assets.assert_called_once()
        mock_add_assets.assert_called_once_with(
            mock_get_series.return_value,
            mock_get_series_assets.return_value,
            "series_id",
        )

        self.assertEqual(series_with_assets, expected_series_with_assets)

    @patch.object(irDataClient, "_get_resource")
    def test_driver_list(self, mock_get_resource):
        # Setup mock return values for different categories
        mock_get_resource.return_value = [
            {"driver_id": 1, "name": "Driver One"},
            {"driver_id": 2, "name": "Driver Two"},
        ]

        expected_endpoint = {
            1: "/data/driver_stats_by_category/oval",
            2: "/data/driver_stats_by_category/road",
            3: "/data/driver_stats_by_category/dirt_oval",
            4: "/data/driver_stats_by_category/dirt_road",
            5: "/data/driver_stats_by_category/sports_car",
            6: "/data/driver_stats_by_category/formula_car",
        }

        for category_id, endpoint in expected_endpoint.items():
            with self.subTest(category_id=category_id):
                drivers = self.client.driver_list(category_id)
                mock_get_resource.assert_called_with(endpoint)
                self.assertEqual(drivers, mock_get_resource.return_value)

        # Test for invalid category ID
        with self.assertRaises(ValueError) as context:
            self.client.driver_list(99)
        self.assertEqual(
            str(context.exception),
            "Invalid category_id '99'. Available categories are: [1, 2, 3, 4, 5, 6]",
        )

    @patch.object(irDataClient, "_get_resource")
    def test_league_get_with_id(self, mock_get_resource):
        # Mock return value
        mock_get_resource.return_value = {"league_id": 123, "name": "Test League"}

        league_id = 123
        include_licenses = True
        expected_payload = {
            "league_id": league_id,
            "include_licenses": include_licenses,
        }

        # Call the method
        league_info = self.client.league_get(league_id, include_licenses)

        # Assertions to ensure _get_resource is called with correct parameters
        mock_get_resource.assert_called_once_with(
            "/data/league/get", payload=expected_payload
        )
        self.assertEqual(league_info, mock_get_resource.return_value)

    def test_league_get_without_id(self):
        # Ensure the method raises RuntimeError when no league_id is provided
        with self.assertRaises(RuntimeError) as context:
            self.client.league_get()
        self.assertEqual(str(context.exception), "Please supply a league_id")

    @patch.object(irDataClient, "_get_resource")
    def test_league_cust_league_sessions_no_params(self, mock_get_resource):
        # Mock return value
        mock_get_resource.return_value = {"sessions": ["session1", "session2"]}

        expected_payload = {"mine": False}

        # Call the method without parameters
        sessions = self.client.league_cust_league_sessions()

        # Assertions to ensure _get_resource is called with correct parameters
        mock_get_resource.assert_called_once_with(
            "/data/league/cust_league_sessions", payload=expected_payload
        )
        self.assertEqual(sessions, mock_get_resource.return_value)

    @patch.object(irDataClient, "_get_resource")
    def test_league_cust_league_sessions_with_params(self, mock_get_resource):
        # Mock return value
        mock_get_resource.return_value = {"sessions": ["session1", "session2"]}

        mine = True
        package_id = 1234
        expected_payload = {"mine": mine, "package_id": package_id}

        # Call the method with parameters
        sessions = self.client.league_cust_league_sessions(
            mine=mine, package_id=package_id
        )

        # Assertions to ensure _get_resource is called with correct parameters
        mock_get_resource.assert_called_once_with(
            "/data/league/cust_league_sessions", payload=expected_payload
        )
        self.assertEqual(sessions, mock_get_resource.return_value)

    @patch.object(irDataClient, "_get_resource")
    def test_league_directory_default_params(self, mock_get_resource):
        # Mock return value
        mock_get_resource.return_value = {"leagues": ["league1", "league2"]}

        # Default payload parameters
        expected_payload = {
            "search": "",
            "tag": "",
            "restrict_to_member": False,
            "restrict_to_recruiting": False,
            "restrict_to_friends": False,
            "restrict_to_watched": False,
            "minimum_roster_count": 0,
            "maximum_roster_count": 999,
            "lowerbound": 1,
            "upperbound": None,
            "sort": None,
            "order": "asc",
        }

        # Call the method without parameters
        leagues = self.client.league_directory()

        # Assertions to ensure _get_resource is called with correct parameters
        mock_get_resource.assert_called_once_with(
            "/data/league/directory", payload=expected_payload
        )
        self.assertEqual(leagues, mock_get_resource.return_value)

    @patch.object(irDataClient, "_get_resource")
    def test_league_directory_with_all_params(self, mock_get_resource):
        # Mock return value
        mock_get_resource.return_value = {"leagues": ["league1", "league2"]}

        # Setup all parameters
        search = "Test League"
        tag = "test"
        restrict_to_member = True
        restrict_to_recruiting = True
        restrict_to_friends = True
        restrict_to_watched = True
        minimum_roster_count = 10
        maximum_roster_count = 50
        lowerbound = 2
        upperbound = 40
        sort = "leaguename"
        order = "desc"

        # Expected payload parameters
        expected_payload = {
            "search": search,
            "tag": tag,
            "restrict_to_member": restrict_to_member,
            "restrict_to_recruiting": restrict_to_recruiting,
            "restrict_to_friends": restrict_to_friends,
            "restrict_to_watched": restrict_to_watched,
            "minimum_roster_count": minimum_roster_count,
            "maximum_roster_count": maximum_roster_count,
            "lowerbound": lowerbound,
            "upperbound": upperbound,
            "sort": sort,
            "order": order,
        }

        # Call the method with all parameters
        leagues = self.client.league_directory(
            search=search,
            tag=tag,
            restrict_to_member=restrict_to_member,
            restrict_to_recruiting=restrict_to_recruiting,
            restrict_to_friends=restrict_to_friends,
            restrict_to_watched=restrict_to_watched,
            minimum_roster_count=minimum_roster_count,
            maximum_roster_count=maximum_roster_count,
            lowerbound=lowerbound,
            upperbound=upperbound,
            sort=sort,
            order=order,
        )

        # Assertions to ensure _get_resource is called with correct parameters
        mock_get_resource.assert_called_once_with(
            "/data/league/directory", payload=expected_payload
        )
        self.assertEqual(leagues, mock_get_resource.return_value)

    @patch.object(irDataClient, "_get_resource")
    def test_league_get_points_systems_with_league_id(self, mock_get_resource):
        # Mock return value
        mock_get_resource.return_value = {"points_systems": ["system1", "system2"]}

        league_id = 123
        expected_payload = {"league_id": league_id}

        # Call the method with only league_id
        points_systems = self.client.league_get_points_systems(league_id)

        # Assertions to ensure _get_resource is called with correct parameters
        mock_get_resource.assert_called_once_with(
            "/data/league/get_points_systems", payload=expected_payload
        )
        self.assertEqual(points_systems, mock_get_resource.return_value)

    @patch.object(irDataClient, "_get_resource")
    def test_league_get_points_systems_with_league_id_and_season_id(
        self, mock_get_resource
    ):
        # Mock return value
        mock_get_resource.return_value = {"points_systems": ["system1", "system2"]}

        league_id = 123
        season_id = 456
        expected_payload = {"league_id": league_id, "season_id": season_id}

        # Call the method with both league_id and season_id
        points_systems = self.client.league_get_points_systems(league_id, season_id)

        # Assertions to ensure _get_resource is called with correct parameters
        mock_get_resource.assert_called_once_with(
            "/data/league/get_points_systems", payload=expected_payload
        )
        self.assertEqual(points_systems, mock_get_resource.return_value)

    @patch.object(irDataClient, "_get_resource")
    @patch.object(irDataClient, "_get_resource_or_link")
    def test_league_roster(self, mock_get_resource_or_link, mock_get_resource):
        mock_get_resource_or_link.return_value = [{"data": "roster_data"}]
        league_id = 123
        include_licenses = True
        expected_payload = {
            "league_id": league_id,
            "include_licenses": include_licenses,
        }

        result = self.client.league_roster(league_id, include_licenses)

        mock_get_resource.assert_called_once_with(
            "/data/league/roster", payload=expected_payload
        )
        mock_get_resource_or_link.assert_called_once_with(
            mock_get_resource.return_value["data_url"]
        )
        self.assertEqual(result, mock_get_resource_or_link.return_value[0])

    @patch.object(irDataClient, "_get_resource")
    def test_league_seasons(self, mock_get_resource):
        mock_get_resource.return_value = [{"season": "season_data"}]
        league_id = 123
        retired = True
        expected_payload = {"league_id": league_id, "retired": retired}

        result = self.client.league_seasons(league_id, retired)

        mock_get_resource.assert_called_once_with(
            "/data/league/seasons", payload=expected_payload
        )
        self.assertEqual(result, mock_get_resource.return_value)

    @patch.object(irDataClient, "_get_resource")
    def test_league_season_standings(self, mock_get_resource):
        mock_get_resource.return_value = {"standings": "standings_data"}
        league_id = 123
        season_id = 456
        car_class_id = 789
        car_id = 1011
        expected_payload = {
            "league_id": league_id,
            "season_id": season_id,
            "car_class_id": car_class_id,
            "car_id": car_id,
        }

        result = self.client.league_season_standings(
            league_id, season_id, car_class_id, car_id
        )

        mock_get_resource.assert_called_once_with(
            "/data/league/season_standings", payload=expected_payload
        )
        self.assertEqual(result, mock_get_resource.return_value)

    @patch.object(irDataClient, "_get_resource")
    def test_league_season_sessions(self, mock_get_resource):
        mock_get_resource.return_value = [{"session": "session_data"}]
        league_id = 123
        season_id = 456
        results_only = True
        expected_payload = {
            "league_id": league_id,
            "season_id": season_id,
            "results_only": results_only,
        }

        result = self.client.league_season_sessions(league_id, season_id, results_only)

        mock_get_resource.assert_called_once_with(
            "/data/league/season_sessions", payload=expected_payload
        )
        self.assertEqual(result, mock_get_resource.return_value)

    @patch.object(irDataClient, "_get_resource")
    def test_lookup_club_history(self, mock_get_resource):
        mock_get_resource.return_value = [{"history": "club_history_data"}]
        season_year = 2021
        season_quarter = 3
        expected_payload = {
            "season_year": season_year,
            "season_quarter": season_quarter,
        }

        result = self.client.lookup_club_history(season_year, season_quarter)

        mock_get_resource.assert_called_once_with(
            "/data/lookup/club_history", payload=expected_payload
        )
        self.assertEqual(result, mock_get_resource.return_value)

    @patch.object(irDataClient, "_get_resource")
    def test_lookup_drivers(self, mock_get_resource):
        mock_get_resource.return_value = [{"driver": "driver_data"}]
        search_term = "Smith"
        league_id = 123
        expected_payload = {"search_term": search_term, "league_id": league_id}

        result = self.client.lookup_drivers(search_term, league_id)

        mock_get_resource.assert_called_once_with(
            "/data/lookup/drivers", payload=expected_payload
        )
        self.assertEqual(result, mock_get_resource.return_value)

    @patch.object(irDataClient, "_get_resource")
    @patch.object(irDataClient, "_get_chunks")
    def test_result_lap_chart_data(self, mock_get_chunks, mock_get_resource):
        mock_get_resource.return_value = {"data": {"chunk_info": ["chunks"]}}
        mock_get_chunks.return_value = {"lap_data": "lap_data"}
        subsession_id = 123
        simsession_number = 0
        expected_payload = {
            "subsession_id": subsession_id,
            "simsession_number": simsession_number,
        }

        result = self.client.result_lap_chart_data(subsession_id, simsession_number)

        mock_get_resource.assert_called_once_with(
            "/data/results/lap_chart_data", payload=expected_payload
        )
        self.assertEqual(result, mock_get_chunks.return_value)

    @patch.object(irDataClient, "_get_resource")
    @patch.object(irDataClient, "_get_chunks")
    def test_result_lap_data(self, mock_get_chunks, mock_get_resource):
        mock_get_resource.return_value = {"chunk_info": ["chunks"]}
        mock_get_chunks.return_value = {"lap": "lap_data"}
        subsession_id = 123
        simsession_number = 0
        cust_id = 456
        expected_payload = {
            "subsession_id": subsession_id,
            "simsession_number": simsession_number,
            "cust_id": cust_id,
        }

        result = self.client.result_lap_data(
            subsession_id, simsession_number, cust_id=cust_id
        )

        mock_get_chunks.assert_called_once()
        self.assertEqual(result, mock_get_chunks.return_value)

    @patch.object(irDataClient, "_get_resource")
    @patch.object(irDataClient, "_get_chunks")
    def test_result_event_log(self, mock_get_chunks, mock_get_resource):
        mock_get_resource.return_value = {"data": {"chunk_info": ["chunks"]}}
        mock_get_chunks.return_value = {"event": "event_log"}
        subsession_id = 123
        simsession_number = 0
        expected_payload = {
            "subsession_id": subsession_id,
            "simsession_number": simsession_number,
        }

        result = self.client.result_event_log(subsession_id, simsession_number)

        mock_get_resource.assert_called_once_with(
            "/data/results/event_log", payload=expected_payload
        )
        mock_get_chunks.assert_called_once()
        self.assertEqual(result, mock_get_chunks.return_value)

    @patch.object(irDataClient, "_get_resource")
    @patch.object(irDataClient, "_get_chunks")
    def test_result_search_hosted(self, mock_get_chunks, mock_get_resource):
        mock_get_chunks.return_value = [{"session": "hosted_session"}]
        start_range_begin = "2022-01-01T00:00:00Z"
        start_range_end = "2022-01-31T23:59:59Z"
        expected_payload = {
            "start_range_begin": start_range_begin,
            "start_range_end": start_range_end,
            "cust_id": 111111,
        }

        result = self.client.result_search_hosted(
            cust_id=111111,
            start_range_begin=start_range_begin,
            start_range_end=start_range_end,
        )

        mock_get_resource.assert_called_once_with(
            "/data/results/search_hosted", payload=expected_payload
        )
        mock_get_chunks.assert_called_once()
        self.assertEqual(result, mock_get_chunks.return_value)

    @patch.object(irDataClient, "_get_resource")
    def test_result_season_results(self, mock_get_resource):
        mock_get_resource.return_value = [{"result": "season_result"}]
        season_id = 123
        event_type = 2
        race_week_num = 5
        expected_payload = {
            "season_id": season_id,
            "event_type": event_type,
            "race_week_num": race_week_num,
        }

        result = self.client.result_season_results(
            season_id, event_type=event_type, race_week_num=race_week_num
        )

        mock_get_resource.assert_called_once_with(
            "/data/results/season_results", payload=expected_payload
        )
        self.assertEqual(result, mock_get_resource.return_value)

    @patch.object(irDataClient, "_get_resource")
    @patch.object(irDataClient, "_get_resource_or_link")
    def test_member_awards(self, mock_get_resource_or_link, mock_get_resource):
        mock_get_resource_or_link.return_value = [{"award": "award_data"}]
        cust_id = 123
        expected_payload = {"cust_id": cust_id}

        result = self.client.member_awards(cust_id)

        mock_get_resource.assert_called_once_with(
            "/data/member/awards", payload=expected_payload
        )
        mock_get_resource_or_link.assert_called_once()
        self.assertEqual(result, mock_get_resource_or_link.return_value[0])

    @patch.object(irDataClient, "_get_resource")
    def test_member_chart_data(self, mock_get_resource):
        mock_get_resource.return_value = {"chart_data": "chart_data"}
        cust_id = 123
        category_id = 2
        chart_type = 1
        expected_payload = {
            "category_id": category_id,
            "chart_type": chart_type,
            "cust_id": cust_id,
        }

        result = self.client.member_chart_data(cust_id, category_id, chart_type)

        mock_get_resource.assert_called_once_with(
            "/data/member/chart_data", payload=expected_payload
        )
        self.assertEqual(result, mock_get_resource.return_value)

    @patch.object(irDataClient, "_get_resource")
    def test_member_profile(self, mock_get_resource):
        mock_get_resource.return_value = {"profile": "profile_data"}
        cust_id = 123
        expected_payload = {"cust_id": cust_id}

        result = self.client.member_profile(cust_id)

        mock_get_resource.assert_called_once_with(
            "/data/member/profile", payload=expected_payload
        )
        self.assertEqual(result, mock_get_resource.return_value)

    @patch.object(irDataClient, "_get_resource")
    def test_stats_member_bests(self, mock_get_resource):
        mock_get_resource.return_value = {"bests": "best_data"}
        cust_id = 123
        car_id = 456
        expected_payload = {"cust_id": cust_id, "car_id": car_id}

        result = self.client.stats_member_bests(cust_id, car_id)

        mock_get_resource.assert_called_once_with(
            "/data/stats/member_bests", payload=expected_payload
        )
        self.assertEqual(result, mock_get_resource.return_value)

    @patch.object(irDataClient, "_get_resource")
    def test_stats_member_career(self, mock_get_resource):
        mock_get_resource.return_value = {"career": "career_data"}
        cust_id = 123
        expected_payload = {"cust_id": cust_id}

        result = self.client.stats_member_career(cust_id)

        mock_get_resource.assert_called_once_with(
            "/data/stats/member_career", payload=expected_payload
        )
        self.assertEqual(result, mock_get_resource.return_value)

    @patch.object(irDataClient, "_get_resource")
    def test_stats_member_recap(self, mock_get_resource):
        mock_get_resource.return_value = {"recap": "recap_data"}
        cust_id = 123
        year = 2021
        quarter = 3
        expected_payload = {"cust_id": cust_id, "year": year, "season": quarter}

        result = self.client.stats_member_recap(cust_id, year, quarter)

        mock_get_resource.assert_called_once_with(
            "/data/stats/member_recap", payload=expected_payload
        )
        self.assertEqual(result, mock_get_resource.return_value)

    @patch.object(irDataClient, "_get_resource")
    def test_stats_member_recent_races(self, mock_get_resource):
        mock_get_resource.return_value = [{"race": "recent_race"}]
        cust_id = 123
        expected_payload = {"cust_id": cust_id}

        result = self.client.stats_member_recent_races(cust_id)

        mock_get_resource.assert_called_once_with(
            "/data/stats/member_recent_races", payload=expected_payload
        )
        self.assertEqual(result, mock_get_resource.return_value)

    @patch.object(irDataClient, "_get_resource")
    def test_stats_member_summary(self, mock_get_resource):
        mock_get_resource.return_value = {"summary": "summary_data"}
        cust_id = 123
        expected_payload = {"cust_id": cust_id}

        result = self.client.stats_member_summary(cust_id)

        mock_get_resource.assert_called_once_with(
            "/data/stats/member_summary", payload=expected_payload
        )
        self.assertEqual(result, mock_get_resource.return_value)

    @patch.object(irDataClient, "_get_resource")
    def test_stats_member_yearly(self, mock_get_resource):
        mock_get_resource.return_value = {"yearly": "yearly_data"}
        cust_id = 123
        expected_payload = {"cust_id": cust_id}

        result = self.client.stats_member_yearly(cust_id)

        mock_get_resource.assert_called_once_with(
            "/data/stats/member_yearly", payload=expected_payload
        )
        self.assertEqual(result, mock_get_resource.return_value)

    @patch.object(irDataClient, "_get_resource")
    @patch.object(irDataClient, "_get_chunks")
    def test_stats_season_driver_standings(self, mock_get_chunks, mock_get_resource):
        mock_get_resource.return_value = {"data": {"chunk_info": ["chunks"]}}
        mock_get_chunks.return_value = {"standings": "driver_standings"}
        season_id = 123
        car_class_id = 456
        expected_payload = {"season_id": season_id, "car_class_id": car_class_id}

        result = self.client.stats_season_driver_standings(season_id, car_class_id)

        mock_get_resource.assert_called_once_with(
            "/data/stats/season_driver_standings", payload=expected_payload
        )
        mock_get_chunks.assert_called_once()
        self.assertEqual(result, mock_get_chunks.return_value)

    @patch.object(irDataClient, "_get_resource")
    @patch.object(irDataClient, "_get_chunks")
    def test_stats_season_supersession_standings(
        self, mock_get_chunks, mock_get_resource
    ):
        mock_get_resource.return_value = {"data": {"chunk_info": ["chunks"]}}
        mock_get_chunks.return_value = {"standings": "supersession_standings"}
        season_id = 123
        car_class_id = 456
        expected_payload = {"season_id": season_id, "car_class_id": car_class_id}

        result = self.client.stats_season_supersession_standings(
            season_id, car_class_id
        )

        mock_get_resource.assert_called_once_with(
            "/data/stats/season_supersession_standings", payload=expected_payload
        )
        mock_get_chunks.assert_called_once()
        self.assertEqual(result, mock_get_chunks.return_value)

    @patch.object(irDataClient, "_get_resource")
    @patch.object(irDataClient, "_get_chunks")
    def test_stats_season_team_standings(self, mock_get_chunks, mock_get_resource):
        mock_get_resource.return_value = {"data": {"chunk_info": ["chunks"]}}
        mock_get_chunks.return_value = {"standings": "team_standings"}
        season_id = 123
        car_class_id = 456
        expected_payload = {"season_id": season_id, "car_class_id": car_class_id}

        result = self.client.stats_season_team_standings(season_id, car_class_id)

        mock_get_resource.assert_called_once_with(
            "/data/stats/season_team_standings", payload=expected_payload
        )
        mock_get_chunks.assert_called_once()
        self.assertEqual(result, mock_get_chunks.return_value)

    @patch.object(irDataClient, "_get_resource")
    @patch.object(irDataClient, "_get_chunks")
    def test_stats_season_tt_standings(self, mock_get_chunks, mock_get_resource):
        mock_get_resource.return_value = {"data": {"chunk_info": ["chunks"]}}
        mock_get_chunks.return_value = {"standings": "tt_standings"}
        season_id = 123
        car_class_id = 456
        expected_payload = {"season_id": season_id, "car_class_id": car_class_id}

        result = self.client.stats_season_tt_standings(season_id, car_class_id)

        mock_get_resource.assert_called_once_with(
            "/data/stats/season_tt_standings", payload=expected_payload
        )
        mock_get_chunks.assert_called_once()
        self.assertEqual(result, mock_get_chunks.return_value)

    @patch.object(irDataClient, "_get_resource")
    @patch.object(irDataClient, "_get_chunks")
    def test_stats_season_tt_results(self, mock_get_chunks, mock_get_resource):
        mock_get_resource.return_value = {"data": {"chunk_info": ["chunks"]}}
        mock_get_chunks.return_value = {"results": "tt_results"}
        season_id = 123
        car_class_id = 456
        race_week_num = 7
        expected_payload = {
            "season_id": season_id,
            "car_class_id": car_class_id,
            "race_week_num": race_week_num,
        }

        result = self.client.stats_season_tt_results(
            season_id, car_class_id, race_week_num
        )

        mock_get_resource.assert_called_once_with(
            "/data/stats/season_tt_results", payload=expected_payload
        )
        mock_get_chunks.assert_called_once()
        self.assertEqual(result, mock_get_chunks.return_value)

    @patch.object(irDataClient, "_get_resource")
    @patch.object(irDataClient, "_get_chunks")
    def test_stats_season_qualify_results(self, mock_get_chunks, mock_get_resource):
        mock_get_resource.return_value = {"data": {"chunk_info": ["chunks"]}}
        mock_get_chunks.return_value = {"records": "qualify_results"}
        season_id = 123
        car_class_id = 456
        race_week_num = 7
        expected_payload = {
            "season_id": season_id,
            "car_class_id": car_class_id,
            "race_week_num": race_week_num,
        }

        result = self.client.stats_season_qualify_results(
            season_id, car_class_id, race_week_num
        )

        mock_get_resource.assert_called_once_with(
            "/data/stats/season_qualify_results", payload=expected_payload
        )
        mock_get_chunks.assert_called_once()
        self.assertEqual(result, mock_get_chunks.return_value)

    @patch.object(irDataClient, "_get_chunks")
    @patch.object(irDataClient, "_get_resource")
    def test_stats_world_records(self, mock_get_resource, mock_get_chunks):
        mock_get_resource.return_value = {"data": {"chunk_info": ["chunks"]}}
        mock_get_chunks.return_value = {"records": "world_records"}
        car_id = 123
        track_id = 456
        expected_payload = {"car_id": car_id, "track_id": track_id}

        result = self.client.stats_world_records(car_id, track_id)

        mock_get_resource.assert_called_once_with(
            "/data/stats/world_records", payload=expected_payload
        )
        mock_get_chunks.assert_called_once()
        self.assertEqual(result, mock_get_chunks.return_value)

    @patch.object(irDataClient, "_get_resource")
    def test_team(self, mock_get_resource):
        mock_get_resource.return_value = {"team": "team_data"}
        team_id = 123
        include_licenses = True
        expected_payload = {"team_id": team_id, "include_licenses": include_licenses}

        result = self.client.team(team_id, include_licenses)

        mock_get_resource.assert_called_once_with(
            "/data/team/get", payload=expected_payload
        )
        self.assertEqual(result, mock_get_resource.return_value)

    @patch.object(irDataClient, "_get_resource")
    def test_season_list(self, mock_get_resource):
        mock_get_resource.return_value = [{"season": "season_list"}]
        season_year = 2022
        season_quarter = 1
        expected_payload = {
            "season_year": season_year,
            "season_quarter": season_quarter,
        }

        result = self.client.season_list(season_year, season_quarter)

        mock_get_resource.assert_called_once_with(
            "/data/season/list", payload=expected_payload
        )
        self.assertEqual(result, mock_get_resource.return_value)

    @patch.object(irDataClient, "_get_resource")
    def test_season_race_guide(self, mock_get_resource):
        mock_get_resource.return_value = [{"race_guide": "race_guide"}]
        start_from = "2022-06-01T00:00:00Z"
        include_end_after_from = True
        expected_payload = {
            "from": start_from,
            "include_end_after_from": include_end_after_from,
        }

        result = self.client.season_race_guide(start_from, include_end_after_from)

        mock_get_resource.assert_called_once_with(
            "/data/season/race_guide", payload=expected_payload
        )
        self.assertEqual(result, mock_get_resource.return_value)

    @patch.object(irDataClient, "_get_resource")
    def test_series_past_seasons(self, mock_get_resource):
        series_id = 123
        mock_get_resource.return_value = {"series": [{"series_id": series_id}]}
        expected_payload = {"series_id": series_id}

        result = self.client.series_past_seasons(series_id)

        mock_get_resource.assert_called_once_with(
            "/data/series/past_seasons", payload=expected_payload
        )
        self.assertEqual(result, mock_get_resource.return_value.get("series"))

    @patch.object(irDataClient, "_get_resource")
    def test_series_seasons(self, mock_get_resource):
        mock_get_resource.return_value = [{"season": "season_data"}]
        include_series = True
        expected_payload = {"include_series": include_series}

        result = self.client.series_seasons(include_series)

        mock_get_resource.assert_called_once_with(
            "/data/series/seasons", payload=expected_payload
        )
        self.assertEqual(result, mock_get_resource.return_value)


if __name__ == "__main__":
    unittest.main()
