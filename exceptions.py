"""Собственные исключения."""


class APIResponseError(Exception):
    """Исключение для неожиданного статуса ответа."""

    pass


class ConnectionError(Exception):
    """Исключение для неожиданного статуса ответа."""

    pass
