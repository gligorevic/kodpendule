"""
Merge Django contrib.admin Latin (sr) translations into project django.po.

Project LOCALE_PATHS override Django's bundled Cyrillic sr catalog when msgids match.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import polib
import django

ROOT = Path(__file__).resolve().parents[1]
EN_ADMIN = Path(django.__file__).resolve().parent / "contrib/admin/locale/en/LC_MESSAGES/django.po"
PROJECT_PO = ROOT / "locale/sr/LC_MESSAGES/django.po"
LATIN_JSON = ROOT / "scripts/admin_latin.json"


def _has_cyrillic(text: str) -> bool:
    return any("\u0400" <= ch <= "\u04FF" for ch in text)


def main() -> int:
    if not LATIN_JSON.exists():
        print("Run scripts/generate_admin_latin.py first.", file=sys.stderr)
        return 1

    data = json.loads(LATIN_JSON.read_text(encoding="utf-8"))
    single: dict[str, str] = data["single"]
    plural: dict[str, list[str]] = data["plural"]

    en = polib.pofile(str(EN_ADMIN))
    proj = polib.pofile(str(PROJECT_PO))
    by_msgid = {e.msgid: e for e in proj if not e.obsolete and e.msgid}

    merged = 0
    for entry in en:
        if not entry.msgid:
            continue

        if entry.msgid_plural:
            forms = plural.get(entry.msgid)
            if not forms:
                continue
            latin_plural = {i: forms[i] for i in range(len(forms))}
            if entry.msgid in by_msgid:
                po_entry = by_msgid[entry.msgid]
            else:
                po_entry = polib.POEntry(msgid=entry.msgid, msgid_plural=entry.msgid_plural)
                proj.append(po_entry)
                by_msgid[entry.msgid] = po_entry
            po_entry.msgid_plural = entry.msgid_plural
            po_entry.msgstr_plural = latin_plural
            if "fuzzy" in po_entry.flags:
                po_entry.flags.remove("fuzzy")
            merged += 1
            continue

        latin = single.get(entry.msgid)
        if not latin:
            continue

        if entry.msgid in by_msgid:
            po_entry = by_msgid[entry.msgid]
            if po_entry.msgstr and not _has_cyrillic(po_entry.msgstr):
                continue
        else:
            po_entry = polib.POEntry(msgid=entry.msgid)
            proj.append(po_entry)
            by_msgid[entry.msgid] = po_entry

        po_entry.msgstr = latin
        if "fuzzy" in po_entry.flags:
            po_entry.flags.remove("fuzzy")
        merged += 1

    proj.metadata["Language"] = "sr"
    proj.save(str(PROJECT_PO))
    proj.save_as_mofile(str(PROJECT_PO.with_suffix(".mo")))
    print(f"Merged/updated {merged} admin strings into {PROJECT_PO}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
