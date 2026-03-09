### Оглавление:
- Описание API.
- Примеры запросов.
- Инструкцию по запуску.
- Описание БД.

## Описание API

URL Shortener Service - cервис для сокращения ссылок с возможностью отслеживания статистики, установки времени жизни и кастомных алиасов.

Возможности:
- Создание коротких ссылок
- Кастомные алиасы (пользовательские короткие коды)
- Установка времени жизни ссылки
- Статистика переходов
- Поиск по оригинальному URL
- Регистрация и авторизация пользователей
- Управление ссылками для зарегистрированных пользователей (обновление/удаление)
- Кэширование популярных ссылок
- Фоновое удаление истекших ссылок
- История истекших ссылок



## Примеры запросов.

- Создание короткой ссылки

POST /links/shorten
Content-Type: application/json

{
  "original_url": "https://example.com/url",
  "custom_alias": "myalias",
  "expires_at": "2026-12-31T23:59:59Z"
}

Ответ:

{
  "short_code": "myalias",
  "original_url": "https://example.com/url",
  "created_at": "2026-03-09T12:00:00Z",
  "expires_at": "2026-12-31T23:59:59Z"
}

- Переход по короткой ссылке

GET /links/{short_code}

GET /links/рtg5fj

- Получение статистики

GET /links/{short_code}/stats

GET /links/рtg5fj/stats

Ответ:

{
  "original_url": "https://example.com/url",
  "short_code": "рtg5fj",
  "created_at": "2026-03-09T12:00:00Z",
  "access_count": 42,
  "last_accessed_at": "2026-03-09T15:30:00Z",
  "expires_at": null
}

- Поиск по оригинальному URL

GET /links/search?original_url=example

Ответ:

[
  {
    "short_code": "abc123",
    "original_url": "https://example.com",
    "created_at": "2026-03-09T12:00:00Z",
    "access_count": 42
  }
]

- Получение истекших ссылок

GET /links/expired

- Проверка ссылки на срок истечения
curl -X 'GET' \
  'http://localhost:9999/links/U1fcoT/expired' \
  -H 'accept: application/json'

Ответ:
{
  "short_code": "U1fcoT",
  "expired": false,
  "expires_at": "2026-04-15T18:38:09.035000+00:00",
  "days_remaining": 36,
  "days_expired": null
}

- Обновление ссылки (требуется авторизация)

PUT /links/{short_code}
Authorization: Bearer token
Content-Type: application/json

{
  "original_url": "https://newexample.com"
}

- Удаление ссылки (требуется авторизация)

DELETE /links/{short_code}
Authorization: Bearer token

- Авторизация (Auth)

POST /auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "123"
}

- Вход и получение токена

POST /auth/jwt/login
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=123

Ответ:

{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
  "token_type": "bearer"
}


Фоновые задачи:

- Ручной запуск очистки неиспользуемых ссылок

POST /tasks/cleanup/unused?days=30

- Проверка статуса задачи

GET /tasks/task/{task_id}

Автоматические задачи:
- Каждый час удаление истекших ссылок
- Каждый день удаление неиспользуемых ссылок (30 дней без переходов)


## Инструкцию по запуску.

Необходимы установненные Docker, Docker Compose, Git

Шаги для запуска:
- 1 - клонировать репозиторий

git clone 

cd project_3

- 2 - создать файл .env

cp .env.example .env


DB_USER=postgres
DB_PASS=postgres
DB_HOST=db
DB_PORT=1221
DB_NAME=shortener

REDIS_HOST=redis
REDIS_PORT=5370

SECRET=your-secret-key-here


- 3 - запустить контейнеры

docker-compose up --build

- 4 - проверить работу 

API: http://localhost:9999

Документация: http://localhost:9999/docs

Flower: http://localhost:8888



## Описание БД.

Таблица users
Поле                Тип	                Описание
id	                Integer	            Первичный ключ
email	            String	Email       пользователя (уникальный)
hashed_password	    String	            Хеш пароля
is_active	        Boolean	            Активен ли аккаунт
is_superuser	    Boolean	            Администратор
is_verified	        Boolean	            Подтвержден ли email


Таблица links
Поле	            Тип	                Описание
id	                Integer	            Первичный ключ
original_url	    String	            Оригинальная длинная ссылка
short_code	        String	            Короткий код (уникальный)
created_at	        DateTime	        Дата создания
expires_at	        DateTime	        Дата истечения (опционально)
last_accessed_at	DateTime	        Последнее использование
access_count	    Integer	            Количество переходов
user_id	            Integer (FK)	    Владелец ссылки (может быть NULL)




