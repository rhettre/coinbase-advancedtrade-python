"""Helpers for working with Coinbase SDK response objects."""

from typing import Any, Dict


def response_to_dict(response: Any) -> Any:
    """Convert dict-like SDK responses and nested objects to plain Python data."""
    if response is None:
        return {}

    if isinstance(response, dict):
        return {key: response_to_dict(value) for key, value in response.items()}

    if isinstance(response, list):
        return [response_to_dict(item) for item in response]

    to_dict = getattr(type(response), "to_dict", None)
    if callable(to_dict):
        return response_to_dict(response.to_dict())

    if hasattr(response, "__dict__"):
        return {
            key: response_to_dict(value)
            for key, value in vars(response).items()
            if not key.startswith("_") and not callable(value)
        }

    return response


def get_response_value(response: Any, key: str, default: Any = None) -> Any:
    """Read a field from either a dict or an SDK response object."""
    if isinstance(response, dict):
        return response.get(key, default)

    if hasattr(response, key):
        return getattr(response, key)

    try:
        value = response[key]
    except (KeyError, TypeError, AttributeError):
        return default

    return default if value is None else value


def ensure_dict(response: Any) -> Dict[str, Any]:
    """Return a dict for responses that should normalize into mappings."""
    response_dict = response_to_dict(response)
    return response_dict if isinstance(response_dict, dict) else {}
