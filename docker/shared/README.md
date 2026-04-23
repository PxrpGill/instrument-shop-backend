# Shared Docker Resources

Общие файлы для всех окружений.

## Содержимое

- `.dockerignore` — исключения при сборке Docker-образов
- `requirements.txt` — Python-зависимости

## Использование

Dockerfile-ы в `dev/` и `prod/` ссылаются на файлы из этой директории:

```dockerfile
COPY ../shared/requirements.txt .
```
