# Контракты API для бекенда instrument-shop

Этот каталог — единый источник правды по контрактам между фронтом (Next.js, см. корень репозитория) и бекендом (Django + django-ninja, ещё не реализован полностью). AI-агент, реализующий бекенд, должен читать JSON-файлы из подкаталогов и приводить эндпоинты в точное соответствие с описанными схемами и примерами.

## Технологический стек бекенда (обязательно)

- **Python 3.11+**
- **Django 5.x** — модели, админка, миграции
- **django-ninja** — роутеры/эндпоинты, валидация через pydantic-схемы
- **JWT (ninja-jwt или djangorestframework-simplejwt)** — для access/refresh-токенов
- **PostgreSQL** — основная БД
- **Pillow** — обработка картинок (генерация webp / mobile-вариантов)
- **CORS** (django-cors-headers) — разрешить origin фронта

## База URL и общие соглашения

- Все эндпоинты — под префиксом `/api/`.
- Формат ответа — JSON; кодировка UTF-8; русский язык в `message`-полях.
- Имена полей JSON — **snake_case** (исключения, где так уже на фронте — `slugStatus`, `descriptionParameters`, `techicalSpecifications`; они приходят с фронта именно в таком виде, и менять их нельзя без правки frontend).
- Все списки изображений могут возвращать пустые объекты — фронт корректно отрендерит fallback. Поля с заглавных `?` в схеме — опциональны.
- Аутентификация — `Authorization: Bearer <access_token>` для эндпоинтов с `"auth": true`.
- Идентификаторы пользователей (`Customer.id`) — UUID-строки, не sequential int. Сделано из соображений безопасности (защита от enumeration / IDOR / утечки количества пользователей). Фронт должен трактовать `id` как opaque string.
- Все ошибки — единый формат `shared/error.json`. См. ниже список кодов.
- Время — ISO 8601 UTC (`2026-05-15T12:34:56Z`). Форматирование под пользователя — на фронте.
- HTML-контент в `content` / `description` / `parameters` приходит уже отрендеренным (теги `<h2>`, `<p>`, `<ul>`, `<blockquote>`, `&nbsp;`, `<br/>` и т.п.). На фронте используется `dangerouslySetInnerHTML` — бекенд обязан санитайзить input из админки (например, через `bleach`), иначе XSS.

## Структура каталога

```
contracts/
├── README.md                  ← этот файл
├── shared/                    ← переиспользуемые схемы ($ref на них из endpoint-файлов)
│   ├── picture.json
│   ├── site-link.json
│   ├── pagination.json
│   ├── error.json
│   ├── product.json
│   ├── product-category.json
│   └── news-card.json
├── pages/                     ← статичная информация (управляется из админки)
│   ├── home.json
│   ├── about-us.json
│   ├── buyers.json
│   ├── feedback.json
│   └── legal.json
├── news/
│   ├── list.json
│   └── single.json
├── catalog/
│   ├── catalog.json           ← /catalog (общий)
│   ├── category.json          ← /catalog/{slug}
│   └── product.json           ← /catalog/{slug}/{id}
├── auth/
│   ├── register.json
│   ├── login.json
│   ├── logout.json
│   ├── refresh.json
│   ├── me.json
│   ├── forgot-password.json
│   └── reset-password.json
├── feedback/
│   └── submit.json
└── favorites/
    ├── list.json
    └── toggle.json
```

Каждый endpoint-файл содержит:

- `endpoint` — метод и путь (для favorites/toggle — `endpoint_add` / `endpoint_remove`)
- `auth` — требуется ли авторизация
- `description` — что делает эндпоинт, кто его вызывает, особенности поведения
- `request` — `query` / `path` / `body` как пример реальных значений (типы видны из значений)
- `responses` — по HTTP-коду: `example` (рабочий JSON-ответ) + опционально `description`
- `notes` — пояснения только для неочевидных полей: обязательность, enum'ы, ограничения, ссылки на shared-схемы, особенности валидации. Поля без notes — их смысл понятен из имени и примера.

Файлы из `shared/` — переиспользуемые типы. На них ссылаются из `notes` фразой вроде «формат shared/product». Каждый содержит `example` (или несколько примеров для разных контекстов, как `example_list` / `example_detail` у product) и `notes`.

## Карта эндпоинтов

### Статичные страницы (управляются из админки)

| Метод | Путь                            | Контракт                  |
| ----- | ------------------------------- | ------------------------- |
| GET   | `/api/pages/home`               | `pages/home.json`         |
| GET   | `/api/pages/about-us`           | `pages/about-us.json`     |
| GET   | `/api/pages/buyers`             | `pages/buyers.json`       |
| GET   | `/api/pages/feedback`           | `pages/feedback.json`     |
| GET   | `/api/pages/legal/{slug}`       | `pages/legal.json`        |

### Новости

| Метод | Путь                  | Контракт            |
| ----- | --------------------- | ------------------- |
| GET   | `/api/news`           | `news/list.json`    |
| GET   | `/api/news/{slug}`    | `news/single.json`  |

### Каталог

| Метод | Путь                                    | Контракт                  |
| ----- | --------------------------------------- | ------------------------- |
| GET   | `/api/catalog`                          | `catalog/catalog.json`    |
| GET   | `/api/catalog/categories/{slug}`        | `catalog/category.json`   |
| GET   | `/api/catalog/products/{id}`            | `catalog/product.json`    |

### Авторизация

| Метод | Путь                          | Контракт                       | Auth |
| ----- | ----------------------------- | ------------------------------ | ---- |
| POST  | `/api/auth/register`          | `auth/register.json`           | —    |
| POST  | `/api/auth/login`             | `auth/login.json`              | —    |
| POST  | `/api/auth/logout`            | `auth/logout.json`             | ✔    |
| POST  | `/api/auth/refresh`           | `auth/refresh.json`            | —    |
| GET   | `/api/auth/me`                | `auth/me.json`                 | ✔    |
| POST  | `/api/auth/forgot-password`   | `auth/forgot-password.json`    | —    |
| POST  | `/api/auth/reset-password`    | `auth/reset-password.json`     | —    |

### Прочее

| Метод       | Путь                              | Контракт                     | Auth |
| ----------- | --------------------------------- | ---------------------------- | ---- |
| POST        | `/api/feedback`                   | `feedback/submit.json`       | —    |
| GET         | `/api/favorites`                  | `favorites/list.json`        | ✔    |
| POST/DELETE | `/api/favorites/{product_id}`     | `favorites/toggle.json`      | ✔    |

## Коды ошибок (единый формат — `shared/error.json`)

| HTTP | code                    | Где встречается                                  |
| ---- | ----------------------- | ------------------------------------------------ |
| 400  | `INVALID_TOKEN`         | reset-password (просрочена ссылка)              |
| 401  | `UNAUTHORIZED`          | любой эндпоинт с `auth: true` без токена         |
| 401  | `INVALID_CREDENTIALS`   | login                                           |
| 401  | `INVALID_TOKEN`         | refresh                                         |
| 404  | `NOT_FOUND`             | single news / product / category / legal        |
| 409  | `EMAIL_ALREADY_TAKEN`   | register                                        |
| 422  | `VALIDATION_ERROR`      | любой эндпоинт с body (см. `fields`)             |
| 429  | `RATE_LIMITED`          | feedback (антиспам)                             |
| 500  | `INTERNAL_ERROR`        | непредвиденные ошибки                           |

## Что бекенд должен предусмотреть, помимо роутов

1. **Админка Django** для редактирования статичных страниц (home, about-us, buyers, feedback, legal-pages, news), категорий каталога, товаров, отзывов.
2. **Загрузка изображений и автонарезка** (см. также `shared/picture.json`). Админ грузит **один файл-источник** (обычно `png` или `jpg`) для desktop и опционально **ещё один** для mobile-варианта. Бекенд автоматически создаёт `webp` и `avif` производные для каждого из них через `Pillow` + `pillow-avif-plugin` (в фоновой задаче celery/django-q по сигналу `post_save`). В ответе API возвращается полный объект `Picture` с тремя форматами × двумя ширинами. Если конвертация ещё не завершилась — возвращать только `original`, фронт корректно подхватит. Соответствие:

   | Что загрузил админ          | Что генерирует бекенд                                                              | Что отдаёт API                                                                       |
   | --------------------------- | ---------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------ |
   | desktop original (jpg/png)  | `webp.src`, `avif.src`                                                              | `{ original: { src }, webp: { src }, avif: { src } }`                                |
   | + mobile original (jpg/png) | дополнительно `webp.mobile`, `avif.mobile`                                          | `{ original: { src, mobile }, webp: { src, mobile }, avif: { src, mobile } }`        |

   Рекомендуемая структура моделей: одна таблица `Image` с полями `source_desktop`, `source_mobile` (загруженные файлы) и `webp_desktop`, `avif_desktop`, `webp_mobile`, `avif_mobile` (результат конверсии).
3. **Pydantic-схемы (ninja)** для ответов — должны строго соответствовать примерам из контрактов. Имена полей — те же.
4. **Поиск/сортировка/фильтрация** для каталога: фильтр по цене, мульти-фильтр по категориям, sort = `popular | price_asc | price_desc | new`.
5. **JWT**: access ≈ 1 час, refresh ≈ 30 дней, ротация refresh-токенов, blacklist при logout.
6. **CORS** настроить под URL фронта (`http://localhost:3000` в dev, продакшн домен — позднее).
7. **Throttling** на `/api/feedback` и `/api/auth/forgot-password` — простой rate-limit по IP.
8. **HTML-санитайзинг** редактируемого админом контента (страницы, новости, описания товаров).

## Откуда брать примеры данных

Все примеры в контрактах основаны на текущих mock-константах фронта — см. `src/views/*/models/*.constants.ts`. При запуске бекенда полезно загрузить эти mock'и как seed-фикстуры (`./manage.py loaddata`), чтобы фронт сразу заработал поверх живого API без правок.

Соответствие mock'ов и эндпоинтов:

| Mock-константа                                                            | Эндпоинт                            |
| ------------------------------------------------------------------------- | ----------------------------------- |
| `src/views/home-page/models/home-page.constants.ts`                       | `GET /api/pages/home`               |
| `src/views/about-us-page/models/about-us-page.constants.ts`               | `GET /api/pages/about-us`           |
| `src/views/buyers-page/models/buyers-page.constants.ts`                   | `GET /api/pages/buyers`             |
| `src/views/feedback-page/models/feedback-page.constants.ts`               | `GET /api/pages/feedback`           |
| `src/views/privacy-policy-page/models/privacy-policy.constants.ts`        | `GET /api/pages/legal/privacy-policy` |
| `src/views/user-agreement-page/models/user-agreement.constants.ts`        | `GET /api/pages/legal/user-agreement` |
| `src/views/personal-data-consent-page/models/personal-data-consent.constants.ts` | `GET /api/pages/legal/personal-data-consent` |
| `src/views/news-page/models/news-page.constants.ts`                       | `GET /api/news`                     |
| `src/views/single-news-page/models/single-news-page.constants.ts`         | `GET /api/news/{slug}`              |
| `src/views/catalog-page/models/catalog-page.constants.ts`                 | `GET /api/catalog`                  |
| `src/views/catalog-category-page/models/catalog-category-page.constants.ts` | `GET /api/catalog/categories/{slug}` |
| `src/views/single-product-page/models/single-product-page.constants.ts`   | `GET /api/catalog/products/{id}`    |
| `src/shared/config/catalog-filters.constants.ts`                          | блок `filter_block` в catalog       |

## Правила работы для AI-агента

1. **Каждый эндпоинт реализуется по своему JSON-файлу.** Если поле в файле помечено как обязательное — оно обязательно в ответе. Если опциональное и значение отсутствует — лучше не возвращать ключ вообще, чем возвращать `null`.
2. **Имена полей менять нельзя.** Фронт типизирован — переименование поля = баг в UI.
3. **Если на этапе реализации обнаруживается потребность в новом поле / эндпоинте** — сначала допиши контракт в этот каталог (`*.json` + строку в README), потом реализуй код. Контракты — первичны.
4. **Сидируй БД из mock'ов фронта** на старте — это минимизирует расхождения и упрощает локальную проверку.
5. **Не реализуй то, чего нет в контрактах** (например, корзину, оплату через сайт — см. `pages/buyers.json`: оплата только в магазине, корзины на сайте нет).
