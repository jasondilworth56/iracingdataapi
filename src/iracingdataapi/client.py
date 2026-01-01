import base64
import csv
import hashlib
import time
import warnings
from datetime import datetime, timedelta, timezone
from io import StringIO
from typing import Annotated, Any, Dict, Literal, Optional, Union

import requests
from pydantic import (
    AwareDatetime,
    BaseModel,
    Field,
    PositiveInt,
    StrictBool,
    StrictInt,
    StrictStr,
    TypeAdapter,
    validate_call,
)

from src.iracingdataapi.models.responses import (
    CarAssetsResponse,
    CarclassGetResponse,
    CarGetResponse,
    CarWithAssetResponse,
    ConstantsCategoriesResponse,
    ConstantsDivisionsResponse,
    ConstantsEventTypesResponse,
    DriverListResponse,
    HostedCombinedSessionsResponse,
    HostedSessionsResponse,
    LeagueCustLeagueSessionsResponse,
    LeagueDirectoryResponse,
    LeagueGetPointsSystemsResponse,
    LeagueGetResponse,
    LeagueMembershipResponse,
    LeagueRosterResponse,
    LeagueSeasonSessionsResponse,
    LeagueSeasonsResponse,
    LeagueSeasonStandingsResponse,
    LookupCountriesResponse,
    LookupDriversResponse,
    LookupFlairsResponse,
    LookupGetResponse,
    LookupLicensesResponse,
    MemberAwardInstancesResponse,
    MemberAwardsResponse,
    MemberChartDataResponse,
    MemberGetResponse,
    MemberInfoResponse,
    MemberParticipationCreditsResponse,
    MemberProfileResponse,
    ResultsEventLogResponse,
    ResultsGetResponse,
    ResultsLapChartDataResponse,
    ResultsLapDataResponse,
    ResultsSearchHostedResponse,
    ResultsSearchSeriesResponse,
    ResultsSeasonResultsResponse,
    SeasonListResponse,
    SeasonRaceGuideResponse,
    SeasonSpectatorSubsessionidsDetailResponse,
    SeasonSpectatorSubsessionidsResponse,
    SeriesAssetsResponse,
    SeriesGetResponse,
    SeriesPastSeasonsResponse,
    SeriesSeasonListResponse,
    SeriesSeasonScheduleResponse,
    SeriesSeasonsResponse,
    SeriesStatsSeriesResponse,
    SeriesWithAssetResponse,
    SessionRegDriversListResponse,
    StatsMemberBestsResponse,
    StatsMemberCareerResponse,
    StatsMemberDivisionResponse,
    StatsMemberRecapResponse,
    StatsMemberRecentRacesResponse,
    StatsMemberSummaryResponse,
    StatsMemberYearlyResponse,
    StatsSeasonDriverStandingsResponse,
    StatsSeasonQualifyResultsResponse,
    StatsSeasonSupersessionStandingsResponse,
    StatsSeasonTeamStandingsResponse,
    StatsSeasonTtResultsResponse,
    StatsSeasonTtStandingsResponse,
    StatsWorldRecordsResponse,
    TeamGetResponse,
    TeamMembershipResponse,
    TimeAttackMemberSeasonResultsResponse,
    TrackAssetsResponse,
    TrackGetResponse,
    TrackWithAssetResponse,
)

from .exceptions import AccessTokenInvalid
from .rate_limit import irRateLimit


class irDataClient:

    def __init__(
        self,
        username=None,
        password=None,
        access_token=None,
        silent=False,
        use_pydantic=False,
    ):
        self.session = requests.Session()
        self.base_url = "https://members-ng.iracing.com"
        self.silent = silent
        self.use_pydantic = use_pydantic

        # Deprecation warning if not using Pydantic types
        if not use_pydantic:
            warnings.warn(
                "Returning raw dictionaries is deprecated and will be removed in a future version. "
                "Set use_pydantic=True to use Pydantic models for improved type safety. "
                "See documentation for migration guide.",
                DeprecationWarning,
                stacklevel=2,
            )

        self.access_token = None
        self.username = None
        self.encoded_password = None

        if access_token and username and password:
            raise AttributeError(
                "You must supply either access token or account credentials, not both"
            )

        if username and password:
            self.username = username
            self.encoded_password = self._encode_password(username, password)

        if access_token:
            self.access_token = access_token

        # assume access token is valid, we'll raise later if necessary
        self.authenticated = True if self.access_token else False

        # Rate limit object - self-contained with defaults
        self.rate_limit = irRateLimit()

    def _encode_password(self, username: str, password: str) -> str:
        initial_hash = hashlib.sha256(
            (password + username.lower()).encode("utf-8")
        ).digest()

        return base64.b64encode(initial_hash).decode("utf-8")

    def _validate_and_return(self, klass: BaseModel, data):
        """Validate data with Pydantic and optionally convert to dict for backwards compatibility."""

        if not self.use_pydantic:
            return data

        validated = TypeAdapter(klass).validate_python(data)
        return validated

    def _login(self) -> str:
        headers = {"Content-Type": "application/json"}
        data = {"email": self.username, "password": self.encoded_password}

        try:
            r = self.session.post(
                "https://members-ng.iracing.com/auth",
                headers=headers,
                json=data,
                timeout=5.0,
            )
            if r.status_code == 429:
                ratelimit_reset = r.headers.get("x-ratelimit-reset")
                if ratelimit_reset:
                    reset_datetime = datetime.fromtimestamp(int(ratelimit_reset))
                    delta = (
                        reset_datetime - datetime.now() + timedelta(milliseconds=500)
                    )
                    if not self.silent:
                        print(f"Rate limited, waiting {delta.total_seconds()} seconds")
                    if delta.total_seconds() > 0:
                        time.sleep(delta.total_seconds())
                return self._login()
        except requests.Timeout:
            raise RuntimeError("Login timed out")
        except requests.ConnectionError:
            raise RuntimeError("Connection error")
        else:
            response_data = r.json()
            if r.status_code == 200 and response_data.get("authcode"):
                # Update rate limit from successful login response
                self.rate_limit.update_from_response(r)
                self.authenticated = True
                return "Logged in"
            else:
                raise RuntimeError("Error from iRacing: ", response_data)

    def _build_url(self, endpoint: str) -> str:
        return self.base_url + endpoint

    def _build_request_headers(self) -> dict:
        headers = {}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"

        return headers

    def _to_utc_z(self, dt: AwareDatetime) -> str:
        # ISO-8601 with trailing Z, seconds precision
        return (
            dt.astimezone(timezone.utc)
            .replace(microsecond=0)
            .isoformat()
            .replace("+00:00", "Z")
        )

    def _get_resource_or_link(
        self, url: str, payload: dict = None
    ) -> list[Union[Dict, str], bool]:
        if not self.authenticated:
            self._login()
            return self._get_resource_or_link(url, payload=payload)

        r = self.session.get(url, params=payload, headers=self._build_request_headers())

        if r.status_code == 401 and self.authenticated:
            # unauthorised, likely due to a timeout, retry after a login
            self.authenticated = False
            if self.access_token:
                raise AccessTokenInvalid("Access token not valid")

            return self._get_resource_or_link(url, payload=payload)

        if r.status_code == 429:
            ratelimit_reset = r.headers.get("x-ratelimit-reset")
            if ratelimit_reset:
                reset_datetime = datetime.fromtimestamp(int(ratelimit_reset))
                delta = reset_datetime - datetime.now() + timedelta(milliseconds=500)
                if not self.silent:
                    print(f"Rate limited, waiting {delta.total_seconds()} seconds")
                if delta.total_seconds() > 0:
                    time.sleep(delta.total_seconds())
            return self._get_resource_or_link(url, payload=payload)

        if r.status_code != 200:
            raise RuntimeError("Unhandled Non-200 response", r)

        # Update rate limit from successful response
        self.rate_limit.update_from_response(r)

        data = r.json()
        if not isinstance(data, list) and "link" in data.keys():
            return [data.get("link"), True]
        else:
            return [data, False]

    def _fetch_link_data(self, url: str) -> Union[list, dict]:
        """
        Fetch data from an external link (e.g., S3 URL) without authentication headers.

        S3 URLs use pre-signed authentication in the URL itself, so adding OAuth headers
        causes authentication failures.

        Args:
            url (str): The URL to fetch data from

        Returns:
            Union[list, dict]: The parsed data (JSON or CSV)
        """
        r = self.session.get(url)

        if r.status_code != 200:
            raise RuntimeError("Unhandled Non-200 response", r)

        # Update rate limit from successful response
        self.rate_limit.update_from_response(r)

        content_type = r.headers.get("Content-Type", "")

        if (
            "application/json" in content_type
            or "application/octet-stream" in content_type
        ):
            return r.json()

        elif "text/csv" in content_type or "text/plain" in content_type:
            return self._parse_csv_response(r.text)

        else:
            raise RuntimeError(f"Unsupported Content-Type: {content_type}")

    def _get_resource(
        self, endpoint: str, payload: Optional[dict] = None
    ) -> Optional[Union[list, dict]]:
        request_url = self._build_url(endpoint)
        resource_obj, is_link = self._get_resource_or_link(request_url, payload=payload)

        if not is_link:
            return resource_obj
        r = self.session.get(resource_obj)

        if r.status_code == 401 and self.authenticated:
            # Unauthenticated, likely due to a timeout, retry after a login
            self.authenticated = False
            self._login()
            return self._get_resource(endpoint, payload=payload)

        if r.status_code == 429:
            print("Rate limited, waiting")
            ratelimit_reset = r.headers.get("x-ratelimit-reset")
            if ratelimit_reset:
                reset_datetime = datetime.fromtimestamp(int(ratelimit_reset))
                delta = reset_datetime - datetime.now()
                if delta.total_seconds() > 0:
                    time.sleep(delta.total_seconds())
            return self._get_resource(endpoint, payload=payload)

        if r.status_code != 200:
            raise RuntimeError("Unhandled Non-200 response", r)

        # Update rate limit from successful response
        self.rate_limit.update_from_response(r)

        content_type = r.headers.get("Content-Type")

        if "application/json" in content_type:
            return r.json()

        elif "text/csv" in content_type or "text/plain" in content_type:
            return self._parse_csv_response(r.text)

        else:
            print("Error: Unsupported Content-Type")
            return None

    def _get_chunks(self, chunks) -> list:
        if not isinstance(chunks, dict):
            # if there are no chunks, return an empty list for compatibility
            return []
        base_url = chunks.get("base_download_url")
        urls = [base_url + x for x in chunks.get("chunk_file_names")]
        list_of_chunks = [self.session.get(url).json() for url in urls]
        output = [item for sublist in list_of_chunks for item in sublist]

        return output

    def _add_assets(self, objects: list, assets: dict | BaseModel, id_key: str) -> list:
        output = []
        for obj in objects:
            if not isinstance(obj, dict):
                obj = obj.__dict__
            a = assets[str(obj[id_key])]
            if not isinstance(a, dict):
                a = a.__dict__
            output.append({**obj, **a})
        return output

    def _parse_csv_response(self, text: str) -> list:
        csv_data = []
        reader = csv.reader(StringIO(text), delimiter=",")

        headers = [header.lower() for header in next(reader)]

        for row in reader:
            if len(row) == len(headers):
                csv_data.append(dict(zip(headers, row)))
            else:
                print("Warning: Row length does not match headers length")

        return csv_data

    @property
    def cars(self) -> Union[CarWithAssetResponse, list[Dict]]:
        cars = self.get_cars()
        car_assets = self.get_cars_assets()
        combined = self._add_assets(cars, car_assets, "car_id")
        return self._validate_and_return(CarWithAssetResponse, combined)

    @property
    def tracks(self) -> Union[TrackWithAssetResponse, list[Dict]]:
        tracks = self.get_tracks()
        track_assets = self.get_tracks_assets()
        combined = self._add_assets(tracks, track_assets, "track_id")
        return self._validate_and_return(TrackWithAssetResponse, combined)

    @property
    def series(self) -> Union[SeriesWithAssetResponse, list[Dict]]:
        series = self.get_series()
        series_assets = self.get_series_assets()
        combined = self._add_assets(series, series_assets, "series_id")
        return self._validate_and_return(SeriesWithAssetResponse, combined)

    def constants_categories(self) -> Union[ConstantsCategoriesResponse, list[Dict]]:
        """Fetches a list containing the racing categories.

        Retrieves a list containing the racing categories and
        the id associated to each category.

        Returns:
            list: A list of dicts representing each category.

        """
        return self._validate_and_return(
            ConstantsCategoriesResponse,
            self._get_resource("/data/constants/categories"),
        )

    def constants_divisions(self) -> Union[ConstantsDivisionsResponse, list[Dict]]:
        """Fetches a list containing the racing divisions.

        Retrieves a list containing the racing divisions and
        the id associated to each division.

        Returns:
            list: A list of dicts representing each division.

        """
        return self._validate_and_return(
            ConstantsDivisionsResponse, self._get_resource("/data/constants/divisions")
        )

    def constants_event_types(self) -> Union[ConstantsEventTypesResponse, list[Dict]]:
        """Fetches a list containing the event types.

        Retrieves a list containing the types of events (i.e. Practice,
        Qualify, Time Trial or Race)

        Returns:
            list: A list of dicts representing each event type.

        """
        return self._validate_and_return(
            ConstantsEventTypesResponse,
            self._get_resource("/data/constants/event_types"),
        )

    @validate_call
    def driver_list(
        self, category_id: Annotated[int, Field(ge=1, le=6)]
    ) -> Union[DriverListResponse, list[Dict]]:
        """Fetches driver list by racing category

        Retrieves a list containing the driver data by category
        (category_id (int): 1 - Oval; 2 - Road; 3 - Dirt oval; 4 - Dirt road; 5 - Sports Car; 6 - Formula Car)

        Returns:
            list: A list of dicts representing driver data.

        """
        category_endpoints = {
            1: "/data/driver_stats_by_category/oval",
            2: "/data/driver_stats_by_category/road",
            3: "/data/driver_stats_by_category/dirt_oval",
            4: "/data/driver_stats_by_category/dirt_road",
            5: "/data/driver_stats_by_category/sports_car",
            6: "/data/driver_stats_by_category/formula_car",
        }

        endpoint = category_endpoints[category_id]
        return self._validate_and_return(
            DriverListResponse, self._get_resource(endpoint)
        )

    def get_cars(self) -> Union[CarGetResponse, list[Dict]]:
        """Fetches a list containing all the cars in the service.

        Retrieves a list containing each car in the service, with
        detailed information related to the car within iRacing.

        Returns:
            list: A list of dicts representing each car information.
        """
        return self._validate_and_return(
            CarGetResponse, self._get_resource("/data/car/get")
        )

    def get_cars_assets(self) -> Union[CarAssetsResponse, Dict]:
        """Fetches a list containing all the car assets in the service.

        Retrieves a list containing each car in the service, with
        detailed assets related to the car (i.e. photos, tech specs, etc.)

        Returns:
            dict: a dict with keys relating to each car id, each containing a further dict of car assets.
        """
        return self._validate_and_return(
            CarAssetsResponse, self._get_resource("/data/car/assets")
        )

    def get_carclasses(self) -> Union[CarclassGetResponse, list[Dict]]:
        """Fetches a list containing all the car classes in the service.

        Retrieves a list containing each car class in the service, including
        all the cars in class and basic information of the car class.

        Returns:
            list: A list of dicts representing assets from each car.

        """
        return self._validate_and_return(
            CarclassGetResponse, self._get_resource("/data/carclass/get")
        )

    def get_tracks(self) -> Union[TrackGetResponse, list[Dict]]:
        """Fetches a list containing all the tracks in the service.

        Retrieves a list containing each track in the service, with
        detailed information related to the track within iRacing.

        Returns:
            list: A list of dicts representing each track information.
        """
        return self._validate_and_return(
            TrackGetResponse, self._get_resource("/data/track/get")
        )

    def get_tracks_assets(self) -> Union[TrackAssetsResponse, Dict]:
        """Fetches a dict containing all the track assets in the service.

        Retrieves a dict containing each track in the service, with
        detailed assets related to the track (i.e. photos, track map, etc.)

        Returns:
            dict: a dict with keys relating to each track id, each containing a further dict of track assets.
        """
        return self._validate_and_return(
            TrackAssetsResponse, self._get_resource("/data/track/assets")
        )

    @validate_call
    def hosted_combined_sessions(
        self, package_id: Optional[PositiveInt] = None
    ) -> Union[HostedCombinedSessionsResponse, Dict]:
        """Fetches a dict containing the combined hosted sessions

        Retrieves a dict containing all the hosted sessions (available through ``sessions`` key)
        including:

        - Hosted sessions that can be joined as driver
        - Hosted sessions that can be joined as spectator
        - Non-league pending sessions for the user

        Args:
            package_id (int): If set, return only sessions using this car or track package ID.

        Returns:
            dict: A dict containing all the combined hosted sessions.
        """
        payload = {}
        if package_id:
            payload["package_id"] = package_id
        return self._validate_and_return(
            HostedCombinedSessionsResponse,
            self._get_resource("/data/hosted/combined_sessions", payload=payload),
        )

    def hosted_sessions(self) -> Union[HostedSessionsResponse, Dict]:
        """Fetches a dict containing the hosted sessions

        Retrieves a dict containing the hosted sessions (available through ``sessions`` key)
        but only **hosted sessions that can be joined as driver.**

        Returns:
            dict: A dict containing all the combined hosted sessions.
        """
        return self._validate_and_return(
            HostedSessionsResponse, self._get_resource("/data/hosted/sessions")
        )

    @validate_call
    def league_get(
        self,
        league_id: Optional[PositiveInt] = None,
        include_licenses: StrictBool = False,
    ) -> Union[LeagueGetResponse, Dict]:
        """Fetches a dict containing information from the league requested.

        Retrieves a dict containing all the information of the league requested.

        Args:
            league_id (int): the ID of the league requested
            include_licenses (bool): whether if you want to include the licenses or not.
                Default ``False``.

        Returns:
            dict: A dict containing all the information of the league requested.
        """
        if not league_id:
            raise RuntimeError("Please supply a league_id")
        payload = {"league_id": league_id, "include_licenses": include_licenses}
        return self._validate_and_return(
            LeagueGetResponse, self._get_resource("/data/league/get", payload=payload)
        )

    @validate_call
    def league_cust_league_sessions(
        self, mine: StrictBool = False, package_id: Optional[PositiveInt] = None
    ) -> Union[LeagueCustLeagueSessionsResponse, Dict]:
        """Fetches a dict containing information from the league requested.

        Retrieves a dict containing all the information of the league requested.

        Args:
            mine (bool): If ``True``, return only sessions created by this user.
            package_id (int): If set, return only sessions using this car or track package ID.

        Returns:
            dict: A dict containing all the information of the league requested.
        """
        payload = {"mine": mine}
        if package_id:
            payload["package_id"] = package_id

        return self._validate_and_return(
            LeagueCustLeagueSessionsResponse,
            self._get_resource("/data/league/cust_league_sessions", payload=payload),
        )

    @validate_call
    def league_directory(
        self,
        search: StrictStr = "",
        tag: StrictStr = "",
        restrict_to_member: StrictBool = False,
        restrict_to_recruiting: StrictBool = False,
        restrict_to_friends: StrictBool = False,
        restrict_to_watched: StrictBool = False,
        minimum_roster_count: PositiveInt = 0,
        maximum_roster_count: PositiveInt = 999,
        lowerbound: PositiveInt = 1,
        upperbound: Optional[PositiveInt] = None,
        sort: Optional[
            Literal["relevance", "leaguename", "displayname", "rostercount"]
        ] = None,
        order: Literal["asc", "desc"] = "asc",
    ) -> Union[LeagueDirectoryResponse, Dict]:
        """Fetches the iRacing leagues that matches the parameters requested

        Retrieves the iRacing leagues that matches the parameters requested by the user.

        Args:
            search (str): Will search against league name, description, owner, and league ID.
            tag (str): One or more tags, comma-separated. (i.e. ``"tag1,tag2"``)
            restrict_to_member (bool): If ``True`` include only leagues for which customer is a member.
            restrict_to_recruiting (bool): If ``True`` include only leagues which are recruiting.
            restrict_to_friends: If ``True`` include only leagues owned by a friend.
            restrict_to_watched: If ``True`` include only leagues owned by a watched member.
            minimum_roster_count (int): If set include leagues with at least this number of members.
            maximum_roster_count (int): If set include leagues with no more than this number of members.
                Defaults to 999.
            lowerbound (int): First row of results to return.  Defaults to 1.
            upperbound (int): Last row of results to return. Defaults to lowerbound + 39.
            sort (str): One of relevance, leaguename, displayname, rostercount.
                Displayname is owners' name. Defaults to relevance.
            order (str): One of ``asc`` or ``desc``. Defaults to asc.

        Returns:
            dict: a dict with the request info including the leagues from the search requested.

        """
        payload = {
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

        return self._validate_and_return(
            LeagueDirectoryResponse,
            self._get_resource("/data/league/directory", payload=payload),
        )

    @validate_call
    def league_get_points_systems(
        self, league_id: PositiveInt, season_id: Optional[PositiveInt] = None
    ) -> Union[LeagueGetPointsSystemsResponse, Dict]:
        """Fetches a dict containing the point system from the league requested.

        Retrieves a dict containing all the information of the league requested.

        Args:
            league_id (int): the id of the league to retrieve the points systems.
            season_id (int): if included and the season is using custom points (points_system_id:2)
             then the custom points option is included in the returned list. Otherwise, the custom points option
             is not returned.

        Returns:
            dict: A dict containing all the requested points systems of the league requested.
        """
        payload = {"league_id": league_id}
        if season_id:
            payload["season_id"] = season_id

        return self._validate_and_return(
            LeagueGetPointsSystemsResponse,
            self._get_resource("/data/league/get_points_systems", payload=payload),
        )

    @validate_call
    def league_membership(
        self, include_league: StrictBool = False
    ) -> Union[LeagueMembershipResponse, list[Dict]]:
        """Fetches a list containing all the leagues the user is currently a member.

        Retrieves a list containing all the leagues the user is member.

        Args:
            include_league (bool): if ``True``, also receives the league detailed information in ``league``.

        Returns:
            list: A list containing all the leagues the user is member.
        """
        payload = {"include_league": include_league}
        return self._validate_and_return(
            LeagueMembershipResponse,
            self._get_resource("/data/league/membership", payload=payload),
        )

    @validate_call
    def league_roster(
        self, league_id: PositiveInt, include_licenses: StrictBool = False
    ) -> Union[LeagueRosterResponse, Dict]:
        """Fetches a dict containing information about the league roster.
        Args:
            league_id (int): the league to retrieve the roster
            include_licenses (bool): if ``True``, also receives license information.
             For faster responses, only request when necessary.

        Returns:
            dict: A dict containing the league roster.
        """
        payload = {"league_id": league_id, "include_licenses": include_licenses}

        resource = self._get_resource("/data/league/roster", payload=payload)

        return self._validate_and_return(
            LeagueRosterResponse, self._fetch_link_data(resource["data_url"])
        )

    @validate_call
    def league_seasons(
        self, league_id: PositiveInt, retired: StrictBool = False
    ) -> Union[LeagueSeasonsResponse, Dict]:
        """Fetches a list containing all the seasons from a league.

        Retrieves a list containing all the seasons from a league.

        Args:
            league_id (int): the league to retrieve the seasons
            retired (bool): Default ``False``. If ``True``, includes seasons which are no longer active.

        Returns:
            list: A list containing all the seasons from a league.
        """
        payload = {"league_id": league_id, "retired": retired}
        return self._validate_and_return(
            LeagueSeasonsResponse,
            self._get_resource("/data/league/seasons", payload=payload),
        )

    @validate_call
    def league_season_standings(
        self,
        league_id: PositiveInt,
        season_id: PositiveInt,
        car_class_id: Optional[PositiveInt] = None,
        car_id: Optional[PositiveInt] = None,
    ) -> Union[LeagueSeasonStandingsResponse, Dict]:
        """Fetches a dict containing all the seasons from a league.

        Retrieves a dict containing all the seasons from a league.

        Args:
            league_id (int): the league to retrieve the standings
            season_id (int): the season to retrieve the standings
            car_class_id (int): the car class id. see :meth:`client.irDataClient.get_carclasses`
             for more info.
            car_id (int): if provided, the car id. see :meth:`client.irDataClient.get_cars`
             for more info.

        Returns:
            dict: A dict containing the season standings from a league season.
        """
        payload = {"league_id": league_id, "season_id": season_id}
        if car_class_id:
            payload["car_class_id"] = car_class_id
        if car_id:
            payload["car_id"] = car_id

        return self._validate_and_return(
            LeagueSeasonStandingsResponse,
            self._get_resource("/data/league/season_standings", payload=payload),
        )

    @validate_call
    def league_season_sessions(
        self,
        league_id: PositiveInt,
        season_id: PositiveInt,
        results_only: StrictBool = False,
    ) -> Union[LeagueSeasonSessionsResponse, Dict]:
        """Fetches a dict containing all the sessions from a league session.

        Retrieves a dict containing all the sessions from a league session.

        Args:
            league_id (int): the league session to retrieve the sessions
            season_id (int): the session to retrieve the sessions
            results_only (bool): if ``True`` include only sessions for which results are available.

        Returns:
            dict: A dict containing the session from a league season.
        """
        payload = {
            "league_id": league_id,
            "season_id": season_id,
            "results_only": results_only,
        }
        return self._validate_and_return(
            LeagueSeasonSessionsResponse,
            self._get_resource("/data/league/season_sessions", payload=payload),
        )

    def lookup_countries(self) -> Union[LookupCountriesResponse, list[Dict]]:
        """The list of country names and the country codes.

        Returns:
            list: a list containing all the country names and country codes.

        """
        return self._validate_and_return(
            LookupCountriesResponse, self._get_resource("/data/lookup/countries")
        )

    @validate_call
    def lookup_drivers(
        self,
        search_term: Optional[StrictStr] = None,
        league_id: Optional[PositiveInt] = None,
    ) -> Union[LookupDriversResponse, list[Dict]]:
        """Lookup for drivers given a search term.

        Retrieves a list of drivers given a search term. It can be narrowed
        the search filtering by league.

        Args:
            search_term (str): a cust_id or partial name for which to search.
            league_id (int): narrow the search to the roster of the given league.

        Returns:
            list: a list of drivers that matches the search terms.

        """
        payload = {"search_term": search_term}
        if league_id:
            payload["league_id"] = league_id

        return self._validate_and_return(
            LookupDriversResponse,
            self._get_resource("/data/lookup/drivers", payload=payload),
        )

    def lookup_flairs(self) -> Union[LookupFlairsResponse, list[Dict]]:
        """All the iRacing flairs.

        Retrieves a list containing all the current flairs.

        Returns:
            list: a list containing all the current flairs.

        """
        return self._validate_and_return(
            LookupFlairsResponse, self._get_resource("/data/lookup/flairs")
        )

    def lookup_get(self) -> Union[LookupGetResponse, list[Dict]]:
        return self._validate_and_return(
            LookupGetResponse, self._get_resource("/data/lookup/get")
        )

    def lookup_licenses(self) -> Union[LookupLicensesResponse, list[Dict]]:
        """All the iRacing licenses.

        Retrieves a list containing all the current licenses, from Rookie to Pro/WC.

        Returns:
            list: a list containing all the current licenses, from Rookie to Pro/WC.

        """
        return self._validate_and_return(
            LookupLicensesResponse, self._get_resource("/data/lookup/licenses")
        )

    @validate_call
    def result(
        self, subsession_id: PositiveInt, include_licenses: StrictBool = False
    ) -> Union[ResultsGetResponse, Dict]:
        """Get the results from a specific session.

        Get the results of a subsession, if authorized to view them.
        series_logo image paths are relative to
        https://images-static.iracing.com/img/logos/series/

        Args:
            subsession_id: the unique id of the subsession from iRacing.
            include_licenses: whether if you want to include the licenses for that session.
             Default ``False``.

        Returns:
            dict: a dict containing all the result information from a subsession.

        """
        payload = {"subsession_id": subsession_id, "include_licenses": include_licenses}
        return self._validate_and_return(
            ResultsGetResponse,
            self._get_resource("/data/results/get", payload=payload),
        )

    @validate_call
    def result_lap_chart_data(
        self, subsession_id: PositiveInt, simsession_number: StrictInt = 0
    ) -> Union[ResultsLapChartDataResponse, list[Dict]]:
        """Get all the lap data from a subsession.

        Retrieves all the lap data from all cars during a sim session (Practice,
        Qualifying, Race)

        Args:
            subsession_id: the unique id of the subsession from iRacing.
            simsession_number: -2 for practice, -1 for qualy, 0 for race.
             Default ``0``.

        Returns:
            list: A list of all the laps completed by all cars.

        """
        payload = {
            "subsession_id": subsession_id,
            "simsession_number": simsession_number,
        }
        resource = self._get_resource("/data/results/lap_chart_data", payload=payload)
        return self._validate_and_return(
            ResultsLapChartDataResponse, self._get_chunks(resource.get("chunk_info"))
        )

    @validate_call
    def result_lap_data(
        self,
        subsession_id: PositiveInt,
        simsession_number: StrictInt = 0,
        cust_id: Optional[PositiveInt] = None,
        team_id: Optional[PositiveInt] = None,
    ) -> Union[ResultsLapDataResponse, list[Dict]]:
        """Get the lap data from a car within a sim session.

         If there are no chunks to get, that's because no laps were done by this cust_id
         on this subsession, return an empty list for compatibility.

        Args:
            subsession_id (int): the unique id of the subsession from iRacing.
            simsession_number (int): -2 for practice, -1 for qualy, 0 for race. Default ``0``.
            cust_id (int): required if the subsession was a single-driver event. Optional for team events.
             If omitted for a team event then the laps driven by all the team's drivers will be included.
            team_id (int): required if the subsession was a team event.

        Returns:
            list: a list containing the lap data from a car within a sim session.

        """
        if (cust_id is None) == (team_id is None):
            raise ValueError("Provide exactly one of cust_id or team_id.")

        payload = {
            "subsession_id": subsession_id,
            "simsession_number": simsession_number,
        }
        if cust_id:
            payload["cust_id"] = cust_id
        if team_id:
            payload["team_id"] = team_id

        resource = self._get_resource("/data/results/lap_data", payload=payload)
        if resource.get("chunk_info"):
            return self._validate_and_return(
                ResultsLapDataResponse, self._get_chunks(resource.get("chunk_info"))
            )

        # if there are no chunks to get, that's because no laps were done by this cust_id
        # on this subsession, return an empty list for compatibility
        return []

    @validate_call
    def result_event_log(
        self, subsession_id: PositiveInt, simsession_number: StrictInt = 0
    ) -> Union[ResultsEventLogResponse, list[Dict]]:
        """Get all the logs from a result sim session.

        Retrieves a list of all events logged during a sim event (Practice, Qualifying, Race)...

        Args:
            subsession_id (int): the unique id of the subsession from iRacing.
            simsession_number (int): -2 for practice, -1 for qualy, 0 for race. Default ``0``.

        Returns:
            list: A list of all the logged events during a sim session.

        """
        payload = {
            "subsession_id": subsession_id,
            "simsession_number": simsession_number,
        }
        resource = self._get_resource("/data/results/event_log", payload=payload)
        return self._validate_and_return(
            ResultsEventLogResponse,
            self._get_chunks(resource.get("chunk_info")),
        )

    @validate_call
    def result_search_hosted(
        self,
        start_range_begin: Optional[AwareDatetime] = None,
        start_range_end: Optional[AwareDatetime] = None,
        finish_range_begin: Optional[AwareDatetime] = None,
        finish_range_end: Optional[AwareDatetime] = None,
        cust_id: Optional[PositiveInt] = None,
        host_cust_id: Optional[PositiveInt] = None,
        session_name: Optional[StrictStr] = None,
        league_id: Optional[PositiveInt] = None,
        league_season_id: Optional[PositiveInt] = None,
        car_id: Optional[PositiveInt] = None,
        track_id: Optional[PositiveInt] = None,
        category_ids: Optional[list[Literal[1, 2, 3, 4]]] = None,
        team_id: Optional[PositiveInt] = None,
    ) -> Union[list[ResultsSearchHostedResponse], list[dict[str, Any]]]:
        """Search for hosted and league sessions.

        Hosted and league sessions. Maximum time frame of 90 days.
        Results split into one or more files with chunks of results.
        For scraping results the most effective approach is to keep track of the maximum end_time
        found during a search then make the subsequent call using that date/time as the finish_range_begin
        and skip any subsessions that are duplicated.

        Results are ordered by subsessionid which is a proxy for start time

        Requires one of: start_range_begin, finish_range_begin AND one of: cust_id, team_id, host_cust_id, session_name

        Args:
            start_range_begin (str): Session start times. ISO-8601 UTC time zero offset: "2022-04-01T15:45Z"
            start_range_end (str): ISO-8601 UTC time zero offset: "2022-04-01T15:45Z".
             Exclusive. May be omitted if start_range_begin is less than 90 days in the past.
            finish_range_begin (str): Session finish times. ISO-8601 UTC time zero offset: "2022-04-01T15:45Z".
            finish_range_end (str): ISO-8601 UTC time zero offset: "2022-04-01T15:45Z".
             Exclusive. May be omitted if finish_range_begin is less than 90 days in the past.
            cust_id (int): The participant's customer ID.
            host_cust_id (int): The host's customer ID.
            session_name (str): Part or all of the session's name.
            league_id (int): Include only results for the league with this ID.
            league_season_id (int): Include only results for the league season with this ID.
            car_id (int): One of the cars used by the session.
            track_id (int): The ID of the track used by the session.
            category_ids (list[int]): Track categories to include in the search (1,2,3,4).  Defaults to all.
            team_id (int): The team ID to search for. Takes priority over cust_id if both are supplied.
        Returns:
            list: a list containing all the hosted results matching criteria.

        """
        if not (start_range_begin or finish_range_begin):
            raise ValueError("Provide start_range_begin or finish_range_begin.")

        if not (cust_id or host_cust_id or session_name or team_id):
            raise ValueError(
                "Provide one of: cust_id, host_cust_id, session_name, team_id."
            )

        # enforce begin < end when both given, and 90-day max window
        if start_range_begin and start_range_end:
            if not start_range_begin < start_range_end:
                raise ValueError("start_range_begin must be before start_range_end.")
            if (start_range_end - start_range_begin).days > 90:
                raise ValueError("start time window exceeds 90 days.")
        if finish_range_begin and finish_range_end:
            if not finish_range_begin < finish_range_end:
                raise ValueError("finish_range_begin must be before finish_range_end.")
            if (finish_range_end - finish_range_begin).days > 90:
                raise ValueError("finish time window exceeds 90 days.")

        if category_ids is not None:
            category_ids = sorted(set(category_ids))
            if not category_ids:
                raise ValueError("category_ids cannot be an empty list.")

        # team_id takes priority over cust_id
        if team_id is not None and cust_id is not None:
            cust_id = None

        payload: dict[str, Any] = {}
        if start_range_begin:
            payload["start_range_begin"] = self._to_utc_z(start_range_begin)
        if start_range_end:
            payload["start_range_end"] = self._to_utc_z(start_range_end)
        if finish_range_begin:
            payload["finish_range_begin"] = self._to_utc_z(finish_range_begin)
        if finish_range_end:
            payload["finish_range_end"] = self._to_utc_z(finish_range_end)

        if cust_id is not None:
            payload["cust_id"] = cust_id
        if host_cust_id is not None:
            payload["host_cust_id"] = host_cust_id
        if session_name is not None:
            payload["session_name"] = session_name
        if league_id is not None:
            payload["league_id"] = league_id
        if league_season_id is not None:
            payload["league_season_id"] = league_season_id
        if car_id is not None:
            payload["car_id"] = car_id
        if track_id is not None:
            payload["track_id"] = track_id
        if category_ids is not None:
            payload["category_ids"] = category_ids
        if team_id is not None:
            payload["team_id"] = team_id

        resource = self._get_resource("/data/results/search_hosted", payload=payload)
        chunks = resource.get("data", {}).get("chunk_info")
        result = self._get_chunks(chunks) if chunks else []
        return self._validate_and_return(ResultsSearchHostedResponse, result)

    @validate_call
    def result_search_series(
        self,
        season_year: Optional[PositiveInt] = None,
        season_quarter: Optional[Literal[1, 2, 3, 4]] = None,
        start_range_begin: Optional[AwareDatetime] = None,
        start_range_end: Optional[AwareDatetime] = None,
        finish_range_begin: Optional[AwareDatetime] = None,
        finish_range_end: Optional[AwareDatetime] = None,
        cust_id: Optional[PositiveInt] = None,
        series_id: Optional[PositiveInt] = None,
        race_week_num: Optional[Annotated[int, Field(ge=0, le=13)]] = None,
        official_only: StrictBool = True,
        event_types: Optional[list[Literal[2, 3, 4, 5]]] = None,
        category_ids: Optional[list[Literal[1, 2, 3, 4]]] = None,
    ) -> Union[ResultsSearchSeriesResponse, list[dict[str, Any]]]:
        if not (
            (season_year and season_quarter) or start_range_begin or finish_range_begin
        ):
            raise ValueError(
                "Provide (season_year & season_quarter) or a date range (start_range_begin or finish_range_begin)."
            )

        # If one of season_year/season_quarter given, require the other
        if (season_year is None) ^ (season_quarter is None):
            raise ValueError(
                "season_year and season_quarter must be provided together."
            )

        # enforce begin < end and 90-day window when both ends given
        if start_range_begin and start_range_end:
            if not start_range_begin < start_range_end:
                raise ValueError("start_range_begin must be before start_range_end.")
            if (start_range_end - start_range_begin).days > 90:
                raise ValueError("Start time window exceeds 90 days.")
        if finish_range_begin and finish_range_end:
            if not finish_range_begin < finish_range_end:
                raise ValueError("finish_range_begin must be before finish_range_end.")
            if (finish_range_end - finish_range_begin).days > 90:
                raise ValueError("Finish time window exceeds 90 days.")

        if event_types is not None:
            event_types = sorted(set(event_types))
            if not event_types:
                raise ValueError("event_types cannot be an empty list.")
        if category_ids is not None:
            category_ids = sorted(set(category_ids))
            if not category_ids:
                raise ValueError("category_ids cannot be an empty list.")

        payload: dict[str, Any] = {}

        if season_year is not None:
            payload["season_year"] = season_year
        if season_quarter is not None:
            payload["season_quarter"] = season_quarter
        if start_range_begin:
            payload["start_range_begin"] = self._to_utc_z(start_range_begin)
        if start_range_end:
            payload["start_range_end"] = self._to_utc_z(start_range_end)
        if finish_range_begin:
            payload["finish_range_begin"] = self._to_utc_z(finish_range_begin)
        if finish_range_end:
            payload["finish_range_end"] = self._to_utc_z(finish_range_end)
        if cust_id is not None:
            payload["cust_id"] = cust_id
        if series_id is not None:
            payload["series_id"] = series_id
        if race_week_num is not None:
            payload["race_week_num"] = race_week_num

        payload["official_only"] = official_only
        if event_types is not None:
            payload["event_types"] = event_types
        if category_ids is not None:
            payload["category_ids"] = category_ids

        resource = self._get_resource("/data/results/search_series", payload=payload)
        chunks = resource.get("data", {}).get("chunk_info")
        result = self._get_chunks(chunks) if chunks else []
        return self._validate_and_return(ResultsSearchSeriesResponse, result)

    @validate_call
    def result_season_results(
        self,
        season_id: PositiveInt,
        event_type: Optional[Literal[2, 3, 4, 5]] = None,
        race_week_num: Optional[Annotated[int, Field(ge=0, le=13)]] = None,
    ) -> Union[ResultsSeasonResultsResponse, Dict]:
        """Get results from a certain race week from a series season.

        Args:
            season_id (int): the id of the season.
            event_type (int): Restrict to one event type: 2 - Practice; 3 - Qualify; 4 - Time Trial; 5 - Race
            race_week_num (int): The first race week of a season is 0.

        Returns:
            dict: a dict containing a list of sessions within the matching criteria.

        """
        payload = {"season_id": season_id}
        if event_type:
            payload["event_type"] = event_type
        if race_week_num is not None:
            payload["race_week_num"] = race_week_num

        return self._validate_and_return(
            ResultsSeasonResultsResponse,
            self._get_resource("/data/results/season_results", payload=payload),
        )

    @validate_call
    def member(
        self, cust_id: StrictStr | StrictInt, include_licenses: StrictBool = False
    ) -> Union[MemberGetResponse, Dict]:
        """Get member profile basic information from one or more members.

        Args:
            cust_id (Union[int, str]): one of several cust_id.
             for one cust_id, use an ``int``. for more cust_ids, use ``str`` separated with commas.
             i.e. ``"custid1,custid2"``
            include_licenses (bool): whether if you want to include the licenses.
             Default ``False``.

        Returns:
            dict: a dict containing the information of one or more members in ``'members'`` section.

        """
        payload = {"cust_ids": cust_id, "include_licenses": include_licenses}

        # Validate the members list
        return self._validate_and_return(
            MemberGetResponse,
            self._get_resource("/data/member/get", payload=payload),
        )

    @validate_call
    def member_awards(
        self, cust_id: Optional[PositiveInt] = None
    ) -> Union[MemberAwardsResponse, list[Dict]]:
        """Fetches a dict containing information on the members awards.
        Args:
            cust_id (int): the iRacing cust_id. Defaults to the authenticated member.

        Returns:
            list: A list of dicts containing all the members awards.  On failure, returns an empty list.
        """
        payload = {}
        if cust_id:
            payload["cust_id"] = cust_id

        resource = self._get_resource("/data/member/awards", payload=payload)

        return self._validate_and_return(
            MemberAwardsResponse, self._fetch_link_data(resource["data_url"])
        )

    @validate_call
    def member_award_instances(
        self, award_id: int, cust_id: Optional[int] = None
    ) -> Union[MemberAwardInstancesResponse, list[Dict]]:
        """Fetches a dict containing information on the members award instances.
        Args:
            cust_id (int): the iRacing cust_id.
            award_id (int): the award id to get instances for.

        Returns:
            list: A list of dicts containing all the members award instances.  On failure, returns an empty list.
        """
        payload = {"award_id": award_id}
        if cust_id:
            payload["cust_id"] = cust_id

        resource = self._get_resource("/data/member/award_instances", payload=payload)

        return self._validate_and_return(
            MemberAwardInstancesResponse,
            self._fetch_link_data(resource["data_url"]),
        )

    @validate_call
    def member_chart_data(
        self,
        cust_id: Optional[PositiveInt] = None,
        category_id: Literal[1, 2, 3, 4, 5, 6] = 2,
        chart_type: Literal[1, 2, 3] = 1,
    ) -> Union[MemberChartDataResponse, Dict]:
        """Get the irating, ttrating or safety rating chart data of a certain category.

        Args:
            cust_id (int): the iRacing cust_id. Defaults to the authenticated member.
            category_id (int): 1 - Oval; 2 - Road; 3 - Dirt oval; 4 - Dirt road; 5 - Sports Car; 6 - Formula Car
            chart_type (int): 1 - iRating; 2 - TT Rating; 3 - License/SR

        Returns:
            dict: a dict containing the time series chart data given the matching criteria.

        """
        payload = {"category_id": category_id, "chart_type": chart_type}
        if cust_id:
            payload["cust_id"] = cust_id

        return self._validate_and_return(
            MemberChartDataResponse,
            self._get_resource("/data/member/chart_data", payload=payload),
        )

    def member_info(self) -> Union[MemberInfoResponse, Dict]:
        """Account info from the authenticated member.

        Returns:
            dict: a dict containing the detailed information from the authenticated member.

        """
        return self._validate_and_return(
            MemberInfoResponse, self._get_resource("/data/member/info")
        )

    def member_participation_credits(
        self,
    ) -> Union[MemberParticipationCreditsResponse, Dict]:
        """Participation credits info from the authenticated member.

        Returns:
            dict: a dict containing the participation credits information from the authenticated member.

        """
        return self._validate_and_return(
            MemberParticipationCreditsResponse,
            self._get_resource("/data/member/participation_credits"),
        )

    @validate_call
    def member_profile(
        self, cust_id: Optional[PositiveInt] = None
    ) -> Union[MemberProfileResponse, Dict]:
        """Detailed profile info from a member.

        Args:
            cust_id (int): The iRacing cust_id. Defaults to the authenticated member.

        Returns:
            dict: a dict containing the detailed profile info from the member requested.

        """
        payload = {}
        if cust_id:
            payload["cust_id"] = cust_id
        return self._validate_and_return(
            MemberProfileResponse,
            self._get_resource("/data/member/profile", payload=payload),
        )

    @validate_call
    def stats_member_bests(
        self,
        cust_id: Optional[PositiveInt] = None,
        car_id: Optional[PositiveInt] = None,
    ) -> Union[StatsMemberBestsResponse, Dict]:
        """Get the member best laptimes from a certain cust_id and car_id.

        Args:
            cust_id (int): The iRacing cust_id. Defaults to the authenticated member.
            car_id (int): The car id. First call should exclude car_id;
             use cars_driven list in return for subsequent calls.

        Returns:
            dict: a dict containing the member best laptimes

        """
        payload = {}
        if cust_id:
            payload["cust_id"] = cust_id
        if car_id:
            payload["car_id"] = car_id

        return self._validate_and_return(
            StatsMemberBestsResponse,
            self._get_resource("/data/stats/member_bests", payload=payload),
        )

    @validate_call
    def stats_member_career(
        self, cust_id: Optional[PositiveInt] = None
    ) -> Union[StatsMemberCareerResponse, Dict]:
        """Get the member career stats from a certain cust_id

        Args:
            cust_id (int): The iRacing cust_id. Defaults to the authenticated member.

        Returns:
            dict: a dict containing the member career stats

        """
        payload = {}
        if cust_id:
            payload["cust_id"] = cust_id
        return self._validate_and_return(
            StatsMemberCareerResponse,
            self._get_resource("/data/stats/member_career", payload=payload),
        )

    @validate_call
    def stats_member_division(
        self,
        event_type: Literal[2, 3, 4, 5],
        season_id: PositiveInt,
    ) -> Union[StatsMemberDivisionResponse, Dict]:
        """Get the member division stats from a certain cust_id

        Args:
            event_type (int): 2 - Practice; 3 - Qualify; 4 - Time   Trial; 5 - Race
            season_id (int): The iRacing season id.
        Returns:
            dict: a dict containing the member division stats
        """
        payload = {"event_type": event_type, "season_id": season_id}
        return self._validate_and_return(
            StatsMemberDivisionResponse,
            self._get_resource("/data/stats/member_division", payload=payload),
        )

    @validate_call
    def stats_member_recap(
        self,
        cust_id: Optional[PositiveInt] = None,
        year: Optional[PositiveInt] = None,
        quarter: Optional[Literal[1, 2, 3, 4]] = None,
    ) -> Union[StatsMemberRecapResponse, Dict]:
        """Get a recap for the member.

        Args:
            cust_id (int): The iRacing cust_id. Defaults  to the authenticated member.
            year (int): Season year; if not supplied the current calendar year (UTC) is used.
            quarter (int): Season (quarter) within the year; if not supplied the recap will be for the entire year.

        Returns:
            dict: a dict containing a recap from the requested season/quarter/member
        """
        payload = {}
        if cust_id:
            payload["cust_id"] = cust_id
        if year:
            payload["year"] = year
        if quarter:
            payload["season"] = quarter
        return self._validate_and_return(
            StatsMemberRecapResponse,
            self._get_resource("/data/stats/member_recap", payload=payload),
        )

    @validate_call
    def stats_member_recent_races(
        self, cust_id: Optional[PositiveInt] = None
    ) -> Union[StatsMemberRecentRacesResponse, Dict]:
        """Get the latest member races from a certain cust_id

        Args:
            cust_id (int): The iRacing cust_id. Defaults to the authenticated member.

        Returns:
            dict: a dict containing the latest member races

        """
        payload = {}
        if cust_id:
            payload = {"cust_id": cust_id}

        return self._validate_and_return(
            StatsMemberRecentRacesResponse,
            self._get_resource("/data/stats/member_recent_races", payload=payload),
        )

    @validate_call
    def stats_member_summary(
        self, cust_id: Optional[PositiveInt] = None
    ) -> Union[StatsMemberSummaryResponse, Dict]:
        """Get the member stats summary from a certain cust_id

        Args:
            cust_id (int): The iRacing cust_id. Defaults to the authenticated member.

        Returns:
            dict: a dict containing the member stats summary

        """
        payload = {}
        if cust_id:
            payload = {"cust_id": cust_id}

        return self._validate_and_return(
            StatsMemberSummaryResponse,
            self._get_resource("/data/stats/member_summary", payload=payload),
        )

    @validate_call
    def stats_member_yearly(
        self, cust_id: Optional[PositiveInt] = None
    ) -> Union[StatsMemberYearlyResponse, Dict]:
        """Get the member stats yearly from a certain cust_id

        Args:
            cust_id (int): The iRacing cust_id. Defaults to the authenticated member.

        Returns:
            dict: a dict containing the member stats yearly

        """
        payload = {}
        if cust_id:
            payload = {"cust_id": cust_id}

        return self._validate_and_return(
            StatsMemberYearlyResponse,
            self._get_resource("/data/stats/member_yearly", payload=payload),
        )

    @validate_call
    def stats_season_driver_standings(
        self,
        season_id: PositiveInt,
        car_class_id: PositiveInt,
        race_week_num: Optional[Annotated[int, Field(ge=0, le=13)]] = None,
        club_id: Optional[PositiveInt] = None,
        division: Optional[Annotated[int, Field(ge=0, le=10)]] = None,
    ) -> Union[StatsSeasonDriverStandingsResponse, list[Dict]]:
        """Get the driver standings from a season.

        Args:
            season_id (int): The iRacing season id.
            car_class_id (int): the iRacing car class id.
            race_week_num (int): the race week number (0-12). Default 0.
            club_id (int): the iRacing club id. Defaults to all (None).
            division (int): the iRacing division. Divisions are 0-based: 0 is Division 1, 10 is Rookie.
                            See /data/constants/divisons for more information. Defaults to all.

        Returns:
            dict: a dict containing the season driver standings

        """
        payload = {"season_id": season_id, "car_class_id": car_class_id}
        if race_week_num is not None:
            payload["race_week_num"] = race_week_num
        if club_id:
            payload["club_id"] = club_id
        if division is not None:
            payload["division"] = division

        resource = self._get_resource(
            "/data/stats/season_driver_standings", payload=payload
        )
        result = self._get_chunks(resource.get("chunk_info"))
        return self._validate_and_return(StatsSeasonDriverStandingsResponse, result)

    @validate_call
    def stats_season_supersession_standings(
        self,
        season_id: PositiveInt,
        car_class_id: PositiveInt,
        race_week_num: Optional[Annotated[int, Field(ge=0, le=13)]] = None,
        club_id: Optional[PositiveInt] = None,
        division: Optional[Annotated[int, Field(ge=0, le=10)]] = None,
    ) -> Union[StatsSeasonSupersessionStandingsResponse, list[Dict]]:
        """Get the supersession standings from a season.

        Args:
            season_id (int): The iRacing season id.
            car_class_id (int): the iRacing car class id.
            race_week_num (int): the race week number (0-12). Default 0.
            club_id (int): the iRacing club id. Defaults to all (None).
            division (int): the iRacing division. Divisions are 0-based: 0 is Division 1, 10 is Rookie.
                            See /data/constants/divisons for more information. Defaults to all.

        Returns:
            dict: a dict containing the season supersession standings

        """
        payload = {"season_id": season_id, "car_class_id": car_class_id}
        if race_week_num is not None:
            payload["race_week_num"] = race_week_num
        if club_id:
            payload["club_id"] = club_id
        if division is not None:
            payload["division"] = division

        resource = self._get_resource(
            "/data/stats/season_supersession_standings", payload=payload
        )
        result = self._get_chunks(resource.get("chunk_info"))
        return self._validate_and_return(
            StatsSeasonSupersessionStandingsResponse, result
        )

    @validate_call
    def stats_season_team_standings(
        self,
        season_id: PositiveInt,
        car_class_id: PositiveInt,
        race_week_num: Optional[Annotated[int, Field(ge=0, le=12)]] = None,
    ) -> Union[StatsSeasonTeamStandingsResponse, Dict]:
        """Get the team standings from a season.

        Args:
            season_id (int): The iRacing season id.
            car_class_id (int): the iRacing car class id.
            race_week_num (int): the race week number (0-12).

        Returns:
            dict: a dict containing the season team standings

        """
        payload = {"season_id": season_id, "car_class_id": car_class_id}
        if race_week_num is not None:
            payload["race_week_num"] = race_week_num

        resource = self._get_resource(
            "/data/stats/season_team_standings", payload=payload
        )
        result = self._get_chunks(resource.get("chunk_info"))
        return self._validate_and_return(StatsSeasonTeamStandingsResponse, result)

    @validate_call
    def stats_season_tt_standings(
        self,
        season_id: PositiveInt,
        car_class_id: PositiveInt,
        race_week_num: Optional[Annotated[int, Field(ge=0, le=12)]] = None,
        club_id: Optional[PositiveInt] = None,
        division: Optional[Annotated[int, Field(ge=0, le=10)]] = None,
    ) -> Union[StatsSeasonTtStandingsResponse, list[Dict]]:
        """Get the Time Trial standings from a season.

        Args:
            season_id (int): The iRacing season id.
            car_class_id (int): the iRacing car class id.
            race_week_num (int): the race week number (0-12).
            club_id (int): the iRacing club id.
            division (int): the iRacing division.

        Returns:
            dict: a dict containing the Time Trial standings

        """
        payload = {"season_id": season_id, "car_class_id": car_class_id}
        if race_week_num is not None:
            payload["race_week_num"] = race_week_num
        if club_id:
            payload["club_id"] = club_id
        if division is not None:
            payload["division"] = division

        resource = self._get_resource(
            "/data/stats/season_tt_standings", payload=payload
        )
        result = self._get_chunks(resource.get("chunk_info"))
        return self._validate_and_return(StatsSeasonTtStandingsResponse, result)

    @validate_call
    def stats_season_tt_results(
        self,
        season_id: PositiveInt,
        car_class_id: PositiveInt,
        race_week_num: Optional[Annotated[int, Field(ge=0, le=12)]] = None,
        club_id: Optional[PositiveInt] = None,
        division: Optional[Annotated[int, Field(ge=0, le=10)]] = None,
    ) -> Union[StatsSeasonTtResultsResponse, list[Dict]]:
        """Get the Time Trial results from a season.

        Args:
            season_id (int): The iRacing season id.
            car_class_id (int): the iRacing car class id.
            race_week_num (int): the race week number (0-12).
            club_id (int): the iRacing club id.
            division (int): the iRacing division.

        Returns:
            dict: a dict containing the Time Trial results

        """
        payload = {
            "season_id": season_id,
            "car_class_id": car_class_id,
            "race_week_num": race_week_num,
        }
        if club_id:
            payload["club_id"] = club_id
        if division is not None:
            payload["division"] = division

        resource = self._get_resource("/data/stats/season_tt_results", payload=payload)
        result = self._get_chunks(resource.get("chunk_info"))
        return self._validate_and_return(StatsSeasonTtResultsResponse, result)

    @validate_call
    def stats_season_qualify_results(
        self,
        season_id: PositiveInt,
        car_class_id: PositiveInt,
        race_week_num: Optional[Annotated[int, Field(ge=0, le=12)]] = None,
        club_id: Optional[PositiveInt] = None,
        division: Optional[Annotated[int, Field(ge=0, le=10)]] = None,
    ) -> Union[StatsSeasonQualifyResultsResponse, list[Dict]]:
        """Get the qualifying results from a season.

        Args:
            season_id (int): The iRacing season id.
            car_class_id (int): the iRacing car class id.
            race_week_num (int): the race week number (0-12).
            club_id (int): the iRacing club id.
            division (int): the iRacing division.

        Returns:
            dict: a dict containing the qualifying results

        """
        payload = {
            "season_id": season_id,
            "car_class_id": car_class_id,
            "race_week_num": race_week_num,
        }
        if club_id:
            payload["club_id"] = club_id
        if division is not None:
            payload["division"] = division

        resource = self._get_resource(
            "/data/stats/season_qualify_results", payload=payload
        )
        result = self._get_chunks(resource.get("chunk_info"))
        return self._validate_and_return(StatsSeasonQualifyResultsResponse, result)

    @validate_call
    def stats_world_records(
        self,
        car_id: PositiveInt,
        track_id: PositiveInt,
        season_year: Optional[PositiveInt] = None,
        season_quarter: Optional[Literal[1, 2, 3, 4]] = None,
    ) -> Union[StatsWorldRecordsResponse, list[Dict]]:
        """Get the world records from a given track and car.

        Args:
            car_id (int): the iRacing car id
            track_id (int): the iRacing track id
            season_year (int): the season year
            season_quarter (int): the season quarter (1, 2, 3, 4). Only applicable when ``season_year`` is used.

        Returns:
            list: a list containing world record entries (as WorldRecord models if use_pydantic is True, otherwise as dicts)

        """
        payload = {"car_id": car_id, "track_id": track_id}
        if season_year:
            payload["season_year"] = season_year
        if season_quarter:
            payload["season_quarter"] = season_quarter

        resource = self._get_resource("/data/stats/world_records", payload=payload)
        result = self._get_chunks(resource.get("data", dict()).get("chunk_info"))
        return self._validate_and_return(StatsWorldRecordsResponse, result)

    @validate_call
    def team(
        self, team_id: PositiveInt, include_licenses: StrictBool = False
    ) -> Union[TeamGetResponse, Dict]:
        """Get detailed team information.

        Args:
            team_id (int): the iRacing unique id from the team.
            include_licenses (bool): include licenses from all team members. For faster responses,
             only request when necesary.

        Returns:
            Team | dict: the team information.

        """
        payload = {"team_id": team_id, "include_licenses": include_licenses}
        return self._validate_and_return(
            TeamGetResponse,
            self._get_resource("/data/team/get", payload=payload),
        )

    def team_membership(self) -> Union[TeamMembershipResponse, Dict]:
        """Get the team membership information from the authenticated member.

        Returns:
            TeamMembership | dict: the team membership information.

        """
        return self._validate_and_return(
            TeamMembershipResponse, self._get_resource("/data/team/membership")
        )

    @validate_call
    def season_list(
        self,
        season_year: PositiveInt,
        season_quarter: Literal[1, 2, 3, 4],
    ) -> Union[SeasonListResponse, Dict]:
        """Get the list of iRacing Official seasons given a year and quarter.

        Args:
            season_year (int): the season year
            season_quarter (int): the season quarter (1, 2, 3, 4). Only applicable when ``season_year`` is used.

        Returns:
            SeasonList | dict: the list of iRacing Official seasons given a year and quarter.

        """
        payload = {"season_year": season_year, "season_quarter": season_quarter}
        return self._validate_and_return(
            SeasonListResponse,
            self._get_resource("/data/season/list", payload=payload),
        )

    @validate_call
    def season_race_guide(
        self,
        start_from: Optional[AwareDatetime] = None,
        include_end_after_from: StrictBool = False,
    ) -> Union[SeasonRaceGuideResponse, Dict]:
        """Get the season schedule race guide.

        Args:
            start_from (str): ISO-8601 offset format. Defaults to the current time.
             Include sessions with start times up to 3 hours after this time.
             Times in the past will be rewritten to the current time.
            include_end_after_from (bool): Include sessions which start before 'from' but end after.

        Returns:
            RaceGuide | dict: the season schedule race guide.

        """
        payload = {}
        if start_from:
            payload["from"] = self._to_utc_z(start_from)
        if include_end_after_from:
            payload["include_end_after_from"] = include_end_after_from

        return self._validate_and_return(
            SeasonRaceGuideResponse,
            self._get_resource("/data/season/race_guide", payload=payload),
        )

    @validate_call
    def season_spectator_subsessionids(
        self, event_types: list[Literal[2, 3, 4, 5]] = [2, 3, 4, 5]
    ) -> Union[SeasonSpectatorSubsessionidsResponse, Dict]:
        """Get the current list of subsession IDs for a given event type

        Args:
            event_types (list[int]): A list of integers that match with iRacing event types as follows:
                2: Practise
                3: Qualify
                4: Time Trial
                5: Race

        Returns:
            list: a list of the matching subsession IDs
        """
        payload = {}
        if event_types:
            payload["event_types"] = ",".join([str(x) for x in event_types])

        result = self._get_resource(
            "/data/season/spectator_subsessionids", payload=payload
        )
        return self._validate_and_return(SeasonSpectatorSubsessionidsResponse, result)

    @validate_call
    def season_spectator_subsessions_detail(
        self,
        event_types: list[Literal[2, 3, 4, 5]] = [2, 3, 4, 5],
        season_ids: list[int] | None = None,
    ) -> Union[SeasonSpectatorSubsessionidsDetailResponse, Dict]:
        """Get the current list of subsession details for a given event type
        Args:
            event_types (list[int]): A list of integers that match with iRacing event types as follows:
                2: Practise
                3: Qualify
                4: Time Trial
                5: Race

        Returns:
            list[Series] | list[dict]: a list containing all the official iRacing series.

        """
        payload = {"event_types": ",".join([str(x) for x in event_types])}
        if season_ids:
            payload["season_ids"] = ",".join([str(x) for x in season_ids])

        return self._validate_and_return(
            SeasonSpectatorSubsessionidsDetailResponse,
            self._get_resource("/data/series/get", payload=payload),
        )

    def get_series(self) -> Union[SeriesGetResponse, list[Dict]]:
        """Get all the official iRacing series.

        Returns:
            list[Series] | list[dict]: a list containing all the official iRacing series.

        """
        return self._validate_and_return(
            SeriesGetResponse, self._get_resource("/data/series/get")
        )

    def get_series_assets(self) -> Union[SeriesAssetsResponse, Dict]:
        """Get all the current official iRacing series assets.

        Get the images, description and logos from the current official iRacing series.
        Image paths are relative to https://images-static.iracing.com/

        Returns:
            Dict[str, SeriesAsset] | dict: a dict mapping series_id to series assets.

        """
        data = self._get_resource("/data/series/assets")
        return self._validate_and_return(SeriesAssetsResponse, data)

    @validate_call
    def series_past_seasons(
        self, series_id: PositiveInt
    ) -> Union[SeriesPastSeasonsResponse, Dict]:
        """Get all seasons for a series.

        Filter list by ``'official'``: ``True`` for seasons with standings.

        Args:
            series_id (): the series id
        Returns:
            SeriesPastSeasons | dict: information about the series and a list of seasons.
        """
        payload = {"series_id": series_id}
        return self._validate_and_return(
            SeriesPastSeasonsResponse,
            self._get_resource("/data/series/past_seasons", payload=payload),
        )

    @validate_call
    def series_seasons(
        self,
        include_series: StrictBool = False,
        season_year: Optional[PositiveInt] = None,
        season_quarter: Optional[Literal[1, 2, 3, 4]] = None,
    ) -> Union[SeriesSeasonsResponse, list[Dict]]:
        """Get the all the seasons.

        To get series and seasons for which standings should be available, filter the list by ``'official'``: ``True``.

        Args:
            include_series (bool): whether if you want to include the series information or not. Default ``False``.

        Returns:
            list[SeriesSeason] | list[dict]: a list containing all the series and seasons.

        """
        payload = {"include_series": include_series}

        if (season_year or season_quarter) and not (season_year and season_quarter):
            raise ValueError(
                "season_year and season_quarter must be provided together."
            )

        if season_year is not None:
            payload["season_year"] = season_year
        if season_quarter is not None:
            payload["season_quarter"] = season_quarter

        return self._validate_and_return(
            SeriesSeasonsResponse,
            self._get_resource("/data/series/seasons", payload=payload),
        )

    @validate_call
    def series_seasons_list(
        self,
        include_series: bool = False,
        season_quarter: Optional[Literal[1, 2, 3, 4]] = None,
        season_year: Optional[PositiveInt] = None,
    ) -> Union[SeriesSeasonListResponse, list[Dict]]:
        """Get the all the seasons.

        To get series and seasons for which standings should be available, filter the list by ``'official'``: ``True``.

        Args:
            include_series: whether if you want to include the series information or not. Default ``False``.
            season_quarter: the season quarter (1, 2, 3, 4). Only applicable when ``season_year`` is used.
            season_year: the season year
        Returns:
            list[SeriesSeason] | list[dict]: a list containing all the series and seasons.

        """
        payload = {"include_series": include_series}

        if (season_year or season_quarter) and not (season_year and season_quarter):
            raise ValueError(
                "season_year and season_quarter must be provided together."
            )

        if season_year is not None:
            payload["season_year"] = season_year
        if season_quarter is not None:
            payload["season_quarter"] = season_quarter
        return self._validate_and_return(
            SeriesSeasonListResponse,
            self._get_resource("/data/series/seasons", payload=payload),
        )

    @validate_call
    def series_season_schedule(
        self, season_id: PositiveInt
    ) -> Union[SeriesSeasonScheduleResponse, Dict]:
        """Get the season schedule for a given season id.

        Args:
            season_id (int): the season id
        Returns:
            SeriesSeasonSchedule | dict: information about the season schedule.
        """
        payload = {"season_id": season_id}
        return self._validate_and_return(
            SeriesSeasonScheduleResponse,
            self._get_resource("/data/series/season_schedule", payload=payload),
        )

    def series_stats(self) -> Union[SeriesStatsSeriesResponse, list[Dict]]:
        """Get the all the series and seasons.

        To get series and seasons for which standings should be available, filter the list by ``'official'``: ``True``.

        Returns:
            list[SeriesStats] | list[dict]: a list containing all the series and seasons.

        """
        return self._validate_and_return(
            SeriesStatsSeriesResponse,
            self._get_resource("/data/series/stats_series"),
        )

    @validate_call
    def session_reg_drivers_list(
        self, subsession_id: PositiveInt
    ) -> Union[SessionRegDriversListResponse, Dict]:
        """Get the list of registered drivers for a given subsession id.

        Args:
            subsession_id (int): the subsession id
        Returns:
            SessionRegDriversList | dict: information about the registered drivers.
        """
        payload = {"subsession_id": subsession_id}
        return self._validate_and_return(
            SessionRegDriversListResponse,
            self._get_resource("/data/session/reg_drivers_list", payload=payload),
        )

    @validate_call
    def time_attack_member_season_results(
        self, ta_comp_season_id: int
    ) -> Union[TimeAttackMemberSeasonResultsResponse, Dict]:
        """Get Time Attack season results for the authenticated member.

        Args:
            ta_comp_season_id (int): the Time Attack competition season id.
        Returns:
            TimeAttackMemberSeasonResults | dict: information about the Time Attack season results.
        """
        payload = {"ta_comp_season_id": ta_comp_season_id}
        return self._validate_and_return(
            TimeAttackMemberSeasonResultsResponse,
            self._get_resource(
                "/data/time_attack/member_season_results", payload=payload
            ),
        )
