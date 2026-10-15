"""Authenticated catalog photo intake without reposting mutable product stock.

Used by catalog-maintenance clients after independent product-photo verification.
The ordinary product editor remains available for deliberate image replacements.
"""
from django import forms
from django.core.exceptions import PermissionDenied
from django.core.validators import URLValidator
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from apps.products.models import Product

MAX_IMAGE_BYTES = 8 * 1024 * 1024


class CatalogImageForm(forms.Form):
    sku = forms.CharField(max_length=64)
    barcode = forms.CharField(max_length=64)
    image = forms.ImageField()
    main_image_source_url = forms.URLField(
        max_length=1000, required=False, assume_scheme='https',
        validators=[URLValidator(schemes=['http', 'https'])],
    )
    main_image_attribution = forms.CharField(max_length=255, required=False)
    main_image_license_url = forms.URLField(
        max_length=1000, required=False, assume_scheme='https',
        validators=[URLValidator(schemes=['http', 'https'])],
    )

    def clean_image(self):
        upload = self.cleaned_data['image']
        if upload.size > MAX_IMAGE_BYTES:
            raise forms.ValidationError('image_too_large')
        photo = upload.image
        if photo.format not in {'JPEG', 'PNG', 'WEBP'}:
            raise forms.ValidationError('unsupported_image_format')
        if photo.width * photo.height > 16_000_000:
            raise forms.ValidationError('image_dimensions_too_large')
        return upload


@require_POST
def catalog_image_upload(request, model_admin):
    if not model_admin.has_change_permission(request):
        raise PermissionDenied
    form = CatalogImageForm(request.POST, request.FILES)
    if not form.is_valid():
        return JsonResponse({'error': 'invalid_upload', 'fields': form.errors.get_json_data()}, status=400)
    with transaction.atomic():
        product = Product.objects.select_for_update().filter(sku=form.cleaned_data['sku']).first()
        if product is None:
            return JsonResponse({'error': 'product_not_found'}, status=404)
        if not model_admin.has_change_permission(request, product):
            raise PermissionDenied
        if product.barcode != form.cleaned_data['barcode']:
            return JsonResponse({'error': 'barcode_mismatch'}, status=409)
        if product.main_image:
            return JsonResponse({'status': 'already_has_image', 'product_id': product.pk})
        product.main_image = form.cleaned_data['image']
        provenance_fields = ['main_image_source_url', 'main_image_attribution', 'main_image_license_url']
        for field in provenance_fields:
            setattr(product, field, form.cleaned_data[field])
        product.save(update_fields=['main_image', 'updated_at', *provenance_fields])
        return JsonResponse({'status': 'uploaded', 'product_id': product.pk, 'url': product.main_image.url})
