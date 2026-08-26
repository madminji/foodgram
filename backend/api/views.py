from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.db.models import Sum
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import NotAuthenticated

from recipes.models import (
    Tag,
    Ingredient,
    Recipe,
    Favorite,
    ShoppingList,
    IngredientRecipe,
    Follow,
    User
)
from .filters import IngredientSearchFilter
from .permissions import IsAuthorAdminOrReadOnly
from .serializers import (
    TagSerializer,
    IngredientSerializer,
    RecipeReadSerializer,
    RecipeWriteSerializer,
    RecipeShortSerializer,
    UserWithRecipesSerializer,
    Base64ImageField
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

    @action(detail=True, methods=['post', 'delete'])
    def favorite(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)

        if request.method == 'POST':
            if Favorite.objects.filter(
                    user=request.user,
                    recipe=recipe
            ).exists():
                return Response(status=status.HTTP_400_BAD_REQUEST)
            Favorite.objects.create(user=request.user, recipe=recipe)
            return Response(
                RecipeShortSerializer(recipe).data,
                status=status.HTTP_201_CREATED
            )
        elif request.method == 'DELETE':
            Favorite.objects.filter(user=request.user, recipe=recipe).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post', 'delete'])
    def shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)

        if request.method == 'POST':
            if ShoppingList.objects.filter(
                    user=request.user,
                    recipe=recipe
            ).exists():
                return Response(status=status.HTTP_400_BAD_REQUEST)
            ShoppingList.objects.create(user=request.user, recipe=recipe)
            return Response(
                RecipeShortSerializer(recipe).data,
                status=status.HTTP_201_CREATED
            )
        elif request.method == 'DELETE':
            ShoppingList.objects.filter(
                user=request.user,
                recipe=recipe
            ).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'])
    def download_shopping_cart(self, request, pk=None):
        if not request.user.is_authenticated:
            raise NotAuthenticated()
        ingredients = IngredientRecipe.objects.filter(
            recipe__shopping_list__user=request.user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(
            total=Sum('amount')
        )

        content = ''
        for item in ingredients:
            name = item['ingredient__name']
            total = item['total']
            unit = item['ingredient__measurement_unit']

            content += f"{name} — {total} ({unit})\n"

        response = HttpResponse(content, content_type='text/plain')
        response['Content-Disposition'] = (
            "attachment; filename='shopping_cart.txt'"
        )
        return response


class UserViewSet(DjoserUserViewSet):
    queryset = User.objects.all()

    def get_queryset(self):
        return User.objects.all()

    @action(detail=False, methods=['get', 'put', 'patch'])
    def me(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise NotAuthenticated()
        return super().me(request, *args, **kwargs)

    @action(detail=True, methods=['post', 'delete'])
    def subscribe(self, request, **kwargs):
        pk = kwargs.get('id')
        following_user = get_object_or_404(User, pk=pk)

        if request.method == 'POST':
            if Follow.objects.filter(
                    user=request.user,
                    following=following_user
            ).exists():
                return Response(status=status.HTTP_400_BAD_REQUEST)
            Follow.objects.create(user=request.user, following=following_user)
            return Response(
                UserWithRecipesSerializer(
                    following_user,
                    context={'request': request}
                ).data,
                status=status.HTTP_201_CREATED
            )
        elif request.method == 'DELETE':
            Follow.objects.filter(
                user=request.user,
                following=following_user
            ).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'])
    def subscriptions(self, request, pk=None):
        if not request.user.is_authenticated:
            raise NotAuthenticated()
        following_users = User.objects.filter(followers__user=request.user)
        return Response(
            UserWithRecipesSerializer(
                following_users,
                many=True,
                context={'request': request}
            ).data,
            status=status.HTTP_200_OK)

    @action(detail=False, methods=['put', 'delete'], url_path='me/avatar')
    def avatar(self, request):
        if not request.user.is_authenticated:
            raise NotAuthenticated()
        if request.method == 'PUT':
            avatar = request.data['avatar']
            avatar_url = Base64ImageField().to_internal_value(avatar)
            request.user.avatar = avatar_url
            request.user.save()
            content = {'avatar': request.build_absolute_uri(request.user.avatar.url)}
            return Response(content, status=status.HTTP_200_OK)
        elif request.method == 'DELETE':
            request.user.avatar.delete(save=False)
            request.user.avatar = None
            request.user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
