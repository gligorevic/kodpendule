from decimal import Decimal
import uuid

from django.conf import settings
from django.core.validators import MinValueValidator, URLValidator
from django.db import models
from django.utils.translation import gettext_lazy as _
from parler.models import TranslatableModel, TranslatedFields

from apps.core.fields import MoneyField


class Product(TranslatableModel):
    category = models.ForeignKey(
        "categories.Category",
        on_delete=models.PROTECT,
        related_name="products",
        verbose_name=_("Category"),
    )
    sku = models.CharField(_("SKU"), max_length=64, unique=True, db_index=True)
    barcode = models.CharField(_("Barcode"), max_length=64, blank=True, db_index=True)
    price = MoneyField(
        verbose_name=_("Price"),
        validators=[MinValueValidator(Decimal("0"))],
    )
    discount_price = MoneyField(
        verbose_name=_("Discount price"),
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0"))],
    )
    main_image = models.ImageField(_("Main image"), upload_to="products/", blank=True)
    main_image_source_url = models.URLField(
        _("Image source URL"), max_length=1000, blank=True,
        validators=[URLValidator(schemes=["http", "https"])],
    )
    main_image_attribution = models.CharField(_("Image attribution"), max_length=255, blank=True)
    main_image_license_url = models.URLField(
        _("Image license URL"), max_length=1000, blank=True,
        validators=[URLValidator(schemes=["http", "https"])],
    )
    stock = models.PositiveIntegerField(_("Stock"), default=0)
    is_archived = models.BooleanField(
        _("Archived"), default=False, db_index=True,
        help_text=_("Archived products are hidden from the shop and cannot be purchased. Clear this option to restore them."),
    )
    minimum_stock_alert = models.PositiveIntegerField(
        _("Minimum stock alert"),
        default=5,
    )
    is_recommended = models.BooleanField(
        _("Recommended product"),
        default=False,
        db_index=True,
    )
    recommended_order = models.PositiveIntegerField(
        _("Recommended sort order"),
        default=0,
    )
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated at"), auto_now=True)

    translations = TranslatedFields(
        name=models.CharField(_("Name"), max_length=255),
        slug=models.SlugField(_("Slug"), max_length=270, unique=True),
        short_description=models.CharField(_("Short description"), max_length=500, blank=True),
        description=models.TextField(_("Description"), blank=True),
        meta_title=models.CharField(_("Meta title"), max_length=70, blank=True),
        meta_description=models.CharField(_("Meta description"), max_length=160, blank=True),
    )

    class Meta:
        verbose_name = _("product")
        verbose_name_plural = _("products")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["category"]),
            models.Index(fields=["stock"]),
            models.Index(fields=["is_recommended", "recommended_order"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["barcode"], condition=~models.Q(barcode=""),
                name="products_unique_nonempty_barcode",
            ),
        ]

    def __str__(self) -> str:
        return self.safe_translation_getter("name", any_language=True) or self.sku

    @property
    def effective_price(self) -> Decimal:
        if self.discount_price is not None and self.discount_price < self.price:
            return self.discount_price
        return self.price

    @property
    def is_low_stock(self) -> bool:
        return self.stock <= self.minimum_stock_alert

    @property
    def has_discount(self) -> bool:
        return (
            self.discount_price is not None
            and self.discount_price < self.price
        )

    def get_absolute_url(self) -> str:
        from apps.core.storefront_urls import shop_reverse
        from apps.core.slugs import localized_slug

        slug = localized_slug(self)
        if not slug:
            return shop_reverse("products:list")
        return shop_reverse("products:detail", slug=slug)


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="gallery_images",
        verbose_name=_("Product"),
    )
    image = models.ImageField(_("Image"), upload_to="products/gallery/")
    alt_text_sr = models.CharField(
        _("Alt text (Serbian)"),
        max_length=255,
        blank=True,
    )
    alt_text_en = models.CharField(
        _("Alt text (English)"),
        max_length=255,
        blank=True,
    )
    sort_order = models.PositiveIntegerField(_("Sort order"), default=0)

    class Meta:
        verbose_name = _("product image")
        verbose_name_plural = _("product images")
        ordering = ["sort_order", "id"]
        indexes = [
            models.Index(fields=["product", "sort_order"]),
        ]

    def __str__(self) -> str:
        return f"Image for {self.product_id} (#{self.pk})"

    def alt_text_for_language(self, language_code: str) -> str:
        if language_code == "en":
            return self.alt_text_en or self.alt_text_sr
        return self.alt_text_sr or self.alt_text_en


class XMLImportBatch(models.Model):
    """Server-side preview and immutable result of an inventory import."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    filename = models.CharField(max_length=255)
    file_sha256 = models.CharField(max_length=64, db_index=True)
    payload = models.JSONField(default=dict)
    categories = models.JSONField(default=dict)
    result = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    applied_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
