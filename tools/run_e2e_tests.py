"""Tests Playwright du site statique TheCol.

Démarre `python -m http.server 8123` dans un subprocess contrôlé/redirigé,
exécute une batterie de tests contre http://127.0.0.1:8123/, puis termine
impérativement le serveur dans `finally`.
"""
from __future__ import annotations

import contextlib
import os
import socket
import subprocess
import sys
import time
import traceback
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ModuleNotFoundError:
    sys.stderr.write(
        "Les tests e2e nécessitent Playwright. Installez-le avec :\n"
        "  python -m pip install playwright\n"
        "  python -m playwright install chromium\n"
    )
    sys.exit(2)

ROOT = Path(__file__).resolve().parent.parent
BASE = "http://127.0.0.1:8123"
EXPECTED_PAGES = [
    "index.html",
    "produits.html",
    "points-de-vente.html",
    "a-propos.html",
    "contact.html",
    "produit-hibiscus.html",
    "produit-mures.html",
    "produit-sureau.html",
    "produit-herbes.html",
    "produit-poire.html",
]
VIEWPORTS = [(320, 720), (375, 720), (390, 800)]

results: list[tuple[str, str, str]] = []  # (status, name, detail)


def record(name: str, ok: bool, detail: str = "") -> None:
    status = "PASS" if ok else "FAIL"
    results.append((status, name, detail))
    print(f"[{status}] {name} {('- ' + detail) if detail else ''}", flush=True)


def can_bind(port: int) -> bool:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(("127.0.0.1", port))
        return True
    except OSError:
        return False
    finally:
        s.close()


def wait_server(port: int, timeout: float = 15.0) -> bool:
    end = time.time() + timeout
    while time.time() < end:
        with contextlib.suppress(OSError):
            with socket.create_connection(("127.0.0.1", port), timeout=0.5):
                return True
        time.sleep(0.1)
    return False


def run_tests() -> int:
    server: subprocess.Popen | None = None
    log_path = ROOT / "_server.log"
    log_handle = None
    try:
        if not can_bind(8123):
            record("serveur:démarrage", False, "port 8123 déjà occupé")
            return 2

        log_handle = log_path.open("wb")
        server = subprocess.Popen(
            [sys.executable, "-m", "http.server", "8123", "--bind", "127.0.0.1"],
            cwd=str(ROOT),
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
        )
        if not wait_server(8123):
            record("serveur:démarrage", False, "timeout attendre 8123")
            return 2
        record("serveur:démarrage", True, f"pid={server.pid}")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)

            # === 1) Les 10 HTML répondent 200, zéro erreur console/page ===
            console_errors: dict[str, list[str]] = {}
            page_errors: dict[str, list[str]] = {}
            status_by_page: dict[str, int] = {}

            for page_name in EXPECTED_PAGES:
                ctx = browser.new_context()
                pg = ctx.new_page()
                ce: list[str] = []
                pe: list[str] = []
                pg.on("console", lambda m, ce=ce: ce.append(f"{m.type}:{m.text}") if m.type in {"error", "warning"} else None)
                pg.on("pageerror", lambda e, pe=pe: pe.append(str(e)))

                url = f"{BASE}/{page_name}"
                resp = pg.goto(url, wait_until="networkidle", timeout=20000)
                status = resp.status if resp else 0
                status_by_page[page_name] = status
                console_errors[page_name] = ce
                page_errors[page_name] = pe
                ctx.close()

            all_ok = True
            for page_name in EXPECTED_PAGES:
                ok = status_by_page[page_name] == 200
                if not ok:
                    all_ok = False
                    record(f"HTTP 200 — {page_name}", False, f"status={status_by_page[page_name]}")
            if all_ok:
                record("HTTP 200 — 10 pages", True, ", ".join(EXPECTED_PAGES))

            any_console = False
            any_page = False
            for page_name in EXPECTED_PAGES:
                if console_errors[page_name]:
                    any_console = True
                    record(f"console — {page_name}", False, "; ".join(console_errors[page_name]))
                if page_errors[page_name]:
                    any_page = True
                    record(f"pageerror — {page_name}", False, "; ".join(page_errors[page_name]))
            if not any_console:
                record("console — 0 erreur/warning", True, "10 pages")
            if not any_page:
                record("pageerror — 0 erreur", True, "10 pages")

            # === 2) Aucun débordement horizontal à 320/375/390 ===
            overflow_pages: list[str] = []
            for w, h in VIEWPORTS:
                ctx = browser.new_context(viewport={"width": w, "height": h})
                pg = ctx.new_page()
                for page_name in EXPECTED_PAGES:
                    pg.goto(f"{BASE}/{page_name}", wait_until="networkidle", timeout=20000)
                    metrics = pg.evaluate(
                        "() => ({sw: document.documentElement.scrollWidth, iw: window.innerWidth})"
                    )
                    if metrics["sw"] > metrics["iw"]:
                        overflow_pages.append(f"{page_name}@{w} sw={metrics['sw']} iw={metrics['iw']}")
                ctx.close()
            if overflow_pages:
                record("responsive — pas de débordement horizontal", False, "; ".join(overflow_pages))
            else:
                record("responsive — pas de débordement horizontal", True, "320/375/390 × 10 pages")

            # === 3) Menu mobile : aria-label bascule, Escape ferme et focus retour ===
            ctx = browser.new_context(viewport={"width": 375, "height": 700})
            pg = ctx.new_page()
            pg.goto(f"{BASE}/index.html", wait_until="networkidle", timeout=20000)
            toggle = pg.locator(".nav-toggle")
            label_before = toggle.get_attribute("aria-label")
            expanded_before = toggle.get_attribute("aria-expanded")
            toggle.click()
            pg.wait_for_timeout(120)
            label_open = toggle.get_attribute("aria-label")
            expanded_open = toggle.get_attribute("aria-expanded")
            body_open = pg.evaluate("() => document.body.classList.contains('nav-open')")
            record(
                "menu — bascule aria-label/aria-expanded",
                (label_before == "Ouvrir le menu" and label_open == "Fermer le menu"
                 and expanded_before == "false" and expanded_open == "true" and body_open),
                f"labels={label_before!r}→{label_open!r}, expanded={expanded_before}→{expanded_open}, nav-open={body_open}",
            )
            pg.keyboard.press("Escape")
            pg.wait_for_timeout(120)
            body_closed = pg.evaluate("() => document.body.classList.contains('nav-open')")
            focused_after = pg.evaluate("() => ({tag: document.activeElement && document.activeElement.tagName, cls: document.activeElement && document.activeElement.className})")
            record(
                "menu — Escape ferme",
                (not body_closed),
                f"nav-open={body_closed}",
            )
            record(
                "menu — focus retour sur toggle",
                (focused_after["cls"] == "nav-toggle"),
                f"focus={focused_after}",
            )
            ctx.close()

            # === 4) Points de vente : pos-root sans aria-live, zone pos-live-status seule, canton aria-pressed, recherche filtre ===
            ctx = browser.new_context(viewport={"width": 1280, "height": 900})
            pg = ctx.new_page()
            pg.goto(f"{BASE}/points-de-vente.html", wait_until="networkidle", timeout=20000)

            root_aria_live = pg.evaluate(
                "() => { const e=document.getElementById('pos-root'); return e && e.getAttribute('aria-live'); }"
            )
            record("pos — pos-root sans aria-live", root_aria_live in (None, ""), f"aria-live={root_aria_live!r}")

            live_status = pg.evaluate(
                "() => { const e=document.getElementById('pos-live-status'); return e ? {tag: e.tagName, ariaLive: e.getAttribute('aria-live')} : null; }"
            )
            record("pos — zone pos-live-status existe seule", live_status is not None and live_status["ariaLive"] == "polite", f"live={live_status}")

            chips_count = pg.locator("#pos-chips .chip").count()
            record("pos — chips de cantons présents", chips_count >= 2, f"chips={chips_count}")

            pg.wait_for_timeout(200)
            before_count = pg.locator("#pos-root .pos-card").count()
            # Cliquer sur le 2e chip (un canton autre que "Tous")
            canton_label = pg.evaluate(
                "() => { const all=document.querySelectorAll('#pos-chips .chip'); return all.length>1 ? all[1].dataset.canton : null; }"
            )
            pg.locator("#pos-chips .chip").nth(1).click()
            pg.wait_for_timeout(150)
            pressed_states = pg.evaluate(
                "() => Array.from(document.querySelectorAll('#pos-chips .chip')).map(c => ({c: c.dataset.canton, p: c.getAttribute('aria-pressed')}))"
            )
            only_one_pressed = sum(1 for s in pressed_states if s["p"] == "true") == 1
            after_count = pg.locator("#pos-root .pos-card").count()
            changed = after_count != before_count
            record(
                "pos — clic canton met aria-pressed et filtre",
                only_one_pressed and changed,
                f"canton={canton_label}, pressed={pressed_states}, cards {before_count}→{after_count}",
            )

            # Remettre "Tous"
            pg.locator("#pos-chips .chip").nth(0).click()
            pg.wait_for_timeout(150)
            all_count = pg.locator("#pos-root .pos-card").count()

            # Recherche réduit le nombre de cartes
            pg.fill("#pos-search", "zzznotfound")
            pg.wait_for_timeout(200)
            search_zero = pg.locator("#pos-root .pos-card").count()
            pg.fill("#pos-search", "")
            pg.wait_for_timeout(200)
            search_full = pg.locator("#pos-root .pos-card").count()
            record(
                "pos — recherche réduit les cartes",
                search_zero == 0 and search_full == all_count,
                f"all={all_count}, search_zero={search_zero}, search_full={search_full}",
            )
            ctx.close()

            # === 5) Fiche Poire : radios 25/50/100 → total 3/5/8.50 ; galerie ===
            ctx = browser.new_context(viewport={"width": 1280, "height": 900})
            pg = ctx.new_page()
            pg.goto(f"{BASE}/produit-poire.html", wait_until="networkidle", timeout=20000)

            totals_by_size: dict[str, str] = {}
            for size, expected in [("25", "CHF 3.00"), ("50", "CHF 5.00"), ("100", "CHF 8.50")]:
                pg.evaluate(
                    f"() => {{ const r=document.querySelector('input[name=format][value=\"{size}\"]'); r.checked=true; r.dispatchEvent(new Event('change', {{bubbles:true}})); }}"
                )
                pg.wait_for_timeout(80)
                total = pg.locator("#pd-total").inner_text()
                totals_by_size[size] = total
            ok_totals = totals_by_size == {"25": "CHF 3.00", "50": "CHF 5.00", "100": "CHF 8.50"}
            record("poire — radios 25/50/100 → total 3/5/8.50", ok_totals, f"totals={totals_by_size}")

            # Quantité + radio
            pg.fill("#pd-qty", "2")
            pg.evaluate(
                "() => { const r=document.querySelector('input[name=format][value=\"50\"]'); r.checked=true; r.dispatchEvent(new Event('change', {bubbles:true})); }"
            )
            pg.wait_for_timeout(80)
            total_qty2 = pg.locator("#pd-total").inner_text()
            record("poire — qty=2 + format 50 → total 10.00", total_qty2 == "CHF 10.00", f"total={total_qty2}")

            # Galerie : changement de vignette modifie l'image principale
            src_before = pg.locator("#pd-main-img").get_attribute("src")
            thumbs = pg.locator(".pd-thumb")
            thumb_count = thumbs.count()
            thumbs.nth(1).click()
            pg.wait_for_timeout(150)
            src_after = pg.locator("#pd-main-img").get_attribute("src")
            record(
                "poire — galerie: vignette change main image",
                src_before != src_after and thumb_count >= 4,
                f"thumbs={thumb_count}, src {src_before} → {src_after}",
            )
            ctx.close()

            # === 6) Panier : ajout, qty, suppression, focus close, Tab piégé, Escape, overlay/body ===
            ctx = browser.new_context(viewport={"width": 1280, "height": 900})
            pg = ctx.new_page()
            # Le panier nécessite d'ajouter depuis une fiche produit pour avoir un localStorage propre
            pg.goto(f"{BASE}/produit-poire.html", wait_until="networkidle", timeout=20000)
            pg.evaluate(
                "() => { const r=document.querySelector('input[name=format][value=\"50\"]'); r.checked=true; r.dispatchEvent(new Event('change', {bubbles:true})); }"
            )
            pg.fill("#pd-qty", "1")
            pg.click("#pd-add")
            pg.wait_for_timeout(200)
            # Le panier s'ouvre automatiquement
            is_open = pg.evaluate("() => document.body.classList.contains('cart-open')")
            items_count = pg.locator("#cart-items .cart-item").count()
            record("panier — ajout ouvre le drawer", is_open and items_count == 1, f"open={is_open}, items={items_count}")

            # Modification qty via + / -
            before_total = pg.locator("#cart-total").inner_text()
            pg.locator("#cart-items .cart-item button[data-ci-inc]").first.click(timeout=2000)
            pg.wait_for_timeout(150)
            after_total = pg.locator("#cart-total").inner_text()
            qty_input_value = pg.locator("#cart-items .cart-item input[type='number']").first.input_value() if pg.locator("#cart-items .cart-item input[type='number']").count() else ""
            record("panier — qty + augmente le total", after_total != before_total, f"total {before_total}→{after_total}, qty={qty_input_value}")

            # Suppression d'un article (bouton "Retirer")
            pg.locator("#cart-items .cart-item button[data-ci-rm]").first.click(timeout=2000)
            pg.wait_for_timeout(200)
            items_after = pg.locator("#cart-items .cart-item").count()
            record("panier — suppression retire l'article", items_after == 0, f"items={items_after}")

            # Ré-ajouter pour tester le reste
            pg.evaluate("() => localStorage.removeItem('thecol-cart')")
            pg.reload(wait_until="networkidle")
            pg.evaluate(
                "() => { const r=document.querySelector('input[name=format][value=\"25\"]'); r.checked=true; r.dispatchEvent(new Event('change', {bubbles:true})); }"
            )
            pg.fill("#pd-qty", "1")
            pg.click("#pd-add")
            pg.wait_for_timeout(200)

            # Ouverture: focus sur close
            open_btn = pg.locator(".cart-btn").first
            open_btn.focus()
            open_btn.click()
            pg.wait_for_timeout(200)
            focus_on_close = pg.evaluate(
                "() => document.activeElement && document.activeElement.id === 'cart-close'"
            )
            record("panier — focus sur #cart-close à l'ouverture", focus_on_close, f"focus={focus_on_close}")

            # Tab piégé : focuser le close, appuyer Tab → focus reste dans le drawer
            pg.locator("#cart-close").focus()
            pg.keyboard.press("Tab")
            pg.wait_for_timeout(100)
            inside_drawer = pg.evaluate(
                "() => { const d=document.getElementById('cart-drawer'); return d && d.contains(document.activeElement); }"
            )
            # Cycle : focuser le premier focusable, Shift+Tab depuis le premier → va au dernier
            pg.evaluate(
                "() => { const d=document.getElementById('cart-drawer'); const f=d.querySelectorAll('a,button,input,select,textarea,[tabindex]:not([tabindex=\"-1\"])'); if(f.length) f[0].focus(); }"
            )
            pg.wait_for_timeout(50)
            pg.keyboard.press("Shift+Tab")
            pg.wait_for_timeout(100)
            trapped_last = pg.evaluate(
                "() => { const d=document.getElementById('cart-drawer'); const f=d.querySelectorAll('a,button,input,select,textarea,[tabindex]:not([tabindex=\"-1\"])'); return f.length>0 && d.contains(f[f.length-1]) && document.activeElement===f[f.length-1]; }"
            )
            record("panier — Tab piégé dans le drawer", inside_drawer and trapped_last, f"inside_after_tab={inside_drawer}, shift_tab_traps={trapped_last}")

            # Escape ferme et focus retour
            # Mettre le focus à l'intérieur du drawer avant Escape
            pg.locator("#cart-close").focus()
            pg.keyboard.press("Escape")
            pg.wait_for_timeout(150)
            closed = pg.evaluate("() => !document.body.classList.contains('cart-open')")
            focused_after_esc = pg.evaluate(
                "() => { const e=document.activeElement; return e ? {tag: e.tagName, cls: e.className} : null; }"
            )
            record("panier — Escape ferme", closed, f"cart-open={not closed}")
            is_cart_btn = focused_after_esc and "cart-btn" in (focused_after_esc.get("cls") or "")
            record("panier — focus retour sur cart-btn", is_cart_btn, f"focus={focused_after_esc}")

            # Overlay/body state quand ouvert
            open_btn.click()
            pg.wait_for_timeout(150)
            overlay_hidden = pg.evaluate("() => { const o=document.getElementById('cart-overlay'); return o.hidden === false; }")
            body_open = pg.evaluate("() => document.body.classList.contains('cart-open')")
            record("panier — overlay visible et body.cart-open", overlay_hidden and body_open, f"overlay_hidden={not overlay_hidden}, body.cart-open={body_open}")
            # Fermer via overlay
            pg.evaluate("() => { document.getElementById('cart-overlay').click(); }")
            pg.wait_for_timeout(150)
            closed_overlay = pg.evaluate("() => !document.body.classList.contains('cart-open')")
            record("panier — clic overlay ferme", closed_overlay, f"closed={closed_overlay}")
            ctx.close()

            # === 7) Contact : soumission invalide ne navigue pas ; valide capture un seul mailto ; copie/feedback ===
            ctx = browser.new_context(viewport={"width": 1280, "height": 900})
            pg = ctx.new_page()
            # Intercepter les navigations (window.location.href=mailto: ne déclenche pas de requête HTTP,
            # mais on peut écouter les frames et requests sortantes)
            navigation_events: list[str] = []
            pg.on("framenavigated", lambda f, ne=navigation_events: ne.append(f.url) if f == pg.main_frame else None)
            request_events: list[str] = []
            pg.on("request", lambda r, re=request_events: re.append(r.url))

            pg.goto(f"{BASE}/contact.html", wait_until="networkidle", timeout=20000)

            # Soumission invalide : email malformé
            pg.fill("#f-nom", "Test")
            pg.fill("#f-email", "pas-un-email")
            pg.fill("#f-sujet", "Sujet")
            pg.fill("#f-question", "Bonjour")
            url_before = pg.url
            # Cliquer le submit — la validation HTML native empêche l'event submit
            pg.evaluate(
                "() => { const f=document.getElementById('contact-form'); const s=f.querySelector('button[type=submit]'); s.click(); }"
            )
            pg.wait_for_timeout(300)
            url_after = pg.url
            navigated = (url_before != url_after)
            mailto_requests = [u for u in request_events if u.startswith("mailto:")]
            record("contact — soumission invalide ne navigue pas", not navigated and not mailto_requests, f"navigated={navigated}, mailto={mailto_requests}")

            # Soumission valide : preventDefault + mailto unique
            request_events.clear()
            navigation_events.clear()
            pg.fill("#f-email", "test@example.com")
            pg.fill("#f-nom", "Jean Test")
            pg.fill("#f-sujet", "Demande test")
            pg.fill("#f-question", "Bonjour, ceci est un test.")
            pg.evaluate(
                "() => { const f=document.getElementById('contact-form'); const s=f.querySelector('button[type=submit]'); s.click(); }"
            )
            pg.wait_for_timeout(400)
            mailto_requests = [u for u in request_events if u.startswith("mailto:")]
            # Certains navigateurs émettent mailto: comme request, d'autres comme navigation
            mailto_navigations = [u for u in navigation_events if u.startswith("mailto:")]
            mailto_all = mailto_requests + mailto_navigations
            # Filtrer pour ne garder que les mailto vers commande@thecol.ch
            mailto_commande = [u for u in mailto_all if "commande@thecol.ch" in u]
            record(
                "contact — mailto unique vers commande@thecol.ch",
                len(mailto_commande) == 1,
                f"mailto_total={len(mailto_all)}, commande={mailto_commande}",
            )

            # Test preventDefault : on clique à nouveau et on vérifie que l'URL de la page n'a pas changé
            # vers une query string de type ?nom=&email=... (soumission GET native)
            url_after_valid = pg.url
            no_native_submit = "?" not in url_after_valid.split("/")[-1] or url_after_valid.endswith("contact.html")
            record("contact — preventDefault (pas de query string native)", no_native_submit, f"url={url_after_valid}")

            # Copie possible + feedback (clipboard peut être limitée)
            request_events.clear()
            # Recharger pour repartir proprement
            pg.goto(f"{BASE}/contact.html", wait_until="networkidle", timeout=20000)
            pg.fill("#f-nom", "Jean Test")
            pg.fill("#f-email", "test@example.com")
            pg.fill("#f-sujet", "Demande test")
            pg.fill("#f-question", "Bonjour, ceci est un test.")
            copy_btn = pg.locator("#contact-copy")
            has_copy = copy_btn.count() == 1
            copy_btn.click()
            pg.wait_for_timeout(300)
            feedback = pg.locator("#contact-feedback").inner_text() if pg.locator("#contact-feedback").count() else ""
            record(
                "contact — bouton copie présent et feedback après clic",
                has_copy and len(feedback) > 0,
                f"copy_present={has_copy}, feedback={feedback!r}",
            )
            ctx.close()

            # === 8) robots.txt / sitemap.xml accessibles ===
            ctx = browser.new_context()
            pg = ctx.new_page()
            resp_robots = pg.goto(f"{BASE}/robots.txt", timeout=10000)
            robots_status = resp_robots.status if resp_robots else 0
            robots_body = resp_robots.text() if resp_robots else ""
            resp_sitemap = pg.goto(f"{BASE}/sitemap.xml", timeout=10000)
            sitemap_status = resp_sitemap.status if resp_sitemap else 0
            sitemap_body = (resp_sitemap.text() if resp_sitemap else "")
            ok_robots = robots_status == 200 and "User-agent" in robots_body
            ok_sitemap = sitemap_status == 200 and "<urlset" in sitemap_body
            record("robots.txt accessible", ok_robots, f"status={robots_status}")
            record("sitemap.xml accessible", ok_sitemap, f"status={sitemap_status}")
            ctx.close()

            browser.close()

        return 0
    except Exception:
        traceback.print_exc()
        record("exception", False, traceback.format_exc())
        return 1
    finally:
        if server is not None:
            try:
                server.terminate()
                server.wait(timeout=5)
            except Exception:
                with contextlib.suppress(Exception):
                    server.kill()
        if log_handle is not None:
            log_handle.close()
        # Attendre que le port soit réellement libéré
        for _ in range(20):
            if can_bind(8123):
                break
            time.sleep(0.1)


def main() -> int:
    rc = run_tests()
    print("\n=== Résumé ===")
    fails = [r for r in results if r[0] == "FAIL"]
    passes = [r for r in results if r[0] == "PASS"]
    print(f"Total : {len(results)} — PASS : {len(passes)} — FAIL : {len(fails)}")
    for status, name, detail in results:
        print(f"[{status}] {name} {('- ' + detail) if detail else ''}")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
