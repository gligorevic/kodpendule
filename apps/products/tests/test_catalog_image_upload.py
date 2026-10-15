import io
import tempfile
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from PIL import Image

from apps.categories.models import Category
from apps.products.models import Product


class CatalogImageUploadTests(TestCase):
    def setUp(self):
        cache.clear()
        self.media = tempfile.TemporaryDirectory()
        self.addCleanup(self.media.cleanup)
        settings = override_settings(MEDIA_ROOT=self.media.name)
        settings.enable()
        self.addCleanup(settings.disable)
        self.user = get_user_model().objects.create_superuser('photos', 'photos@example.invalid', 'test-only')
        self.client.force_login(self.user)
        category = Category.objects.create(name='Food', slug='photo-test-food')
        self.product = Product.objects.create(category=category, sku='001', barcode='860000000001', price=Decimal('24.99'), stock=8, name='Product', slug='photo-test-product')
        self.url = reverse('admin:products_product_import_image')

    def photo(self):
        buffer=io.BytesIO()
        Image.new('RGB', (10, 10), 'white').save(buffer, format='PNG')
        return SimpleUploadedFile('product.png', buffer.getvalue(), content_type='image/png')

    def upload(self, **overrides):
        payload={'sku': '001', 'barcode': '860000000001', 'image': self.photo()}
        payload.update(overrides)
        return self.client.post(self.url, payload)

    def test_updates_image_only_and_keeps_latest_stock(self):
        Product.objects.filter(pk=self.product.pk).update(stock=3)
        result=self.upload(stock='8', price='1.00', category='999')
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json()['status'], 'uploaded')
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 3)
        self.assertEqual(self.product.price, Decimal('24.99'))
        self.assertTrue(self.product.main_image)

    def test_replay_does_not_replace_existing_image(self):
        self.upload()
        self.product.refresh_from_db()
        old=self.product.main_image.name
        result=self.upload()
        self.product.refresh_from_db()
        self.assertEqual(result.json()['status'], 'already_has_image')
        self.assertEqual(self.product.main_image.name, old)

    def test_provenance_saved_and_caption_only_shown_when_provided(self):
        detail_url = self.product.get_absolute_url()
        self.assertNotContains(self.client.get(detail_url), 'class="shop-gallery__attribution"')
        source = 'https://world.openfoodfacts.org/product/860000000001'
        license_url = 'https://creativecommons.org/licenses/by-sa/3.0/'
        response = self.upload(
            main_image_source_url=source,
            main_image_attribution='Open Food Facts — <Contributor>',
            main_image_license_url=license_url,
        )
        self.assertEqual(response.status_code, 200)
        self.product.refresh_from_db()
        self.assertEqual(self.product.main_image_source_url, source)
        self.assertEqual(self.product.main_image_attribution, 'Open Food Facts — <Contributor>')
        self.assertEqual(self.product.main_image_license_url, license_url)
        self.assertEqual(self.product.stock, 8)
        detail = self.client.get(detail_url)
        self.assertContains(detail, 'class="shop-gallery__attribution"')
        self.assertContains(detail, f'href="{source}"')
        self.assertContains(detail, f'href="{license_url}"')
        self.assertContains(detail, 'Open Food Facts — &lt;Contributor&gt;')
        self.upload(main_image_attribution='Replacement')
        self.product.refresh_from_db()
        self.assertEqual(self.product.main_image_attribution, 'Open Food Facts — <Contributor>')

    def test_provenance_urls_only_accept_http_or_https(self):
        for field in ('main_image_source_url', 'main_image_license_url'):
            for url in ('javascript:alert(1)', 'ftp://example.com/photo'):
                with self.subTest(field=field, url=url):
                    self.assertEqual(self.upload(**{field: url}).status_code, 400)

    def test_wrong_identity_rejected(self):
        self.assertEqual(self.upload(barcode='other-product').status_code, 409)
        self.product.refresh_from_db()
        self.assertFalse(self.product.main_image)

    def test_invalid_image_rejected(self):
        result=self.upload(image=SimpleUploadedFile('bad.png', b'not an image'))
        self.assertEqual(result.status_code, 400)

    def test_unsupported_format_and_size_limits(self):
        for image_format, size, padding in [('GIF', (10, 10), 0), ('PNG', (4001, 4000), 0), ('PNG', (10, 10), 8 * 1024 * 1024)]:
            with self.subTest(format=image_format, size=size, padding=padding):
                buffer=io.BytesIO()
                Image.new('RGB', size, 'white').save(buffer, format=image_format)
                upload=SimpleUploadedFile('photo.'+image_format.lower(), buffer.getvalue()+b' ' * padding)
                self.assertEqual(self.upload(image=upload).status_code, 400)

    def test_permission_required(self):
        self.user.is_superuser=False
        self.user.save()
        self.assertEqual(self.upload().status_code, 403)

    def test_post_and_csrf_required(self):
        self.assertEqual(self.client.get(self.url).status_code, 405)
        client=Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        self.assertEqual(client.post(self.url, {'sku':'001','barcode':'860000000001','image':self.photo()}).status_code, 403)

    def test_anonymous_cannot_upload(self):
        self.client.logout()
        self.assertEqual(self.upload().status_code, 302)
