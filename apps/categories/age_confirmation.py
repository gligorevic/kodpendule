from apps.categories.models import Category


def requires_age_confirmation(products):
    """Read current category rules, including ancestors, on every checkout."""
    category_ids = {product.category_id for product in products}
    if not category_ids:
        return False
    categories = {
        pk: (parent_id, required)
        for pk, parent_id, required in Category.objects.values_list(
            "pk", "parent_id", "requires_age_confirmation"
        )
    }
    for category_id in category_ids:
        visited = set()
        while category_id in categories and category_id not in visited:
            visited.add(category_id)
            parent_id, required = categories[category_id]
            if required:
                return True
            category_id = parent_id
    return False
