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

# Changelog

**1.0.4**
-   Bug fix: Previously an attempt wouldn't be retried if the authentication data became stale. This release fixes that

**1.0.3**

-   Added the endpoints described in the [August 22nd update](https://forums.iracing.com/discussion/comment/219438/#Comment_219438)

**1.0.2**

-   Adjusted login flow to avoid logging in on instantiation of an `irDataClient` object
-   Login now happens either on the initial call to an iRacing endpoint, or whenever a `401 Unauthorized` response is received form iRacing

**1.0.1**

-   Adjusted `result_search_series` to allow searches by date range without using season years and quarters.
