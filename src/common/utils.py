"""
Common utilities for Printy API.
"""
from decimal import Decimal


def decimal_from_value(value):
    """Safely convert to Decimal."""
    if value is None:
        return None
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))
