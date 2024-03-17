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
idc.stats_member_summary(cust_id=20979)

# get latest results of a member
idc.stats_member_recent_races(cust_id=209179)

# get all laps for a specific driver in a race
idc.result_lap_data(subsession_id=43720351, cust_id=209179)
```

All available methods of `irDataClient` are included in `client.py`.

# Contributing

I welcome all pull requests for improvements or missing endpoints over time as they are added by iRacing.

# Changelog
**1.1.6**
-   More rate limiting fixes

**1.1.5**
-   Add rate limiting to `_get_resource`

**1.1.4**
-   Fix `result_search_series` to correctly include `finish_range_begin` as an option
-   Fix `season_spectator_subsessionids` to correctly return the IDs rather than the object

**1.1.3**
-   Bug fix for some 5xx errors that are thrown by iRacing
-   Added the `season_spectator_subsessionids()` endpoint

**1.1.0**
-   Added docstrings to all methods for developer experience
-   Renamed `series()` to `get_series()` for consistency. **Breaking change:** For that same consistency, `series` has been reimplemented as a property which returns the series with their assets. To amend your implementation, either switch to `get_series()` or remove any brackets in your call of `series`.
-   Renamed `get_carclass()` to `get_carclasses()` to be more consistent with other endpoints. **NOTE:** `get_carclass()` will be removed in a future release.
-   Added assets to the returned data of `tracks`. If you prefer not to get those assets, use `get_tracks()`.
-   Removed redundant cookie handling code, as that is all handled within `requests.Session`
-   Fixed a ratelimiting error
-   Fixed a ratelimiting bug
-   Fixed a bug related to empty results
-   Improved handling of results


**1.0.6**
-   Bug fix in `result_lap_data` method, which will now return an empty list for any `cust_id`/`subsession_id` combinations for which laps were not turned.

**1.0.5**
-   Added a wait when hitting a rate limit

**1.0.4**
-   Bug fix: Previously an attempt wouldn't be retried if the authentication data became stale. This release fixes that

**1.0.3**

-   Added the endpoints described in the [August 22nd update](https://forums.iracing.com/discussion/comment/219438/#Comment_219438)

**1.0.2**

-   Adjusted login flow to avoid logging in on instantiation of an `irDataClient` object
-   Login now happens either on the initial call to an iRacing endpoint, or whenever a `401 Unauthorized` response is received form iRacing

**1.0.1**

-   Adjusted `result_search_series` to allow searches by date range without using season years and quarters.
