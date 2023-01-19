import base64
import hashlib

import requests


class irDataClient:
    def __init__(self, username=None, password=None):
        self.authenticated = False
        self.session = requests.Session()
        self.base_url = "https://members-ng.iracing.com"

        self._login(username=username, password=password)

        self.cars = self.get_cars()
        tracks = self.get_tracks()
        track_assets = self.get_tracks_assets()
        for track in tracks:
            a = track_assets[str(track['track_id'])]
            for key in a.keys():
                track[key] = a[key]

        self.tracks = tracks


    def _login(self, username=None, password=None):
        if not username or not password:
            raise RuntimeError("Please supply a username and password")

        # iRacing requires Base64 encoded string as of 2022 season 3
        password_hash = hashlib.sha256(
            (password + username.lower()).encode("utf-8")
        ).digest()
        password_b64 = base64.b64encode(password_hash).decode("utf-8")

        payload = {"email": username, "password": password_b64}

        r = self.session.post(self._build_url("/auth"), json=payload)

        if r.status_code != 200:
            raise RuntimeError("Error from iRacing: ", r.json())

        self.authenticated = True
        return True

    def _build_url(self, endpoint):
        return self.base_url + endpoint

    def _get_resource_or_link(self, url, payload=None):
        r = self.session.get(url, params=payload)
        if r.status_code != 200:
            raise RuntimeError(r.json())
        if "link" in r.json().keys():
            return [r.json()["link"], True]
        else:
            return [r.json(), False]
        #return r.json()["link"]

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

    def get_cars(self):
        return self._get_resource("/data/car/get")

    def get_tracks(self):
        return self._get_resource("/data/track/get")

    def get_tracks_assets(self):
        return self._get_resource("/data/track/assets")

    def league(self, league_id=None, include_licenses=False):
        if not league_id:
            raise RuntimeError("Please supply a league_id")
        payload = {"league_id": league_id, "include_licenses": include_licenses}
        return self._get_resource("/data/league/get", payload=payload)

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
        if resource["chunk_info"]:
            return self._get_chunks(resource["chunk_info"])
        return None

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
            raise RuntimeError("Please supply either start_range_begin or finish_range_begin")
        
        if not (cust_id or host_cust_id):
            raise RuntimeError("Please supply either cust_id or host_cust_id")
        
        # params = locals()
        # payload = {}
        # for x in params.keys():
        #     if x != 'self' and params[x]:
        #         payload[x] = params[x]
        
        # resource = self._get_resource("/data/results/search_hosted", payload=payload)
        # return self._get_chunks(resource["chunk_info"])
        raise NotImplementedError("This endpoint is not implemented yet.")        

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
        self, season_id, car_class_id, race_week_num=None
    ):
        payload = {"season_id": season_id, "car_class_id": car_class_id}
        if race_week_num:
            payload["race_week_num"] = race_week_num

        resource = self._get_resource(
            "/data/stats/season_driver_standings", payload=payload
        )
        return self._get_chunks(resource["chunk_info"])

    def stats_season_supersession_standings(
        self, season_id, car_class_id, race_week_num=None
    ):
        payload = {"season_id": season_id, "car_class_id": car_class_id}
        if race_week_num:
            payload["race_week_num"] = race_week_num

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

    def team(self, team_id, include_licenses=False):
        payload = {"team_id": team_id, "include_licenses": include_licenses}
        return self._get_resource("/data/team/get", payload=payload)

    def series(self):
        return self._get_resource("/data/series/get")

    def series_seasons(self, include_series=False):
        payload = {"include_series": include_series}
        return self._get_resource("/data/series/seasons", payload=payload)

    def series_stats(self):
        return self._get_resource("/data/series/stats_series")

    def search_series(
            self,
            season_year=None,
            season_quarter=None,
            start_range_begin=None,
            start_range_end=None,
            finish_range_begin=None, finish_range_end=None,
            cust_id=None, series_id=None, race_week_num=None,
            official_only=True,
            event_types=None,
            category_ids=None):
        if not(season_year or season_quarter):
            raise RuntimeError("Please supply Season Year and Season Quarter")

        params = locals()
        payload = {}
        for x in params.keys():
            if x != 'self' and params[x]:
                payload[x] = params[x]

        resource = self._get_resource("/data/results/search_series", payload=payload)
        return self._get_chunks(resource["data"]["chunk_info"])
