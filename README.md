# Foodgram

Фудграм это сайт, на котором пользователи публикуют свои рецепты, добавляют чужие рецепты в избранное и подписываются на публикации других авторов. Зарегистрированным пользователям доступна функция «Список покупок» — он позволяет собрать список продуктов, необходимых для приготовления выбранных блюд, и скачать его одним файлом.

Проект доступен по адресу: [https://foodgram-study.myftp.biz](https://foodgram-study.myftp.biz)

## Возможности

- Публикация, редактирование и удаление собственных рецептов
- Добавление рецептов в избранное
- Подписка на публикации других авторов
- Список покупок с автоматическим суммированием одинаковых ингредиентов и выгрузкой в файл
- Фильтрация рецептов по тегам
- Короткие ссылки на рецепты
- Смена аватара и пароля

## Технологии

- Python, Django, Django REST Framework, Djoser
- PostgreSQL
- Nginx, Gunicorn
- Docker
- GitHub Actions (CI/CD)

## Как запустить проект локально

1. Клонировать репозиторий:
```bash
git clone git@github.com:madminji/foodgram.git
cd foodgram
```

2. Создать файл `.env` в папке `infra/` со следующим содержимым:
```env
POSTGRES_DB=foodgram
POSTGRES_USER=foodgram_user
POSTGRES_PASSWORD=foodgram_password
DB_HOST=db
DB_PORT=5432
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=foodgram-study.myftp.biz,localhost,127.0.0.1
```

3. Перейти в папку `infra/` и запустить проект через Docker Compose:
```bash
cd infra
docker compose up --build
```

4. Применить миграции, собрать статику и создать суперпользователя:
```bash
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py collectstatic --no-input
docker compose exec backend cp -r /app/collected_static/. /backend_static/static/
docker compose exec backend python manage.py createsuperuser
```

5. (Опционально) Загрузить тестовые ингредиенты:
```bash
docker compose exec backend python manage.py load_ingredients
```

Проект будет доступен по адресу [http://localhost:7000](http://localhost:7000).

## Разворачивание на удалённом сервере

Проект настроен на автоматический деплой через GitHub Actions при пуше в ветку `main`:

1. Тестирование бэкенда (flake8, Django-тесты)
2. Сборка и публикация Docker-образов (backend, frontend, gateway) в Docker Hub
3. Копирование `docker-compose.production.yml` на сервер и перезапуск контейнеров
4. Применение миграций и сборка статики
5. Уведомление в Telegram об успешном деплое

Для работы CI/CD в репозитории должны быть настроены секреты:

| Секрет | Назначение |
|---|---|
| `DOCKER_USERNAME`, `DOCKER_PASSWORD` | Docker Hub |
| `HOST`, `USER`, `SSH_KEY` | доступ к серверу |
| `TELEGRAM_TO`, `TELEGRAM_TOKEN` | уведомления о деплое |


## Автор

[Мадина Тахирова](https://github.com/madminji)