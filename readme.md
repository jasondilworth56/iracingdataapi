# About

iracing-data-api is a simple Python wrapper around the General Data API released by iRacing in January 2022 and documented [here](https://forums.iracing.com/discussion/15068/general-availability-of-data-api/).

The client allows easy access to some of the most useful endpoints of the data API. 

# Installation
`pip install iracingdataapi`

# Examples

```python
from iracingdataapi.client import irDataClient

idc = irDataClient(username=[YOUR iRACING USERNAME], password=[YOUR iRACING PASSWORD])

# get the summary data of a member
idc.get_member_summary(cust_id=20979)

# get latest results of a member
idc.get_member_recent_races(cust_id=209179)

# get all laps for a specific driver in a race
idc.get_result_lap_data(subsession_id=43720351, cust_id=209179)
```

All available methods of `irDataClient` are included in `client.py`.

# Contributing

I welcome all pull requests for improvements or missing endpoints over time as they are added by iRacing.