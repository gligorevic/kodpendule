import uuid

from django.test import TestCase

from apps.categories.models import Category
from apps.core.slugs import unique_slug_for_translation


class UniqueSlugForTranslationTests(TestCase):
    def test_reserved_slugs_avoid_batch_collision(self) -> None:
        category = Category.objects.create(is_active=True)
        sr = category.translations.model(master=category, language_code="sr", name="Piće")
        en = category.translations.model(master=category, language_code="en", name="Piće")

        sr.slug = unique_slug_for_translation(sr)
        en.slug = unique_slug_for_translation(en, reserved={sr.slug})

        self.assertNotEqual(sr.slug, en.slug)
        self.assertTrue(en.slug.startswith(f"{sr.slug}-"))

    def test_base_override_avoids_existing_slug(self) -> None:
        suffix = uuid.uuid4().hex[:8]
        existing = Category.objects.create(is_active=True)
        existing.set_current_language("sr")
        existing.name = "Existing"
        existing.slug = f"pice-{suffix}"
        existing.save()

        category = Category.objects.create(is_active=True)
        trans = category.translations.model(
            master=category,
            language_code="sr",
            name="Piće",
        )
        trans.slug = unique_slug_for_translation(
            trans,
            base_override=f"pice-{suffix}",
        )
        self.assertNotEqual(trans.slug, f"pice-{suffix}")


class PrefetchedSlugTests(TestCase):
    def setUp(self):
        from django.core.cache import cache

        cache.clear()
        self.addCleanup(cache.clear)
        self.root = Category.objects.create(is_active=True)
        self.root.set_current_language("sr")
        self.root.name = "Hrana"
        self.root.slug = "hrana-prefetch"
        self.root.save()
        self.child = Category.objects.create(parent=self.root, is_active=True)
        self.child.set_current_language("sr")
        self.child.name = "Voće"
        self.child.slug = "voce-prefetch"
        self.child.save()

    def test_prefetched_slug_and_language_fallback_do_not_query(self):
        from apps.core.slugs import localized_slug

        category = Category.objects.prefetch_related("translations").get(pk=self.root.pk)
        with self.assertNumQueries(0):
            self.assertEqual(localized_slug(category, "sr"), "hrana-prefetch")
            self.assertEqual(localized_slug(category, "en"), "hrana-prefetch")

    def test_prefetched_category_path_reuses_parent_and_translations(self):
        from apps.categories.selectors import category_path_for_url

        child = Category.objects.select_related("parent").prefetch_related(
            "translations", "parent__translations"
        ).get(pk=self.child.pk)
        with self.assertNumQueries(0):
            self.assertEqual(category_path_for_url(child, "en"), "hrana-prefetch/voce-prefetch")

    def test_uncached_parent_path_and_inactive_ancestor(self):
        from apps.categories.selectors import category_path_for_url

        child = Category.objects.prefetch_related("translations").get(pk=self.child.pk)
        with self.assertNumQueries(2):
            self.assertEqual(category_path_for_url(child, "sr"), "hrana-prefetch/voce-prefetch")
        Category.objects.filter(pk=self.root.pk).update(is_active=False)
        child = Category.objects.prefetch_related("translations").get(pk=self.child.pk)
        self.assertEqual(category_path_for_url(child, "sr"), "")
