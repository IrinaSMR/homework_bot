class SendMessageException(Exception):
    """Исключение для проверки отправки сообщения."""

    pass


class GetAPIException(Exception):
    """Исключение для проверки запроса к API."""

    pass


class APIResponseException(Exception):
    """Исключение для проверки корректности ответа API."""

    pass


class StatusException(Exception):
    """Исключение для проверки статуса в ответе API."""

    pass

class JsonException(Exception):
    """Исключение при сериализации в json."""

    pass