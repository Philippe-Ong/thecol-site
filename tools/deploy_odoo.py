#!/usr/bin/env python3
"""Déploie le dossier odoo/ sur une base Odoo (API JSON-2, Odoo 19+).

Remplace les collages manuels décrits dans odoo/README.md :

  assets    images, polices et montagne.svg → médiathèque Odoo (publics),
            les URL GitHub Pages sont réécrites vers /web/image|content/...
  styles    odoo/*.scss concaténés → user_custom_rules.scss
  scripts   odoo/*.js concaténés → user_custom_javascript.js
  pages     /, /contactus, /about-us, /nos-produits, /distributeurs (+ SEO)
  footer    contenu du pied de page (odoo/pied-de-page.xml)
  header    logo du site, bloc téléphone de démonstration masqué
  site      nom du site et de la société, titres et traductions des pages
            d'Odoo (boutique, panier, connexion…), CGV de /terms, /privacy
  menus     menu principal
  products  5 saveurs à variantes « Format » 25/50/100 cl (tools/products.json)
  livraison modes de livraison des CGV : La Poste (paliers selon le montant),
            par nos soins à Fribourg et lors de la tournée VD/GE/VS/NE/JU ;
            canton obligatoire dans les adresses en Suisse
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
import html
import json
import mimetypes
import os
import re
import sys
import unicodedata
import urllib.error
import urllib.parse
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
PRODUCT_REF = re.compile(r"tc-produit:(\w+)")  # lien vers une fiche produit, clé de products.json

# Ordre de collage de odoo/README.md
SCSS_FILES = ["thecol.scss", "distributeurs.scss", "produits.scss", "contact.scss",
              "a-propos.scss", "entete-pied.scss", "boutique.scss", "fiche-produit.scss",
              "pages-odoo.scss"]
JS_FILES = ["distributeurs.js", "prix-formats.js", "fiches-saveurs.js"]
SCSS_URL = "/website/static/src/scss/user_custom_rules.scss"
JS_URL = "/website/static/src/js/user_custom_javascript.js"
BUNDLE = "web.assets_frontend"
PALETTE_URL = "/website/static/src/scss/options/colors/user_color_palette.scss"
THEME_COLORS = {"o-color-1": "#1b8347", "o-color-2": "#14613a"}  # primaire, secondaire

# Pages créées par le script : url → (clé de vue, nom, fichier, page statique pour le SEO)
NEW_PAGES = [
    ("/nos-produits", "website.nos-produits", "Nos produits", "produits.xml", "produits.html"),
    ("/distributeurs", "website.distributeurs", "Points de vente", "distributeurs.xml", "points-de-vente.html"),
    ("/about-us", "website.about-us", "À propos", "a-propos.xml", "a-propos.html"),
]
SEO_EXISTING = [("website.homepage", "index.html"), ("website.contactus", "contact.html")]

MENU = [("Accueil", "/"), ("Nos produits", "/nos-produits"),
        ("Points de vente", "/distributeurs"), ("À propos", "/about-us")]
MENU_REMOVED = ["/shop"]  # « Boutique » : on commande depuis Nos produits → fiche produit

FORMAT_VALUES = ["25", "50", "100"]  # clés de tools/products.json → « 25 cl »…
TAX_RATE = 2.6  # TVA réduite, boissons sans alcool ; prix de products.json TTC
LOGO_FILE = "assets/web/logo-header.png"
HEADER_HIDDEN_VIEWS = ["website.header_text_element"]

# Étape « site ». Le nom du site suit chaque titre d'onglet (« Panier | ThéCol ») ;
# celui de la société, le « Copyright © » du pied de page et les e-mails de commande.
SITE_NAME = "ThéCol"
COMPANY_NAME = "ThéCol Sàrl"
# Nom de société donné par Odoo à la création de la base (« thecol-test ») : seul
# ce cas est renommé, un nom déjà saisi à la main est conservé.
COMPANY_PLACEHOLDER = re.compile(r"^[a-z0-9_-]+$")
# Pages rendues par un gabarit d'Odoo : sans titre SEO, l'onglet affiche le nom
# interne (anglais) du gabarit, « Products », « Shopping Cart », « Login »…
VIEW_SEO = {
    "website_sale.products": ("Boutique en ligne — ThéCol | Thés froids artisanaux suisses",
                              "Commandez en ligne les thés froids artisanaux ThéCol : Hibiscus, Mûres "
                              "sauvages, Fleur de Sureau, Herbes des Alpes et Poire à Botzi, en 25, 50 ou 100 cl."),
    "website_sale.cart": ("Panier — ThéCol", None),
    "website_sale.address": ("Commande : adresse — ThéCol", None),
    "website_sale.payment": ("Commande : paiement — ThéCol", None),
    "website_sale.confirmation": ("Commande confirmée — ThéCol", None),
    "web.login": ("Connexion — ThéCol", None),
    "auth_signup.signup": ("Créer un compte — ThéCol", None),
    "auth_signup.reset_password": ("Mot de passe oublié — ThéCol", None),
    "http_routing.404": ("Page introuvable — ThéCol", None),
    "website.page_404": ("Page introuvable — ThéCol", None),
    "website.list_hybrid": ("Résultats de recherche — ThéCol", None),
    "account.account_terms_conditions_page": (
        "Conditions générales de vente — ThéCol",
        "Conditions générales de vente de la boutique en ligne ThéCol : prix, disponibilité, "
        "paiement, livraison, retours et protection des données."),
}
# Termes qu'Odoo 20 ne traduit pas encore en français (constatés sur le site)
TRANSLATIONS = {
    "portal.address_form_fields": {"Name": "Nom", "Company": "Société", "City...": "Ville…"},
    "website.website_search_box_input": {"Search...": "Rechercher…"},
    "website_sale.products": {"Grid": "Grille",
                              "Try to refine your search criteria.": "Essayez d'affiner vos critères de recherche."},
    "website_sale.total": {"Paid": "Payé"},
    "website.layout": {"breadcrumb": "Fil d'Ariane"},
}
UNPUBLISHED_PAGES = ["/privacy"]  # page vide créée par Odoo ; les CGV ont une section « Protection des données »

# Étape « livraison » : les modes décrits dans les CGV (contact.xml, « Livraison et transport »).
# Envoi postal : (commande TTC inférieure à, participation TTC), None = au-delà du dernier palier.
# PALIERS PROVISOIRES (13.11.2026) : à remplacer par les tarifs réels, puis --steps livraison.
POSTAL_TIERS = [(30, 9.00), (60, 12.00), (100, 15.00), (None, 0.00)]
# (référence du produit de livraison, qui sert à retrouver le mode ; nom ; cantons, [] = toute
# la Suisse ; prix fixe, None = paliers POSTAL_TIERS ; texte affiché au client sous le nom)
CARRIERS = [
    ("LIV-POSTE", "Envoi postal (La Poste)", [], None,
     "Expédition par La Poste sous 3 à 5 jours environ."),
    ("LIV-FRIBOURG", "Livraison par nos soins (canton de Fribourg)", ["FR"], 0.0,
     "Nous livrons nous-mêmes votre commande sous 3 à 5 jours environ."),
    ("LIV-TOURNEE", "Livraison par nos soins (tournée régionale)", ["VD", "GE", "VS", "NE", "JU"], 0.0,
     "Vaud, Genève, Valais, Neuchâtel et Jura : nous livrons votre commande lors de notre "
     "prochaine tournée chez nos distributeurs de la région, sous 30 jours au maximum."),
]
SHIPPING_COUNTRY = "CH"
# Mode créé par Odoo (gratuit, tous pays) : retiré du site, gardé pour les commandes saisies au bureau.
CARRIERS_UNPUBLISHED = ["delivery.free_delivery_carrier"]
# Odoo a chaque canton en plusieurs fiches, une par langue : « Freiburg » (code FR),
# « Fribourg » (FR-FR), « Friburgo » (FR-IT). Le client choisit l'une d'elles dans le
# formulaire d'adresse : un mode limité à des cantons les vise toutes.
STEPS = ["assets", "styles", "scripts", "pages", "footer", "header", "site", "menus", "products",
         "livraison", "verify"]


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


def same_xml(a, b):
    """Odoo réenregistre <div></div> en <div/> et &#160; en espace insécable :
    on compare la forme canonique, espaces regroupés."""
    canon = lambda s: re.sub(r"\s+", " ", ET.canonicalize(s.strip()))
    try:
        return canon(a) == canon(b)
    except ET.ParseError:
        return a.strip() == b.strip()


PRICES_LINE = re.compile(r"^(\s*var PRICES = ).*;$", re.M)


def format_prices_json():
    """Table des prix par format pour prix-formats.js, d'après tools/products.json."""
    catalog = json.loads((ROOT / "tools" / "products.json").read_text(encoding="utf-8"))
    strip = lambda s: "".join(c for c in unicodedata.normalize("NFD", s.lower())
                              if not unicodedata.combining(c)).strip()
    return json.dumps({strip(p["name"]): {"%s cl" % f: float(p["formats"][f]) for f in FORMAT_VALUES}
                       for p in catalog.values()}, ensure_ascii=False)


def static_meta(html_file):
    """<title> et meta description d'une page du site statique."""
    html = (ROOT / html_file).read_text(encoding="utf-8")
    title = re.search(r"<title>(.*?)</title>", html, re.S)
    desc = re.search(r'<meta name="description" content="([^"]*)"', html)
    unescape = lambda s: s.replace("&amp;", "&").replace("&#39;", "'").replace("&quot;", '"').strip()
    return (unescape(title.group(1)) if title else None,
            unescape(desc.group(1)) if desc else None)


RULE_KEYS = ["variable", "operator", "max_value", "list_base_price", "list_price"]


def postal_rules():
    """Règles de prix d'Odoo d'après POSTAL_TIERS (la première règle vérifiée donne le prix)."""
    if len(POSTAL_TIERS) < 2 or POSTAL_TIERS[-1][0] is not None:
        raise SystemExit("POSTAL_TIERS : au moins un palier, puis (None, prix) pour la suite")
    rules = []
    for seq, (limit, fee) in enumerate(POSTAL_TIERS, start=1):
        op, value = ("<", limit) if limit is not None else (">=", POSTAL_TIERS[-2][0])
        rules.append({"sequence": seq * 10, "variable": "price", "operator": op,
                      "max_value": float(value), "list_base_price": float(fee), "list_price": 0.0})
    return rules


def postal_text():
    """Fin du texte affiché sous « Envoi postal » au moment de choisir la livraison."""
    text = " Participation aux frais selon le montant de la commande"
    if POSTAL_TIERS[-1][1] == 0:
        text += ", offerte dès CHF %g" % POSTAL_TIERS[-2][0]
    return text + "."


def changes(record, vals):
    """Valeurs de vals qui diffèrent de record (lu par search_read)."""
    out = {}
    for k, v in vals.items():
        cur = record.get(k)
        if isinstance(v, list):  # many2many écrit en [[6, 0, ids]]
            same = set(cur or []) == set(v[0][2])
        elif isinstance(cur, list):  # many2one lu en [id, nom]
            same = cur[0] == v
        elif isinstance(v, float):
            same = abs((cur or 0.0) - v) < 0.001
        else:
            same = (cur or False) == (v or False)
        if not same:
            out[k] = v
    return out


def cgv_terms_html():
    """CGV de la page /terms, tirées de la section id="cgv" de odoo/contact.xml.

    Une seule source pour les deux pages : les accordéons <details> deviennent
    des titres <h2> suivis de leurs paragraphes.
    """
    m = re.search(r'<section\b[^>]*\bid="cgv".*?</section>', read_text("contact.xml"), re.S)
    if not m:
        raise SystemExit('contact.xml : section id="cgv" introuvable')
    section = ET.fromstring(m.group(0))
    inner = lambda el: (el.text or "") + "".join(ET.tostring(c, encoding="unicode") for c in el)
    overline = section.find(".//*[@class='tc-overline']")
    title = section.find(".//h2")
    lead = section.find(".//*[@class='tc-lead']")
    parts = ['<div class="tc-terms">']
    if overline is not None:
        parts.append('<p class="tc-terms-overline">%s</p>' % html.escape(overline.text.strip()))
    parts.append("<h1>%s</h1>" % html.escape(title.text.strip()))
    if lead is not None:
        parts.append('<p class="tc-terms-lead">%s</p>' % inner(lead).strip())
    for det in section.iter("details"):
        summary = det.find("summary")
        parts.append("<h2>%s</h2>" % html.escape((summary.text or "").strip()))
        body = det.find("div")
        parts.extend(ET.tostring(p, encoding="unicode").strip() for p in body)
    parts.append("</div>")
    return "\n".join(parts)


class Deployer:
    def __init__(self, odoo):
        self.odoo = odoo
        self.asset_urls = {}
        self.product_urls = {}
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
        text = GH_REF.sub(lambda m: self.asset_urls[m.group(1)], text)
        return PRODUCT_REF.sub(lambda m: self.product_url(m.group(1)), text)

    def product_url(self, pid):
        """URL de la fiche produit (« tc-produit:hibiscus » dans les XML).

        L'URL contient l'id Odoo (/shop/hibiscus-3), différent d'une base à
        l'autre : elle est donc lue dans la base au moment du déploiement.
        """
        if pid not in self.product_urls:
            catalog = json.loads((ROOT / "tools" / "products.json").read_text(encoding="utf-8"))
            if pid not in catalog:
                raise SystemExit("tc-produit:%s : clé absente de tools/products.json" % pid)
            name = catalog[pid]["name"]
            found = self.odoo.read("product.template", [["name", "=", name]], ["website_url"], limit=1)
            if found:
                self.product_urls[pid] = found[0]["website_url"]
            else:  # base neuve : l'étape products n'a pas encore créé le produit
                print("  ⚠ produit « %s » introuvable : lien vers la recherche, "
                      "relancer --steps pages après products" % name)
                self.product_urls[pid] = "/shop?search=" + urllib.parse.quote(name)
        return self.product_urls[pid]

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
        # Couleurs du thème (comme Site → Thème → Couleurs) : tous les btn-primary
        # d'Odoo (« Ajouter au panier », formulaires…) passent du violet au vert.
        if self.odoo.dry_run:
            print("  [dry-run] palette du thème : %s" % THEME_COLORS)
            return
        self.odoo.call("website.assets", "make_scss_customization", url=PALETTE_URL, values=THEME_COLORS)
        print("  palette du thème : %s" % THEME_COLORS)

    def step_scripts(self):
        content = self.concat(JS_FILES, "/* ===== odoo/%s (tools/deploy_odoo.py) ===== */\n")
        content, n = PRICES_LINE.subn(lambda m: m.group(1) + format_prices_json() + ";", content)
        if n != 1:
            raise SystemExit("prix-formats.js : ligne « var PRICES = … ; » introuvable")
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
        if same_xml(view["arch"], arch):
            print("  inchangé : %s" % label)
            return
        self.backup(label, view["arch"])
        # En anglais (langue source) : les autres langues sont recalculées terme à terme
        # à partir de cette version, comme pour une modification dans l'éditeur.
        self.odoo.write("ir.ui.view", [view["id"]], {"arch": arch}, label,
                        context={"lang": "en_US"})
        # Pour un terme à peine modifié (« CHF 3.00 » → « CHF 3,00 », « Barrage 14 » →
        # « Barrage 21 »), Odoo garde l'ancienne traduction : la langue du site, que voient
        # les visiteurs, reçoit donc aussi le nouveau texte.
        if self.lang != "en_US":
            self.odoo.write("ir.ui.view", [view["id"]], {"arch": arch}, "%s (%s)" % (label, self.lang),
                            context={"lang": self.lang})

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

    def step_header(self):
        logo = (ROOT / LOGO_FILE).read_bytes()
        sha1 = hashlib.sha1(logo).hexdigest()
        site = self.odoo.read("website", [["id", "=", self.website_id]], ["logo"])[0]
        current = site["logo"]
        if isinstance(current, dict):  # Odoo 20 : binaire renvoyé en {"content": base64}
            current = current.get("content")
        if not isinstance(current, str) or hashlib.sha1(base64.b64decode(current)).hexdigest() != sha1:
            self.odoo.write("website", [self.website_id], {"logo": b64(logo)}, "logo " + LOGO_FILE)
        # Bloc « Texte » de l'en-tête (faux numéro +1 555…) : le site statique n'en a pas.
        # Écrit avec website_id dans le contexte → copie propre au site, la vue générique reste.
        for key in HEADER_HIDDEN_VIEWS:
            view = self.find_view(key)
            if view and view["active"]:
                self.odoo.write("ir.ui.view", [view["id"]], {"active": False}, "masquer " + key)

    # ------------------------------------------------------------------- site
    def step_site(self):
        # Hors contexte du site : sinon Odoo copierait chaque gabarit générique
        # pour le site (COW) et la copie ne suivrait plus les mises à jour d'Odoo.
        generic = {"website_id": False}

        site = self.odoo.read("website", [["id", "=", self.website_id]], ["name", "company_id"])[0]
        if site["name"] != SITE_NAME:
            self.odoo.write("website", [self.website_id], {"name": SITE_NAME}, "nom du site → " + SITE_NAME)
        company = self.odoo.read("res.company", [["id", "=", site["company_id"][0]]],
                                 ["name", "terms_type", "invoice_terms_html"])[0]
        if COMPANY_PLACEHOLDER.match(company["name"]):
            self.odoo.write("res.company", [company["id"]], {"name": COMPANY_NAME},
                            "société « %s » → %s" % (company["name"], COMPANY_NAME))
        elif company["name"] != COMPANY_NAME:
            print("  société « %s » conservée (nom déjà saisi)" % company["name"])

        for key, (title, desc) in VIEW_SEO.items():
            for view in self.odoo.read("ir.ui.view", [["key", "=", key]],
                                       ["website_meta_title", "website_meta_description"],
                                       context={"active_test": False}):
                vals = {"website_meta_title": title}
                if desc:
                    vals["website_meta_description"] = desc
                if any(view[k] != v for k, v in vals.items()):
                    self.odoo.write("ir.ui.view", [view["id"]], vals, "titre " + key, context=generic)

        for key, terms in TRANSLATIONS.items():
            for view in self.odoo.read("ir.ui.view", [["key", "=", key]], ["id"],
                                       context={"active_test": False}):
                current = self.odoo.call("ir.ui.view", "get_field_translations", ids=[view["id"]],
                                         field_name="arch_db", langs=[self.lang])
                rows = current[0] if current and isinstance(current[0], list) else current
                done = {r["source"]: r["value"] for r in rows}
                todo = {src: dst for src, dst in terms.items() if src in done and done[src] != dst}
                if not todo:
                    continue
                if self.odoo.dry_run:
                    print("  [dry-run] traduire %s : %s" % (key, ", ".join(todo)))
                    continue
                self.odoo.call("ir.ui.view", "update_field_translations", ids=[view["id"]],
                               field_name="arch_db", translations={self.lang: todo}, context=generic)
                print("  traduit %s : %s" % (key, ", ".join("%s → %s" % kv for kv in todo.items())))

        for url in UNPUBLISHED_PAGES:
            for page in self.odoo.read("website.page", [["url", "=", url],
                                                        ["website_id", "in", [self.website_id, False]]],
                                       ["is_published"]):
                if page["is_published"]:
                    self.odoo.write("website.page", [page["id"]], {"is_published": False},
                                    "dépublier " + url, context=generic)

        # /terms affiche les « Conditions générales » de la société (Comptabilité →
        # Paramètres) : texte d'exemple d'Odoo (« My Company », droit américain) remplacé.
        if company["terms_type"] != "html":
            print("  /terms désactivée (conditions générales en texte simple) : rien à faire")
            return
        terms = cgv_terms_html()
        flat = lambda s: " ".join(html.unescape(re.sub(r"<[^>]+>", " ", s or "")).split())
        if flat(company["invoice_terms_html"]) != flat(terms):
            self.odoo.write("res.company", [company["id"]], {"invoice_terms_html": terms},
                            "CGV de /terms (depuis contact.xml)")

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
        for url in MENU_REMOVED:
            menu = by_url.get(url)
            if not menu:
                continue
            if self.odoo.dry_run:
                print("  [dry-run] supprimer website.menu #%s : %s" % (menu["id"], menu["name"]))
            else:
                self.odoo.call("website.menu", "unlink", ids=[menu["id"]])
                print("  supprimé website.menu #%s : %s" % (menu["id"], menu["name"]))

    # --------------------------------------------------------------- products
    def sale_tax_id(self):
        """TVA suisse à taux réduit (boissons sans alcool), prix catalogue TTC.

        La localisation CH ne fournit que « 2.6% » hors taxe : on la copie
        (lignes de répartition et grille de TVA comprises) en version TTC, sans
        toucher à l'originale qui peut servir aux factures hors taxe.
        """
        base = [["type_tax_use", "=", "sale"], ["amount_type", "=", "percent"], ["amount", "=", TAX_RATE]]
        found = self.odoo.read("account.tax", base + [["price_include_override", "=", "tax_included"]],
                               ["name"], limit=1)
        if found:
            return found[0]["id"]
        src = self.odoo.read("account.tax", base, ["name"], limit=1, order="id")
        if not src:
            raise SystemExit("Taxe de vente %s %% introuvable (localisation suisse installée ?)" % TAX_RATE)
        name = "%s%% TTC" % TAX_RATE
        if self.odoo.dry_run:
            print("  [dry-run] copier la taxe « %s » en « %s »" % (src[0]["name"], name))
            return None
        new_id = self.odoo.call("account.tax", "copy", ids=[src[0]["id"]], default={
            "name": name, "price_include_override": "tax_included"})[0]
        print("  créé account.tax #%s : %s" % (new_id, name))
        return new_id

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

        tax_id = self.sale_tax_id()
        for seq, (pid, p) in enumerate(catalog.items(), start=1):
            prices = {f: float(p["formats"][f]) for f in FORMAT_VALUES}
            base = prices[FORMAT_VALUES[0]]
            title, desc = static_meta(p["page"])
            image = (ROOT / "assets" / "web" / ("produit-%s.jpg" % pid)).read_bytes()
            vals = {
                "list_price": base,
                "taxes_id": [[6, 0, [tax_id] if tax_id else []]],
                "sale_ok": True,
                "is_published": True,
                "website_sequence": seq * 10,
                "website_meta_title": title,  # sinon « Hibiscus | <nom du site> »
                "website_meta_description": desc,
            }
            found = self.odoo.read("product.template", [["name", "=", p["name"]]],
                                   ["description_ecommerce"], limit=1)
            if found:
                tmpl_id = found[0]["id"]
                # « Description ecommerce » : réservée aux ingrédients / valeurs nutritives
                # saisis dans Odoo. On n'y met plus la meta description (doublon du bloc
                # de fiches-saveurs.js) et on retire celle qu'une version précédente y avait mise.
                flat = lambda s: " ".join(html.unescape(re.sub(r"<[^>]+>", "", s or "")).split())
                if desc and flat(found[0]["description_ecommerce"]) == flat(desc):
                    vals["description_ecommerce"] = False
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

    # -------------------------------------------------------------- livraison
    def ref(self, xmlid):
        """Id d'un enregistrement d'Odoo d'après son identifiant XML (module.nom)."""
        module, name = xmlid.split(".", 1)
        found = self.odoo.read("ir.model.data", [["module", "=", module], ["name", "=", name]],
                               ["res_id"], limit=1)
        return found[0]["res_id"] if found else None

    def step_livraison(self):
        country = self.odoo.read("res.country", [["code", "=", SHIPPING_COUNTRY]], ["state_required"], limit=1)[0]
        states = {}  # « FR » → ids des fiches Freiburg, Fribourg, Friburgo
        for s in self.odoo.read("res.country.state", [["country_id", "=", country["id"]]], ["code"]):
            states.setdefault(s["code"].split("-")[0], []).append(s["id"])
        # Sans canton dans l'adresse, seul l'envoi postal serait proposé (CGV : options « basées
        # sur le canton sélectionné »), même à un client de Fribourg.
        if not country["state_required"]:
            self.odoo.write("res.country", [country["id"]], {"state_required": True},
                            "canton obligatoire dans les adresses en Suisse")

        # Frais de port : prestation accessoire, même TVA que les thés (2,6 %, montants TTC).
        tax_id = self.sale_tax_id()
        categ_id = self.ref("delivery.product_category_deliveries")
        for seq, (code, name, cantons, price, text) in enumerate(CARRIERS, start=1):
            unknown = [c for c in cantons if c not in states]
            if unknown:
                raise SystemExit("Cantons inconnus dans la base : %s" % ", ".join(unknown))
            if price is None:
                text += postal_text()
            product = {"name": name, "type": "service", "sale_ok": False, "list_price": price or 0.0,
                       "taxes_id": [[6, 0, [tax_id] if tax_id else []]],
                       "description_sale": text}  # affiché sous le nom du mode au moment de commander
            if categ_id:
                product["categ_id"] = categ_id
            carrier = {"name": name, "sequence": seq * 10,
                       "delivery_type": "base_on_rule" if price is None else "fixed",
                       "country_ids": [[6, 0, [country["id"]]]],
                       "state_ids": [[6, 0, [i for c in cantons for i in states[c]]]],
                       "is_published": True, "active": True}
            found = self.odoo.read("delivery.carrier", [["product_id.default_code", "=", code]],
                                   list(carrier) + ["product_id"], limit=1, context={"active_test": False})
            if not found:
                product_id = self.odoo.create("product.product", dict(
                    product, default_code=code, purchase_ok=False, invoice_policy="order"),
                    "produit de livraison " + code)
                if price is None:
                    carrier["price_rule_ids"] = [[0, 0, r] for r in postal_rules()]
                self.odoo.create("delivery.carrier", dict(carrier, product_id=product_id), name)
                continue
            carrier_id, product_id = found[0]["id"], found[0]["product_id"][0]
            current = self.odoo.read("product.product", [["id", "=", product_id]], list(product),
                                     context={"active_test": False})[0]
            diff = changes(current, product)
            if diff:
                self.odoo.write("product.product", [product_id], diff, "%s : %s" % (code, ", ".join(diff)))
            diff = changes(found[0], carrier)
            if diff:
                self.odoo.write("delivery.carrier", [carrier_id], diff, "%s : %s" % (name, ", ".join(diff)))
            if price is None:
                rules = self.odoo.read("delivery.price.rule", [["carrier_id", "=", carrier_id]], RULE_KEYS,
                                       order="sequence, id")
                key = lambda r: tuple(round(r[k], 2) if isinstance(r[k], float) else r[k] for k in RULE_KEYS)
                if [key(r) for r in rules] != [key(r) for r in postal_rules()]:
                    self.odoo.write("delivery.carrier", [carrier_id], {"price_rule_ids": [[5, 0, 0]] + [
                        [0, 0, r] for r in postal_rules()]}, "%s : paliers" % name)
        print("  envoi postal : %s" % ", ".join(
            ("moins de %g → %.2f" % (limit, fee)) if limit else ("dès %g → %.2f" % (POSTAL_TIERS[-2][0], fee))
            for limit, fee in POSTAL_TIERS))

        for xmlid in CARRIERS_UNPUBLISHED:
            carrier_id = self.ref(xmlid)
            if not carrier_id:
                print("  ⚠ %s introuvable : vérifier à la main les modes publiés" % xmlid)
            found = carrier_id and self.odoo.read("delivery.carrier", [["id", "=", carrier_id]],
                                                  ["name", "is_published"], context={"active_test": False})
            if found and found[0]["is_published"]:
                self.odoo.write("delivery.carrier", [carrier_id], {"is_published": False},
                                "retirer du site « %s »" % found[0]["name"])

    # ----------------------------------------------------------------- verify
    def step_verify(self):
        ok = True
        for url in ["/", "/nos-produits", "/distributeurs", "/about-us", "/contactus", "/shop"]:
            try:
                with urllib.request.urlopen(self.odoo.url + url, timeout=60) as resp:
                    page = resp.read().decode("utf-8", "replace")
                    status = resp.status
            except urllib.error.HTTPError as e:
                page, status = "", e.code
            custom = "tc-footer" in page
            print("  %-15s HTTP %s %s" % (url, status, "ok" if custom else "← pied de page ThéCol absent"))
            ok &= status == 200 and custom
            if url == "/":
                css = re.search(r'href="(/web/assets/[^"]*web\.assets_frontend[^"]*\.css)"', page)
                if css:
                    with urllib.request.urlopen(self.odoo.url + css.group(1), timeout=60) as resp:
                        bundle = resp.read().decode("utf-8", "replace")
                    compiled = ".tc-hero" in bundle
                    print("  bundle CSS     %s" % ("ok (.tc-hero présent)" if compiled
                                                   else "← styles ThéCol absents : erreur de compilation ?"))
                    ok &= compiled
        # Pages d'Odoo : titre ThéCol (pas le nom du gabarit) et vraies CGV
        for url in ["/shop", "/shop/cart", "/web/login", "/terms"]:
            try:
                with urllib.request.urlopen(self.odoo.url + url, timeout=60) as resp:
                    page = resp.read().decode("utf-8", "replace")
            except urllib.error.HTTPError as e:
                page = e.read().decode("utf-8", "replace")
            title = re.search(r"<title>(.*?)</title>", page, re.S)
            title = html.unescape(title.group(1).strip()) if title else ""
            good = SITE_NAME in title and (url != "/terms" or "My Company" not in page)
            print("  %-15s %s" % (url, "ok (%s)" % title if good else "← titre ou contenu à contrôler : %s" % title))
            ok &= good
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
