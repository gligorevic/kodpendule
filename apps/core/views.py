import logging

from django.conf import settings
from django.contrib import messages
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.utils.translation import check_for_language, gettext_lazy as _
from django.views.decorators.http import require_POST
from django.views.generic import FormView, TemplateView

from apps.core.contact_details import resolve_contact_details
from apps.core.forms import ContactForm
from apps.core.mixins import ShopLanguageMixin
from apps.core.services.contact_email import send_contact_form_email
from apps.core.models import FooterSettings, SiteSettings
from apps.core.utils import activate_parler_language
from apps.categories.models import Category
from apps.categories.selectors import get_nav_categories
from apps.products.models import Product
from apps.products.selectors import (
    active_products_qs,
    promo_products_qs,
    recommended_products_qs,
)

logger = logging.getLogger(__name__)


class HomeView(ShopLanguageMixin, TemplateView):
    template_name = "pages/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        lang = self.shop_language
        site = SiteSettings.objects.language(lang).filter(pk=1).first()
        context.update(
            {
                "meta_title": (
                    site.safe_translation_getter("default_meta_title")
                    if site
                    else None
                )
                or (site.safe_translation_getter("site_name") if site else None),
                "meta_description": (
                    site.safe_translation_getter("default_meta_description") if site else ""
                ),
                "canonical_url": self.request.build_absolute_uri(),
            }
        )
        product_qs = active_products_qs(lang)

        new_arrivals = list(product_qs[:8])
        for product in new_arrivals:
            activate_parler_language(product, lang)

        promo_sale_products = list(promo_products_qs(lang)[:8])
        for product in promo_sale_products:
            activate_parler_language(product, lang)

        recommended_products = list(recommended_products_qs(lang))
        for product in recommended_products:
            activate_parler_language(product, lang)

        nav_categories = list(get_nav_categories(lang))
        for category in nav_categories:
            activate_parler_language(category, lang)

        # A useful first shelf: available, photographed products from different
        # departments, without changing merchandising flags or inventing offers.
        parents = dict(
            Category.objects.filter(is_active=True).values_list("pk", "parent_id")
        )
        roots = {}
        for category_id in parents:
            current = category_id
            visited = set()
            while current in parents and current not in visited:
                visited.add(current)
                if parents[current] is None:
                    roots[category_id] = current
                    break
                current = parents[current]

        available = list(
            product_qs.filter(stock__gt=0)
            .exclude(main_image="")
            .order_by("pk")
            .values_list("pk", "category_id")
        )
        first_by_root = {}
        for product_id, category_id in available:
            root_id = roots.get(category_id)
            if root_id is not None:
                first_by_root.setdefault(root_id, product_id)

        selected_ids = [
            first_by_root[category.pk]
            for category in nav_categories
            if category.pk in first_by_root
        ][:8]
        selected = set(selected_ids)
        for product_id, _category_id in available:
            if len(selected_ids) == 8:
                break
            if product_id not in selected:
                selected_ids.append(product_id)
                selected.add(product_id)

        # Hydrate only the selected eight, with the existing translations,
        # category and gallery prefetches; preserve the department-first order.
        selected_products = {
            product.pk: product for product in product_qs.filter(pk__in=selected_ids)
        }
        everyday_products = [selected_products[pk] for pk in selected_ids if pk in selected_products]
        for product in everyday_products:
            activate_parler_language(product, lang)

        # Editorial spotlight only — admin-picked recommended product with an image.
        featured_product = next(
            (p for p in recommended_products if p.main_image),
            None,
        )

        context.update(
            {
                "new_arrivals": new_arrivals,
                "everyday_products": everyday_products,
                "promo_sale_products": promo_sale_products,
                "featured_product": featured_product,
                "home_nav_categories": nav_categories,
                "recommended_products": recommended_products,
                "home_stats": {
                    "product_count": product_qs.count(),
                    "category_count": len(nav_categories),
                },
            }
        )
        return context


class ContactView(ShopLanguageMixin, FormView):
    template_name = "pages/contact.html"
    form_class = ContactForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        lang = self.shop_language
        footer = FooterSettings.objects.language(lang).filter(pk=1).first()
        context.update(
            {
                "meta_title": _("Contact"),
                "canonical_url": self.request.build_absolute_uri(),
                "contact_details": resolve_contact_details(footer),
            }
        )
        return context

    def form_valid(self, form):
        if form.is_spam_submission():
            logger.info("Contact form honeypot triggered; discarding submission")
            messages.success(
                self.request,
                _("Thank you! Your message has been sent. We will get back to you soon."),
            )
            return super().form_valid(form)

        sent = send_contact_form_email(
            name=form.cleaned_data["name"],
            email=form.cleaned_data["email"],
            phone=form.cleaned_data.get("phone", ""),
            message=form.cleaned_data["message"],
        )
        if sent:
            messages.success(
                self.request,
                _("Thank you! Your message has been sent. We will get back to you soon."),
            )
        else:
            logger.warning("Contact form email was not sent (SMTP or recipients missing)")
            messages.error(
                self.request,
                _(
                    "We could not send your message right now. "
                    "Please try again later or call us using the details below."
                ),
            )
        return super().form_valid(form)

    def get_success_url(self):
        from apps.core.storefront_urls import shop_reverse

        return shop_reverse("core:contact", language=self.shop_language)


class TermsView(ShopLanguageMixin, TemplateView):
    template_name = "pages/terms.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "meta_title": _("Terms of Service"),
                "canonical_url": self.request.build_absolute_uri(),
            }
        )
        return context


class PrivacyView(ShopLanguageMixin, TemplateView):
    template_name = "pages/privacy.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "meta_title": _("Privacy Policy"),
                "canonical_url": self.request.build_absolute_uri(),
            }
        )
        return context


def robots_txt(request: HttpRequest) -> HttpResponse:
    """Crawler rules for the storefront; sitemap URL follows the current host."""
    from apps.core.storefront_urls import storefront_paths_for_robots

    sitemap_url = request.build_absolute_uri("/sitemap.xml")
    lines = [
        "User-agent: *",
        "Disallow: /admin/",
    ]
    for path_prefix in storefront_paths_for_robots():
        if path_prefix not in ("/",):
            lines.append(f"Disallow: {path_prefix}")
    lines.extend(
        [
            "",
            f"Sitemap: {sitemap_url}",
        ]
    )
    if settings.DEBUG:
        lines.insert(2, "Disallow: /")
    body = "\n".join(lines) + "\n"
    return HttpResponse(body, content_type="text/plain; charset=utf-8")


@require_POST
def set_shop_language(request: HttpRequest) -> HttpResponse:
    """Set storefront language cookie and redirect to the localized equivalent URL."""
    from django.utils import translation
    from urllib.parse import urlsplit, urlunsplit

    from apps.core.storefront_urls import translate_storefront_url

    language = request.POST.get("language")
    next_url = request.POST.get("next") or "/"
    if not language or not check_for_language(language):
        return HttpResponseRedirect(next_url)

    parts = urlsplit(next_url)
    localized_path = translate_storefront_url(parts.path, language)
    redirect_to = urlunsplit(
        (parts.scheme, parts.netloc, localized_path, parts.query, parts.fragment)
    )

    translation.activate(language)
    response = HttpResponseRedirect(redirect_to)
    response.set_cookie(
        settings.LANGUAGE_COOKIE_NAME,
        language,
        max_age=settings.LANGUAGE_COOKIE_AGE,
        path=settings.LANGUAGE_COOKIE_PATH,
        domain=settings.LANGUAGE_COOKIE_DOMAIN,
        secure=settings.LANGUAGE_COOKIE_SECURE,
        httponly=settings.LANGUAGE_COOKIE_HTTPONLY,
        samesite=settings.LANGUAGE_COOKIE_SAMESITE,
    )
    return response
