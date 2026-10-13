#!/usr/bin/env python3
"""Déploie le dossier odoo/ sur une base Odoo (API JSON-2, Odoo 19+).

Remplace les collages manuels décrits dans odoo/README.md :

  assets    images, polices et montagne.svg → médiathèque Odoo (publics),
            les URL GitHub Pages sont réécrites vers /web/image|content/...
  styles    odoo/*.scss concaténés → user_custom_rules.scss
  scripts   odoo/*.js concaténés → user_custom_javascript.js
  pages     /, /contactus, /about-us, /nos-produits, /distributeurs (+ SEO)
  footer    contenu du pied de page (odoo/pied-de-page.xml)
  menus     menu principal
  products  5 saveurs à variantes « Format » 25/50/100 cl (tools/products.json)
  verify    relit les pages publiques et le bundle CSS

Le script est rejouable : il met à jour ce qui existe déjà au lieu de dupliquer.
Avant chaque écriture de vue, l'ancien code est sauvegardé dans .odoo-backup/.

Clé API : Odoo → Mon profil → Sécurité du compte → Nouvelle clé API, puis
variable d'environnement ODOO_API_KEY ou fichier .odoo-api-key à la racine
du dépôt (ignoré par Git).

    py tools/deploy_odoo.py --dry-run          # lecture seule, affiche le plan
    py tools/deploy_odoo.py                    # base de test (par défaut)
    py tools/deploy_odoo.py --steps styles,scripts
    py tools/deploy_odoo.py --url https://www.thecol.ch --production

Python standard, aucune dépendance.
"""

import argparse
import base64
import hashlib
import json
import mimetypes
import os
import re
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ODOO_DIR = ROOT / "odoo"
BACKUP_DIR = ROOT / ".odoo-backup"
KEY_FILE = ROOT / ".odoo-api-key"
DEFAULT_URL = "https://thecol-test.odoo.com"

GH = "https://philippe-ong.github.io/thecol-site/"
GH_REF = re.compile(re.escape(GH) + r"(assets/[^\"')\s]+)")
ASSET_MARK = "thecol-site:"  # ir.attachment.description, pour retrouver nos fichiers

# Ordre de collage de odoo/README.md
SCSS_FILES = ["thecol.scss", "distributeurs.scss", "produits.scss", "contact.scss",
              "a-propos.scss", "entete-pied.scss", "boutique.scss", "fiche-produit.scss"]
JS_FILES = ["distributeurs.js", "prix-formats.js", "fiches-saveurs.js"]
SCSS_URL = "/website/static/src/scss/user_custom_rules.scss"
JS_URL = "/website/static/src/js/user_custom_javascript.js"
BUNDLE = "web.assets_frontend"

# Pages créées par le script : url → (clé de vue, nom, fichier, page statique pour le SEO)
NEW_PAGES = [
    ("/nos-produits", "website.nos-produits", "Nos produits", "produits.xml", "produits.html"),
    ("/distributeurs", "website.distributeurs", "Points de vente", "distributeurs.xml", "points-de-vente.html"),
    ("/about-us", "website.about-us", "À propos", "a-propos.xml", "a-propos.html"),
]
SEO_EXISTING = [("website.homepage", "index.html"), ("website.contactus", "contact.html")]

MENU = [("Accueil", "/"), ("Nos produits", "/nos-produits"), ("Boutique", "/shop"),
        ("Points de vente", "/distributeurs"), ("À propos", "/about-us")]

FORMAT_VALUES = ["25", "50", "100"]  # clés de tools/products.json → « 25 cl »…
STEPS = ["assets", "styles", "scripts", "pages", "footer", "menus", "products", "verify"]


class OdooError(RuntimeError):
    pass


class Odoo:
    def __init__(self, url, key, dry_run):
        self.url = url.rstrip("/")
        self.key = key
        self.dry_run = dry_run
        self.ctx = {}

    def call(self, model, method, **params):
        if self.ctx or "context" in params:
            params["context"] = {**self.ctx, **params.get("context", {})}
        req = urllib.request.Request(
            "%s/json/2/%s/%s" % (self.url, model, method),
            data=json.dumps(params).encode("utf-8"),
            headers={"Authorization": "bearer " + self.key,
                     "Content-Type": "application/json; charset=utf-8"},
            method="POST")
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "replace")
            try:
                msg = json.loads(body).get("message") or body
            except ValueError:
                msg = body[:500]
            raise OdooError("%s.%s → HTTP %s : %s" % (model, method, e.code, msg)) from None

    def read(self, model, domain, fields, **kw):
        return self.call(model, "search_read", domain=domain, fields=fields, **kw)

    def create(self, model, vals, label, **kw):
        if self.dry_run:
            print("  [dry-run] créer %s : %s" % (model, label))
            return None
        new_id = self.call(model, "create", vals_list=[vals], **kw)[0]
        print("  créé %s #%s : %s" % (model, new_id, label))
        return new_id

    def write(self, model, ids, vals, label, **kw):
        if self.dry_run:
            print("  [dry-run] modifier %s %s : %s" % (model, ids, label))
            return
        self.call(model, "write", ids=ids, vals=vals, **kw)
        print("  modifié %s %s : %s" % (model, ids, label))


def b64(data):
    return base64.b64encode(data).decode("ascii")


def read_text(name):
    return (ODOO_DIR / name).read_text(encoding="utf-8")


MIMETYPES = {".webp": "image/webp", ".woff2": "font/woff2", ".svg": "image/svg+xml"}


def guess_mimetype(name):
    ext = os.path.splitext(name)[1].lower()
    return MIMETYPES.get(ext) or mimetypes.guess_type(name)[0] or "application/octet-stream"


def check_xml(arch, label):
    """Odoo refuse une vue mal formée : on le sait avant d'envoyer quoi que ce soit."""
    try:
        ET.fromstring(arch)
    except ET.ParseError as e:
        raise SystemExit("XML invalide pour %s : %s" % (label, e))


def static_meta(html_file):
    """<title> et meta description d'une page du site statique."""
    html = (ROOT / html_file).read_text(encoding="utf-8")
    title = re.search(r"<title>(.*?)</title>", html, re.S)
    desc = re.search(r'<meta name="description" content="([^"]*)"', html)
    unescape = lambda s: s.replace("&amp;", "&").replace("&#39;", "'").replace("&quot;", '"').strip()
    return (unescape(title.group(1)) if title else None,
            unescape(desc.group(1)) if desc else None)


class Deployer:
    def __init__(self, odoo):
        self.odoo = odoo
        self.asset_urls = {}
        site = odoo.read("website", [], ["name", "menu_id", "default_lang_id"], limit=1, order="id")[0]
        self.website_id = site["id"]
        self.menu_id = site["menu_id"] and site["menu_id"][0]
        lang = odoo.read("res.lang", [["id", "=", site["default_lang_id"][0]]], ["code"])
        self.lang = lang[0]["code"]
        print("Site « %s » (#%s), langue %s" % (site["name"], self.website_id, self.lang))
        # Contexte du site : les vues génériques sont copiées pour ce site (COW).
        odoo.ctx = {"website_id": self.website_id, "lang": self.lang}

    # ------------------------------------------------------------------ assets
    def step_assets(self):
        paths = set()
        for f in ODOO_DIR.iterdir():
            if f.suffix in (".xml", ".scss", ".js"):
                paths.update(GH_REF.findall(f.read_text(encoding="utf-8")))
        for rel in sorted(paths):
            local = ROOT / rel
            if not local.is_file():
                raise SystemExit("Fichier introuvable : %s" % local)
            data = local.read_bytes()
            sha1 = hashlib.sha1(data).hexdigest()
            name = local.name
            found = self.odoo.read("ir.attachment", [["description", "=", ASSET_MARK + rel]],
                                   ["checksum"], limit=1)
            if found and found[0]["checksum"] == sha1:
                att_id = found[0]["id"]
            elif found:
                att_id = found[0]["id"]
                self.odoo.write("ir.attachment", [att_id], {"raw": b64(data), "mimetype": guess_mimetype(name)}, rel)
            else:
                att_id = self.odoo.create("ir.attachment", {
                    "name": name,
                    "raw": b64(data),  # Odoo 20 : plus de champ « datas »
                    "mimetype": guess_mimetype(name),
                    "public": True,
                    "res_model": "ir.ui.view",
                    "res_id": 0,
                    "description": ASSET_MARK + rel,
                }, rel)
            # La version (hash) change l'URL à chaque nouveau fichier → cache longue durée.
            # /web/content n'accepte pas la forme <id>-<hash> sur Odoo 20 : ?unique= à la place.
            if not att_id:
                url = GH + rel
            elif local.suffix in (".webp", ".jpg", ".jpeg", ".png"):
                url = "/web/image/%s-%s/%s" % (att_id, sha1[:8], name)
            else:
                url = "/web/content/%s/%s?unique=%s" % (att_id, name, sha1[:8])
            self.asset_urls[rel] = url
        print("  %d fichiers dans la médiathèque" % len(paths))

    def rewrite(self, text):
        if not self.asset_urls:
            self.step_assets()
        return GH_REF.sub(lambda m: self.asset_urls[m.group(1)], text)

    # ------------------------------------------------------- styles / scripts
    def save_custom_asset(self, url, content, file_type):
        """Enregistre comme le bouton Sauvegarder de l'éditeur HTML/SCSS d'Odoo.

        Ne pas recréer à la main ir.attachment + ir.asset : sur Odoo 20 l'override
        n'est pas rattaché au bundle (JS ignoré, SCSS → erreur 500 sur tout le site).
        """
        if self.odoo.dry_run:
            print("  [dry-run] enregistrer %s (%d caractères)" % (url, len(content)))
            return
        self.odoo.call("website.assets", "save_asset", url=url, bundle=BUNDLE,
                       content=content, file_type=file_type)
        print("  enregistré %s (%d caractères)" % (url, len(content)))

    def concat(self, files, comment):
        parts = []
        for name in files:
            parts.append(comment % name)
            parts.append(self.rewrite(read_text(name)).rstrip() + "\n")
        return "\n".join(parts)

    def step_styles(self):
        content = self.concat(SCSS_FILES, "/* ===== odoo/%s (tools/deploy_odoo.py) ===== */\n")
        self.save_custom_asset(SCSS_URL, content, "scss")

    def step_scripts(self):
        content = self.concat(JS_FILES, "/* ===== odoo/%s (tools/deploy_odoo.py) ===== */\n")
        self.save_custom_asset(JS_URL, content, "js")

    # ------------------------------------------------------------------ views
    def find_view(self, key):
        """Vue propre au site si elle existe, sinon la vue générique."""
        views = self.odoo.read("ir.ui.view", [["key", "=", key],
                                              ["website_id", "in", [self.website_id, False]]],
                               ["arch", "website_id", "name", "active"],
                               context={"active_test": False})
        views.sort(key=lambda v: not v["website_id"])
        return views[0] if views else None

    def backup(self, key, arch):
        host = re.sub(r"\W+", "_", self.odoo.url.split("//", 1)[-1])
        path = BACKUP_DIR / host / (key + ".xml")
        if not path.exists():  # garder la toute première version d'origine
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(arch, encoding="utf-8")
            print("  sauvegarde → %s" % path.relative_to(ROOT))

    def write_arch(self, view, arch, label):
        check_xml(arch, label)
        if view["arch"].strip() == arch.strip():
            print("  inchangé : %s" % label)
            return
        self.backup(label, view["arch"])
        # En anglais (langue source) : les autres langues sont recalculées terme à terme
        # à partir de cette version, comme pour une modification dans l'éditeur.
        self.odoo.write("ir.ui.view", [view["id"]], {"arch": arch}, label,
                        context={"lang": "en_US"})

    def write_seo(self, key, html_file):
        title, desc = static_meta(html_file)
        view = self.find_view(key)
        if view and (title or desc):
            self.odoo.write("ir.ui.view", [view["id"]],
                            {"website_meta_title": title, "website_meta_description": desc},
                            "SEO " + key)

    def step_pages(self):
        home = self.find_view("website.homepage")
        self.write_arch(dict(home, key="website.homepage"),
                        self.rewrite(read_text("accueil.xml")), "website.homepage")
        # Installé avec l'eCommerce, Odoo dépublie l'accueil et redirige / vers /shop.
        for page in self.odoo.read("website.page", [["url", "=", "/"],
                                                    ["website_id", "=", self.website_id]],
                                   ["is_published"]):
            if not page["is_published"]:
                self.odoo.write("website.page", [page["id"]], {"is_published": True}, "publier /")

        contact = self.find_view("website.contactus")
        head = contact["arch"].split('<div id="wrap"', 1)[0].rstrip()
        body = self.rewrite(read_text("contact.xml"))
        self.write_arch(dict(contact, key="website.contactus"),
                        head + "\n" + body, "website.contactus")

        for url, key, name, xml_file, html_file in NEW_PAGES:
            # Les fichiers se terminent par </t></t> mais commencent sans la 1re ligne
            # <t name=… t-name=…> (et sans le t-call du layout pour a-propos.xml).
            body = self.rewrite(read_text(xml_file)).rstrip()
            if body.lstrip().startswith("<div"):
                body = '    <t t-call="website.layout">\n' + body
            arch = '<t name="%s" t-name="%s">\n%s\n' % (name, key, body)
            view = self.find_view(key)
            if view:
                self.write_arch(dict(view, key=key), arch, key)
                view_id = view["id"]
            else:
                check_xml(arch, key)
                view_id = self.odoo.create("ir.ui.view", {
                    "name": name, "type": "qweb", "key": key, "arch": arch,
                    "website_id": self.website_id,
                }, key)
            pages = self.odoo.read("website.page", [["url", "=", url],
                                                    ["website_id", "in", [self.website_id, False]]],
                                   ["is_published"])
            if not pages:
                self.odoo.create("website.page", {
                    "url": url, "view_id": view_id, "website_id": self.website_id,
                    "is_published": True, "website_indexed": True,
                }, url)
            elif not pages[0]["is_published"]:
                self.odoo.write("website.page", [pages[0]["id"]], {"is_published": True}, url)

        if not self.odoo.dry_run:
            for _, key, _, _, html_file in NEW_PAGES:
                self.write_seo(key, html_file)
            for key, html_file in SEO_EXISTING:
                self.write_seo(key, html_file)

    def step_footer(self):
        view = self.find_view("website.footer_custom")
        if not view or not view["active"]:
            raise SystemExit("Pied de page « website.footer_custom » introuvable ou inactif : "
                             "choisir le modèle de pied de page par défaut dans l'éditeur.")
        body = self.rewrite(read_text("pied-de-page.xml")).rstrip()
        new, n = re.subn(r'(<div id="footer"[^>]*>).*?(?=\s*</xpath>)',
                         lambda m: m.group(1) + "\n" + body, view["arch"], flags=re.S)
        if n != 1:
            raise SystemExit('Pied de page : <div id="footer"> … </xpath> non trouvé.')
        self.write_arch(dict(view, key="website.footer_custom"), new, "website.footer_custom")

    # ------------------------------------------------------------------ menus
    def step_menus(self):
        existing = self.odoo.read("website.menu", [["parent_id", "=", self.menu_id]],
                                  ["name", "url", "sequence"])
        by_url = {m["url"]: m for m in existing}
        for seq, (name, url) in enumerate(MENU, start=1):
            vals = {"name": name, "sequence": seq * 10}
            menu = by_url.get(url)
            if not menu:
                self.odoo.create("website.menu", dict(vals, url=url, parent_id=self.menu_id,
                                                      website_id=self.website_id), name)
            elif menu["name"] != name or menu["sequence"] != seq * 10:
                self.odoo.write("website.menu", [menu["id"]], vals, name)

    # --------------------------------------------------------------- products
    def step_products(self):
        catalog = json.loads((ROOT / "tools" / "products.json").read_text(encoding="utf-8"))
        names = {f: "%s cl" % f for f in FORMAT_VALUES}

        attr = self.odoo.read("product.attribute", [["name", "=", "Format"]], ["value_ids"], limit=1)
        if attr:
            attr_id = attr[0]["id"]
        else:
            attr_id = self.odoo.create("product.attribute", {
                "name": "Format", "display_type": "pills", "create_variant": "always",
                "value_ids": [[0, 0, {"name": names[f], "sequence": i}]
                              for i, f in enumerate(FORMAT_VALUES)],
            }, "attribut Format")
        values = {}
        if attr_id:
            for v in self.odoo.read("product.attribute.value", [["attribute_id", "=", attr_id]], ["name"]):
                values[v["name"]] = v["id"]
            missing = [n for n in names.values() if n not in values]
            if missing:
                raise SystemExit("Attribut « Format » sans les valeurs %s" % missing)

        for seq, (pid, p) in enumerate(catalog.items(), start=1):
            prices = {f: float(p["formats"][f]) for f in FORMAT_VALUES}
            base = prices[FORMAT_VALUES[0]]
            _, desc = static_meta(p["page"])
            image = (ROOT / "assets" / "web" / ("produit-%s.jpg" % pid)).read_bytes()
            vals = {
                "list_price": base,
                "sale_ok": True,
                "is_published": True,
                "website_sequence": seq * 10,
                "description_ecommerce": "<p>%s</p>" % desc if desc else False,
                "website_meta_description": desc,
            }
            found = self.odoo.read("product.template", [["name", "=", p["name"]]], ["id"], limit=1)
            if found:
                tmpl_id = found[0]["id"]
                self.odoo.write("product.template", [tmpl_id], vals, p["name"])
            else:
                tmpl_id = self.odoo.create("product.template", dict(
                    vals, name=p["name"], image_1920=b64(image),
                    attribute_line_ids=[[0, 0, {"attribute_id": attr_id,
                                                "value_ids": [[6, 0, list(values.values())]]}]],
                ), p["name"])
            if not tmpl_id:
                continue
            for ptav in self.odoo.read("product.template.attribute.value",
                                       [["product_tmpl_id", "=", tmpl_id],
                                        ["attribute_id", "=", attr_id]],
                                       ["name", "price_extra"]):
                fmt = ptav["name"].split()[0]
                extra = round(prices[fmt] - base, 2)
                if abs(ptav["price_extra"] - extra) > 0.001:
                    self.odoo.write("product.template.attribute.value", [ptav["id"]],
                                    {"price_extra": extra}, "%s %s +%.2f" % (p["name"], ptav["name"], extra))

    # ----------------------------------------------------------------- verify
    def step_verify(self):
        ok = True
        for url in ["/", "/nos-produits", "/distributeurs", "/about-us", "/contactus", "/shop"]:
            try:
                with urllib.request.urlopen(self.odoo.url + url, timeout=60) as resp:
                    html = resp.read().decode("utf-8", "replace")
                    status = resp.status
            except urllib.error.HTTPError as e:
                html, status = "", e.code
            custom = "tc-footer" in html
            print("  %-15s HTTP %s %s" % (url, status, "ok" if custom else "← pied de page ThéCol absent"))
            ok &= status == 200 and custom
            if url == "/":
                css = re.search(r'href="(/web/assets/[^"]*web\.assets_frontend[^"]*\.css)"', html)
                if css:
                    with urllib.request.urlopen(self.odoo.url + css.group(1), timeout=60) as resp:
                        bundle = resp.read().decode("utf-8", "replace")
                    compiled = ".tc-hero" in bundle
                    print("  bundle CSS     %s" % ("ok (.tc-hero présent)" if compiled
                                                   else "← styles ThéCol absents : erreur de compilation ?"))
                    ok &= compiled
        print("Vérification : %s" % ("OK" if ok else "à contrôler"))


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--url", default=os.environ.get("ODOO_URL", DEFAULT_URL))
    ap.add_argument("--steps", default=",".join(STEPS), help="parmi : " + ",".join(STEPS))
    ap.add_argument("--dry-run", action="store_true", help="lecture seule")
    ap.add_argument("--production", action="store_true",
                    help="autorise une URL qui n'est pas une base de test")
    args = ap.parse_args()

    if "test" not in args.url and not args.production:
        sys.exit("%s ne ressemble pas à une base de test : ajouter --production." % args.url)
    key = os.environ.get("ODOO_API_KEY") or (KEY_FILE.read_text().strip() if KEY_FILE.exists() else "")
    if not key:
        sys.exit("Clé API absente : variable ODOO_API_KEY ou fichier %s" % KEY_FILE.name)
    steps = [s.strip() for s in args.steps.split(",") if s.strip()]
    unknown = set(steps) - set(STEPS)
    if unknown:
        sys.exit("Étapes inconnues : %s" % ", ".join(sorted(unknown)))

    odoo = Odoo(args.url, key, args.dry_run)
    try:
        dep = Deployer(odoo)
        for step in STEPS:
            if step in steps:
                print("== %s" % step)
                getattr(dep, "step_" + step)()
    except OdooError as e:
        sys.exit("Erreur Odoo : %s" % e)


if __name__ == "__main__":
    main()
