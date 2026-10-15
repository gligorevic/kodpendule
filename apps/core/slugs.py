"""Slug helpers for Parler models (language-aware URLs)."""

from typing import Iterable

from django.conf import settings
from django.utils.text import slugify

from apps.core.utils import get_shop_language


def slug_from_name(name: str, *, max_length: int = 270) -> str:
    """Build a URL slug from a display name."""
    return slugify(name, allow_unicode=True)[:max_length]


def unique_slug_for_translation(
    translation,
    *,
    fallback: str = "",
    reserved: Iterable[str] | None = None,
    base_override: str | None = None,
) -> str:
    """Return a slug unique across all rows of the translation model."""
    Translation = translation.__class__
    name = (getattr(translation, "name", None) or "").strip()
    if base_override:
        base = (
            slug_from_name(base_override)
            or slug_from_name(name)
            or slug_from_name(fallback)
            or "item"
        )
    else:
        base = slug_from_name(name) or slug_from_name(fallback) or "item"
    reserved_set = {slug for slug in (reserved or ()) if slug}
    candidate = base
    suffix = 2
    while (
        Translation.objects.filter(slug=candidate)
        .exclude(pk=translation.pk)
        .exists()
        or candidate in reserved_set
    ):
        candidate = f"{base}-{suffix}"
        suffix += 1
    return candidate


def localized_slug(obj, language: str | None = None) -> str:
    """
    Slug for the requested UI language, falling back to other translations.
    Reuse prefetched translation rows without Parler's active-language filter.
    """
    lang = language or get_shop_language()

    if hasattr(obj, "translations") and obj.pk:
        # .all() consumes Django's prefetch cache; filtering the translation
        # model directly caused a fresh query for every link on the page.
        translations = list(obj.translations.all())
        by_language = {trans.language_code: trans for trans in translations}
        for try_lang in translation_languages_to_try(lang):
            trans = by_language.get(try_lang)
            if trans and getattr(trans, "slug", None):
                return trans.slug
        for trans in sorted(translations, key=lambda row: row.pk):
            if getattr(trans, "slug", None):
                return trans.slug

    slug = obj.safe_translation_getter("slug", language_code=lang)
    if slug:
        return slug
    return obj.safe_translation_getter("slug", any_language=True) or ""


def translation_languages_to_try(language: str | None = None) -> list[str]:
    """Order of language codes to use when resolving a slug."""
    lang = language or get_shop_language()
    codes = [lang]
    default = settings.PARLER_DEFAULT_LANGUAGE_CODE
    if default not in codes:
        codes.append(default)
    for code, _ in settings.LANGUAGES:
        if code not in codes:
            codes.append(code)
    return codes
