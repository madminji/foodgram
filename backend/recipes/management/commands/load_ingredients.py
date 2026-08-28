import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    def handle(self, *args, **options):
        data_dir = Path(settings.BASE_DIR) / 'data' / 'ingredients.json'
        with open(data_dir, encoding='utf-8') as f:
            data = json.load(f)
        for item in data:
            Ingredient.objects.get_or_create(
                name=item['name'],
                measurement_unit=item['measurement_unit']
            )
        self.stdout.write('Ингредиенты загружены')
