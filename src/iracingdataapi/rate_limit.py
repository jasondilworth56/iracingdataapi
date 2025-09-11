"""
Rate limiting functionality for iRacing API responses.

Provides the irRateLimit class for handling rate limit information
from HTTP response headers.
"""

from datetime import datetime, timezone
import requests


class irRateLimit:
    """
    Represents rate limiting information from iRacing API responses.

    This class encapsulates rate limiting data extracted from HTTP response headers
    provided by the iRacing API. Rate limiting helps prevent API abuse and ensures
    fair usage across all consumers.

    The iRacing API provides rate limit information through three HTTP headers:
        - x-ratelimit-limit: The current total rate limit (requests per time window)
        - x-ratelimit-remaining: How much of the rate limit you have remaining
        - x-ratelimit-reset: When the rate limit will reset (epoch timestamp)

    This class uses an "all or nothing" approach when updating from HTTP responses -
    rate limit data is only updated when ALL THREE headers are present. This ensures
    complete and useful rate limiting information.

    Examples:
        # Rate limit objects are automatically created and managed during API usage
        client = irDataClient(username="user", password="pass")
        client.get_cars()  # Makes API request
        
        # Check rate limit status
        if client.rate_limit.has_data:
            print(f"Remaining: {client.rate_limit.remaining}")
            if client.rate_limit.is_rate_limited:
                print("Rate limited! No requests remaining.")
    """

    def __init__(self) -> None:
        """
        Initialize rate limit object with type-safe default values.
        
        Creates an irRateLimit object with default values that are safe to access
        but indicate no actual rate limit data has been received yet. Use the
        has_data property to check if the object contains real API data.
        
        Default values:
            - limit: 0 (safe default)
            - remaining: 0 (safe default, indicates no requests available)
            - reset: 0 (epoch time 0 = 1970-01-01 00:00:00 UTC)
            - has_data: False (indicates defaults, not real API data)
        """
        self._limit: int = 0
        self._remaining: int = 0
        self._reset: int = 0
        self._has_data: bool = False
    
    def _update_from_response(self, response: requests.Response) -> None:
        """
        Internal method to update rate limit values from response headers.
        
        Args:
            response (requests.Response): HTTP response object from requests library.
                All required rate limit headers are guaranteed to be present and valid
                due to validation in the calling update_from_response() method.
                
        Note:
            This is an internal method. Headers are guaranteed to be present and
            contain valid integer values due to validation in the calling method.
        """
        # Headers and values are guaranteed to be valid due to calling method validation
        self._limit = int(response.headers['x-ratelimit-limit'])
        self._remaining = int(response.headers['x-ratelimit-remaining'])
        self._reset = int(response.headers['x-ratelimit-reset'])
        self._has_data = True
    
    def update_from_response(self, response: requests.Response) -> bool:
        """
        Update rate limit data from a new HTTP response.
        
        This is the main method for updating rate limit information. It safely
        handles responses that may or may not contain rate limit headers.
        
        Args:
            response (requests.Response): HTTP response object from requests library
                that may contain rate limit headers. If all three required headers are present
                (x-ratelimit-limit, x-ratelimit-remaining, x-ratelimit-reset) and contain
                valid integer values, the object's data will be updated. Otherwise, existing data is preserved.
        
        Returns:
            bool: True if rate limit headers were found with valid data and updated,
                False if headers were missing, incomplete, or contained invalid values.
                
        Example:
            client.rate_limit.update_from_response(response)
            if client.rate_limit.has_data:
                print(f'Remaining: {client.rate_limit.remaining}')
        """
        headers = response.headers
        if (headers.get('x-ratelimit-limit') and 
            headers.get('x-ratelimit-remaining') and 
            headers.get('x-ratelimit-reset')):
            
            # Validate that all header values can be converted to integers
            try:
                int(headers['x-ratelimit-limit'])
                int(headers['x-ratelimit-remaining'])
                int(headers['x-ratelimit-reset'])
            except (ValueError, TypeError):
                return False  # Invalid data, preserve existing state
            
            self._update_from_response(response)
            return True
        return False
    
    @property
    def has_data(self) -> bool:
        """
        Whether the rate limit object contains actual data from API responses.
        
        This property indicates if the rate limit object has been populated with
        real data from HTTP response headers. When False, the object contains
        only default values and should not be considered valid rate limit information.
        
        Returns:
            bool: True if populated with API response data, False if only defaults.
            
        Example:
            if client.rate_limit.has_data:
                print(f'API Rate limit: {client.rate_limit.remaining} remaining')
            else:
                print("No rate limit data available yet")
        """
        return self._has_data
    
    @property
    def limit(self) -> int:
        """
        The total rate limit for the current time window.

        This value comes from the x-ratelimit-limit HTTP header and represents
        the maximum number of requests allowed per time window.

        Returns:
            int: The total rate limit.
        """
        return self._limit
    
    @property
    def remaining(self) -> int:
        """
        Number of requests remaining in the current rate limit window.

        This value comes from the x-ratelimit-remaining HTTP header and indicates
        how many more requests can be made before hitting the rate limit.

        Returns:
            int: Remaining requests in the current window.
        """
        return self._remaining
    
    @property
    def reset(self) -> int:
        """
        Unix timestamp when the rate limit will reset.

        This value comes from the x-ratelimit-reset HTTP header and represents
        the time (as seconds since Unix epoch) when the rate limit counter
        will reset, and you'll have your full quota available again.

        Returns:
            int: Unix epoch timestamp of rate limit reset.
        """
        return self._reset
    
    @property
    def reset_time(self) -> datetime:
        """
        Rate limit reset time as a UTC datetime object.

        Converts the Unix timestamp from the reset property into a timezone-aware
        datetime object in UTC. Unix timestamps are inherently UTC, so this
        preserves the correct timezone information.

        Returns:
            datetime: When the rate limit will reset, as a UTC datetime object.
                Always timezone-aware (UTC). For default values, returns 
                1970-01-01 00:00:00+00:00 (Unix epoch).
        """
        return datetime.fromtimestamp(self._reset, tz=timezone.utc)
    
    @property
    def seconds_until_reset(self) -> float:
        """
        Number of seconds until the rate limit resets.

        Calculates the time remaining until the rate limit counter resets
        based on the current UTC time and the reset timestamp from the API.
        Uses UTC for consistent calculations regardless of local timezone.

        Returns:
            float: Seconds until rate limit reset. Returns 0.0 if the reset
                time has already passed. Always returns a non-negative value.
        """
        delta = self.reset_time - datetime.now(timezone.utc)
        return max(0.0, delta.total_seconds())
    
    @property
    def is_rate_limited(self) -> bool:
        """
        Whether the current rate limit has been exhausted.
        
        Returns:
            bool: True if no requests remaining and we have valid data, False otherwise.
                Returns False if has_data is False (no valid rate limit data).
        """
        return self.has_data and self.remaining == 0