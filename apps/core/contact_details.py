from __future__ import annotations

from dataclasses import dataclass

from django.utils.translation import gettext_lazy as _

from apps.core.models import FooterSettings


DEFAULT_SHOP_PHONE = "+381 62 164 2224"
DEFAULT_SHOP_SECONDARY_PHONE = "+381 63 8305 320"
DEFAULT_SHOP_EMAIL = "kodpendule@gmail.com"


@dataclass(frozen=True)
class ContactDetails:
    phone: str
    email: str
    address: str
    working_hours: str
    secondary_phone: str = DEFAULT_SHOP_SECONDARY_PHONE

    @property
    def phones(self) -> tuple[str, ...]:
        return tuple(dict.fromkeys(phone for phone in (self.phone, self.secondary_phone) if phone))


def _footer_has_content(footer: FooterSettings | None) -> bool:
    if not footer:
        return False
    return bool(
        (footer.phone or "").strip()
        or (footer.email or "").strip()
        or (footer.address or "").strip()
        or (footer.working_hours or "").strip()
    )


def resolve_contact_details(footer: FooterSettings | None) -> ContactDetails:
    """Admin footer settings when set; otherwise fixed placeholder contact info."""
    if _footer_has_content(footer):
        return ContactDetails(
            phone=(footer.phone or "").strip(),
            email=(footer.email or "").strip(),
            address=(footer.address or "").strip(),
            working_hours=(footer.working_hours or "").strip(),
        )
    return ContactDetails(
        phone=DEFAULT_SHOP_PHONE,
        email=DEFAULT_SHOP_EMAIL,
        address=str(_("Karađorđeva 11\n22408 Vrdnik")),
        working_hours=str(
            _("Mon–Fri: 9:00–17:00\nSat: 9:00–13:00")
        ),
    )
