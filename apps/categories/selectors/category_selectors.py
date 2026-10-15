from collections import defaultdict
from dataclasses import dataclass, field

from django.db.models import Prefetch, QuerySet

from apps.categories.models import Category
from apps.core.slugs import localized_slug, translation_languages_to_try
from apps.core.utils import get_shop_language


def _language(language: str | None) -> str:
    return language or get_shop_language()


def active_categories_qs(language: str | None = None) -> QuerySet[Category]:
    lang = _language(language)
    return (
        Category.objects.filter(is_active=True)
        .prefetch_related("translations")
        .order_by("sort_order", "pk")
    )


def get_nav_categories(language: str | None = None) -> QuerySet[Category]:
    """Top-level categories for header navigation."""
    return active_categories_qs(language).filter(parent__isnull=True)


def _category_at_slug(
    slug: str,
    *,
    parent: Category | None,
    language: str,
) -> Category | None:
    base_qs = active_categories_qs(language).select_related("parent").prefetch_related(
        "translations"
    )
    if parent is None:
        base_qs = base_qs.filter(parent__isnull=True)
    else:
        base_qs = base_qs.filter(parent=parent)
    for try_lang in translation_languages_to_try(language):
        category = (
            base_qs.filter(
                translations__language_code=try_lang,
                translations__slug=slug,
            )
            .distinct()
            .first()
        )
        if category is not None:
            category.set_current_language(language)
            return category
    category = base_qs.filter(translations__slug=slug).distinct().first()
    if category is not None:
        category.set_current_language(language)
    return category


def get_category_slug_path(category: Category, language: str | None = None) -> list[str]:
    """Slugs from root to category for hierarchical storefront URLs."""
    lang = _language(language)
    chain: list[Category] = []
    current: Category | None = category
    seen_ids: set[int] = set()
    while current is not None:
        if current.pk in seen_ids:
            break
        seen_ids.add(current.pk)
        if not current.is_active:
            return []
        chain.append(current)
        if current.parent_id is None:
            break
        # Keep the supplied, already-prefetched category. Reuse a parent loaded
        # by select_related, or fetch just the missing ancestor and translations.
        if "parent" in current._state.fields_cache:
            current = current.parent
        else:
            current = (
                Category.objects.filter(pk=current.parent_id, is_active=True)
                .prefetch_related("translations")
                .first()
            )
            if current is None:
                return []
    slugs = [localized_slug(node, lang) for node in reversed(chain)]
    return slugs if all(slugs) else []


def category_path_for_url(category: Category, language: str | None = None) -> str:
    return "/".join(get_category_slug_path(category, language))


def get_category_by_path(path: str, language: str | None = None) -> Category | None:
    """Resolve a category from a hierarchical path such as parent/child/grandchild."""
    normalized = (path or "").strip("/")
    if not normalized:
        return None
    lang = _language(language)
    parent: Category | None = None
    category: Category | None = None
    for segment in normalized.split("/"):
        category = _category_at_slug(segment, parent=parent, language=lang)
        if category is None:
            return None
        parent = category
    return category


def get_category_by_slug(slug: str, language: str | None = None) -> Category | None:
    lang = _language(language)
    base_qs = (
        Category.objects.filter(is_active=True)
        .select_related("parent")
        .prefetch_related("translations")
    )
    for try_lang in translation_languages_to_try(lang):
        category = (
            base_qs.filter(
                translations__language_code=try_lang,
                translations__slug=slug,
            )
            .distinct()
            .first()
        )
        if category is not None:
            category.set_current_language(lang)
            return category
    category = base_qs.filter(translations__slug=slug).distinct().first()
    if category is not None:
        category.set_current_language(lang)
    return category


def get_child_categories(parent: Category, language: str | None = None) -> QuerySet[Category]:
    lang = _language(language)
    return (
        active_categories_qs(lang)
        .filter(parent=parent)
        .prefetch_related(
            Prefetch(
                "children",
                queryset=active_categories_qs(lang),
            )
        )
    )


def get_all_categories(language: str | None = None) -> QuerySet[Category]:
    """All active categories (flat queryset)."""
    return active_categories_qs(language).select_related("parent")


@dataclass
class CategoryTreeNode:
    category: Category
    children: list["CategoryTreeNode"] = field(default_factory=list)


def _sort_tree_nodes(nodes: list[CategoryTreeNode]) -> None:
    nodes.sort(key=lambda node: (node.category.sort_order, node.category.pk))
    for node in nodes:
        _sort_tree_nodes(node.children)


def build_category_tree(
    categories: list[Category] | QuerySet[Category],
    *,
    root_parent_id: int | None = None,
) -> list[CategoryTreeNode]:
    """
    Build a nested tree from a flat category list.
    root_parent_id=None → top-level roots only (parent is null).
    root_parent_id=<pk> → direct children of that category as roots.
    """
    category_list = list(categories)
    by_parent: dict[int | None, list[Category]] = defaultdict(list)
    known_ids = {category.pk for category in category_list}

    for category in category_list:
        parent_id = category.parent_id
        if parent_id is not None and parent_id not in known_ids:
            by_parent[None].append(category)
        else:
            by_parent[parent_id].append(category)

    def build_level(parent_id: int | None) -> list[CategoryTreeNode]:
        nodes: list[CategoryTreeNode] = []
        for category in by_parent.get(parent_id, []):
            nodes.append(
                CategoryTreeNode(
                    category=category,
                    children=build_level(category.pk),
                )
            )
        _sort_tree_nodes(nodes)
        return nodes

    return build_level(root_parent_id)


def get_category_tree(language: str | None = None) -> list[CategoryTreeNode]:
    """Top-level category tree for the categories index page."""
    return build_category_tree(get_all_categories(language), root_parent_id=None)


def get_category_subtree(
    parent: Category,
    language: str | None = None,
) -> list[CategoryTreeNode]:
    """Nested subcategory tree under a category (direct children as roots)."""
    return build_category_tree(get_all_categories(language), root_parent_id=parent.pk)
