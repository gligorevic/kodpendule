from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse
from apps.categories.models import Category
from apps.products.models import Product


class AdminWorkspaceTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser('workspace', 'workspace@example.com', 'testpass')
        self.client.force_login(self.user)
        self.root = Category.objects.create(name='Food', slug='food')
        self.child = Category.objects.create(name='Biscuits', slug='biscuits', parent=self.root)
        self.grandchild = Category.objects.create(name='Chocolate', slug='chocolate', parent=self.child)
        self.other = Category.objects.create(name='Other', slug='other')
        self.missing = self.product('Tea missing', self.grandchild, stock=0)
        self.photo = self.product('Tea photo', self.child, stock=2, main_image='products/test.jpg')
        self.outside = self.product('Tea other', self.other, stock=20)
        self.url = reverse('admin:products_product_changelist')

    def product(self, name, category, **kwargs):
        return Product.objects.create(name=name, slug=name.replace(' ', '-').lower(), sku=name, price=100, category=category, minimum_stock_alert=3, **kwargs)

    def ids(self, **params):
        response = self.client.get(self.url, params)
        self.assertEqual(response.status_code, 200)
        return set(response.context['cl'].result_list.values_list('pk', flat=True))

    def test_category_includes_descendants_and_filters_combine_with_search(self):
        self.assertEqual(self.ids(category=self.root.pk), {self.missing.pk, self.photo.pk})
        self.assertEqual(self.ids(category=self.root.pk, photo='missing', stock_state='low', q='Tea'), {self.missing.pk})
        self.assertEqual(self.ids(category='invalid'), set())

    def test_stock_and_photo_filters(self):
        self.assertEqual(self.ids(stock_state='out'), {self.missing.pk})
        self.assertEqual(self.ids(stock_state='low'), {self.missing.pk, self.photo.pk})
        self.assertEqual(self.ids(stock_state='available'), {self.photo.pk, self.outside.pk})
        self.assertEqual(self.ids(photo='present'), {self.photo.pk})

    def test_category_dropdown_and_quick_filters_preserve_search(self):
        response = self.client.get(self.url, {'q': 'Tea', 'category': self.root.pk})
        self.assertContains(response, 'id="kp-filter-category"')
        self.assertContains(response, 'stock_state=out')
        self.assertContains(response, 'q=Tea&amp;category=')
        self.assertContains(response, 'kp-product-thumb')

    def test_product_form_contains_pricing_stock_and_translated_fields(self):
        response = self.client.get(reverse('admin:products_product_change', args=[self.photo.pk]))
        self.assertEqual(response.status_code, 200)
        for field in ('price', 'discount_price', 'stock', 'main_image', 'category', 'name_sr', 'name_en'):
            self.assertContains(response, 'name="' + field + '"')
        self.assertContains(response, 'kp-form-sections')

    def test_home_respects_staff_permissions(self):
        viewer = get_user_model().objects.create_user('viewer', is_staff=True)
        viewer.user_permissions.add(Permission.objects.get(content_type__app_label='products', codename='view_product'))
        self.client.force_login(viewer)
        response = self.client.get(reverse('admin:index'))
        self.assertTrue(response.context['home_can_products'])
        self.assertFalse(response.context['home_can_orders'])
        self.assertNotIn('home_recent_orders', response.context)
        self.assertNotContains(response, reverse('admin:products_product_import_xml'))
        self.assertEqual(self.client.get(reverse('admin:products_product_import_xml')).status_code, 403)
