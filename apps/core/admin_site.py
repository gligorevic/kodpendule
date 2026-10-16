"""
Serbian admin URL paths and legacy English redirects.
"""

from __future__ import annotations

from functools import update_wrapper

from django.contrib import admin
from django.shortcuts import redirect
from django.urls import path, re_path

from apps.core.admin_slugs import DASHBOARD_ADMIN_SLUG, LEGACY_ADMIN_PATHS, admin_path_for_model


def redirect_legacy_admin(request, slug: str, rest: str = ""):
    """Redirect /admin/<legacy>/… to /admin/<serbian-slug>/…"""
    target = f"/admin/{slug}/"
    if rest:
        target = f"{target}{rest.lstrip('/')}"
    query = request.META.get("QUERY_STRING", "")
    if query:
        target = f"{target}?{query}"
    return redirect(target, permanent=False)


def legacy_admin_redirect_patterns():
    patterns = []
    for legacy, slug in LEGACY_ADMIN_PATHS.items():
        patterns.append(
            re_path(
                rf"^admin/{legacy}(?P<rest>.*)$",
                lambda request, rest="", slug=slug: redirect_legacy_admin(
                    request, slug, rest
                ),
                name=f"admin_legacy_{legacy.replace('/', '_')}",
            )
        )
    patterns.append(
        re_path(
            r"^admin/dashboard/(?P<rest>.*)$",
            lambda request, rest="": redirect_legacy_admin(
                request, DASHBOARD_ADMIN_SLUG, rest
            ),
            name="admin_legacy_dashboard",
        )
    )
    return patterns


def patch_admin_site_urls() -> None:
    """Use Serbian slugs in admin.site URL patterns (idempotent)."""
    site = admin.site
    if getattr(site, "_kp_serbian_urls_patched", False):
        return

    original_get_urls = site.get_urls

    def get_urls(self):
        from django.contrib.contenttypes import views as contenttype_views
        from django.urls import include
        from django.urls import re_path as django_re_path

        def wrap(view, cacheable=False):
            def wrapper(*args, **kwargs):
                return self.admin_view(view, cacheable)(*args, **kwargs)

            wrapper.admin_site = self
            from django.urls import reverse_lazy

            wrapper.login_url = reverse_lazy("admin:login", current_app=self.name)
            return update_wrapper(wrapper, view)

        from apps.core.admin_email import email_diagnostics

        urlpatterns = [
            path("mejlovi/", wrap(email_diagnostics), name="email_diagnostics"),
            path("", wrap(self.index), name="index"),
            path("login/", self.login, name="login"),
            path("logout/", wrap(self.logout), name="logout"),
            path(
                "password_change/",
                wrap(self.password_change, cacheable=True),
                name="password_change",
            ),
            path(
                "password_change/done/",
                wrap(self.password_change_done, cacheable=True),
                name="password_change_done",
            ),
            path("autocomplete/", wrap(self.autocomplete_view), name="autocomplete"),
            path("jsi18n/", wrap(self.i18n_javascript, cacheable=True), name="jsi18n"),
            path(
                "r/<int:content_type_id>/<path:object_id>/",
                wrap(contenttype_views.shortcut),
                name="view_on_site",
            ),
        ]

        valid_app_labels = []
        for model, model_admin in self._registry.items():
            urlpatterns.append(
                path(
                    admin_path_for_model(model),
                    include(model_admin.urls),
                ),
            )
            if model._meta.app_label not in valid_app_labels:
                valid_app_labels.append(model._meta.app_label)

        if valid_app_labels:
            regex = r"^(?P<app_label>" + "|".join(valid_app_labels) + ")/$"
            urlpatterns.append(
                django_re_path(regex, wrap(self.app_index), name="app_list"),
            )

        if self.final_catch_all_view:
            urlpatterns.append(
                django_re_path(r"(?P<url>.*)$", wrap(self.catch_all_view)),
            )

        return urlpatterns

    site.get_urls = get_urls.__get__(site, type(site))
    site._kp_serbian_urls_patched = True
