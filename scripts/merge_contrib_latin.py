"""Merge Latin translations for django.contrib.auth (and other admin labels) into django.po."""
from __future__ import annotations

from pathlib import Path

import polib

ROOT = Path(__file__).resolve().parents[1]
PROJECT_PO = ROOT / "locale/sr/LC_MESSAGES/django.po"

AUTH_LATIN: dict[str, str] = {
    "group": "grupa",
    "groups": "grupe",
    "Group": "Grupa",
    "Groups": "Grupe",
    "Add group": "Dodaj grupu",
    "permission": "dozvola",
    "permissions": "dozvole",
    "Authentication and Authorization": "Autentifikacija i autorizacija",
    "Authentication and authorization": "Autentifikacija i autorizacija",
    "Personal info": "Lični podaci",
    "Important dates": "Važni datumi",
    "username": "korisničko ime",
    "password": "lozinka",
    "last login": "poslednja prijava",
    "first name": "ime",
    "last name": "prezime",
    "staff status": "status osoblja",
    "superuser status": "status superkorisnika",
    "user permissions": "korisničke dozvole",
    "Logged out": "Odjavljen",
    "Password confirmation": "Potvrda lozinke",
    "Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.": (
        "Obavezno. Najviše 150 znakova. Dozvoljena su samo slova, cifre i @/./+/-/_."
    ),
    "Enter the same password as before, for verification.": (
        "Unesite istu lozinku ponovo radi potvrde."
    ),
    "Your password can’t be too similar to your other personal information.": (
        "Vaša lozinka ne sme biti previše slična vašim drugim ličnim podacima."
    ),
    "Your password can’t be a commonly used password.": (
        "Vaša lozinka ne sme biti često korišćena lozinka."
    ),
    "Your password can’t be entirely numeric.": (
        "Vaša lozinka ne sme sadržati samo cifre."
    ),
    "The two password fields didn’t match.": "Unete lozinke se ne podudaraju.",
    "This password is too common.": "Ova lozinka se previše često koristi.",
    "This password is entirely numeric.": "Ova lozinka sadrži samo cifre.",
    "The password is too similar to the %(verbose_name)s.": (
        "Lozinka je previše slična podatku: %(verbose_name)s."
    ),
    "Enter a valid username. This value may contain only letters, numbers, and @/./+/-/_ characters.": (
        "Unesite ispravno korisničko ime. Dozvoljena su samo slova, cifre i znakovi @/./+/-/_."
    ),
    "A user with that username already exists.": (
        "Korisnik sa tim korisničkim imenom već postoji."
    ),
    "Enter a valid email address.": "Unesite ispravnu email adresu.",
    "Please enter a correct %(username)s and password. Note that both fields may be case-sensitive.": (
        "Unesite ispravno %(username)s i lozinku. Oba polja mogu razlikovati velika i mala slova."
    ),
    "This account is inactive.": "Ovaj nalog nije aktivan.",
}


# Django uses ngettext for these messages. Serbian needs all three plural forms;
# a plain msgstr would silently leave the built-in Cyrillic translation in use.
AUTH_LATIN_PLURALS = {
    "Your password must contain at least %(min_length)d character.": (
        "Your password must contain at least %(min_length)d characters.",
        (
            "Vaša lozinka mora da sadrži najmanje %(min_length)d znak.",
            "Vaša lozinka mora da sadrži najmanje %(min_length)d znaka.",
            "Vaša lozinka mora da sadrži najmanje %(min_length)d znakova.",
        ),
    ),
    "This password is too short. It must contain at least %(min_length)d character.": (
        "This password is too short. It must contain at least %(min_length)d characters.",
        (
            "Ova lozinka je prekratka. Mora da sadrži najmanje %(min_length)d znak.",
            "Ova lozinka je prekratka. Mora da sadrži najmanje %(min_length)d znaka.",
            "Ova lozinka je prekratka. Mora da sadrži najmanje %(min_length)d znakova.",
        ),
    ),
}


def main() -> None:
    proj = polib.pofile(str(PROJECT_PO))
    by_msgid = {e.msgid: e for e in proj if not e.obsolete and e.msgid}
    merged = 0
    for msgid, latin in AUTH_LATIN.items():
        if msgid in by_msgid:
            entry = by_msgid[msgid]
        else:
            entry = polib.POEntry(msgid=msgid, msgstr=latin)
            proj.append(entry)
            by_msgid[msgid] = entry
        entry.msgstr = latin
        if "fuzzy" in entry.flags:
            entry.flags.remove("fuzzy")
        merged += 1
    for msgid, (plural, forms) in AUTH_LATIN_PLURALS.items():
        entry = by_msgid.get(msgid)
        if entry is None:
            entry = polib.POEntry(msgid=msgid)
            proj.append(entry)
        entry.msgstr = ""
        entry.msgid_plural = plural
        entry.msgstr_plural = dict(enumerate(forms))
        if "fuzzy" in entry.flags:
            entry.flags.remove("fuzzy")
        merged += 1
    proj.save(str(PROJECT_PO))
    proj.save_as_mofile(str(PROJECT_PO.with_suffix(".mo")))
    print(f"Merged {merged} contrib auth strings")


if __name__ == "__main__":
    main()
