import re

from rest_framework import serializers

USERNAME_REGEX = re.compile(r'^[\w.@+-]+\Z', re.ASCII)


def validate_username_not_me(value):
    if value.lower() == 'me':
        raise serializers.ValidationError(
            'Использовать имя "me" запрещено.'
        )

    return value


def validate_unique_ingredients(ingredients):
    ingredient_ids = [item['id'].id for item in ingredients]

    if len(ingredient_ids) != len(set(ingredient_ids)):
        raise serializers.ValidationError(
            'Ингредиенты не должны повторяться.'
        )

    return ingredients


def validate_unique_tags(tags):
    tag_ids = [tag.id for tag in tags]

    if len(tag_ids) != len(set(tag_ids)):
        raise serializers.ValidationError(
            'Теги не должны повторяться.'
        )

    return tags
