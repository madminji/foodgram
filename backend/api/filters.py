import django_filters
from rest_framework.filters import SearchFilter

from recipes.models import Recipe, Tag


class IngredientSearchFilter(SearchFilter):
    search_param = 'name'


class RecipeFilter(django_filters.FilterSet):
    tags = django_filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
    )
    is_favorited = django_filters.NumberFilter(
        method='filter_is_favorited',
    )
    is_in_shopping_cart = django_filters.NumberFilter(
        method='filter_is_in_shopping_cart',
    )

    class Meta:
        model = Recipe
        fields = ('author', 'tags', 'is_favorited', 'is_in_shopping_cart')

    def _filter_by_relation(self, queryset, value, relation_name):
        if not self.request.user.is_authenticated:
            return queryset

        lookup = {f'{relation_name}__user': self.request.user}

        if value == 1:
            return queryset.filter(**lookup)

        return queryset.exclude(**lookup)

    def filter_is_favorited(self, queryset, name, value):
        return self._filter_by_relation(
            queryset=queryset,
            relation_name='favorites',
            value=value
        )

    def filter_is_in_shopping_cart(self, queryset, name, value):
        return self._filter_by_relation(
            queryset=queryset,
            relation_name='shopping_list',
            value=value
        )
