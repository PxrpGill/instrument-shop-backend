from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.shared.models import Image, TimeStampedModel


class Review(TimeStampedModel):
    """Отзыв покупателя. Глобальная сущность — не привязана к странице/товару.

    Страницы выбирают отзывы из общего пула через свои through-модели
    (например, HomePageReview в apps.pages).
    """

    title = models.CharField(
        max_length=255,
        verbose_name="Заголовок",
        help_text="Короткий заголовок отзыва.",
    )
    description = models.TextField(
        verbose_name="Текст отзыва",
    )
    grade = models.PositiveSmallIntegerField(
        verbose_name="Оценка",
        help_text="Целое число от 1 до 5.",
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    author_full_name = models.CharField(
        max_length=255,
        verbose_name="Имя автора",
    )
    author_icon = models.ForeignKey(
        Image,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        verbose_name="Аватар автора",
        help_text="Опциональная аватарка автора отзыва.",
    )
    is_published = models.BooleanField(
        default=True,
        verbose_name="Опубликован",
        help_text="Снимите галочку, чтобы скрыть отзыв со всех страниц.",
    )

    class Meta:
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.author_full_name}: {self.title}"
