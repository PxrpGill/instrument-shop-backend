---
name: security-audit
description: Comprehensive security auditing for Django applications including dependency scanning, static analysis, and security best practices
---

# Skill: security-audit

**Назначение:** Поиск и устранение уязвимостей, dependency audit, security best practices

**Триггеры:** `security`, `уязвимость`, `audit`, `scan`, `vulnerability`, `dependency`, `safe`, `защита`

**Инструменты:** pip-audit, safety, bandit, semgrep, django-admin check --deploy, dependency-check

---

## Troubleshooting Flowchart

```
Security Audit Start
        │
        ▼
┌─────────────────────────┐
│ Тип аудита              │
│ ┌─────────┐ ┌─────────┐  │
│ │Code     │ │Dep      │  │
│ │Scan     │ │Audit    │  │
│ └────┬────┘ └────┬────┘  │
└──────┼──────────┼───────┘
       │          │
       ▼          ▼
┌───────────┐ ┌───────────┐
│ Static    │ │ Package   │
│ Analysis  │ │ Scan      │
│ - bandit  │ │ - safety  │
│ - semgrep │ │ - pip-    │
│           │ │   audit   │
└─────┬─────┘ └─────┬─────┘
       │          │
       ▼          ▼
┌───────────┐ ┌───────────┐
│ Django    │ │ Manual    │
│ Check     │ │ Review    │
│ --deploy  │ │ - Auth    │
│           │ │ - Input   │
│           │ │ - Output  │
└─────┬─────┘ └─────┬─────┘
       │          │
       ▼          ▼
┌─────────────────────────┐
│ Исправления             │
│ - Обновить пакеты       │
│ - Исправь код           │
│ - Напиши тест           │
└─────────────────────────┘
```

---

## 1. Dependency Scanning

### pip-audit

```bash
# Установка
pip install pip-audit

# Сканирование
pip-audit

# Формат вывода
pip-audit -r requirements.txt

# JSON для CI/CD
pip-audit --format=json > audit.json

# Фильтр по severity
pip-audit --fix  # Автоматическое обновление
```

### safety

```bash
# Установка
pip install safety

# Проверка
safety check

# Проверка конкретного файла
safety check -r requirements.txt

# Проверка с выводом JSON
safety check --json --output security-report.json

# Ignore определенный vulnerability
safety check --ignore=25853 --ignore=62897
```

### Запуск в CI/CD

```yaml
# .github/workflows/security.yml
name: Security Audit

on: [push, pull_request]

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          
      - name: Install dependencies
        run: pip install pip-audit safety
      
      - name: Run pip-audit
        run: pip-audit -r requirements.txt --format=json | tee audit-results.json
      
      - name: Run safety check
        run: safety check -r requirements.txt --json --output safety-report.json
```

---

## 2. Static Code Analysis

### bandit

```bash
# Установка
pip install bandit

# Сканирование проекта
bandit -r apps/

# Сканирование конкретного файла
bandit apps/orders/services.py

# Формат вывода
bandit -r apps/ -f txt
bandit -r apps/ -f json -o bandit-report.json

# Исключить директории
bandit -r apps/ -x tests,node_modules,.venv
```

### semgrep

```bash
# Установка
pip install semgrep

# Инициализация
semgrep install

# Сканирование
semgrep --config=p/security-secrets apps/

# Кастомные правила
semgrep --config=semgrep-rules/apps.yaml apps/

# Сканирование на secrets
semgrep --config=p/secrets apps/
```

### Кастомные semgrep правила

```yaml
# semgrep-rules/django-sql-injection.yaml
rules:
  - id: django-sql-injection
    patterns:
      - pattern: |
          Model.objects.raw($UNSAFE, ...)
      - pattern: |
          cursor.execute($UNSAFE, ...)
    message: Possible SQL injection vulnerability
    severity: ERROR
    languages:
      - python
```

---

## 3. Django Security Check

### Базовый check

```bash
# Development check
python manage.py check

# Production check (строгий режим)
python manage.py check --deploy
```

### Common issues

```python
# settings.py - Security settings

# ❌ Опасно
DEBUG = True
SECRET_KEY = 'hardcoded-secret-key'
ALLOWED_HOSTS = ['*']

# ✅ Безопасно
DEBUG = False
SECRET_KEY = env('SECRET_KEY')  # Минимум 50 символов
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost'])

# CSRF для API
CSRF_TRUSTED_ORIGINS = ['https://yourdomain.com']

# HTTPS
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000  # 1 год
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
```

### Проверка SECRET_KEY

```python
# management/commands/check_secret.py
import os
import random

def check_secret_key():
    from django.conf import settings
    
    key = settings.SECRET_KEY
    
    # Проверка длины
    if len(key) < 50:
        print("WARNING: SECRET_KEY is too short (minimum 50 characters)")
    
    # Проверка на default значение
    if key in ['django-insecure', 'CHANGE_ME', 'SET-SECRET-KEY']:
        print("ERROR: SECRET_KEY uses default value")
        
    # Проверка энтропии
    entropy = len(set(key)) / len(key)
    if entropy < 0.5:
        print("WARNING: SECRET_KEY has low entropy")
```

---

## 4. Authentication Security

### Password validation

```python
# settings.py
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 12,  # Усиленный требования
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]
```

### JWT Security

```python
# apps/users/jwt.py
from datetime import datetime, timedelta
from django.conf import settings
import jwt

class JWTSecurity:
    @staticmethod
    def create_token(user_id: int, token_type: str = 'access') -> str:
        now = datetime.utcnow()
        
        payload = {
            'user_id': user_id,
            'type': token_type,
            'iat': now,
            'exp': now + timedelta(minutes=15 if token_type == 'access' else 10080),
        }
        
        return jwt.encode(
            payload,
            settings.SECRET_KEY,
            algorithm='HS256'
        )
    
    @staticmethod
    def decode_token(token: str) -> dict:
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=['HS256']
            )
            
            # Дополнительная проверка типа токена
            if payload.get('type') != 'access':
                raise jwt.InvalidTokenError("Invalid token type")
                
            return payload
        except jwt.ExpiredSignatureError:
            raise ValueError("Token expired")
        except jwt.InvalidTokenError as e:
            raise ValueError(f"Invalid token: {str(e)}")
```

### Rate limiting

```python
# settings.py - напоминание настроек
MIDDLEWARE = [
    # ...
    'ratelimit.middleware.RateLimitMiddleware',
]

# apps/products/public_api.py - пример
from ninja.throttling import AnonRateThrottle

class PublicRateThrottle(AnonRateThrottle):
    rate = '100/minute'
```

---

## 5. Input Validation & Sanitization

### Schema validation

```python
# apps/orders/schemas.py - обязательная валидация
from pydantic import BaseModel, EmailStr, field_validator
from typing import List

class OrderCreateSchema(BaseModel):
    contact_email: EmailStr  # Валидация email
    contact_phone: str
    
    @field_validator('contact_phone')
    @classmethod
    def validate_phone(cls, v: str) -> str:
        # Только цифры, +, пробелы
        import re
        if not re.match(r'^[\d\s\+\-\(\)]+$', v):
            raise ValueError('Invalid phone format')
        return v

class OrderItemSchema(BaseModel):
    product_id: int
    quantity: int
    
    @field_validator('quantity')
    @classmethod
    def validate_quantity(cls, v: int) -> int:
        if v <= 0:
            raise ValueError('Quantity must be positive')
        if v > 10000:
            raise ValueError('Quantity exceeds maximum allowed')
        return v
```

### XSS Prevention

```python
# ❌ Опасно - экранировать вручную
def render_user_content(content: str) -> str:
    return f"<div>{content}</div>"  # XSS vulnerability!

# ✅ Безопасно - использование Django templates
from django.utils.safestring import mark_safe

def render_safe(content: str) -> SafeString:
    # Django автоматически экранирует
    from django.template import Template, Context
    t = Template("{{ content }}")
    return t.render(Context({'content': content}))
```

### SQL Injection Prevention

```python
# ❌ Опасно
def unsafe_search(query):
    sql = f"SELECT * FROM products WHERE name LIKE '%{query}%'"
    return Product.objects.raw(sql)

# ✅ Безопасно
def safe_search(query):
    return Product.objects.filter(name__icontains=query)

# ✅ Для сложных запросов - parameterized
from django.db import connection

def complex_search(params):
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT * FROM orders WHERE status = %s AND created_at > %s",
            [params['status'], params['date']]
        )
        return cursor.fetchall()
```

---

## 6. Output Security

### Response headers

```python
# settings.py - настроить в prod
MIDDLEWARE = [
    # ...
]

# nginx default.conf (docker/prod/nginx/default.conf)
# Добавить заголовки безопасности

server {
    # ...
    
    # Security headers
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self'" always;
    add_header Permissions-Policy "geolocation=(), microphone=(), camera=()" always;
}
```

### CORS настройка

```python
# settings.py
CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=[])

# ❌ Опасно - wildcard с credentials
# CORS_ALLOW_CREDENTIALS = True
# CORS_ALLOWED_ORIGINS = ["*"]  # ЗАПРЕЩЕНО

# ✅ Безопасно
CORS_ALLOW_CREDENTIALS = False
CORS_ALLOWED_ORIGINS = [
    "https://example.com",
    "https://app.example.com",
]

# Для credentials
# CORS_ALLOWED_ORIGINS = ["https://example.com"]  # Без wildcard
# CORS_ALLOW_CREDENTIALS = True  # Только если разрешены конкретные origins
```

---

## 7. Manual Security Review

### Checklist для API endpoints

- [ ] Все endpoints требуют аутентификацию где нужно
- [ ] Используется proper authorization (permission classes)
- [ ] Input validation на всех входных данных
- [ ] Output encoding для предотвращения XSS
- [ ] SQL queries parameterized
- [ ] Rate limiting applied
- [ ] Sensitive data не логируется
- [ ] Error messages не раскрывают internals
- [ ] HTTPS required для authentication
- [ ] JWT tokens have proper expiration

### Review authentication

```python
# apps/users/api/controllers.py - проверка паттернов

# ✅ Правильно
@router.post("/login")
def login(request, credentials: LoginSchema):
    # Валидация credentials
    # Rate limiting
    # Возврат токена с expiration
    pass

# ❌ Неправильно
@router.post("/login")
def login(request, username: str, password: str):  # No schema validation
    # No rate limiting
    # Password in plain text
    pass
```

### Review authorization

```python
# ✅ Правильно
class OrderController:
    @router.get("/orders/{order_id}")
    @inject_permissions([VIEW_ORDER])
    def get_order(request, order_id: int):
        order = Order.objects.get(id=order_id)
        
        # Проверка что пользователь может видеть этот заказ
        if not request.user.has_perm('orders.view_order'):
            if order.customer_id != request.user.customer_id:
                raise HttpError(403, "Access denied")
        pass

# ❌ Неправильно
@router.get("/orders/{order_id}")
def get_order(request, order_id: int):
    # No permission check
    return Order.objects.get(id=order_id)
```

---

## 8. Common Vulnerabilities

### IDOR (Insecure Direct Object Reference)

```python
# ❌ Уязвимо
@router.get("/orders/{order_id}")
def get_order(request, order_id: int):
    return Order.objects.get(id=order_id)

# ✅ Защищено
@router.get("/orders/{order_id}")
@inject_permissions([VIEW_ORDER])
def get_order(request, order_id: int):
    order = Order.objects.get(id=order_id)
    
    # IDOR защита
    if not request.user.is_staff:
        if order.customer_id != request.user.customer_id:
            raise HttpError(403, "Not your order")
            
    return order
```

### Mass Assignment

```python
# ❌ Уязвимо - принимает любые поля
class OrderCreateSchema(BaseModel):
    class Config:
        model_config = ConfigDict(extra='allow')  # Опасно!
    
# ✅ Безопасно - только разрешенные поля
class OrderCreateSchema(BaseModel):
    contact_email: EmailStr
    contact_phone: str
    delivery_address: str
    items: List[OrderItemSchema]
    
    class Config:
        extra='forbid'  # Запретить_extra поля
```

### Race Conditions

```python
# ❌ Уязвимо
def deduct_stock(product_id, quantity):
    product = Product.objects.get(id=product_id)
    if product.stock >= quantity:
        product.stock -= quantity  # Race condition!
        product.save()

# ✅ Защищено
@transaction.atomic
def deduct_stock_safe(product_id, quantity):
    product = Product.objects.select_for_update().get(id=product_id)
    if product.stock >= quantity:
        product.stock -= quantity
        product.save()
    else:
        raise ValueError("Insufficient stock")
```

---

## 9. Logging Security Events

```python
# apps/core/security_logger.py
import logging

security_logger = logging.getLogger('security')

class SecurityEvents:
    @staticmethod
    def log_login_attempt(user: str, success: bool, ip: str):
        level = 'INFO' if success else 'WARNING'
        getattr(security_logger, level.lower())(
            f"Login {'success' if success else 'failed'} for user: {user}",
            extra={'ip': ip, 'user': user}
        )
    
    @staticmethod
    def log_permission_denied(user_id: int, resource: str, action: str):
        security_logger.warning(
            f"Permission denied: user={user_id} action={action} resource={resource}",
            extra={'user_id': user_id}
        )
    
    @staticmethod
    def log_suspicious_activity(ip: str, description: str):
        security_logger.critical(
            f"Suspicious activity from {ip}: {description}",
            extra={'ip': ip}
        )
```

### Alert на подозрительную активность

```python
# middleware.py
class SecurityAlertMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.failed_attempts = {}
        
    def __call__(self, request):
        # Track failed login attempts
        ip = self.get_client_ip(request)
        
        if self.is_login_endpoint(request):
            if self.detect_brute_force(ip):
                SecurityEvents.log_suspicious_activity(
                    ip, 
                    f"Possible brute force: {self.failed_attempts[ip]} attempts"
                )
                return HttpResponseForbidden("Rate limit exceeded")
                
        return self.get_response(request)
```

---

## 10. Commands Quick Reference

```bash
# Dependency scan
pip-audit -r requirements.txt
safety check -r requirements.txt --json

# Static analysis
bandit -r apps/ -f json -o bandit.json
semgrep --config=p/security-secrets apps/

# Django security check
python manage.py check --deploy

# Find secrets in code
grep -r "password\s*=\s*['\"]" apps/
grep -r "api_key\s*=" apps/
grep -r "secret\s*=" apps/

# Test SSL/TLS
openssl s_client -connect example.com:443 -showcerts

# Check headers
curl -I https://example.com/api/
```

---

## Checklist Security Audit

- [ ] pip-audit прошел без критических уязвимостей
- [ ] bandit не нашел высоких уязвимостей
- [ ] Django check --deploy прошел
- [ ] SECRET_KEY не default и минимум 50 символов
- [ ] CSRF настроен для форм
- [ ] CORS без wildcard с credentials
- [ ] Rate limiting на auth endpoints
- [ ] Input validation на всех endpoints
- [ ] No SQL injection vulnerabilities
- [ ] No XSS vulnerabilities
- [ ] IDOR protection implemented
- [ ] Sensitive data не в логах
- [ ] Error messages не раскрывают internals
- [ ] Security headers set (X-Frame-Options, CSP, etc.)
- [ ] JWT tokens have proper expiration