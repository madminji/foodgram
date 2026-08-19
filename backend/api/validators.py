import re

from rest_framework import serializers

USERNAME_REGEX = re.compile(r'^[\w.@+-]+\Z', re.ASCII)


def validate_username_not_me(value):
    if value.lower() == 'me':
        raise serializers.ValidationError(
            'Использовать имя "me" запрещено.'
        )

    return value
