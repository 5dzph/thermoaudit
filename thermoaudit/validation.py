"""Small, strict validators shared by the public API and CLI."""

import math


class ValidationError(ValueError):
    """Input is incomplete, ambiguous or outside the supported schema."""


def number(value, path, minimum=None, maximum=None):
    if isinstance(value, bool) or not isinstance(value, (float, int)):
        raise ValidationError(f"{path}: expected a JSON number")
    try:
        result = float(value)
    except (OverflowError, ValueError):
        raise ValidationError(f"{path}: number is outside the supported range") from None
    if not math.isfinite(result):
        raise ValidationError(f"{path}: number must be finite")
    if minimum is not None and result < minimum:
        raise ValidationError(f"{path}: must be >= {minimum}")
    if maximum is not None and result > maximum:
        raise ValidationError(f"{path}: must be <= {maximum}")
    return result


def positive(value, path):
    result = number(value, path, minimum=0)
    if result == 0:
        raise ValidationError(f"{path}: must be > 0")
    return result


def text(value, path):
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"{path}: expected a non-empty string")
    return value


def array(value, path, nonempty=True):
    if not isinstance(value, list) or (nonempty and not value):
        raise ValidationError(f"{path}: expected {'non-empty ' if nonempty else ''}array")
    return value


def obj(value, path, required, optional=()):
    if not isinstance(value, dict):
        raise ValidationError(f"{path}: expected object")
    missing = set(required) - value.keys()
    extra = value.keys() - set(required) - set(optional)
    if missing or extra:
        raise ValidationError(f"{path}: missing={sorted(missing)}, unknown={sorted(extra)}")
    return value


def finite_result(value, path):
    if not math.isfinite(value):
        raise ValidationError(f"{path}: numeric overflow; rescale your input")
    return value
