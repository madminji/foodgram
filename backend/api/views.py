from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from recipes.models import (
    Favorite,
    Follow,
    Ingredient,
    IngredientRecipe,
    Recipe,
    ShoppingList,
    Tag,
    User,
)

from .exceptions import BadRequestError
from .filters import IngredientSearchFilter, RecipeFilter
from .permissions import IsAuthorAdminOrReadOnly
from .serializers import (
    Base64ImageField,
    IngredientSerializer,
    RecipeReadSerializer,
    RecipeShortSerializer,
    RecipeWriteSerializer,
    TagSerializer,
    UserWithRecipesSerializer,
)
from .utils import encode_base62, decode_base62


def short_link_redirect(request, short_code):
    recipe_id = decode_base62(short_code)

    recipe = get_object_or_404(
        Recipe,
        pk=recipe_id
    )

    return redirect(f'/recipes/{recipe.id}/')


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
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

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

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=(IsAuthenticated,)
    )
    def favorite(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        is_favorite_exists = Favorite.objects.filter(
            user=request.user,
            recipe=recipe
        ).exists()

        if request.method == 'POST':
            if is_favorite_exists:
                raise BadRequestError('Рецепт уже добавлен в избранное.')
            Favorite.objects.create(user=request.user, recipe=recipe)
            return Response(
                RecipeShortSerializer(recipe).data,
                status=status.HTTP_201_CREATED
            )
        elif request.method == 'DELETE':
            if not is_favorite_exists:
                raise BadRequestError('Рецепта нет в избранном.')
            Favorite.objects.filter(user=request.user, recipe=recipe).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=(IsAuthenticated,)
    )
    def shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        is_shopping_cart_exists = ShoppingList.objects.filter(
            user=request.user,
            recipe=recipe
        ).exists()

        if request.method == 'POST':
            if is_shopping_cart_exists:
                raise BadRequestError('Рецепт уже добавлен в список покупок.')
            ShoppingList.objects.create(user=request.user, recipe=recipe)
            return Response(
                RecipeShortSerializer(recipe).data,
                status=status.HTTP_201_CREATED
            )
        elif request.method == 'DELETE':
            if not is_shopping_cart_exists:
                raise BadRequestError('Рецепта нет в списке покупок.')
            ShoppingList.objects.filter(
                user=request.user,
                recipe=recipe
            ).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=(IsAuthenticated,)
    )
    def download_shopping_cart(self, request, pk=None):
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

    @action(detail=True, methods=['get'], url_path='get-link')
    def get_link(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        return Response({
            'short-link': request.build_absolute_uri(
                f'/s/{encode_base62(recipe.id)}/'
            )
        }
        )


class UserViewSet(DjoserUserViewSet):
    queryset = User.objects.all()

    def get_permissions(self):
        if self.action in ('update', 'partial_update', 'destroy'):
            return (IsAuthenticated(),)
        return super().get_permissions()

    @action(
        detail=False,
        methods=['get', 'put', 'patch'],
        permission_classes=(IsAuthenticated,)
    )
    def me(self, request, *args, **kwargs):
        return super().me(request, *args, **kwargs)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=(IsAuthenticated,)
    )
    def subscribe(self, request, **kwargs):
        pk = kwargs.get('id')
        following_user = get_object_or_404(User, pk=pk)
        is_subscription_exists = Follow.objects.filter(
            user=request.user,
            following=following_user
        ).exists()

        if request.method == 'POST':
            if request.user == following_user:
                raise BadRequestError('Нельзя подписаться на самого себя.')

            if is_subscription_exists:
                raise BadRequestError(
                    'Вы уже подписаны на этого пользователя.'
                )
            Follow.objects.create(user=request.user, following=following_user)
            return Response(
                UserWithRecipesSerializer(
                    following_user,
                    context={'request': request}
                ).data,
                status=status.HTTP_201_CREATED
            )
        elif request.method == 'DELETE':
            if not is_subscription_exists:
                raise BadRequestError(
                    'Вы не были подписаны на этого пользователя.'
                )
            Follow.objects.filter(
                user=request.user,
                following=following_user
            ).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=(IsAuthenticated,)
    )
    def subscriptions(self, request, pk=None):
        following_users = User.objects.filter(followers__user=request.user)

        page = self.paginate_queryset(following_users)

        if page is not None:
            serializer = UserWithRecipesSerializer(
                page,
                many=True,
                context={'request': request}
            )
            return self.get_paginated_response(serializer.data)

        serializer = UserWithRecipesSerializer(
            following_users,
            many=True,
            context={'request': request}
        )

        return Response(serializer.data)

    @action(
        detail=False,
        methods=['put', 'delete'],
        url_path='me/avatar',
        permission_classes=(IsAuthenticated,)
    )
    def avatar(self, request):
        if request.method == 'PUT':
            avatar = request.data.get('avatar')
            if avatar is None:
                return Response(
                    {'avatar': ['Это поле обязательно.']},
                    status=status.HTTP_400_BAD_REQUEST
                )
            avatar_file = Base64ImageField().to_internal_value(avatar)
            request.user.avatar = avatar_file
            request.user.save()
            content = {
                'avatar': request.build_absolute_uri(request.user.avatar.url)
            }
            return Response(content, status=status.HTTP_200_OK)
        elif request.method == 'DELETE':
            request.user.avatar.delete(save=False)
            request.user.avatar = None
            request.user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
