# About

iracing-data-api is a simple Python wrapper around the General Data API released by iRacing in January 2022 and documented [here](https://forums.iracing.com/discussion/15068/general-availability-of-data-api/).

The client allows easy access to some of the most useful endpoints of the data API.

# Pre-installation

Ensure that you have marked your account with iRacing for legacy authentication - accounts with 2FA will not work with the API. This is a limitation of iRacing, not this wrapper.

# Installation

`pip install iracingdataapi`

# Examples

## Using Oauth2 access token

When you have acquired an Oauth2 access token from iRacing, and have ensured that token is valid, you can
use it like so in this client:

```python
from iracingdataapi.client import irDataClient

idc = irDataClient(access_token=[YOUR OAUTH2 TOKEN])
```

The rest of the client will work exactly the same, except that when that token expires you will find the client
raises an `AccessTokenInvalid` exception. For now, managing refreshing of tokens etc is outside the scope of
this client, so build around that exception and reinitialise the client with a new token when necessary. For instance:

```python
try:
  lap_data = idc.result_lap_data(subsession_id=12345678, cust_id=987654)
except AccessTokenInvalid:
  # access token is invalid
  new_token = do_something_in_your_code_to_refresh_token()
  idc = irDataClient(access_token=[NEW TOKEN])
  lap_data = idc.result_lap_data(subsession_id=12345678, cust_id=987654)
```

All available methods of `irDataClient` are included in `client.py`.

## Enabling Pydantic type hinting

You can opt-in to use of Pydantic model objects in the return of all method endpoints by initialising with `use_pydantic` like so:

```python
idc = irDataClient(access_token=[YOUR OAUTH2 TOKEN], use_pydantic=True)
```

# Contributing

I welcome all pull requests for improvements or missing endpoints over time as they are added by iRacing.

# Changelog

**1.3.0**

- Added a minimal Oauth2 implementation. You can now choose to send either username/password credentials as before, or use the iRacing Oauth2 token to make your requests. More information in the readme.

**1.2.3**

- Update `result_search_hosted` to remove the `cust_id`/`host_cust_id` requirement, and also add the `team_id` parameter. Thanks @glenbecker for that.

**1.2.2**

- Added `driver_list` endpoint, thanks to @nylanderj for that
- Corrected issues where `if [parameter]` would skip if the parameter was correctly set to 0, e.g. `race_week_num`. Thanks to @abelsm2 for that
- Added initial test setup
- Added type hints throughout

**1.2.0**
Thanks to @ablesm2 for these changes.

- Added missing endpoints
  - `time_attack_member_season_results()`
    `stats_member_recap()`
    `stats_member_division()`
    `series_past_seasons()`
    `league_roster()`
- Removed check for cust_id on methods that default the currently logged in member:
  - `stats_member_summary()`
    `stats_member_yearly()`
    `stats_member_recent_races()`

**1.1.6**

- More rate limiting fixes

**1.1.5**

- Add rate limiting to `_get_resource`

**1.1.4**

- Fix `result_search_series` to correctly include `finish_range_begin` as an option
- Fix `season_spectator_subsessionids` to correctly return the IDs rather than the object

**1.1.3**

- Bug fix for some 5xx errors that are thrown by iRacing
- Added the `season_spectator_subsessionids()` endpoint

**1.1.0**

- Added docstrings to all methods for developer experience
- Renamed `series()` to `get_series()` for consistency. **Breaking change:** For that same consistency, `series` has been reimplemented as a property which returns the series with their assets. To amend your implementation, either switch to `get_series()` or remove any brackets in your call of `series`.
- Renamed `get_carclass()` to `get_carclasses()` to be more consistent with other endpoints. **NOTE:** `get_carclass()` will be removed in a future release.
- Added assets to the returned data of `tracks`. If you prefer not to get those assets, use `get_tracks()`.
- Removed redundant cookie handling code, as that is all handled within `requests.Session`
- Fixed a ratelimiting error
- Fixed a ratelimiting bug
- Fixed a bug related to empty results
- Improved handling of results

**1.0.6**

- Bug fix in `result_lap_data` method, which will now return an empty list for any `cust_id`/`subsession_id` combinations for which laps were not turned.

**1.0.5**

- Added a wait when hitting a rate limit

**1.0.4**

- Bug fix: Previously an attempt wouldn't be retried if the authentication data became stale. This release fixes that

**1.0.3**

- Added the endpoints described in the [August 22nd update](https://forums.iracing.com/discussion/comment/219438/#Comment_219438)

**1.0.2**

- Adjusted login flow to avoid logging in on instantiation of an `irDataClient` object
- Login now happens either on the initial call to an iRacing endpoint, or whenever a `401 Unauthorized` response is received form iRacing

**1.0.1**

- Adjusted `result_search_series` to allow searches by date range without using season years and quarters.
