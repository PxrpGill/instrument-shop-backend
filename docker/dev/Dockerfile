# Dev stage - наследуем runtime из shared
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBUG=True

WORKDIR /app

# Устанавливаем gettext для поддержки переводов
RUN apt-get update && apt-get install -y --no-install-recommends \
    gettext \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем зависимости
COPY docker/shared/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Создаем непривилегированного пользователя
RUN useradd --create-home --shell /bin/bash appuser

# Копируем код (будет перезаписан volume при разработке)
COPY . .

RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

# Для dev переопределяется в docker-compose.dev.yml
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]