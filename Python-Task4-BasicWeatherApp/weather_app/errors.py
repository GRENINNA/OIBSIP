"""User-facing error types for weather and location services."""


class WeatherAppError(RuntimeError):
    """Base class for errors safe to display inside the GUI."""


class APIKeyMissingError(WeatherAppError):
    """No WeatherAPI.com API key was supplied."""


class AuthenticationError(WeatherAppError):
    """The WeatherAPI.com API key was rejected."""


class LocationNotFoundError(WeatherAppError):
    """The requested city or ZIP code could not be resolved."""


class RateLimitError(WeatherAppError):
    """The API request allowance was exhausted."""


class PlanAccessError(WeatherAppError):
    """The API key's subscription does not include the requested resource."""


class NetworkError(WeatherAppError):
    """A timeout or connection problem prevented the request."""


class ServiceError(WeatherAppError):
    """A remote service returned an unexpected failure."""


class ResponseFormatError(WeatherAppError):
    """A remote response did not contain the expected data."""
