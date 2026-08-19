from rest_framework import viewsets, status
from rest_framework.response import Response

from recipes.models import Tag, Ingredient, Recipe
from .filters import IngredientSearchFilter
from .permissions import IsAuthorAdminOrReadOnly
from .serializers import (
    TagSerializer,
    IngredientSerializer,
    RecipeReadSerializer,
    RecipeWriteSerializer
)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = (IngredientSearchFilter,)
    search_fields = ['^name']


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = (IsAuthorAdminOrReadOnly,)

    def get_serializer_class(self):
        if self.request.method in ('POST', 'PATCH', 'PUT'):
            return RecipeWriteSerializer
        return RecipeReadSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        recipe = serializer.save(author=request.user)
        return Response(
            RecipeReadSerializer(recipe, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=partial
        )
        serializer.is_valid(raise_exception=True)
        recipe = serializer.save()
        return Response(
            RecipeReadSerializer(recipe, context={'request': request}).data,
            status=status.HTTP_200_OK
        )
