from django.contrib import admin

from recipes.models import User, Follow, Tag, Ingredient, Recipe, IngredientRecipe, Favorite, ShoppingList

admin.site.register(User)
admin.site.register(Follow)
admin.site.register(Tag)
admin.site.register(Ingredient)
admin.site.register(Recipe)
admin.site.register(IngredientRecipe)
admin.site.register(Favorite)
admin.site.register(ShoppingList)
