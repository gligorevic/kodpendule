"""Create/update locale/sr/LC_MESSAGES/djangojs.po with Serbian Latin admin JS strings."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import polib
import django

ROOT = Path(__file__).resolve().parents[1]
EN_JS = Path(django.__file__).resolve().parent / "contrib/admin/locale/en/LC_MESSAGES/djangojs.po"
PROJECT_JS = ROOT / "locale/sr/LC_MESSAGES/djangojs.po"
LATIN_JSON = ROOT / "scripts/djangojs_latin.json"


def main() -> int:
    if not LATIN_JSON.exists():
        print("Run scripts/generate_djangojs_latin.py first.", file=sys.stderr)
        return 1

    data = json.loads(LATIN_JSON.read_text(encoding="utf-8"))
    single: dict[str, str] = data["single"]
    plural: dict[str, list[str]] = data["plural"]
    context_map: dict[str, str] = data.get("context", {})

    en = polib.pofile(str(EN_JS))
    if PROJECT_JS.exists():
        proj = polib.pofile(str(PROJECT_JS))
    else:
        proj = polib.POFile()
        proj.metadata = {
            "Project-Id-Version": "Kod Pendule",
            "Language": "sr",
            "Content-Type": "text/plain; charset=UTF-8",
            "Plural-Forms": "nplurals=3; plural=(n%10==1 && n%100!=11 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2);",
        }

    by_key: dict[tuple[str, str], polib.POEntry] = {}
    for e in proj:
        if e.obsolete or not e.msgid:
            continue
        by_key[(e.msgctxt or "", e.msgid)] = e

    merged = 0
    for entry in en:
        if not entry.msgid:
            continue
        ctx = entry.msgctxt or ""
        key = (ctx, entry.msgid)

        if entry.msgid_plural:
            forms = plural.get(entry.msgid)
            if not forms:
                continue
            if key in by_key:
                po_entry = by_key[key]
            else:
                po_entry = polib.POEntry(msgid=entry.msgid, msgctxt=ctx or None, msgid_plural=entry.msgid_plural)
                proj.append(po_entry)
                by_key[key] = po_entry
            po_entry.msgstr_plural = {i: forms[i] for i in range(len(forms))}
            merged += 1
            continue

        latin = context_map.get(f"{ctx}|{entry.msgid}") or single.get(entry.msgid)
        if not latin:
            continue

        if key in by_key:
            po_entry = by_key[key]
        else:
            po_entry = polib.POEntry(msgid=entry.msgid, msgctxt=ctx or None)
            proj.append(po_entry)
            by_key[key] = po_entry
        po_entry.msgstr = latin
        merged += 1

    PROJECT_JS.parent.mkdir(parents=True, exist_ok=True)
    proj.save(str(PROJECT_JS))
    proj.save_as_mofile(str(PROJECT_JS.with_suffix(".mo")))
    print(f"Wrote {merged} entries to {PROJECT_JS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
