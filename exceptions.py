"""Собственные исключения."""


class APIResponseError(Exception):
    """Исключение для неожиданного статуса ответа."""


class UnavailablePageError(Exception):
    """Исключение для неожиданного статуса ответа."""
