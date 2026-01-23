import base64
import hashlib
import json
import unittest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import requests
from pydantic_core import ValidationError

from src.iracingdataapi.client import irDataClient
from src.iracingdataapi.exceptions import AccessTokenInvalid
from src.iracingdataapi.models.cars import CarWithAsset
from src.iracingdataapi.models.laps import ChartLap, Lap
from src.iracingdataapi.models.leagues import (
    DriverStanding,
    League,
    LeagueDirectoryItem,
    LeaguePointsSystem,
    LeagueSeason,
    RosterItem,
)
from src.iracingdataapi.models.lookups import LookupDriver
from src.iracingdataapi.models.members import DriverFromCSV, MemberAward, MemberLicense
from src.iracingdataapi.models.responses import (
    CarAssetsResponse,
    CarGetResponse,
    LeagueCustLeagueSessionsResponse,
    LeagueDirectoryResponse,
    LeagueGetPointsSystemsResponse,
    LeagueRosterResponse,
    LeagueSeasonSessionsResponse,
    LeagueSeasonsResponse,
    LeagueSeasonStandingsResponse,
    ResultsGetResponse,
    ResultsSeasonResultsResponse,
    SeriesAssetsResponse,
    SeriesGetResponse,
    TrackAssetsResponse,
    TrackGetResponse,
)
from src.iracingdataapi.models.results import ResultEventLog
from src.iracingdataapi.models.series import SeriesWithAsset
from src.iracingdataapi.models.sessions import LeagueSession
from src.iracingdataapi.models.tracks import TrackWithAsset


class TestIrDataClient(unittest.TestCase):
    maxDiff = None

    def setUp(self):
        self.client = irDataClient(access_token="some-mock-token", use_pydantic=True)
        self.access_token_client = self.client
        # Client for tests with incomplete mock data
        self.dict_client = irDataClient(
            username="test_user", password="test_password", use_pydantic=False
        )

    def _get_mock_data(self, filename):
        with open(f"tests/mock_return_data/{filename}", "r", encoding="utf-8") as file:
            return json.loads(file.read())

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
        mock_get_resource.return_value = self._get_mock_data("result.json")

        subsession_id = 12345
        include_licenses = True
        response = self.client.result(
            subsession_id=subsession_id, include_licenses=include_licenses
        )

        mock_get_resource.assert_called_once_with(
            "/data/results/get",
            payload={
                "subsession_id": subsession_id,
                "include_licenses": include_licenses,
            },
        )
        self.assertIsInstance(response, ResultsGetResponse)
        self.assertEqual(response.subsession_id, 82263872)

    @patch.object(irDataClient, "_get_resource")
    def test_result_with_parameters_and_team(self, mock_get_resource):
        mock_get_resource.return_value = self._get_mock_data("result_with_team.json")

        subsession_id = 12345
        include_licenses = True
        response = self.client.result(
            subsession_id=subsession_id, include_licenses=include_licenses
        )

        mock_get_resource.assert_called_once_with(
            "/data/results/get",
            payload={
                "subsession_id": subsession_id,
                "include_licenses": include_licenses,
            },
        )
        self.assertIsInstance(response, ResultsGetResponse)
        self.assertEqual(response.subsession_id, 82799850)

    @patch.object(irDataClient, "_get_resource")
    def test_result_without_optional_parameters(self, mock_get_resource):
        mock_get_resource.return_value = self._get_mock_data("result.json")

        subsession_id = 12345
        self.client.result(subsession_id=subsession_id)

        mock_get_resource.assert_called_once_with(
            "/data/results/get",
            payload={"subsession_id": subsession_id, "include_licenses": False},
        )

    def test_result_missing_subsession_id(self):
        with self.assertRaises(ValidationError) as context:
            self.client.result()
        self.assertIn(
            "1 validation error for irDataClient.result\nsubsession_id",
            str(context.exception),
        )

    @patch.object(irDataClient, "_get_resource")
    def test_season_spectator_subsessionids_with_default_event_types(
        self, mock_get_resource
    ):

        mock_get_resource.return_value = self._get_mock_data(
            "season_spectator_subsessionids.json"
        )

        self.client.season_spectator_subsessionids()

        mock_get_resource.assert_called_once_with(
            "/data/season/spectator_subsessionids", payload={"event_types": "2,3,4,5"}
        )

    @patch.object(irDataClient, "_get_resource")
    def test_season_spectator_subsessionids_with_empty_response(
        self, mock_get_resource
    ):

        mock_get_resource.return_value = {
            "subsession_ids": [],
            "success": True,
            "event_types": [2, 3, 4, 5],
        }

        self.client.season_spectator_subsessionids()

        mock_get_resource.assert_called_once_with(
            "/data/season/spectator_subsessionids", payload={"event_types": "2,3,4,5"}
        )

    @patch.object(irDataClient, "_get_resource")
    def test_hosted_combined_sessions_with_package_id(self, mock_get_resource):
        mock_get_resource.return_value = self._get_mock_data(
            "hosted_combined_sessions.json"
        )

        package_id = 456
        self.client.hosted_combined_sessions(package_id=package_id)

        mock_get_resource.assert_called_once_with(
            "/data/hosted/combined_sessions", payload={"package_id": package_id}
        )

    @patch.object(irDataClient, "_get_resource")
    def test_hosted_combined_sessions_without_package_id(self, mock_get_resource):
        mock_get_resource.return_value = self._get_mock_data(
            "hosted_combined_sessions.json"
        )

        self.client.hosted_combined_sessions()

        mock_get_resource.assert_called_once_with(
            "/data/hosted/combined_sessions", payload={}
        )

    @patch.object(irDataClient, "_get_chunks")
    @patch.object(irDataClient, "_get_resource")
    def test_result_search_series_with_required_parameters(
        self, mock_get_resource, mock_get_chunks
    ):
        mock_get_resource.return_value = {"data": {"chunk_info": "chunk_data"}}
        mock_get_chunks.return_value = self._get_mock_data("result_search_series.json")

        season_year = 2021
        season_quarter = 2
        self.client.result_search_series(
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

    @patch.object(irDataClient, "_get_chunks")
    @patch.object(irDataClient, "_get_resource")
    def test_result_search_series_with_all_parameters(
        self, mock_get_resource, mock_get_chunks
    ):
        mock_get_resource.return_value = {"data": {"chunk_info": "chunk_data"}}
        mock_get_chunks.return_value = self._get_mock_data("result_search_series.json")

        season_year = 2021
        season_quarter = 2
        start_range_begin = datetime(2021, 1, 1, tzinfo=timezone.utc)
        start_range_end = "2021-01-31T23:59:00Z"
        finish_range_begin = datetime(2021, 1, 1, tzinfo=timezone.utc)
        finish_range_end = "2021-01-31T23:59:00Z"
        cust_id = 12345
        series_id = 67890
        race_week_num = 3
        official_only = True
        event_types = [2, 3]
        category_ids = [1, 2]

        self.client.result_search_series(
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
                "start_range_begin": "2021-01-01T00:00:00Z",
                "start_range_end": start_range_end,
                "finish_range_begin": "2021-01-01T00:00:00Z",
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

    @patch.object(irDataClient, "_get_chunks")
    @patch.object(irDataClient, "_get_resource")
    def test_result_search_series_with_partial_parameters(
        self, mock_get_resource, mock_get_chunks
    ):
        mock_get_resource.return_value = {"data": {"chunk_info": "chunk_data"}}
        mock_get_chunks.return_value = self._get_mock_data("result_search_series.json")

        start_range_begin = "2021-01-01T00:00:00Z"
        finish_range_begin = "2021-01-01T00:00:00Z"
        cust_id = 12345

        self.client.result_search_series(
            start_range_begin=start_range_begin,
            finish_range_begin=finish_range_begin,
            cust_id=cust_id,
        )

        mock_get_resource.assert_called_once_with(
            "/data/results/search_series",
            payload={
                "start_range_begin": "2021-01-01T00:00:00Z",
                "finish_range_begin": "2021-01-01T00:00:00Z",
                "cust_id": 12345,
                "official_only": True,
            },
        )
        mock_get_chunks.assert_called_once_with("chunk_data")

    @patch.object(irDataClient, "_get_chunks")
    @patch.object(irDataClient, "_get_resource")
    def test_result_search_series_raises_without_required_parameters(
        self, mock_get_resource, mock_get_chunks
    ):
        with self.assertRaises(ValueError) as context:
            self.client.result_search_series()
        self.assertIn(
            "Provide (season_year & season_quarter) or a date range (start_range_begin or finish_range_begin)",
            str(context.exception),
        )
        mock_get_resource.assert_not_called()
        mock_get_chunks.assert_not_called()

    @patch.object(irDataClient, "_get_chunks")
    @patch.object(irDataClient, "_get_resource")
    def test_result_search_series_passes_false_params(
        self, mock_get_resource, mock_get_chunks
    ):
        mock_get_resource.return_value = {"data": {"chunk_info": "chunk_data"}}
        mock_get_chunks.return_value = self._get_mock_data("result_search_series.json")

        season_year = 2021
        season_quarter = 2
        race_week_num = 0
        official_only = False

        self.client.result_search_series(
            season_year=season_year,
            season_quarter=season_quarter,
            race_week_num=race_week_num,
            official_only=official_only,
        )

        mock_get_resource.assert_called_once_with(
            "/data/results/search_series",
            payload={
                "season_year": 2021,
                "season_quarter": 2,
                "race_week_num": 0,
                "official_only": False,
            },
        )
        mock_get_chunks.assert_called_once_with("chunk_data")

    @patch.object(irDataClient, "_get_resource")
    def test_member_with_required_parameters(self, mock_get_resource):
        mock_get_resource.return_value = self._get_mock_data("member.json")

        cust_id = 12345
        self.client.member(cust_id=cust_id)

        mock_get_resource.assert_called_once_with(
            "/data/member/get", payload={"cust_ids": cust_id, "include_licenses": False}
        )

    @patch.object(irDataClient, "_get_resource")
    def test_member_with_all_parameters(self, mock_get_resource):
        mock_get_resource.return_value = self._get_mock_data("member.json")

        cust_id = 12345
        include_licenses = True
        self.client.member(cust_id=cust_id, include_licenses=include_licenses)

        mock_get_resource.assert_called_once_with(
            "/data/member/get",
            payload={"cust_ids": cust_id, "include_licenses": include_licenses},
        )

    def test_member_missing_cust_id(self):
        with self.assertRaises(ValidationError) as context:
            self.client.member()
        self.assertIn(
            "1 validation error for irDataClient.member\ncust_id",
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
        mock_print.assert_called_with(
            "Warning: Row length does not match headers length"
        )

    @patch.object(irDataClient, "get_cars")
    @patch.object(irDataClient, "get_cars_assets")
    def test_cars_property(self, mock_get_cars_assets, mock_get_cars):
        # Setup mock return values
        mock_get_cars.return_value = CarGetResponse(
            self._get_mock_data("get_cars.json")
        )
        mock_get_cars_assets.return_value = CarAssetsResponse(
            self._get_mock_data("get_cars_assets.json")
        )

        # Access the property to trigger the chain of method calls
        cars_with_assets = self.client.cars

        # Assertions to ensure cars property includes assets
        mock_get_cars.assert_called_once()
        mock_get_cars_assets.assert_called_once()

        self.assertIsInstance(cars_with_assets, list)
        self.assertIsInstance(cars_with_assets[0], CarWithAsset)

    @patch.object(irDataClient, "get_tracks")
    @patch.object(irDataClient, "get_tracks_assets")
    def test_tracks_property(self, mock_get_tracks_assets, mock_get_tracks):
        # Setup mock return values
        mock_get_tracks.return_value = TrackGetResponse(
            self._get_mock_data("get_tracks.json")
        )
        mock_get_tracks_assets.return_value = TrackAssetsResponse(
            self._get_mock_data("get_tracks_assets.json")
        )

        # Access the property to trigger the chain of method calls
        tracks_with_assets = self.client.tracks

        # Assertions to ensure tracks property includes assets
        mock_get_tracks.assert_called_once()
        mock_get_tracks_assets.assert_called_once()

        self.assertIsInstance(tracks_with_assets, list)
        self.assertIsInstance(tracks_with_assets[0], TrackWithAsset)

    @patch.object(irDataClient, "get_series")
    @patch.object(irDataClient, "get_series_assets")
    def test_series_property(self, mock_get_series_assets, mock_get_series):
        # Setup mock return values
        mock_get_series.return_value = SeriesGetResponse(
            self._get_mock_data("get_series.json")
        )
        mock_get_series_assets.return_value = SeriesAssetsResponse(
            self._get_mock_data("get_series_assets.json")
        )

        # Access the property to trigger the chain of method calls
        series_with_assets = self.client.series

        # Assertions to ensure series property includes assets
        mock_get_series.assert_called_once()
        mock_get_series_assets.assert_called_once()

        self.assertIsInstance(series_with_assets, list)
        self.assertIsInstance(series_with_assets[0], SeriesWithAsset)

    @patch.object(irDataClient, "_get_resource")
    def test_driver_list(self, mock_get_resource):
        # Setup mock return values for different categories
        mock_get_resource.return_value = self._get_mock_data("driver_list.json")

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
                self.assertIsInstance(drivers, list)
                self.assertIsInstance(drivers[0], DriverFromCSV)

        # Test for invalid category ID
        with self.assertRaises(ValidationError) as context:
            self.client.driver_list(99)
        # Just check that error message contains the expected parts (ignore version number)
        error_str = str(context.exception)
        self.assertIn("Input should be less than or equal to 6", error_str)
        self.assertIn("input_value=99", error_str)

    @patch.object(irDataClient, "_get_resource")
    def test_league_get_with_id(self, mock_get_resource):
        # Mock return value with complete required fields
        mock_get_resource.return_value = self._get_mock_data("league_get.json")

        expected_payload = {
            "league_id": 123,
            "include_licenses": False,
        }

        # Call the method
        league_info = self.client.league_get(123)

        # Assertions to ensure _get_resource is called with correct parameters
        mock_get_resource.assert_called_once_with(
            "/data/league/get", payload=expected_payload
        )
        self.assertIsInstance(league_info, League)

    @patch.object(irDataClient, "_get_resource")
    def test_league_get_include_licenses(self, mock_get_resource):
        # Mock return value with complete required fields
        mock_get_resource.return_value = self._get_mock_data(
            "league_get_with_licenses.json"
        )

        expected_payload = {
            "league_id": 123,
            "include_licenses": True,
        }

        # Call the method
        league_info = self.client.league_get(123, include_licenses=True)

        # Assertions to ensure _get_resource is called with correct parameters
        mock_get_resource.assert_called_once_with(
            "/data/league/get", payload=expected_payload
        )
        self.assertIsInstance(league_info, League)
        self.assertIsInstance(league_info.roster[0].licenses[0], MemberLicense)

    def test_league_get_without_id(self):
        # Ensure the method raises RuntimeError when no league_id is provided
        with self.assertRaises(RuntimeError) as context:
            self.client.league_get()
        self.assertEqual(str(context.exception), "Please supply a league_id")

    @patch.object(irDataClient, "_get_resource")
    def test_league_cust_league_sessions_no_params(self, mock_get_resource):
        # Mock return value
        mock_get_resource.return_value = self._get_mock_data(
            "league_cust_league_sessions.json"
        )

        expected_payload = {"mine": False}

        # Call the method without parameters
        response = self.client.league_cust_league_sessions()

        # Assertions to ensure _get_resource is called with correct parameters
        mock_get_resource.assert_called_once_with(
            "/data/league/cust_league_sessions", payload=expected_payload
        )
        self.assertIsInstance(response, LeagueCustLeagueSessionsResponse)
        self.assertIsInstance(response.sessions[0], LeagueSession)

    @patch.object(irDataClient, "_get_resource")
    def test_league_cust_league_sessions_with_params(self, mock_get_resource):
        # Mock return value
        mock_get_resource.return_value = self._get_mock_data(
            "league_cust_league_sessions_with_package.json"
        )

        expected_payload = {"mine": True, "package_id": 1234}

        # Call the method with parameters
        response = self.client.league_cust_league_sessions(mine=True, package_id=1234)

        # Assertions to ensure _get_resource is called with correct parameters
        mock_get_resource.assert_called_once_with(
            "/data/league/cust_league_sessions", payload=expected_payload
        )
        self.assertIsInstance(response, LeagueCustLeagueSessionsResponse)

    @patch.object(irDataClient, "_get_resource")
    def test_league_directory_default_params(self, mock_get_resource):
        # Mock return value
        mock_get_resource.return_value = self._get_mock_data("league_directory.json")

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
        response = self.client.league_directory()

        # Assertions to ensure _get_resource is called with correct parameters
        mock_get_resource.assert_called_once_with(
            "/data/league/directory", payload=expected_payload
        )
        self.assertIsInstance(response, LeagueDirectoryResponse)
        self.assertIsInstance(response.results_page[0], LeagueDirectoryItem)

    @patch.object(irDataClient, "_get_resource")
    def test_league_directory_with_all_params(self, mock_get_resource):
        # Mock return value
        mock_get_resource.return_value = self._get_mock_data(
            "league_directory_search.json"
        )

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
        self.client.league_directory(
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

    @patch.object(irDataClient, "_get_resource")
    def test_league_get_points_systems_with_league_id(self, mock_get_resource):
        # Mock return value
        mock_get_resource.return_value = self._get_mock_data(
            "league_get_points_systems.json"
        )

        league_id = 123
        expected_payload = {"league_id": league_id}

        # Call the method with only league_id
        response = self.client.league_get_points_systems(league_id)

        # Assertions to ensure _get_resource is called with correct parameters
        mock_get_resource.assert_called_once_with(
            "/data/league/get_points_systems", payload=expected_payload
        )
        self.assertIsInstance(response, LeagueGetPointsSystemsResponse)
        self.assertIsInstance(response.points_systems[0], LeaguePointsSystem)

    @patch.object(irDataClient, "_get_resource")
    def test_league_get_points_systems_with_league_id_and_season_id(
        self, mock_get_resource
    ):
        # Mock return value
        mock_get_resource.return_value = self._get_mock_data(
            "league_get_points_systems.json"
        )

        league_id = 123
        season_id = 456
        expected_payload = {"league_id": league_id, "season_id": season_id}

        # Call the method with both league_id and season_id
        self.client.league_get_points_systems(league_id, season_id)

        # Assertions to ensure _get_resource is called with correct parameters
        mock_get_resource.assert_called_once_with(
            "/data/league/get_points_systems", payload=expected_payload
        )

    @patch.object(irDataClient, "_get_resource")
    @patch.object(irDataClient, "_fetch_link_data")
    def test_league_roster(self, mock_fetch_link_data, mock_get_resource):
        mock_get_resource.return_value = {"data_url": "https://s3.amazonaws.com/test"}
        mock_fetch_link_data.return_value = self._get_mock_data("league_roster.json")
        league_id = 123
        include_licenses = False
        expected_payload = {
            "league_id": league_id,
            "include_licenses": include_licenses,
        }

        result = self.client.league_roster(league_id, include_licenses)

        mock_get_resource.assert_called_once_with(
            "/data/league/roster", payload=expected_payload
        )
        self.assertIsInstance(result, LeagueRosterResponse)
        self.assertIsInstance(result.roster[0], RosterItem)

    @patch.object(irDataClient, "_get_resource")
    @patch.object(irDataClient, "_fetch_link_data")
    def test_league_roster_with_licenses(self, mock_fetch_link_data, mock_get_resource):
        mock_get_resource.return_value = {"data_url": "https://s3.amazonaws.com/test"}
        mock_fetch_link_data.return_value = self._get_mock_data(
            "league_roster_with_licenses.json"
        )
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
        self.assertIsInstance(result, LeagueRosterResponse)
        self.assertIsInstance(result.roster[0], RosterItem)

    @patch.object(irDataClient, "_get_resource")
    def test_league_seasons(self, mock_get_resource):
        mock_get_resource.return_value = self._get_mock_data("league_seasons.json")
        league_id = 123
        retired = False
        expected_payload = {"league_id": league_id, "retired": retired}

        result = self.client.league_seasons(league_id, retired)

        mock_get_resource.assert_called_once_with(
            "/data/league/seasons", payload=expected_payload
        )
        self.assertIsInstance(result, LeagueSeasonsResponse)
        self.assertIsInstance(result.seasons[0], LeagueSeason)

    @patch.object(irDataClient, "_get_resource")
    def test_league_season_standings(self, mock_get_resource):
        mock_get_resource.return_value = self._get_mock_data(
            "league_season_standings.json"
        )

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
        self.assertIsInstance(result, LeagueSeasonStandingsResponse)
        self.assertIsInstance(result.standings.driver_standings[0], DriverStanding)

    @patch.object(irDataClient, "_get_resource")
    def test_league_season_sessions(self, mock_get_resource):
        mock_get_resource.return_value = self._get_mock_data(
            "league_season_sessions.json"
        )

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
        self.assertIsInstance(result, LeagueSeasonSessionsResponse)

    @patch.object(irDataClient, "_get_resource")
    def test_lookup_drivers(self, mock_get_resource):
        mock_data = self._get_mock_data("lookup_drivers.json")
        mock_get_resource.return_value = mock_data
        search_term = "Smith"
        league_id = 123
        expected_payload = {"search_term": search_term, "league_id": league_id}

        result = self.client.lookup_drivers(search_term, league_id)

        mock_get_resource.assert_called_once_with(
            "/data/lookup/drivers", payload=expected_payload
        )
        self.assertIsInstance(result, list)
        self.assertIsInstance(result[0], LookupDriver)
        self.assertEqual(result[0].display_name, mock_data[0]["display_name"])

    @patch.object(irDataClient, "_get_resource")
    @patch.object(irDataClient, "_get_chunks")
    def test_result_lap_chart_data(self, mock_get_chunks, mock_get_resource):
        mock_get_resource.return_value = {"data": {"chunk_info": ["chunks"]}}
        mock_get_chunks.return_value = self._get_mock_data("result_lap_chart_data.json")
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
        self.assertIsInstance(result, list)
        if len(result) > 0:
            self.assertIsInstance(result[0], ChartLap)

    @patch.object(irDataClient, "_get_resource")
    @patch.object(irDataClient, "_get_chunks")
    def test_result_lap_data(self, mock_get_chunks, mock_get_resource):
        mock_get_resource.return_value = {"chunk_info": ["chunks"]}
        mock_get_chunks.return_value = self._get_mock_data("result_lap_data.json")
        subsession_id = 123
        simsession_number = 0
        cust_id = 456

        result = self.client.result_lap_data(
            subsession_id, simsession_number, cust_id=cust_id
        )

        mock_get_chunks.assert_called_once()
        self.assertIsInstance(result, list)
        if len(result) > 0:
            self.assertIsInstance(result[0], Lap)

    @patch.object(irDataClient, "_get_resource")
    @patch.object(irDataClient, "_get_chunks")
    def test_result_event_log(self, mock_get_chunks, mock_get_resource):
        mock_get_resource.return_value = {"data": {"chunk_info": ["chunks"]}}
        mock_get_chunks.return_value = self._get_mock_data("result_event_log.json")
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
        self.assertIsInstance(result, list)
        if len(result) > 0:
            self.assertIsInstance(result[0], ResultEventLog)

    @patch.object(irDataClient, "_get_resource")
    @patch.object(irDataClient, "_get_chunks")
    def test_result_search_hosted_simple(self, mock_get_chunks, mock_get_resource):
        mock_get_chunks.return_value = self._get_mock_data("result_search_hosted.json")
        start_range_begin = "2022-01-01T00:00:00Z"
        start_range_end = "2022-01-31T23:59:59Z"
        expected_payload = {
            "start_range_begin": start_range_begin,
            "start_range_end": start_range_end,
            "cust_id": 111111,
        }

        self.client.result_search_hosted(
            cust_id=111111,
            start_range_begin=start_range_begin,
            start_range_end=start_range_end,
        )

        mock_get_resource.assert_called_once_with(
            "/data/results/search_hosted", payload=expected_payload
        )
        mock_get_chunks.assert_called_once()

    @patch.object(irDataClient, "_get_resource")
    def test_result_season_results(self, mock_get_resource):
        mock_get_resource.return_value = self._get_mock_data(
            "result_season_results.json"
        )
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
        self.assertIsInstance(result, ResultsSeasonResultsResponse)

    @patch.object(irDataClient, "_get_resource")
    @patch.object(irDataClient, "_fetch_link_data")
    def test_member_awards(self, mock_fetch_link_data, mock_get_resource):
        mock_get_resource.return_value = {"data_url": "https://s3.amazonaws.com/test"}
        mock_fetch_link_data.return_value = self._get_mock_data("member_awards.json")
        cust_id = 123
        expected_payload = {"cust_id": cust_id}

        result = self.client.member_awards(cust_id)

        mock_get_resource.assert_called_once_with(
            "/data/member/awards", payload=expected_payload
        )
        mock_fetch_link_data.assert_called_once_with("https://s3.amazonaws.com/test")
        self.assertIsInstance(result[0], MemberAward)

    @patch.object(irDataClient, "_get_resource")
    def test_member_chart_data(self, mock_get_resource):
        mock_get_resource.return_value = self._get_mock_data(
            "member_chart_data_irating.json"
        )
        cust_id = 123
        category_id = 2
        chart_type = 1
        expected_payload = {
            "category_id": category_id,
            "chart_type": chart_type,
            "cust_id": cust_id,
        }

        self.client.member_chart_data(cust_id, category_id, chart_type)

        mock_get_resource.assert_called_once_with(
            "/data/member/chart_data", payload=expected_payload
        )

    @patch.object(irDataClient, "_get_resource")
    def test_member_profile(self, mock_get_resource):
        mock_get_resource.return_value = self._get_mock_data("member_profile.json")
        cust_id = 123
        expected_payload = {"cust_id": cust_id}

        self.client.member_profile(cust_id)

        mock_get_resource.assert_called_once_with(
            "/data/member/profile", payload=expected_payload
        )

    @patch.object(irDataClient, "_get_resource")
    def test_member_profile_no_activity(self, mock_get_resource):
        mock_get_resource.return_value = self._get_mock_data("member_profile_no_activity.json")
        cust_id = 123
        expected_payload = {"cust_id": cust_id}

        self.client.member_profile(cust_id)

        mock_get_resource.assert_called_once_with(
            "/data/member/profile", payload=expected_payload
        )

    @patch.object(irDataClient, "_get_resource")
    def test_stats_member_bests(self, mock_get_resource):
        mock_get_resource.return_value = self._get_mock_data("stats_member_bests.json")
        cust_id = 123
        car_id = 456
        expected_payload = {"cust_id": cust_id, "car_id": car_id}

        self.client.stats_member_bests(cust_id, car_id)

        mock_get_resource.assert_called_once_with(
            "/data/stats/member_bests", payload=expected_payload
        )

    @patch.object(irDataClient, "_get_resource")
    def test_stats_member_career(self, mock_get_resource):
        mock_get_resource.return_value = self._get_mock_data("stats_member_career.json")
        cust_id = 123
        expected_payload = {"cust_id": cust_id}

        self.client.stats_member_career(cust_id)

        mock_get_resource.assert_called_once_with(
            "/data/stats/member_career", payload=expected_payload
        )

    @patch.object(irDataClient, "_get_resource")
    def test_stats_member_recap(self, mock_get_resource):
        mock_get_resource.return_value = self._get_mock_data("stats_member_recap.json")
        cust_id = 123
        year = 2021
        quarter = 3
        expected_payload = {"cust_id": cust_id, "year": year, "season": quarter}

        self.client.stats_member_recap(cust_id, year, quarter)

        mock_get_resource.assert_called_once_with(
            "/data/stats/member_recap", payload=expected_payload
        )

    @patch.object(irDataClient, "_get_resource")
    def test_stats_member_recent_races(self, mock_get_resource):
        mock_get_resource.return_value = self._get_mock_data(
            "stats_member_recent_races.json"
        )
        cust_id = 123
        expected_payload = {"cust_id": cust_id}

        self.client.stats_member_recent_races(cust_id)

        mock_get_resource.assert_called_once_with(
            "/data/stats/member_recent_races", payload=expected_payload
        )

    @patch.object(irDataClient, "_get_resource")
    def test_stats_member_summary(self, mock_get_resource):
        mock_get_resource.return_value = self._get_mock_data(
            "stats_member_summary.json"
        )
        cust_id = 123
        expected_payload = {"cust_id": cust_id}

        self.client.stats_member_summary(cust_id)

        mock_get_resource.assert_called_once_with(
            "/data/stats/member_summary", payload=expected_payload
        )

    @patch.object(irDataClient, "_get_resource")
    def test_stats_member_yearly(self, mock_get_resource):
        mock_get_resource.return_value = self._get_mock_data("stats_member_yearly.json")
        cust_id = 123
        expected_payload = {"cust_id": cust_id}

        self.client.stats_member_yearly(cust_id)

        mock_get_resource.assert_called_once_with(
            "/data/stats/member_yearly", payload=expected_payload
        )

    @patch.object(irDataClient, "_get_resource")
    @patch.object(irDataClient, "_get_chunks")
    def test_stats_season_driver_standings(self, mock_get_chunks, mock_get_resource):
        mock_get_resource.return_value = {"data": {"chunk_info": ["chunks"]}}
        mock_get_chunks.return_value = self._get_mock_data(
            "stats_season_driver_standings.json"
        )
        season_id = 123
        car_class_id = 456
        expected_payload = {"season_id": season_id, "car_class_id": car_class_id}

        self.client.stats_season_driver_standings(season_id, car_class_id)

        mock_get_resource.assert_called_once_with(
            "/data/stats/season_driver_standings", payload=expected_payload
        )
        mock_get_chunks.assert_called_once()

        # test for 0 inputs which used to remove the input
        self.client.stats_season_driver_standings(
            season_id=season_id, car_class_id=car_class_id, race_week_num=0, division=0
        )
        mock_get_resource.assert_called_with(
            "/data/stats/season_driver_standings",
            payload={
                "season_id": season_id,
                "car_class_id": car_class_id,
                "race_week_num": 0,
                "division": 0,
            },
        )

    @patch.object(irDataClient, "_get_resource")
    @patch.object(irDataClient, "_get_chunks")
    def test_stats_season_supersession_standings(
        self, mock_get_chunks, mock_get_resource
    ):
        mock_get_resource.return_value = {"data": {"chunk_info": ["chunks"]}}
        mock_get_chunks.return_value = self._get_mock_data(
            "stats_season_supersession_standings.json"
        )
        season_id = 123
        car_class_id = 456
        expected_payload = {"season_id": season_id, "car_class_id": car_class_id}

        self.client.stats_season_supersession_standings(season_id, car_class_id)

        mock_get_resource.assert_called_once_with(
            "/data/stats/season_supersession_standings", payload=expected_payload
        )
        mock_get_chunks.assert_called_once()

        # test for 0 inputs which used to remove the input
        self.client.stats_season_supersession_standings(
            season_id=season_id, car_class_id=car_class_id, race_week_num=0, division=0
        )
        mock_get_resource.assert_called_with(
            "/data/stats/season_supersession_standings",
            payload={
                "season_id": season_id,
                "car_class_id": car_class_id,
                "race_week_num": 0,
                "division": 0,
            },
        )

    @patch.object(irDataClient, "_get_resource")
    @patch.object(irDataClient, "_get_chunks")
    def test_stats_season_team_standings(self, mock_get_chunks, mock_get_resource):
        mock_get_resource.return_value = {"data": {"chunk_info": ["chunks"]}}

        season_id = 123
        car_class_id = 456
        expected_payload = {"season_id": season_id, "car_class_id": car_class_id}

        self.client.stats_season_team_standings(season_id, car_class_id)

        mock_get_resource.assert_called_once_with(
            "/data/stats/season_team_standings", payload=expected_payload
        )
        mock_get_chunks.assert_called_once()

        self.client.stats_season_team_standings(
            season_id, car_class_id, race_week_num=0
        )

        mock_get_resource.assert_called_with(
            "/data/stats/season_team_standings",
            payload={
                "season_id": season_id,
                "car_class_id": car_class_id,
                "race_week_num": 0,
            },
        )

    @patch.object(irDataClient, "_get_resource")
    @patch.object(irDataClient, "_get_chunks")
    def test_stats_season_tt_standings(self, mock_get_chunks, mock_get_resource):
        mock_get_resource.return_value = {"data": {"chunk_info": ["chunks"]}}
        mock_get_chunks.return_value = self._get_mock_data(
            "stats_season_tt_standings.json"
        )
        season_id = 123
        car_class_id = 456
        expected_payload = {"season_id": season_id, "car_class_id": car_class_id}

        self.client.stats_season_tt_standings(season_id, car_class_id)

        mock_get_resource.assert_called_once_with(
            "/data/stats/season_tt_standings", payload=expected_payload
        )
        mock_get_chunks.assert_called_once()

        self.client.stats_season_tt_standings(
            season_id, car_class_id, race_week_num=0, division=0
        )

        mock_get_resource.assert_called_with(
            "/data/stats/season_tt_standings",
            payload={
                "season_id": season_id,
                "car_class_id": car_class_id,
                "race_week_num": 0,
                "division": 0,
            },
        )

    @patch.object(irDataClient, "_get_resource")
    @patch.object(irDataClient, "_get_chunks")
    def test_stats_season_tt_results(self, mock_get_chunks, mock_get_resource):
        mock_get_resource.return_value = {"data": {"chunk_info": ["chunks"]}}
        mock_get_chunks.return_value = self._get_mock_data(
            "stats_season_tt_results.json"
        )
        season_id = 123
        car_class_id = 456
        race_week_num = 7
        expected_payload = {
            "season_id": season_id,
            "car_class_id": car_class_id,
            "race_week_num": race_week_num,
        }

        self.client.stats_season_tt_results(season_id, car_class_id, race_week_num)

        mock_get_resource.assert_called_once_with(
            "/data/stats/season_tt_results", payload=expected_payload
        )
        mock_get_chunks.assert_called_once()

        self.client.stats_season_tt_results(
            season_id, car_class_id, race_week_num, division=0
        )

        mock_get_resource.assert_called_with(
            "/data/stats/season_tt_results",
            payload={
                "season_id": season_id,
                "car_class_id": car_class_id,
                "race_week_num": race_week_num,
                "division": 0,
            },
        )

    @patch.object(irDataClient, "_get_resource")
    @patch.object(irDataClient, "_get_chunks")
    def test_stats_season_qualify_results(self, mock_get_chunks, mock_get_resource):
        mock_get_resource.return_value = {"data": {"chunk_info": ["chunks"]}}
        mock_get_chunks.return_value = self._get_mock_data(
            "stats_season_qualify_results.json"
        )
        season_id = 123
        car_class_id = 456
        race_week_num = 7
        expected_payload = {
            "season_id": season_id,
            "car_class_id": car_class_id,
            "race_week_num": race_week_num,
        }

        self.client.stats_season_qualify_results(season_id, car_class_id, race_week_num)

        mock_get_resource.assert_called_once_with(
            "/data/stats/season_qualify_results", payload=expected_payload
        )
        mock_get_chunks.assert_called_once()

        self.client.stats_season_qualify_results(
            season_id, car_class_id, race_week_num, division=0
        )

        mock_get_resource.assert_called_with(
            "/data/stats/season_qualify_results",
            payload={
                "season_id": season_id,
                "car_class_id": car_class_id,
                "race_week_num": race_week_num,
                "division": 0,
            },
        )

    @patch.object(irDataClient, "_get_chunks")
    @patch.object(irDataClient, "_get_resource")
    def test_stats_world_records(self, mock_get_resource, mock_get_chunks):
        mock_get_resource.return_value = {
            "data": {"chunk_info": ["chunks"], "type": "world_records"}
        }
        mock_get_chunks.return_value = self._get_mock_data("stats_world_records.json")
        car_id = 123
        track_id = 456
        expected_payload = {"car_id": car_id, "track_id": track_id}

        self.client.stats_world_records(car_id, track_id)

        mock_get_resource.assert_called_once_with(
            "/data/stats/world_records", payload=expected_payload
        )
        mock_get_chunks.assert_called_once()

    @patch.object(irDataClient, "_get_resource")
    def test_team(self, mock_get_resource):
        mock_get_resource.return_value = self._get_mock_data("team.json")
        team_id = 123
        include_licenses = True
        expected_payload = {"team_id": team_id, "include_licenses": include_licenses}

        self.client.team(team_id, include_licenses)

        mock_get_resource.assert_called_once_with(
            "/data/team/get", payload=expected_payload
        )

    @patch.object(irDataClient, "_get_resource")
    def test_season_list(self, mock_get_resource):
        mock_get_resource.return_value = self._get_mock_data("season_list.json")
        season_year = 2022
        season_quarter = 1
        expected_payload = {
            "season_year": season_year,
            "season_quarter": season_quarter,
        }

        self.client.season_list(season_year, season_quarter)

        mock_get_resource.assert_called_once_with(
            "/data/season/list", payload=expected_payload
        )

    @patch.object(irDataClient, "_get_resource")
    def test_season_race_guide(self, mock_get_resource):
        mock_get_resource.return_value = self._get_mock_data("season_race_guide.json")
        start_from = "2022-06-01T00:00:00Z"
        include_end_after_from = True
        expected_payload = {
            "from": start_from,
            "include_end_after_from": include_end_after_from,
        }

        self.client.season_race_guide(start_from, include_end_after_from)

        mock_get_resource.assert_called_once_with(
            "/data/season/race_guide", payload=expected_payload
        )

    @patch.object(irDataClient, "_get_resource")
    def test_series_past_seasons(self, mock_get_resource):
        series_id = 123
        mock_get_resource.return_value = self._get_mock_data("series_past_seasons.json")
        expected_payload = {"series_id": series_id}

        self.client.series_past_seasons(series_id)

        mock_get_resource.assert_called_once_with(
            "/data/series/past_seasons", payload=expected_payload
        )

    @patch.object(irDataClient, "_get_resource")
    def test_series_seasons(self, mock_get_resource):
        mock_get_resource.return_value = self._get_mock_data("series_seasons.json")
        include_series = True
        expected_payload = {"include_series": include_series}

        self.client.series_seasons(include_series)

        mock_get_resource.assert_called_once_with(
            "/data/series/seasons", payload=expected_payload
        )

    def test_access_token_or_credentials(self):
        """
        It should not be possible to supply both credentials and an access token
        """
        with self.assertRaises(AttributeError):
            irDataClient(
                username="a@user.com",
                password="somepassword",
                access_token="an-access-token",
            )

    @patch("requests.Session.get")
    def test_access_token_invalid_raises(self, mock_requests_get):
        """
        When an access token is no longer valid, it should raise a specific exception for consumers to build around
        """

        mock_requests_get.return_value = MagicMock(status_code=401)
        with self.assertRaises(AccessTokenInvalid):
            subsession_id = 12345
            include_licenses = True
            self.access_token_client.result(
                subsession_id=subsession_id, include_licenses=include_licenses
            )


if __name__ == "__main__":
    unittest.main()
