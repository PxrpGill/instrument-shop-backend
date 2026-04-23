# Dev Docker Makefile
# Запуск из: docker/dev/

DOCKER_COMPOSE = docker compose -f docker-compose.yml

COLOR_RESET = \033[0m
COLOR_GREEN = \033[32m
COLOR_YELLOW = \033[33m
COLOR_BLUE = \033[34m

.PHONY: help build up down logs restart clean shell migrate test

help:
	@echo "$(COLOR_GREEN)Dev-команды (Docker):$(COLOR_RESET)"
	@echo "$(COLOR_BLUE)  build  $(COLOR_RESET) - Собрать образ"
	@echo "$(COLOR_BLUE)  up     $(COLOR_RESET) - Запустить контейнеры"
	@echo "$(COLOR_BLUE)  down   $(COLOR_RESET) - Остановить контейнеры"
	@echo "$(COLOR_BLUE)  logs   $(COLOR_RESET) - Показать логи"
	@echo "$(COLOR_BLUE)  clean  $(COLOR_RESET) - Удалить контейнеры и образы"
	@echo "$(COLOR_BLUE)  shell  $(COLOR_RESET) - Зайти в контейнер"
	@echo "$(COLOR_BLUE)  migrate$(COLOR_RESET) - Выполнить миграции отдельным one-off контейнером"

build:
	@echo "$(COLOR_YELLOW)Сборка dev-образа...$(COLOR_RESET)"
	$(DOCKER_COMPOSE) build --no-cache
	@echo "$(COLOR_GREEN)Готово!$(COLOR_RESET)"

up:
	@echo "$(COLOR_YELLOW)Запуск dev...$(COLOR_RESET)"
	$(DOCKER_COMPOSE) up -d --build
	@echo "$(COLOR_GREEN)Dev запущен!$(COLOR_RESET)"
	@echo "$(COLOR_BLUE)http://localhost:8000/api/$(COLOR_RESET)"

down:
	$(DOCKER_COMPOSE) down

logs:
	$(DOCKER_COMPOSE) logs -f

restart: down up

clean:
	$(DOCKER_COMPOSE) down -v --rmi all --remove-orphans

shell:
	$(DOCKER_COMPOSE) exec web bash

migrate:
	$(DOCKER_COMPOSE) up -d db
	$(DOCKER_COMPOSE) run --rm web python manage.py migrate
