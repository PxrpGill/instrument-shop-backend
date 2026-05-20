"""Жёстко типизированные модели публичных страниц.

Каждая страница — singleton (pk=1). Структуру определяет соответствующий
контракт в `contracts/pages/*.json`. Универсального page builder здесь нет.
"""

from __future__ import annotations

from django.db import models

from apps.products.models import Product
from apps.reviews.models import Review
from apps.shared.models import Image, TimeStampedModel
from apps.shared.services.sanitize import sanitize_html


class SingletonModel(TimeStampedModel):
    """База для singleton-страниц.

    Гарантирует ровно одну запись с pk=1. Создаётся лениво
    через get_solo(), запись не удаляется через delete().
    """

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):  # pragma: no cover - защита от случайного удаления
        pass

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


# =============================================================================
# Home page
# =============================================================================


class HomePage(SingletonModel):
    """Главная страница: hero + about + reviews + showcase + news_cta.

    Каждая секция опциональна. Если у hero нет title — секция не отдаётся
    клиенту целиком (см. apps/pages/services.py::serialize_home_page).
    """

    # ---- hero ----
    hero_title = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="Hero · заголовок",
    )
    hero_description = models.TextField(
        blank=True,
        default="",
        verbose_name="Hero · описание (HTML)",
        help_text="Допустимы теги br, p, strong, em и т. п. (см. sanitize_html).",
    )
    hero_button_title = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="Hero · текст кнопки",
    )
    hero_button_href = models.CharField(
        max_length=500,
        blank=True,
        default="",
        verbose_name="Hero · ссылка кнопки",
    )
    hero_poster = models.ForeignKey(
        Image,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        verbose_name="Hero · постер",
    )

    # ---- about_company ----
    about_title = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="О компании · заголовок",
    )
    about_content = models.TextField(
        blank=True,
        default="",
        verbose_name="О компании · содержимое (HTML)",
    )
    about_poster = models.ForeignKey(
        Image,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        verbose_name="О компании · постер",
    )

    # ---- reviews ----
    reviews_title = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="Отзывы · заголовок",
    )
    reviews = models.ManyToManyField(
        Review,
        through="HomePageReview",
        related_name="home_pages",
        blank=True,
        verbose_name="Отзывы",
    )

    # ---- showcase ----
    showcase_title = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="Витрина · заголовок",
    )
    showcase_button_title = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="Витрина · текст кнопки",
    )
    showcase_button_href = models.CharField(
        max_length=500,
        blank=True,
        default="",
        verbose_name="Витрина · ссылка кнопки",
    )

    # ---- news_cta ----
    news_cta_title = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="Новости · заголовок",
    )
    news_cta_description = models.TextField(
        blank=True,
        default="",
        verbose_name="Новости · описание",
    )
    news_cta_button_title = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="Новости · текст кнопки",
    )
    news_cta_button_href = models.CharField(
        max_length=500,
        blank=True,
        default="",
        verbose_name="Новости · ссылка кнопки",
    )
    news_cta_poster = models.ForeignKey(
        Image,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        verbose_name="Новости · постер",
    )

    class Meta:
        verbose_name = "Главная страница"
        verbose_name_plural = "Главная страница"

    def __str__(self) -> str:
        return "Главная страница"

    def save(self, *args, **kwargs):
        self.hero_description = sanitize_html(self.hero_description)
        self.about_content = sanitize_html(self.about_content)
        self.news_cta_description = sanitize_html(self.news_cta_description)
        super().save(*args, **kwargs)


class HomePageReview(models.Model):
    """Through-модель: какие отзывы показываем на главной и в каком порядке."""

    home_page = models.ForeignKey(
        HomePage,
        on_delete=models.CASCADE,
        related_name="home_reviews",
    )
    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name="+",
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name="Порядок",
    )

    class Meta:
        verbose_name = "Отзыв на главной"
        verbose_name_plural = "Отзывы на главной"
        ordering = ["order"]
        unique_together = [("home_page", "review")]

    def __str__(self) -> str:
        return f"{self.review} (порядок: {self.order})"


class HomePageShowcase(models.Model):
    """Группа товаров на главной (вкладка в витрине)."""

    home_page = models.ForeignKey(
        HomePage,
        on_delete=models.CASCADE,
        related_name="showcases",
    )
    title = models.CharField(
        max_length=255,
        verbose_name="Название группы",
        help_text="Подпись таба на витрине, например «Электроинструмент».",
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name="Порядок",
    )
    products = models.ManyToManyField(
        Product,
        through="HomePageShowcaseProduct",
        related_name="home_showcases",
        blank=True,
        verbose_name="Товары",
    )

    class Meta:
        verbose_name = "Группа витрины"
        verbose_name_plural = "Группы витрины"
        ordering = ["order"]

    def __str__(self) -> str:
        return self.title


class HomePageShowcaseProduct(models.Model):
    """Through-модель: товар внутри группы витрины + порядок."""

    showcase = models.ForeignKey(
        HomePageShowcase,
        on_delete=models.CASCADE,
        related_name="showcase_products",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="+",
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name="Порядок",
    )

    class Meta:
        verbose_name = "Товар в группе витрины"
        verbose_name_plural = "Товары в группах витрины"
        ordering = ["order"]
        unique_together = [("showcase", "product")]

    def __str__(self) -> str:
        return f"{self.showcase.title}: {self.product.name}"


# =============================================================================
# About-us / Buyers (структурно идентичны)
# =============================================================================


class BannerContentPageMixin(SingletonModel):
    """Общая структура страниц с баннером сверху и HTML-контентом."""

    banner_title = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="Баннер · заголовок",
    )
    banner_description = models.TextField(
        blank=True,
        default="",
        verbose_name="Баннер · описание",
    )
    banner_poster = models.ForeignKey(
        Image,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        verbose_name="Баннер · постер",
    )
    content = models.TextField(
        blank=True,
        default="",
        verbose_name="Контент (HTML)",
        help_text="HTML рендерится на фронте через dangerouslySetInnerHTML.",
    )

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.content = sanitize_html(self.content)
        super().save(*args, **kwargs)


class AboutUsPage(BannerContentPageMixin):
    class Meta:
        verbose_name = "Страница «О компании»"
        verbose_name_plural = "Страница «О компании»"

    def __str__(self) -> str:
        return "О компании"


class BuyersPage(BannerContentPageMixin):
    class Meta:
        verbose_name = "Страница «Покупателям»"
        verbose_name_plural = "Страница «Покупателям»"

    def __str__(self) -> str:
        return "Покупателям"


# =============================================================================
# Feedback page
# =============================================================================


class FeedbackPage(SingletonModel):
    """Страница /feedback: только заголовок секции + news_cta."""

    section_title = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="Секция · заголовок",
    )
    section_description = models.TextField(
        blank=True,
        default="",
        verbose_name="Секция · описание (HTML)",
    )

    news_cta_title = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="Новости · заголовок",
    )
    news_cta_description = models.TextField(
        blank=True,
        default="",
        verbose_name="Новости · описание",
    )
    news_cta_button_title = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="Новости · текст кнопки",
    )
    news_cta_button_href = models.CharField(
        max_length=500,
        blank=True,
        default="",
        verbose_name="Новости · ссылка кнопки",
    )
    news_cta_poster = models.ForeignKey(
        Image,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        verbose_name="Новости · постер",
    )

    class Meta:
        verbose_name = "Страница «Обратная связь»"
        verbose_name_plural = "Страница «Обратная связь»"

    def __str__(self) -> str:
        return "Обратная связь"

    def save(self, *args, **kwargs):
        self.section_description = sanitize_html(self.section_description)
        self.news_cta_description = sanitize_html(self.news_cta_description)
        super().save(*args, **kwargs)


# =============================================================================
# Legal documents
# =============================================================================


class LegalDocumentSlugChoices(models.TextChoices):
    PRIVACY_POLICY = "privacy-policy", "Политика конфиденциальности"
    USER_AGREEMENT = "user-agreement", "Пользовательское соглашение"
    PERSONAL_DATA_CONSENT = (
        "personal-data-consent",
        "Согласие на обработку персональных данных",
    )


class LegalDocument(TimeStampedModel):
    """Юридический документ. Три фиксированных значения slug."""

    slug = models.CharField(
        max_length=64,
        primary_key=True,
        choices=LegalDocumentSlugChoices.choices,
        verbose_name="Slug",
    )
    title = models.CharField(
        max_length=255,
        verbose_name="Заголовок",
    )
    last_updated = models.CharField(
        max_length=10,
        verbose_name="Дата обновления",
        help_text="Формат ДД.ММ.ГГГГ (как отображается на фронте).",
    )

    class Meta:
        verbose_name = "Юридический документ"
        verbose_name_plural = "Юридические документы"
        ordering = ["slug"]

    def __str__(self) -> str:
        return self.title or self.get_slug_display()


class LegalSection(models.Model):
    """Раздел юридического документа. Plain text, абзацы — `\\n\\n`."""

    document = models.ForeignKey(
        LegalDocument,
        on_delete=models.CASCADE,
        related_name="sections",
        verbose_name="Документ",
    )
    anchor_id = models.SlugField(
        max_length=64,
        verbose_name="Якорь (id)",
        help_text="Уникален в пределах документа. Используется для TOC и якорей.",
    )
    title = models.CharField(
        max_length=255,
        verbose_name="Заголовок раздела",
    )
    content = models.TextField(
        verbose_name="Текст",
        help_text="Plain text. Абзацы разделяются двумя переводами строки.",
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name="Порядок",
    )

    class Meta:
        verbose_name = "Раздел документа"
        verbose_name_plural = "Разделы документа"
        ordering = ["order"]
        unique_together = [("document", "anchor_id")]

    def __str__(self) -> str:
        return f"{self.document_id} · {self.title}"
