from django.apps import AppConfig


class SharedConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.shared"
    verbose_name = "Общие компоненты"

    def ready(self) -> None:
        from . import signals  # noqa: F401
