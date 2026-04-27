# 04 Public Catalog API ✅

### BE-011 Create public categories list endpoint

**Goal:** отдать категории без обязательной авторизации сотрудника.

**Implementation scope:**
- создать публичный endpoint списка категорий;
- не использовать staff permission-check для публичного чтения;
- вернуть только данные, нужные storefront.

**Done when:**
- гость может получить список категорий;
- endpoint не раскрывает внутренние поля.

**Depends on:** none

### BE-012 Create public products list endpoint

**Goal:** отдать публичный список товаров.

**Implementation scope:**
- создать endpoint списка товаров для storefront;
- возвращать только `published` товары;
- поддержать базовую пагинацию, если она уже принята в проекте, либо оставить явный TODO.

**Done when:**
- гость получает только опубликованные товары;
- черновики и архивные товары не возвращаются.

**Depends on:** `BE-001`

### BE-013 Create public product detail endpoint

**Goal:** отдать публичную карточку товара.

**Implementation scope:**
- создать endpoint детальной карточки товара;
- возвращать только `published` товар;
- подгружать категории и изображения оптимизированно.

**Done when:**
- карточка товара доступна без staff permissions;
- неопубликованный товар не виден в публичном API.

**Depends on:** `BE-001`

### BE-014 Add category filter to public product list

**Goal:** фильтровать публичный каталог по категории.

**Implementation scope:**
- добавить фильтрацию по `category_id` и/или `category_slug`;
- покрыть тестом.

**Done when:**
- фильтрация возвращает только товары нужной категории;
- API поведение проверено тестом.

**Depends on:** `BE-012`

### BE-015 Add product name search to public product list

**Goal:** добавить поиск товаров по названию.

**Implementation scope:**
- добавить query param для поиска;
- реализовать `icontains` или другой согласованный MVP-поиск;
- покрыть тестом.

**Done when:**
- товары можно искать по части названия;
- поиск работает только по публичной выдаче.

**Depends on:** `BE-012`

