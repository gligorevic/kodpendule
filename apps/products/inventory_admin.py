"""Small admin adapter; import business rules remain in the service."""
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.http import HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext as _

from apps.categories.models import Category
from apps.products.forms import InventoryCategoryForm, InventoryXMLUploadForm
from apps.products.models import XMLImportBatch
from apps.products.services.inventory_xml import (
    MAX_XML_BYTES, InventoryImportError, apply_import, build_preview, save_categories,
)


def inventory_import_view(model_admin, request, batch_id=None):
    if not model_admin.has_change_permission(request):
        raise PermissionDenied
    if request.method not in ("GET", "POST"):
        return HttpResponseNotAllowed(["GET", "POST"])
    context = {
        **model_admin.admin_site.each_context(request),
        "opts": model_admin.model._meta,
        "title": _("Import inventory XML"),
    }
    if batch_id is None:
        form = InventoryXMLUploadForm(request.POST or None, request.FILES or None)
        if request.method == "POST" and form.is_valid():
            upload = form.cleaned_data["xml_file"]
            try:
                batch = build_preview(upload.read(MAX_XML_BYTES + 1), user=request.user, filename=upload.name)
            except InventoryImportError as exc:
                form.add_error("xml_file", str(exc))
            else:
                return redirect("admin:products_product_xml_preview", batch_id=batch.pk)
        context.update({"upload_form": form, "recent_batches": XMLImportBatch.objects.filter(created_by=request.user)[:10]})
        return render(request, "admin/products/product/import_xml.html", context)

    batch = get_object_or_404(XMLImportBatch, pk=batch_id, created_by=request.user)
    rows = batch.payload["rows"]
    show_new = request.GET.get("show") == "new"
    visible_rows = [row for row in rows if row["action"] == "new"] if show_new else rows
    page = Paginator(visible_rows, 50).get_page(request.GET.get("page"))
    categories = [(str(category.pk), str(category)) for category in Category.objects.filter(is_active=True).prefetch_related("translations")]
    form = InventoryCategoryForm(
        request.POST if request.method == "POST" and request.POST.get("action") == "categories" else None,
        rows=page.object_list, categories=categories, selected=batch.categories,
    )
    error = None
    if request.method == "POST":
        action = request.POST.get("action")
        try:
            if action == "categories" and form.is_valid():
                selections = {row["sku"]: form.cleaned_data[f"category_{row['line']}"] for row in page.object_list if row["action"] == "new"}
                save_categories(batch.pk, user=request.user, categories=selections)
                messages.success(request, _("Category choices saved. Continue reviewing or apply the import."))
                return redirect(request.get_full_path())
            elif action == "apply":
                result = apply_import(batch.pk, user=request.user, acknowledge_rejected=request.POST.get("acknowledge_rejected") == "on")
                messages.success(request, _("Inventory imported: %(created)s new, %(updated)s updated, %(unchanged)s unchanged, %(rejected)s excluded.") % result)
                return redirect("admin:products_product_xml_preview", batch_id=batch.pk)
            elif action != "categories":
                raise InventoryImportError(_("Invalid import action."))
        except InventoryImportError as exc:
            error = str(exc)
    table_rows = []
    for row in page.object_list:
        table_rows.append({**row, "category_field": form[f"category_{row['line']}"] if row["action"] == "new" else None})
    remaining = sum(row["action"] == "new" and row["sku"] not in batch.categories for row in rows)
    context.update({
        "batch": batch, "page_obj": page, "table_rows": table_rows, "category_form": form,
        "error": error, "remaining": remaining, "show_new": show_new,
        "can_add": model_admin.has_add_permission(request),
        "has_new_on_page": any(row["action"] == "new" for row in page.object_list),
    })
    return render(request, "admin/products/product/import_xml.html", context)
