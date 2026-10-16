from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import path, reverse
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.contrib import messages

from apps.accounts.forms import CustomerContactImportForm
from apps.core.kp_admin import KPModelAdmin
from apps.core.locale_dates import latin_short_datetime
from apps.accounts.models import CustomerContact, CustomerProfile, User
from apps.accounts.services.customer_contact_csv import (
    EXPORT_FIELDNAMES,
    export_contacts_csv,
    import_contacts_csv,
)


class CustomerProfileInline(admin.StackedInline):
    model = CustomerProfile
    can_delete = False
    extra = 0
    verbose_name = _("Customer profile")
    verbose_name_plural = _("Customer profiles")


@admin.register(User)
class UserAdmin(KPModelAdmin, DjangoUserAdmin):
    sortable_by = ()
    list_display = (
        "username",
        "email",
        "full_name_display",
        "date_joined_display",
        "is_active",
        "customer_contact_link",
    )
    list_filter = ("is_active",)
    search_help_text = _("Search by name, username or email.")
    ordering = ("-date_joined",)
    search_fields = ("username", "email", "first_name", "last_name")
    inlines = [CustomerProfileInline]

    def get_queryset(self, request):
        """Shop registrations only — staff and superuser accounts are excluded."""
        return (
            super()
            .get_queryset(request)
            .filter(is_staff=False, is_superuser=False)
            .select_related("profile")
        )

    @admin.display(description=_("Name"))
    def full_name_display(self, obj: User) -> str:
        return obj.get_full_name() or "—"

    @admin.display(description=_("Registered"), ordering="date_joined")
    def date_joined_display(self, obj: User) -> str:
        if not obj.date_joined:
            return "—"
        return latin_short_datetime(obj.date_joined)

    @admin.display(description=_("Customer contact"))
    def customer_contact_link(self, obj: User) -> str:
        contact = CustomerContact.objects.filter(user_id=obj.pk).first()
        if contact is None:
            return "—"
        url = reverse("admin:accounts_customercontact_change", args=[contact.pk])
        return format_html('<a href="{}">{}</a>', url, contact.email)


@admin.register(CustomerContact)
class CustomerContactAdmin(KPModelAdmin):
    change_list_template = "admin/accounts/customercontact/change_list.html"
    list_display = (
        "email",
        "full_name_display",
        "phone",
        "delivery_display",
        "account_link",
        "order_count",
        "registered_at_display",
        "last_seen_at_display",
    )
    search_fields = (
        "email",
        "first_name",
        "last_name",
        "phone",
        "delivery_street",
        "delivery_city_name",
        "user__username",
    )
    readonly_fields = (
        "email",
        "first_name",
        "last_name",
        "phone",
        "delivery_street",
        "delivery_city_name",
        "user",
        "order_count",
        "registered_at",
        "first_seen_at",
        "last_seen_at",
    )
    list_filter = (("user", admin.EmptyFieldListFilter), "delivery_city_name")
    search_help_text = _("Search by customer name, email, phone or delivery address.")
    fieldsets = (
        (_("Contact details"), {"fields": ("first_name", "last_name", "email", "phone")}),
        (_("Delivery"), {"fields": ("delivery_street", "delivery_city_name")}),
        (_("Account activity"), {"fields": ("user", "order_count", "registered_at", "last_seen_at")}),
        (_("Timestamps"), {"classes": ("collapse",), "fields": ("first_seen_at",)}),
    )
    list_select_related = ("user",)
    ordering = ("-last_seen_at",)

    def has_add_permission(self, request):
        return False


    def get_urls(self):
        urls = [
            path(
                "import-csv/",
                self.admin_site.admin_view(self.import_csv_view),
                name="accounts_customercontact_import_csv",
            ),
            path(
                "export-csv/",
                self.admin_site.admin_view(self.export_csv_view),
                name="accounts_customercontact_export_csv",
            ),
        ]
        return urls + super().get_urls()

    @admin.action(description=_("Export selected to CSV"))
    def export_selected_csv(self, request, queryset):
        if not queryset.exists():
            self.message_user(request, _("No customers selected."), level=messages.WARNING)
            return None

        stamp = timezone.localdate().strftime("%Y%m%d")
        response = HttpResponse(
            export_contacts_csv(queryset),
            content_type="text/csv; charset=utf-8",
        )
        response["Content-Disposition"] = (
            f'attachment; filename="customer-contacts-{stamp}.csv"'
        )
        return response

    actions = ["export_selected_csv", "delete_selected"]

    def export_csv_view(self, request: HttpRequest) -> HttpResponse:
        if not self.has_view_permission(request):
            return redirect("admin:index")

        changelist = self.get_changelist_instance(request)
        queryset = changelist.get_queryset(request)
        stamp = timezone.localdate().strftime("%Y%m%d")
        response = HttpResponse(
            export_contacts_csv(queryset),
            content_type="text/csv; charset=utf-8",
        )
        response["Content-Disposition"] = (
            f'attachment; filename="customer-contacts-{stamp}.csv"'
        )
        return response

    def import_csv_view(self, request: HttpRequest) -> HttpResponse:
        if not self.has_change_permission(request):
            return redirect("admin:index")

        form = CustomerContactImportForm(request.POST or None, request.FILES or None)
        result = None

        if request.method == "POST" and form.is_valid():
            upload = form.cleaned_data["csv_file"]
            try:
                result = import_contacts_csv(upload)
            except ValueError as exc:
                form.add_error("csv_file", str(exc))
            else:
                messages.success(
                    request,
                    _("Import finished: %(created)s created, %(updated)s updated, %(skipped)s skipped.")
                    % {
                        "created": result.created,
                        "updated": result.updated,
                        "skipped": result.skipped,
                    },
                )
                return redirect(reverse("admin:accounts_customercontact_changelist"))

        context = {
            **self.admin_site.each_context(request),
            "opts": self.model._meta,
            "title": _("Import customer contacts"),
            "form": form,
            "result": result,
            "export_columns": EXPORT_FIELDNAMES,
        }
        return render(request, "admin/accounts/customercontact/import_csv.html", context)

    @admin.display(description=_("Registered at"), ordering="registered_at")
    def registered_at_display(self, obj: CustomerContact) -> str:
        if not obj.registered_at:
            return "—"
        return latin_short_datetime(obj.registered_at)

    @admin.display(description=_("Last activity"), ordering="last_seen_at")
    def last_seen_at_display(self, obj: CustomerContact) -> str:
        return latin_short_datetime(obj.last_seen_at)

    @admin.display(description=_("Name"))
    def full_name_display(self, obj: CustomerContact) -> str:
        return obj.full_name or "—"

    @admin.display(description=_("Delivery"))
    def delivery_display(self, obj: CustomerContact) -> str:
        street = (obj.delivery_street or "").strip()
        city = (obj.delivery_city_name or "").strip()
        if street and city:
            return f"{street}, {city}"
        return street or city or "—"

    @admin.display(description=_("Account"))
    def account_link(self, obj: CustomerContact) -> str:
        if not obj.user_id:
            return "—"
        user = obj.user
        url = reverse("admin:accounts_user_change", args=[user.pk])
        return format_html('<a href="{}">{}</a>', url, user.username)
