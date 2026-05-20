from django.apps import AppConfig, apps


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.users'
    verbose_name = 'Пользователи'

    def ready(self) -> None:
        # SimpleJWT.token_blacklist держит модель OutstandingToken абстрактной,
        # если путь приложения не присутствует литерально в INSTALLED_APPS,
        # поэтому подменить AppConfig через INSTALLED_APPS нельзя —
        # переопределяем verbose_name здесь.
        try:
            apps.get_app_config('token_blacklist').verbose_name = 'Чёрный список токенов'
        except LookupError:
            pass
