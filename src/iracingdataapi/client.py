import base64
import hashlib
import time
from datetime import datetime, timedelta

import requests


class irDataClient:
    def __init__(self, username=None, password=None):
        self.authenticated = False
        self.session = requests.Session()
        self.base_url = "https://members-ng.iracing.com"

        self.username = username
        self.encoded_password = self._encode_password(username, password)

    def _encode_password(self, username, password):
        initial_hash = hashlib.sha256(
            (password + username.lower()).encode("utf-8")
        ).digest()

        return base64.b64encode(initial_hash).decode("utf-8")

    def _login(self):
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
                print("Rate limited, waiting")
                ratelimit_reset = r.headers.get("x-ratelimit-reset")
                if ratelimit_reset:
                    reset_datetime = datetime.fromtimestamp(int(ratelimit_reset))
                    delta = reset_datetime - datetime.now()
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
                self.authenticated = True
                return "Logged in"
            else:
                raise RuntimeError("Error from iRacing: ", response_data)

    def _build_url(self, endpoint):
        return self.base_url + endpoint

    def _get_resource_or_link(self, url, payload=None):
        if not self.authenticated:
            self._login()
            return self._get_resource_or_link(url, payload=payload)

        r = self.session.get(url, params=payload)

        if r.status_code == 401:
            # unauthorised, likely due to a timeout, retry after a login
            self.authenticated = False
            return self._get_resource_or_link(url, payload=payload)

        if r.status_code == 429:
            print("Rate limited, waiting")
            ratelimit_reset = r.headers.get("x-ratelimit-reset")
            if ratelimit_reset:
                reset_datetime = datetime.fromtimestamp(int(ratelimit_reset))
                delta = reset_datetime - datetime.now()
                if delta.total_seconds() > 0:
                    time.sleep(delta.total_seconds())
            return self._get_resource_or_link(url, payload=payload)

        if r.status_code != 200:
            raise RuntimeError("Unhandled Non-200 response", r)
        data = r.json()
        if not isinstance(data, list) and "link" in data.keys():
            return [data.get("link"), True]
        else:
            return [data, False]

    def _get_resource(self, endpoint, payload=None):
        request_url = self._build_url(endpoint)
        resource_obj, is_link = self._get_resource_or_link(request_url, payload=payload)
        if not is_link:
            return resource_obj
        r = self.session.get(resource_obj)

        if r.status_code == 401:
            # unauthorised, likely due to a timeout, retry after a login
            self.authenticated = False
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

        return r.json()

    def _get_chunks(self, chunks):
        if not isinstance(chunks, dict):
            # if there are no chunks, return an empty list for compatibility
            return []
        base_url = chunks.get("base_download_url")
        urls = [base_url + x for x in chunks.get("chunk_file_names")]
        list_of_chunks = [self.session.get(url).json() for url in urls]
        output = [item for sublist in list_of_chunks for item in sublist]

        return output

    def _add_assets(self, objects, assets, id_key):
        for obj in objects:
            a = assets[str(obj[id_key])]
            for key in a.keys():
                obj[key] = a[key]
        return objects

    @property
    def cars(self):
        cars = self.get_cars()
        car_assets = self.get_cars_assets()
        return self._add_assets(cars, car_assets, "car_id")

    @property
    def tracks(self):
        tracks = self.get_tracks()
        track_assets = self.get_tracks_assets()
        return self._add_assets(tracks, track_assets, "track_id")

    @property
    def series(self):
        series = self.get_series()
        series_assets = self.get_series_assets()
        return self._add_assets(series, series_assets, "series_id")

    def constants_categories(self):
        """Fetches a list containing the racing categories.

        Retrieves a list containing the racing categories and
        the id associated to each category.

        Returns:
            list: A list of dicts representing each category.

        """
        return self._get_resource("/data/constants/categories")

    def constants_divisions(self):
        """Fetches a list containing the racing divisions.

        Retrieves a list containing the racing divisions and
        the id associated to each division.

        Returns:
            list: A list of dicts representing each division.

        """
        return self._get_resource("/data/constants/divisions")

    def constants_event_types(self):
        """Fetches a list containing the event types.

        Retrieves a list containing the types of events (i.e. Practice,
        Qualify, Time Trial or Race)

        Returns:
            A list of dicts representing each event type.

        """
        return self._get_resource("/data/constants/event_types")

    def get_cars(self):
        """Fetches a list containing all the cars in the service.

        Retrieves a list containing each car in the service, with
        detailed information related to the car within iRacing.

        Returns:
            list: A list of dicts representing each car information.
        """
        return self._get_resource("/data/car/get")

    def get_cars_assets(self):
        """Fetches a list containing all the car assets in the service.

        Retrieves a list containing each car in the service, with
        detailed assets related to the car (i.e. photos, tech specs, etc.)

        Returns:
            list: A list of dicts representing assets from each car.
        """
        return self._get_resource("/data/car/assets")

    def get_carclasses(self):
        """Fetches a list containing all the car classes in the service.

        Retrieves a list containing each car class in the service, including
        all the cars in class and basic information of the car class.

        Returns:
            list: A list of dicts representing assets from each car.

        """
        return self._get_resource("/data/carclass/get")

    def get_carclass(self):
        """
        get_carclass() is deprecated and will be removed in a future release, please use get_carclasses()
        """
        print(
            "get_carclass() is deprecated and will be removed in a future release, please use get_carclasses()"
        )
        return self.get_carclasses()

    def get_tracks(self):
        """Fetches a list containing all the tracks in the service.

        Retrieves a list containing each track in the service, with
        detailed information related to the track within iRacing.

        Returns:
            list: A list of dicts representing each track information.
        """
        return self._get_resource("/data/track/get")

    def get_tracks_assets(self):
        """Fetches a list containing all the track assets in the service.

        Retrieves a list containing each track in the service, with
        detailed assets related to the track (i.e. photos, track map, etc.)

        Returns:
            list: A list of dicts representing assets from each track.
        """
        return self._get_resource("/data/track/assets")

    def hosted_combined_sessions(self, package_id=None):
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
        return self._get_resource("/data/hosted/combined_sessions", payload=payload)

    def hosted_sessions(self):
        """Fetches a dict containing the hosted sessions

        Retrieves a dict containing the hosted sessions (available through ``sessions`` key)
        but only **hosted sessions that can be joined as driver.**

        Returns:
            dict: A dict containing all the combined hosted sessions.
        """
        return self._get_resource("/data/hosted/sessions")

    def league_get(self, league_id=None, include_licenses=False):
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
        return self._get_resource("/data/league/get", payload=payload)

    def league_cust_league_sessions(self, mine=False, package_id=None):
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

        return self._get_resource("/data/league/cust_league_sessions")

    def league_directory(
        self,
        search="",
        tag="",
        restrict_to_member=False,
        restrict_to_recruiting=False,
        restrict_to_friends=False,
        restrict_to_watched=False,
        minimum_roster_count=0,
        maximum_roster_count=999,
        lowerbound=1,
        upperbound=None,
        sort=None,
        order="asc",
    ):
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
        params = locals()
        payload = {}
        for x in params.keys():
            if x != "self":
                payload[x] = params[x]

        return self._get_resource("/data/league/directory", payload=payload)

    def league_get_points_systems(self, league_id, season_id=None):
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

        return self._get_resource("/data/league/get_points_systems", payload=payload)

    def league_membership(self, include_league=False):
        """Fetches a list containing all the leagues the user is currently a member.

        Retrieves a list containing all the leagues the user is member.

        Args:
            include_league (bool): if ``True``, also receives the league detailed information in ``league``.

        Returns:
            list: A list containing all the leagues the user is member.
        """
        payload = {"include_league": include_league}
        return self._get_resource("/data/league/membership", payload=payload)

    def league_seasons(self, league_id, retired=False):
        """Fetches a list containing all the seasons from a league.

        Retrieves a list containing all the seasons from a league.

        Args:
            league_id (int): the league to retrieve the seasons
            retired (bool): Default ``False``. If ``True``, includes seasons which are no longer active.

        Returns:
            list: A list containing all the seasons from a league.
        """
        payload = {"league_id": league_id, "retired": retired}
        return self._get_resource("/data/league/seasons", payload=payload)

    def league_season_standings(
        self, league_id, season_id, car_class_id=None, car_id=None
    ):
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

        return self._get_resource("/data/league/season_standings", payload=payload)

    def league_season_sessions(self, league_id, season_id, results_only=False):
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
        return self._get_resource("/data/league/season_sessions", payload=payload)

    def lookup_club_history(self, season_year, season_quarter):
        """The club history for a year and season.

        Note: returns an earlier history if requested quarter does not have a club history

        Args:
            season_year (int): the season year
            season_quarter (int): the season quarter (1, 2, 3, 4)

        Returns:
            list: a list containing all the history from all clubs in the requested year and season.

        """
        payload = {"season_year": season_year, "season_quarter": season_quarter}
        return self._get_resource("/data/lookup/club_history", payload=payload)

    def lookup_countries(self):
        """The list of country names and the country codes.

        Returns:
            list: a list containing all the country names and country codes.

        """
        return self._get_resource("/data/lookup/countries")

    def lookup_drivers(self, search_term=None, league_id=None):
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

        return self._get_resource("/data/lookup/drivers", payload=payload)

    def lookup_get(self):
        return self._get_resource("/data/lookup/get")

    def lookup_licenses(self):
        """All the iRacing licenses.

        Retrieves a list containing all the current licenses, from Rookie to Pro/WC.

        Returns:
            list: a list containing all the current licenses, from Rookie to Pro/WC.

        """
        return self._get_resource("/data/lookup/licenses")

    def result(self, subsession_id=None, include_licenses=False):
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
        if not subsession_id:
            raise RuntimeError("Please supply a subsession_id")

        payload = {"subsession_id": subsession_id, "include_licenses": include_licenses}
        return self._get_resource("/data/results/get", payload=payload)

    def result_lap_chart_data(self, subsession_id=None, simsession_number=0):
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
        if not subsession_id:
            raise RuntimeError("Please supply a subsession_id")

        payload = {
            "subsession_id": subsession_id,
            "simsession_number": simsession_number,
        }
        resource = self._get_resource("/data/results/lap_chart_data", payload=payload)
        return self._get_chunks(resource.get("chunk_info"))

    def result_lap_data(
        self, subsession_id=None, simsession_number=0, cust_id=None, team_id=None
    ):
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
        if not subsession_id:
            raise RuntimeError("Please supply a subsession_id")

        if not cust_id and not team_id:
            raise RuntimeError("Please supply either a cust_id or a team_id")

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
            return self._get_chunks(resource.get("chunk_info"))

        # if there are no chunks to get, that's because no laps were done by this cust_id
        # on this subsession, return an empty list for compatibility
        return []

    def result_event_log(self, subsession_id=None, simsession_number=0):
        """Get all the logs from a result sim session.

        Retrieves a list of all events logged during a sim event (Practice, Qualifying, Race)...

        Args:
            subsession_id (int): the unique id of the subsession from iRacing.
            simsession_number (int): -2 for practice, -1 for qualy, 0 for race. Default ``0``.

        Returns:
            list: A list of all the logged events during a sim session.

        """
        if not subsession_id:
            raise RuntimeError("Please supply a subsession_id")

        payload = {
            "subsession_id": subsession_id,
            "simsession_number": simsession_number,
        }
        resource = self._get_resource("/data/results/event_log", payload=payload)
        return self._get_chunks(resource.get("chunk_info"))

    def result_search_hosted(
        self,
        start_range_begin=None,
        start_range_end=None,
        finish_range_begin=None,
        finish_range_end=None,
        cust_id=None,
        host_cust_id=None,
        session_name=None,
        league_id=None,
        league_season_id=None,
        car_id=None,
        track_id=None,
        category_ids=None,
    ):
        """Search for hosted and league sessions.

        Hosted and league sessions. Maximum time frame of 90 days.
        Results split into one or more files with chunks of results.
        For scraping results the most effective approach is to keep track of the maximum end_time
        found during a search then make the subsequent call using that date/time as the finish_range_begin
        and skip any subsessions that are duplicated.

        Results are ordered by subsessionid which is a proxy for start time

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
        Returns:
            list: a list containing all the hosted results matching criteria.

        """
        if not (start_range_begin or finish_range_begin):
            raise RuntimeError(
                "Please supply either start_range_begin or finish_range_begin"
            )

        if not (cust_id or host_cust_id):
            raise RuntimeError("Please supply either cust_id or host_cust_id")

        params = locals()
        payload = {}
        for x in params.keys():
            if x != "self" and params[x]:
                payload[x] = params[x]

        resource = self._get_resource("/data/results/search_hosted", payload=payload)
        return self._get_chunks(resource.get("data", dict()).get("chunk_info"))

    def result_search_series(
        self,
        season_year=None,
        season_quarter=None,
        start_range_begin=None,
        start_range_end=None,
        finish_range_begin=None,
        finish_range_end=None,
        cust_id=None,
        series_id=None,
        race_week_num=None,
        official_only=True,
        event_types=None,
        category_ids=None,
    ):
        """Search for official series sessions.

        Official series.  Maximum time frame of 90 days. Results split into one or more files with chunks
        of results. For scraping results the most effective approach is to keep track
        of the maximum end_time found during a search then make the subsequent call using that
        date/time as the finish_range_begin and skip any subsessions that are duplicated.
        Results are ordered by subsessionid which is a proxy for start time but groups
        together multiple splits of a series when multiple series launch sessions at the same time.
        Requires at least one of: season_year and season_quarter, start_range_begin, finish_range_begin.

        Args:
            season_year (int): the season year
            season_quarter (int): the season quarter (1, 2, 3, 4)
            start_range_begin (str): Session start times. ISO-8601 UTC time zero offset: "2022-04-01T15:45Z"
             Exclusive. May be omitted if finish_range_begin is less than 90 days in the past.
            start_range_end (str): ISO-8601 UTC time zero offset: "2022-04-01T15:45Z".
             Exclusive. May be omitted if start_range_begin is less than 90 days in the past.
            finish_range_begin (str): Session finish times. ISO-8601 UTC time zero offset: "2022-04-01T15:45Z".
            finish_range_end (str): ISO-8601 UTC time zero offset: "2022-04-01T15:45Z".
            cust_id (int): The participant's customer ID.
            series_id (id): Include only sessions for series with this ID.
            race_week_num (id): Include only sessions with this race week number.
            official_only (bool): If true, include only sessions earning championship points. Defaults to all.
            event_types (list[int]): Types of events to include in the search. Defaults to all. event_types=2,3,4,5
            category_ids (list[int]): Track categories to include in the search (1,2,3,4).  Defaults to all.

        Returns:
            list: a list containing all the hosted results matching criteria.

        """
        if not (
            (season_year and season_quarter) or start_range_begin or finish_range_begin
        ):
            raise RuntimeError(
                "Please supply Season Year and Season Quarter or a date range"
            )

        params = locals()
        payload = {}
        for x in params.keys():
            if x != "self" and params[x]:
                payload[x] = params[x]

        resource = self._get_resource("/data/results/search_series", payload=payload)
        return self._get_chunks(resource.get("data", dict()).get("chunk_info"))

    def result_season_results(self, season_id, event_type=None, race_week_num=None):
        """Get results from a certain race week from a series season.

        Args:
            season_id (int): the id of the session.
            event_type (int): Restrict to one event type: 2 - Practice; 3 - Qualify; 4 - Time Trial; 5 - Race
            race_week_num (int): The first race week of a season is 0.

        Returns:
            list: a list of sessions within the matching criteria.

        """
        payload = {"season_id": season_id}
        if event_type:
            payload["event_type"] = event_type
        if race_week_num:
            payload["race_week_num"] = race_week_num

        return self._get_resource("/data/results/season_results", payload=payload)

    def member(self, cust_id=None, include_licenses=False):
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
        if not cust_id:
            raise RuntimeError("Please supply a cust_id")

        payload = {"cust_ids": cust_id, "include_licenses": include_licenses}
        return self._get_resource("/data/member/get", payload=payload)

    def member_chart_data(self, cust_id=None, category_id=2, chart_type=1):
        """Get the irating, ttrating or safety rating chart data of a certain category.

        Args:
            cust_id (int): the iRacing cust_id
            category_id (int): 1 - Oval; 2 - Road; 3 - Dirt oval; 4 - Dirt road
            chart_type (int): 1 - iRating; 2 - TT Rating; 3 - License/SR

        Returns:
            dict: a dict containing the time series chart data given the matching criteria.

        """
        payload = {"category_id": category_id, "chart_type": chart_type}
        if cust_id:
            payload["cust_id"] = cust_id

        return self._get_resource("/data/member/chart_data", payload=payload)

    def member_info(self):
        """Account info from the authenticated member.

        Returns:
            dict: a dict containing the detailed information from the authenticated member.

        """
        return self._get_resource("/data/member/info")

    def member_profile(self, cust_id=None):
        """Detailed profile info from a member.

        Args:
            cust_id (int): The iRacing cust_id. Default the authenticated member.

        Returns:
            dict: a dict containing the detailed profile info from the member requested.

        """
        payload = {}
        if cust_id:
            payload["cust_id"] = cust_id
        return self._get_resource("/data/member/profile", payload=payload)

    def stats_member_bests(self, cust_id=None, car_id=None):
        """Get the member best laptimes from a certain cust_id and car_id.

        Args:
            cust_id (int): The iRacing cust_id. Default the authenticated member.
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

        return self._get_resource("/data/stats/member_bests", payload=payload)

    def stats_member_career(self, cust_id=None):
        """Get the member career stats from a certain cust_id

        Args:
            cust_id (int): The iRacing cust_id. Default the authenticated member.

        Returns:
            dict: a dict containing the member career stats

        """
        if not cust_id:
            raise RuntimeError("Please supply a cust_id")

        payload = {"cust_id": cust_id}
        return self._get_resource("/data/stats/member_career", payload=payload)

    def stats_member_recent_races(self, cust_id=None):
        """Get the latest member races from a certain cust_id

        Args:
            cust_id (int): The iRacing cust_id. Default the authenticated member.

        Returns:
            dict: a dict containing the latest member races

        """
        if not cust_id:
            raise RuntimeError("Please supply a cust_id")

        payload = {"cust_id": cust_id}
        return self._get_resource("/data/stats/member_recent_races", payload=payload)

    def stats_member_summary(self, cust_id=None):
        """Get the member stats summary from a certain cust_id

        Args:
            cust_id (int): The iRacing cust_id. Default the authenticated member.

        Returns:
            dict: a dict containing the member stats summary

        """
        if not cust_id:
            raise RuntimeError("Please supply a cust_id")

        payload = {"cust_id": cust_id}
        return self._get_resource("/data/stats/member_summary", payload=payload)

    def stats_member_yearly(self, cust_id=None):
        """Get the member stats yearly from a certain cust_id

        Args:
            cust_id (int): The iRacing cust_id. Default the authenticated member.

        Returns:
            dict: a dict containing the member stats yearly

        """
        if not cust_id:
            raise RuntimeError("Please supply a cust_id")
        payload = {"cust_id": cust_id}
        return self._get_resource("/data/stats/member_yearly", payload=payload)

    def stats_season_driver_standings(
        self, season_id, car_class_id, race_week_num=None, club_id=None, division=None
    ):
        """Get the driver standings from a season.

        Args:
            season_id (int): The iRacing season id.
            car_class_id (int): the iRacing car class id.
            race_week_num (int): the race week number (0-12). Default 0.
            club_id (int): the iRacing club id.
            division (int): the iRacing division.

        Returns:
            dict: a dict containing the season driver standings

        """
        payload = {"season_id": season_id, "car_class_id": car_class_id}
        if race_week_num:
            payload["race_week_num"] = race_week_num
        if club_id:
            payload["club_id"] = club_id
        if division:
            payload["division"] = division

        resource = self._get_resource(
            "/data/stats/season_driver_standings", payload=payload
        )
        return self._get_chunks(resource.get("chunk_info"))

    def stats_season_supersession_standings(
        self, season_id, car_class_id, race_week_num=None, club_id=None, division=None
    ):
        """Get the supersession standings from a season.

        Args:
            season_id (int): The iRacing season id.
            car_class_id (int): the iRacing car class id.
            race_week_num (int): the race week number (0-12). Default 0.
            club_id (int): the iRacing club id.
            division (int): the iRacing division.

        Returns:
            dict: a dict containing the season supersession standings

        """
        payload = {"season_id": season_id, "car_class_id": car_class_id}
        if race_week_num:
            payload["race_week_num"] = race_week_num
        if club_id:
            payload["club_id"] = club_id
        if division:
            payload["division"] = division

        resource = self._get_resource(
            "/data/stats/season_supersession_standings", payload=payload
        )
        return self._get_chunks(resource.get("chunk_info"))

    def stats_season_team_standings(self, season_id, car_class_id, race_week_num=None):
        """Get the team standings from a season.

        Args:
            season_id (int): The iRacing season id.
            car_class_id (int): the iRacing car class id.
            race_week_num (int): the race week number (0-12). Default 0.

        Returns:
            dict: a dict containing the season team standings

        """
        payload = {"season_id": season_id, "car_class_id": car_class_id}
        if race_week_num:
            payload["race_week_num"] = race_week_num

        resource = self._get_resource(
            "/data/stats/season_team_standings", payload=payload
        )
        return self._get_chunks(resource.get("chunk_info"))

    def stats_season_tt_standings(
        self, season_id, car_class_id, race_week_num=None, club_id=None, division=None
    ):
        """Get the Time Trial standings from a season.

        Args:
            season_id (int): The iRacing season id.
            car_class_id (int): the iRacing car class id.
            race_week_num (int): the race week number (0-12). Default 0.
            club_id (int): the iRacing club id.
            division (int): the iRacing division.

        Returns:
            dict: a dict containing the Time Trial standings

        """
        payload = {"season_id": season_id, "car_class_id": car_class_id}
        if race_week_num:
            payload["race_week_num"] = race_week_num
        if club_id:
            payload["club_id"] = club_id
        if division:
            payload["division"] = division

        resource = self._get_resource(
            "/data/stats/season_tt_standings", payload=payload
        )
        return self._get_chunks(resource.get("chunk_info"))

    def stats_season_tt_results(
        self, season_id, car_class_id, race_week_num, club_id=None, division=None
    ):
        """Get the Time Trial results from a season.

        Args:
            season_id (int): The iRacing season id.
            car_class_id (int): the iRacing car class id.
            race_week_num (int): the race week number (0-12). Default 0.
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
        if division:
            payload["division"] = division

        resource = self._get_resource("/data/stats/season_tt_results", payload=payload)
        return self._get_chunks(resource.get("chunk_info"))

    def stats_season_qualify_results(
        self, season_id, car_class_id, race_week_num, club_id=None, division=None
    ):
        """Get the qualifying results from a season.

        Args:
            season_id (int): The iRacing season id.
            car_class_id (int): the iRacing car class id.
            race_week_num (int): the race week number (0-12). Default 0.
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
        if division:
            payload["division"] = division

        resource = self._get_resource(
            "/data/stats/season_qualify_results", payload=payload
        )
        return self._get_chunks(resource.get("chunk_info"))

    def stats_world_records(
        self, car_id, track_id, season_year=None, season_quarter=None
    ):
        """Get the world records from a given track and car.

        Args:
            car_id (int): the iRacing car id
            track_id (int): the iRacing track id
            season_year (int): the season year
            season_quarter (int): the season quarter (1, 2, 3, 4). Only applicable when ``season_year`` is used.

        Returns:
            dict: a dict containing the world records

        """
        payload = {"car_id": car_id, "track_id": track_id}
        if season_year:
            payload["season_year"] = season_year
        if season_quarter:
            payload["season_quarter"] = season_quarter

        resource = self._get_resource("/data/stats/world_records", payload=payload)
        return self._get_chunks(resource.get("data", dict()).get("chunk_info"))

    def team(self, team_id, include_licenses=False):
        """Get detailed team information.

        Args:
            team_id (int): the iRacing unique id from the team.
            include_licenses (bool): include licenses from all team members. For faster responses,
             only request when necesary.

        Returns:
            dict: a dict containing the team information.

        """
        payload = {"team_id": team_id, "include_licenses": include_licenses}
        return self._get_resource("/data/team/get", payload=payload)

    def season_list(self, season_year, season_quarter):
        """Get the list of iRacing Official seasons given a year and quarter.

        Args:
            season_year (int): the season year
            season_quarter (int): the season quarter (1, 2, 3, 4). Only applicable when ``season_year`` is used.

        Returns:
            dict: a dict containing the list of iRacing Official seasons given a year and quarter.

        """
        payload = {"season_year": season_year, "season_quarter": season_quarter}
        return self._get_resource("/data/season/list", payload=payload)

    def season_race_guide(self, start_from=None, include_end_after_from=None):
        """Get the season schedule race guide.

        Args:
            start_from (str): ISO-8601 offset format. Defaults to the current time.
             Include sessions with start times up to 3 hours after this time.
             Times in the past will be rewritten to the current time.
            include_end_after_from (bool): Include sessions which start before 'from' but end after.

        Returns:
            dict: a dict containing the season schedule race guide.

        """
        payload = {}
        if start_from:
            payload["from"] = start_from
        if include_end_after_from:
            payload["include_end_after_from"] = include_end_after_from

        return self._get_resource("/data/season/race_guide", payload=payload)

    def season_spectator_subsessionids(self, event_types=[2, 3, 4, 5]):
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

        return self._get_resource(
            "/data/season/spectator_subsessionids", payload=payload
        )["subsession_ids"]

    def get_series(self):
        """Get all the current official iRacing series.

        Returns:
            list: a list containing all the official iRacing series.

        """
        return self._get_resource("/data/series/get")

    def get_series_assets(self):
        """Get all the current official iRacing series assets.

        Get the images, description and logos from the current official iRacing series.

        Returns:
            dict: a dict containing all the current official iRacing series assets.

        """
        return self._get_resource("/data/series/assets")

    def series_assets(self):
        print(
            "series_assets() is deprecated and will be removed in a future release, please update to use get_series_assets"
        )
        return self.get_series_assets()

    def series_seasons(self, include_series=False):
        """Get the all the seasons.

        To get series and seasons for which standings should be available, filter the list by ``'official'``: ``True``.

        Args:
            include_series (bool): whether if you want to include the series information or not. Default ``False``.

        Returns:
            list: a list containing all the series and seasons.

        """
        payload = {"include_series": include_series}
        return self._get_resource("/data/series/seasons", payload=payload)

    def series_stats(self):
        """Get the all the series and seasons.

        To get series and seasons for which standings should be available, filter the list by ``'official'``: ``True``.

        Returns:
            list: a list containing all the series and seasons.

        """
        return self._get_resource("/data/series/stats_series")
