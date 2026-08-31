from django.conf import settings
from djoser.serializers import (
    UserCreateSerializer as DjoserUserCreateSerializer,
)
from rest_framework import serializers

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
from .fields import Base64ImageField
from .validators import (
    USERNAME_REGEX,
    validate_unique_ingredients,
    validate_unique_tags,
    validate_username_not_me,
)


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class IngredientWriteSerializer(serializers.Serializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(min_value=1)


class RecipeShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class UserCreateSerializer(DjoserUserCreateSerializer):
    username = serializers.RegexField(
        regex=USERNAME_REGEX,
        max_length=settings.USERNAME_MAX_LENGTH,
        validators=(validate_username_not_me,),
    )

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password'
        )


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar'
        )

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        if not user.is_authenticated:
            return False
        return Follow.objects.filter(user=user, following=obj).exists()


class UserWithRecipesSerializer(UserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'avatar', 'recipes', 'recipes_count'
        )

    def get_recipes(self, obj):
        recipes = obj.recipes.all()
        request = self.context.get('request')

        if request:
            recipes_limit = request.query_params.get('recipes_limit')

            if recipes_limit:
                recipes = recipes[:int(recipes_limit)]

        return RecipeShortSerializer(
            recipes,
            many=True,
            context=self.context,
        ).data

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj).count()


class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(required=True)

    class Meta:
        model = User
        fields = ('avatar',)


class RecipeReadSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    author = UserSerializer(read_only=True)
    ingredients = IngredientInRecipeSerializer(
        many=True,
        read_only=True,
        source='ingredientrecipe_set'
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time'
        )

    def _check_relation_exists(self, obj, model):
        user = self.context['request'].user
        if not user.is_authenticated:
            return False
        return model.objects.filter(recipe=obj, user=user).exists()

    def get_is_favorited(self, obj):
        return self._check_relation_exists(obj=obj, model=Favorite)

    def get_is_in_shopping_cart(self, obj):
        return self._check_relation_exists(obj=obj, model=ShoppingList)


class RecipeWriteSerializer(serializers.ModelSerializer):
    ingredients = IngredientWriteSerializer(
        many=True,
        allow_empty=False,
    )
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        required=True,
        allow_empty=False,
    )
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time'
        )

    def validate(self, data):
        if self.instance:
            if 'ingredients' not in data:
                raise serializers.ValidationError({
                    'ingredients': 'Это поле обязательно.'
                })

            if 'tags' not in data:
                raise serializers.ValidationError({
                    'tags': 'Это поле обязательно.'
                })

        if 'ingredients' in data:
            validate_unique_ingredients(data['ingredients'])

        if 'tags' in data:
            validate_unique_tags(data['tags'])

        return data

    def to_representation(self, instance):
        return RecipeReadSerializer(
            instance, context=self.context
        ).data

    def _create_ingredients(self, recipe, ingredients):
        ingredient_recipe_list = [
            IngredientRecipe(
                recipe=recipe,
                ingredient=ingredient['id'],
                amount=ingredient['amount'])
            for ingredient in ingredients
        ]
        IngredientRecipe.objects.bulk_create(ingredient_recipe_list)

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self._create_ingredients(recipe=recipe, ingredients=ingredients)
        return recipe

    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients', [])
        tags = validated_data.pop('tags', [])

        instance = super().update(instance, validated_data)

        instance.tags.set(tags)
        instance.ingredientrecipe_set.all().delete()
        self._create_ingredients(recipe=instance, ingredients=ingredients)

        return instance
