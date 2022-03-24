import requests

class irDataClient:
    def __init__(self, username=None, password=None):
        self.authenticated = False
        self.session = requests.Session()
        self.base_url = "https://members-ng.iracing.com"

        self._login(username=username, password=password)

        self.cars = self.get_cars()
        self.tracks = self.get_tracks()


    def _login(self, username=None, password=None):
        if not username or not password:
            raise RuntimeError("Please supply a username and password")
        
        payload = {
            "email": username,
            "password": password
        }

        r = self.session.post(self._build_url("/auth"), json=payload)

        if r.status_code != 200:
            raise RuntimeError("Error from iRacing: ", r.json())

        self.authenticated = True
        return True

    def _build_url(self, endpoint):
        return self.base_url + endpoint

    def _get_resource_link(self, url, payload=None):
        r = self.session.get(url, params=payload)
        if r.status_code != 200:
            raise RuntimeError(r.json())
        
        return r.json()['link']

    def _get_resource(self, endpoint, payload=None):
        request_url = self._build_url(endpoint)
        resource_link = self._get_resource_link(request_url, payload=payload)
        r = self.session.get(resource_link)
        if r.status_code != 200:
            raise RuntimeError(r.json())

        return r.json()
    
    def _get_chunks(self, chunks):
        base_url = chunks['base_download_url']
        urls = [base_url+x for x in chunks['chunk_file_names']]
        list_of_chunks = [self.session.get(url).json() for url in urls]
        output = [item for sublist in list_of_chunks for item in sublist]
    
        return output

    def get_cars(self):
        return self._get_resource("/data/car/get")
    
    def get_tracks(self):
        return self._get_resource("/data/track/get")
    
    def get_league(self, league_id=None, include_licenses=False):
        if not league_id:
            raise RuntimeError("Please supply a league_id")
        payload = {"league_id": league_id, "include_licenses": include_licenses}
        return self._get_resource("/data/league/get", payload=payload)

    def get_result(self, subsession_id=None, include_licenses=False):
        if not subsession_id:
            raise RuntimeError("Please supply a subsession_id")
        
        payload = {"subsession_id": subsession_id, "include_licenses": include_licenses}
        return self._get_resource("/data/results/get", payload=payload)
    
    def get_result_lap_chart_data(self, subsession_id=None, simsession_number=0):
        if not subsession_id:
            raise RuntimeError("Please supply a subsession_id")
        
        payload = {"subsession_id": subsession_id, "simsession_number": simsession_number}
        resource = self._get_resource("/data/results/lap_chart_data", payload=payload)
        return self._get_chunks(resource['chunk_info'])

    def get_result_lap_data(self, subsession_id=None, simsession_number=0, cust_id=None, team_id=None):
        if not subsession_id:
            raise RuntimeError("Please supply a subsession_id")
        
        if not cust_id and not team_id:
            raise RuntimeError("Please supply either a cust_id or a team_id")
        
        payload = {"subsession_id": subsession_id, "simsession_number": simsession_number}
        if cust_id:
            payload["cust_id"] = cust_id
        if team_id:
            payload["team_id"] = team_id
   
        resource = self._get_resource("/data/results/lap_data", payload=payload)
        return self._get_chunks(resource['chunk_info'])

    def get_member(self, cust_id=None, include_licenses=False):
        if not cust_id:
            raise RuntimeError("Please supply a cust_id")
        
        payload= {"cust_ids": cust_id, "include_licenses": include_licenses}
        return self._get_resource("/data/member/get", payload=payload)
    
    def get_member_career(self, cust_id=None):
        if not cust_id:
            raise RuntimeError("Please supply a cust_id")
        
        payload = {"cust_id": cust_id}
        return self._get_resource("/data/stats/member_career", payload=payload)
    
    def get_member_recent_races(self, cust_id=None):
        if not cust_id:
            raise RuntimeError("Please supply a cust_id")
        
        payload = {"cust_id": cust_id}
        return self._get_resource("/data/stats/member_recent_races", payload=payload)

    def get_member_summary(self, cust_id=None):
        if not cust_id:
            raise RuntimeError("Please supply a cust_id")
        
        payload = {"cust_id": cust_id}
        return self._get_resource("/data/stats/member_summary", payload=payload)

    def get_member_yearly(self, cust_id=None):
        if not cust_id:
            raise RuntimeError("Please supply a cust_id")
        
        payload = {"cust_id": cust_id}
        return self._get_resource("/data/stats/member_yearly", payload=payload)