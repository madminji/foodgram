from rest_framework import status
from rest_framework.exceptions import APIException


class BadRequestError(APIException):
    """Универсальная 400-ошибка с произвольным текстом причины."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Некорректный запрос.'
    default_code = 'bad_request'
