"""Diagnostic Playwright : repère les éléments qui dépassent innerWidth à 320px.

Pour index.html et a-propos.html, à 320px de largeur, on liste tous les éléments
du DOM dont `getBoundingClientRect()` (gauche ou droite) dépasse la largeur
de viewport. On collecte aussi une métrique `scrollWidth` du document.

On groupe par sélecteur (sélecteur CSS recalculé via path / tag / class / id).
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
BASE = "http://127.0.0.1:8123"
PAGES = ["index.html", "a-propos.html"]
WIDTH = 320
HEIGHT = 720


def describe(el_desc: dict) -> str:
    """Construit une étiquette lisible pour un élément."""
    parts = [el_desc.get("tag", "?")]
    if el_desc.get("id"):
        parts.append("#" + el_desc["id"])
    cls = el_desc.get("class") or ""
    if cls:
        parts.append("." + ".".join(cls.split()))
    return "".join(parts)


def collect(page) -> dict:
    """JavaScript qui parcourt tous les éléments et signale ceux qui dépassent."""
    return page.evaluate(
        """() => {
            const iw = window.innerWidth;
            const out = [];
            function visit(el) {
                if (!(el instanceof Element)) return;
                const cs = getComputedStyle(el);
                if (cs.display === 'none' || cs.visibility === 'hidden') return;
                if (cs.position === 'fixed' || cs.position === 'absolute') return; // hors flux visuel
                const r = el.getBoundingClientRect();
                if (r.width === 0 && r.height === 0) return;
                const overflowLeft = r.left < -0.5;
                const overflowRight = r.right > iw + 0.5;
                if (overflowLeft || overflowRight) {
                    out.push({
                        tag: el.tagName.toLowerCase(),
                        id: el.id || null,
                        class: el.className && typeof el.className === 'string' ? el.className : null,
                        rect: { left: r.left, right: r.right, width: r.width, top: r.top },
                        scrollWidth: el.scrollWidth,
                        clientWidth: el.clientWidth,
                        text: (el.textContent || '').trim().slice(0, 40),
                    });
                }
                for (const c of el.children) visit(c);
            }
            visit(document.documentElement);
            return {
                innerWidth: iw,
                docScrollWidth: document.documentElement.scrollWidth,
                bodyScrollWidth: document.body.scrollWidth,
                candidates: out,
            };
        }"""
    )


def run() -> int:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        for page_name in PAGES:
            ctx = browser.new_context(viewport={"width": WIDTH, "height": HEIGHT})
            pg = ctx.new_page()
            url = f"{BASE}/{page_name}"
            pg.goto(url, wait_until="networkidle", timeout=20000)
            # attendre que les .reveal aient leur classe .in (sinon opacity:0 reste)
            pg.wait_for_timeout(400)
            data = collect(pg)
            print(f"\n=== {page_name} @ {WIDTH}px ===")
            print(
                f"innerWidth={data['innerWidth']} "
                f"docScrollWidth={data['docScrollWidth']} "
                f"bodyScrollWidth={data['bodyScrollWidth']}"
            )
            # Regrouper par sélecteur (tag + id + classes)
            by_selector: dict[str, list[dict]] = defaultdict(list)
            for el in data["candidates"]:
                key = describe(el)
                by_selector[key].append(el)

            # Trier pour reproductibilité
            sorted_items = sorted(by_selector.items(), key=lambda kv: kv[0])
            for sel, items in sorted_items:
                # Garder 1 exemple représentatif (le plus grand dépassement)
                items.sort(key=lambda e: max(e["rect"]["right"] - e["rect"]["left"], 0), reverse=True)
                # En-tête : sélecteur et nombre d'occurrences
                print(f"  - {sel}  ({len(items)} occurrence(s))")
                for it in items[:5]:
                    rect = it["rect"]
                    print(
                        f"      left={rect['left']:.1f} right={rect['right']:.1f} "
                        f"width={rect['width']:.1f} top={rect['top']:.1f} "
                        f"scrollW={it['scrollWidth']} clientW={it['clientWidth']} "
                        f"text={it['text']!r}"
                    )
            # Si scrollWidth dépasse innerWidth, c'est le pb global
            if data["docScrollWidth"] > data["innerWidth"]:
                print(
                    f"  ! documentElement.scrollWidth={data['docScrollWidth']} > innerWidth={data['innerWidth']}"
                )
            ctx.close()
        browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(run())
