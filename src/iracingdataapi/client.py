import base64
import hashlib
import os
from http.cookiejar import LWPCookieJar

import requests


class irDataClient:
    def __init__(self, username=None, password=None, cookie_file=None):
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

    def _login(self, cookie_file=None):
        if cookie_file:
            self.session.cookies = LWPCookieJar(cookie_file)
            if not os.path.exists(cookie_file):
                self.session.cookies.save()
            else:
                self.session.cookies.load(ignore_discard=True)
        headers = {"Content-Type": "application/json"}
        data = {"email": self.username, "password": self.encoded_password}

        try:
            r = self.session.post(
                "https://members-ng.iracing.com/auth",
                headers=headers,
                json=data,
                timeout=5.0,
            )
        except requests.Timeout:
            raise RuntimeError("Login timed out")
        except requests.ConnectionError:
            raise RuntimeError("Connection error")
        else:
            response_data = r.json()
            if r.status_code == 200 and response_data["authcode"]:
                if cookie_file:
                    self.session.cookies.save(ignore_discard=True)
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

        if r.status_code != 200:
            raise RuntimeError(r.json())
        data = r.json()
        if not isinstance(data, list) and "link" in data.keys():
            return [data["link"], True]
        else:
            return [data, False]

    def _get_resource(self, endpoint, payload=None):
        request_url = self._build_url(endpoint)
        resource_obj, is_link = self._get_resource_or_link(request_url, payload=payload)
        if not is_link:
            return resource_obj
        r = self.session.get(resource_obj)
        if r.status_code != 200:
            raise RuntimeError(r.json())
        return r.json()

    def _get_chunks(self, chunks):
        base_url = chunks["base_download_url"]
        urls = [base_url + x for x in chunks["chunk_file_names"]]
        list_of_chunks = [self.session.get(url).json() for url in urls]
        output = [item for sublist in list_of_chunks for item in sublist]

        return output

    @property
    def cars(self):
        return self.get_cars()

    @property
    def tracks(self):
        tracks = self.get_tracks()
        track_assets = self.get_tracks_assets()
        for track in tracks:
            a = track_assets[str(track["track_id"])]
            for key in a.keys():
                track[key] = a[key]

        return tracks

    def constants_categories(self):
        return self._get_resource("/data/constants/categories")

    def constants_divisions(self):
        return self._get_resource("/data/constants/divisions")

    def constants_event_types(self):
        return self._get_resource("/data/constants/event_types")

    def get_cars(self):
        return self._get_resource("/data/car/get")

    def get_cars_assets(self):
        return self._get_resource("/data/car/assets")

    def get_carclass(self):
        return self._get_resource("/data/carclass/get")

    def get_tracks(self):
        return self._get_resource("/data/track/get")

    def get_tracks_assets(self):
        return self._get_resource("/data/track/assets")

    def hosted_combined_sessions(self, package_id=None):
        payload = {}
        if package_id:
            payload["package_id"] = package_id
        return self._get_resource("/data/hosted/combined_sessions", payload=payload)

    def hosted_sessions(self):
        return self._get_resource("/data/hosted/sessions")

    def league_get(self, league_id=None, include_licenses=False):
        if not league_id:
            raise RuntimeError("Please supply a league_id")
        payload = {"league_id": league_id, "include_licenses": include_licenses}
        return self._get_resource("/data/league/get", payload=payload)

    def league_cust_league_sessions(self, mine=False, package_id=None):
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
        params = locals()
        payload = {}
        for x in params.keys():
            if x != "self":
                payload[x] = params[x]

        return self._get_resource("/data/league/directory", payload=payload)

    def league_get_points_systems(self, league_id, season_id=None):
        payload = {"league_id": league_id}
        if season_id:
            payload["season_id"] = season_id

        return self._get_resource("/data/league/get_points_systems", payload=payload)

    def league_membership(self, include_league=False):
        payload = {"include_league": include_league}
        return self._get_resource("/data/league/membership", payload=payload)

    def league_seasons(self, league_id, retired=False):
        payload = {"league_id": league_id, "retired": retired}
        return self._get_resource("/data/league/seasons", payload=payload)

    def league_season_standings(
        self, league_id, season_id, car_class_id=None, car_id=None
    ):
        payload = {"league_id": league_id, "season_id": season_id}
        if car_class_id:
            payload["car_class_id"] = car_class_id
        if car_id:
            payload["car_id"] = car_id

        return self._get_resource("/data/league/season_standings", payload=payload)

    def league_season_sessions(self, league_id, season_id, results_only=False):
        payload = {
            "league_id": league_id,
            "season_id": season_id,
            "results_only": results_only,
        }
        return self._get_resource("/data/league/season_sessions", payload=payload)

    def lookup_club_history(self, season_year, season_quarter):
        payload = {"season_year": season_year, "season_quarter": season_quarter}
        return self._get_resource("/data/lookup/club_history", payload=payload)

    def lookup_countries(self):
        return self._get_resource("/data/lookup/countries")

    def lookup_drivers(self, search_term=None, league_id=None):
        payload = {"search_term": search_term}
        if league_id:
            payload["league_id"] = league_id

        return self._get_resource("/data/lookup/drivers", payload=payload)

    def lookup_get(self):
        return self._get_resource("/data/lookup/get")

    def lookup_licenses(self):
        return self._get_resource("/data/lookup/licenses")

    def result(self, subsession_id=None, include_licenses=False):
        if not subsession_id:
            raise RuntimeError("Please supply a subsession_id")

        payload = {"subsession_id": subsession_id, "include_licenses": include_licenses}
        return self._get_resource("/data/results/get", payload=payload)

    def result_lap_chart_data(self, subsession_id=None, simsession_number=0):
        if not subsession_id:
            raise RuntimeError("Please supply a subsession_id")

        payload = {
            "subsession_id": subsession_id,
            "simsession_number": simsession_number,
        }
        resource = self._get_resource("/data/results/lap_chart_data", payload=payload)
        return self._get_chunks(resource["chunk_info"])

    def result_lap_data(
        self, subsession_id=None, simsession_number=0, cust_id=None, team_id=None
    ):
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
        return self._get_chunks(resource["chunk_info"])

    def result_event_log(self, subsession_id=None, simsession_number=0):
        if not subsession_id:
            raise RuntimeError("Please supply a subsession_id")

        payload = {
            "subsession_id": subsession_id,
            "simsession_number": simsession_number,
        }
        resource = self._get_resource("/data/results/event_log", payload=payload)
        return self._get_chunks(resource["chunk_info"])

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
        return self._get_chunks(resource["data"]["chunk_info"])

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
        if not ((season_year and season_quarter) or (start_range_begin)):
            raise RuntimeError(
                "Please supply Season Year and Season Quarter or a date range"
            )

        params = locals()
        payload = {}
        for x in params.keys():
            if x != "self" and params[x]:
                payload[x] = params[x]

        resource = self._get_resource("/data/results/search_series", payload=payload)
        return self._get_chunks(resource["data"]["chunk_info"])

    def result_season_results(self, season_id, event_type=None, race_week_num=None):
        payload = {"season_id": season_id}
        if event_type:
            payload["event_type"] = event_type
        if race_week_num:
            payload["race_week_num"] = race_week_num

        return self._get_resource("/data/results/season_results", payload=payload)

    def member(self, cust_id=None, include_licenses=False):
        if not cust_id:
            raise RuntimeError("Please supply a cust_id")

        payload = {"cust_ids": cust_id, "include_licenses": include_licenses}
        return self._get_resource("/data/member/get", payload=payload)

    def member_chart_data(self, cust_id=None, category_id=2, chart_type=1):
        payload = {"category_id": category_id, "chart_type": chart_type}
        if cust_id:
            payload["cust_id"] = cust_id

        return self._get_resource("/data/member/chart_data", payload=payload)

    def member_info(self):
        return self._get_resource("/data/member/info")

    def member_profile(self, cust_id=None):
        payload = {}
        if cust_id:
            payload["cust_id"] = cust_id
        return self._get_resource("/data/member/profile", payload=payload)

    def stats_member_bests(self, cust_id=None, car_id=None):
        payload = {}
        if cust_id:
            payload["cust_id"] = cust_id
        if car_id:
            payload["car_id"] = car_id

        return self._get_resource("/data/stats/member_bests", payload=payload)

    def stats_member_career(self, cust_id=None):
        if not cust_id:
            raise RuntimeError("Please supply a cust_id")

        payload = {"cust_id": cust_id}
        return self._get_resource("/data/stats/member_career", payload=payload)

    def stats_member_recent_races(self, cust_id=None):
        if not cust_id:
            raise RuntimeError("Please supply a cust_id")

        payload = {"cust_id": cust_id}
        return self._get_resource("/data/stats/member_recent_races", payload=payload)

    def stats_member_summary(self, cust_id=None):
        if not cust_id:
            raise RuntimeError("Please supply a cust_id")

        payload = {"cust_id": cust_id}
        return self._get_resource("/data/stats/member_summary", payload=payload)

    def stats_member_yearly(self, cust_id=None):
        if not cust_id:
            raise RuntimeError("Please supply a cust_id")

        payload = {"cust_id": cust_id}
        return self._get_resource("/data/stats/member_yearly", payload=payload)

    def stats_season_driver_standings(
        self, season_id, car_class_id, race_week_num=None, club_id=None, division=None
    ):
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
        return self._get_chunks(resource["chunk_info"])

    def stats_season_supersession_standings(
        self, season_id, car_class_id, race_week_num=None, club_id=None, division=None
    ):
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
        return self._get_chunks(resource["chunk_info"])

    def stats_season_team_standings(self, season_id, car_class_id, race_week_num=None):
        payload = {"season_id": season_id, "car_class_id": car_class_id}
        if race_week_num:
            payload["race_week_num"] = race_week_num

        resource = self._get_resource(
            "/data/stats/season_team_standings", payload=payload
        )
        return self._get_chunks(resource["chunk_info"])

    def stats_season_tt_standings(
        self, season_id, car_class_id, race_week_num=None, club_id=None, division=None
    ):
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
        return self._get_chunks(resource["chunk_info"])

    def stats_season_tt_results(
        self, season_id, car_class_id, race_week_num, club_id=None, division=None
    ):
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
        return self._get_chunks(resource["chunk_info"])

    def stats_season_qualify_results(
        self, season_id, car_class_id, race_week_num, club_id=None, division=None
    ):
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
        return self._get_chunks(resource["chunk_info"])

    def stats_world_records(
        self, car_id, track_id, season_year=None, season_quarter=None
    ):
        payload = {"car_id": car_id, "track_id": track_id}
        if season_year:
            payload["season_year"] = season_year
        if season_quarter:
            payload["season_quarter"] = season_quarter

        resource = self._get_resource("/data/stats/world_records", payload=payload)
        return self._get_chunks(resource["data"]["chunk_info"])

    def team(self, team_id, include_licenses=False):
        payload = {"team_id": team_id, "include_licenses": include_licenses}
        return self._get_resource("/data/team/get", payload=payload)

    def season_list(self, season_year, season_quarter):
        payload = {"season_year": season_year, "season_quarter": season_quarter}
        return self._get_resource("/data/season/list", payload=payload)

    def season_race_guide(self, start_from=None, include_end_after_from=None):
        payload = {}
        if start_from:
            payload["from"] = start_from
        if include_end_after_from:
            payload["include_end_after_from"] = include_end_after_from

        return self._get_resource("/data/season/race_guide", payload=payload)

    def series(self):
        return self._get_resource("/data/series/get")

    def series_assets(self):
        return self._get_resource("/data/series/assets")

    def series_seasons(self, include_series=False):
        payload = {"include_series": include_series}
        return self._get_resource("/data/series/seasons", payload=payload)

    def series_stats(self):
        return self._get_resource("/data/series/stats_series")
