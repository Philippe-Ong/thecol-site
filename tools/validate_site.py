#!/usr/bin/env python3
"""Valide le site statique ThéCol depuis la racine du dépôt.

``tools/products.json`` est l'unique source de vérité explicite du catalogue :
identifiants, noms, pages, images, formats et prix. Le présent script compare les
copies destinées au navigateur (PRODUCTS de main.js et HTML/JSON-LD) à ce fichier.

Le validateur n'utilise que la bibliothèque standard Python. Usage :
    python tools/validate_site.py
"""
from __future__ import annotations

import html
import json
import re
import sys
from collections import Counter
from decimal import Decimal, InvalidOperation
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parent.parent
PRODUCTS_FILE = ROOT / "tools" / "products.json"
EXPECTED_PAGES = (
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
)
OG_FIELDS = ("og:title", "og:description", "og:url", "og:image", "og:type")
TWITTER_FIELDS = (
    "twitter:card",
    "twitter:title",
    "twitter:description",
    "twitter:url",
    "twitter:image",
)
EXTERNAL_SCHEMES = {"http", "https", "mailto", "tel", "data", "javascript"}
FORMAT_KEYS = ("25", "50", "100")


class SiteParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: list[str] = []
        self.h1_count = 0
        self.images: list[dict[str, str]] = []
        self.references: list[tuple[str, str, int]] = []
        self.metas: dict[str, list[str]] = {}
        self.canonicals: list[str] = []
        self.jsonld_texts: list[str] = []
        self._jsonld_parts: list[str] | None = None
        self._line = 1

    def handle_starttag(self, tag: str, attrs_list: list[tuple[str, str | None]]) -> None:
        attrs = {key.lower(): value or "" for key, value in attrs_list}
        self._line = self.getpos()[0]
        if attrs.get("id"):
            self.ids.append(attrs["id"])
        if tag.lower() == "h1":
            self.h1_count += 1
        if tag.lower() == "img":
            self.images.append(attrs)
        for attr in ("href", "src"):
            if attrs.get(attr):
                self.references.append((attr, attrs[attr], self._line))
        if attrs.get("srcset"):
            for candidate in parse_srcset(attrs["srcset"]):
                self.references.append(("srcset", candidate, self._line))
        if tag.lower() == "meta":
            key = attrs.get("property") or attrs.get("name")
            if key:
                self.metas.setdefault(key.lower(), []).append(attrs.get("content", "").strip())
        if tag.lower() == "link" and "canonical" in attrs.get("rel", "").lower().split():
            self.canonicals.append(attrs.get("href", "").strip())
        if tag.lower() == "script" and attrs.get("type", "").lower() == "application/ld+json":
            self._jsonld_parts = []

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)

    def handle_data(self, data: str) -> None:
        if self._jsonld_parts is not None:
            self._jsonld_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "script" and self._jsonld_parts is not None:
            self.jsonld_texts.append("".join(self._jsonld_parts).strip())
            self._jsonld_parts = None


def parse_srcset(value: str) -> list[str]:
    candidates = []
    for part in value.split(","):
        item = part.strip()
        if item:
            candidates.append(item.split()[0])
    return candidates


def add_error(errors: list[str], page: str, message: str) -> None:
    errors.append(f"{page}: {message}")


def decimal_value(value: object) -> Decimal | None:
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def schema_types(value: object) -> set[str]:
    if isinstance(value, str):
        return {value}
    if isinstance(value, list):
        return {item for item in value if isinstance(item, str)}
    return set()


def schema_nodes(value: object):
    if isinstance(value, dict):
        yield value
        graph = value.get("@graph")
        if isinstance(graph, list):
            for item in graph:
                yield from schema_nodes(item)
    elif isinstance(value, list):
        for item in value:
            yield from schema_nodes(item)


def is_absolute_http_url(value: str) -> bool:
    parsed = urlsplit(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def local_target(page_path: Path, reference: str) -> Path | None:
    value = html.unescape(reference.strip())
    if not value or value.startswith("#") or value.startswith("//"):
        return None
    parsed = urlsplit(value)
    if parsed.scheme.lower() in EXTERNAL_SCHEMES or parsed.netloc:
        return None
    path = unquote(parsed.path).replace("\\", "/")
    if not path:
        return None
    if path.startswith("/"):
        relative = PurePosixPath(path.lstrip("/"))
        parts = relative.parts
        if parts and parts[0] == "thecol-site":
            relative = PurePosixPath(*parts[1:])
        return ROOT.joinpath(*relative.parts)
    return page_path.parent.joinpath(*PurePosixPath(path).parts)


def validate_references(page: str, path: Path, parser: SiteParser, errors: list[str]) -> None:
    seen: set[tuple[str, str]] = set()
    for attr, value, line in parser.references:
        key = (attr, value)
        if key in seen:
            continue
        seen.add(key)
        target = local_target(path, value)
        if target is None:
            continue
        try:
            resolved = target.resolve()
            resolved.relative_to(ROOT.resolve())
        except (OSError, ValueError):
            add_error(errors, page, f"ligne {line}: {attr} sort de la racine ({value!r})")
            continue
        if not resolved.exists():
            add_error(errors, page, f"ligne {line}: fichier local introuvable dans {attr}: {value!r}")


def parse_jsonld(page: str, parser: SiteParser, errors: list[str]) -> list[dict[str, object]]:
    nodes: list[dict[str, object]] = []
    for index, text in enumerate(parser.jsonld_texts, 1):
        try:
            document = json.loads(text)
        except json.JSONDecodeError as exc:
            add_error(errors, page, f"JSON-LD #{index} invalide: {exc.msg} (ligne {exc.lineno})")
            continue
        nodes.extend(node for node in schema_nodes(document) if isinstance(node, dict))
    return nodes


def validate_page(page: str, path: Path, parser: SiteParser, errors: list[str]) -> list[dict[str, object]]:
    duplicates = sorted(key for key, count in Counter(parser.ids).items() if count > 1)
    if duplicates:
        add_error(errors, page, "ID dupliqué(s): " + ", ".join(duplicates))
    if parser.h1_count != 1:
        add_error(errors, page, f"exactement un h1 requis, trouvé: {parser.h1_count}")
    for index, attrs in enumerate(parser.images, 1):
        decorative = attrs.get("aria-hidden", "").lower() == "true" or attrs.get("role", "").lower() in {"presentation", "none"}
        if not decorative and not attrs.get("alt", "").strip():
            add_error(errors, page, f"img #{index}: alt non vide requis (ou décoration explicite via aria-hidden/role)")
    if len(parser.canonicals) != 1:
        add_error(errors, page, f"exactement un canonical requis, trouvé: {len(parser.canonicals)}")
    elif not is_absolute_http_url(parser.canonicals[0]):
        add_error(errors, page, f"canonical non absolu: {parser.canonicals[0]!r}")
    for field in OG_FIELDS:
        values = parser.metas.get(field, [])
        if len(values) != 1 or not values[0]:
            add_error(errors, page, f"balise {field} unique et non vide requise")
        elif field in {"og:url", "og:image"} and not is_absolute_http_url(values[0]):
            add_error(errors, page, f"{field} doit être une URL absolue")
    for field in TWITTER_FIELDS:
        values = parser.metas.get(field, [])
        if len(values) != 1 or not values[0]:
            add_error(errors, page, f"balise {field} unique et non vide requise")
        elif field in {"twitter:url", "twitter:image"} and not is_absolute_http_url(values[0]):
            add_error(errors, page, f"{field} doit être une URL absolue")
    validate_references(page, path, parser, errors)
    return parse_jsonld(page, parser, errors)


def validate_required_schema(page: str, nodes: list[dict[str, object]], required: set[str], errors: list[str]) -> None:
    present: set[str] = set()
    for node in nodes:
        present.update(schema_types(node.get("@type")))
    missing = sorted(required - present)
    if missing:
        add_error(errors, page, "type(s) JSON-LD requis absent(s): " + ", ".join(missing))


def parse_products_js(text: str, errors: list[str]) -> dict[str, dict[str, object]]:
    match = re.search(r"\bvar\s+PRODUCTS\s*=\s*\{(?P<body>.*?)\n\s*\};", text, re.S)
    if not match:
        errors.append("js/main.js: objet PRODUCTS introuvable")
        return {}
    result: dict[str, dict[str, object]] = {}
    entry_re = re.compile(
        r"^\s*(?P<id>[A-Za-z0-9_-]+)\s*:\s*\{\s*"
        r'name:\s*"(?P<name>[^"]+)"\s*,\s*'
        r'img:\s*"(?P<img>[^"]+)"\s*,\s*'
        r'page:\s*"(?P<page>[^"]+)"\s*,\s*'
        r"formats:\s*\{(?P<formats>[^}]*)\}\s*\}\s*,?\s*$"
    )
    format_re = re.compile(r"(?P<size>\d+)\s*:\s*(?P<price>\d+(?:\.\d+)?)")
    for line in match.group("body").splitlines():
        if not line.strip():
            continue
        entry = entry_re.match(line)
        if not entry:
            errors.append(f"js/main.js: entrée PRODUCTS non analysable: {line.strip()}")
            continue
        result[entry.group("id")] = {
            "name": entry.group("name"),
            "image": entry.group("img"),
            "page": entry.group("page"),
            "formats": {item.group("size"): Decimal(item.group("price")) for item in format_re.finditer(entry.group("formats"))},
        }
    return result


def validate_products_file(products: object, errors: list[str]) -> dict[str, dict[str, object]]:
    if not isinstance(products, dict) or len(products) != 5:
        errors.append("tools/products.json: exactement 5 produits requis")
        return products if isinstance(products, dict) else {}
    normalized: dict[str, dict[str, object]] = {}
    pages: set[str] = set()
    for product_id, raw in products.items():
        if not isinstance(product_id, str) or not isinstance(raw, dict):
            errors.append("tools/products.json: chaque produit doit être un objet identifié par une chaîne")
            continue
        name, page, image, formats = raw.get("name"), raw.get("page"), raw.get("image"), raw.get("formats")
        if not all(isinstance(value, str) and value.strip() for value in (name, page, image)):
            errors.append(f"tools/products.json: {product_id}: name, page et image non vides requis")
            continue
        if page in pages:
            errors.append(f"tools/products.json: page dupliquée: {page}")
        pages.add(page)
        if not isinstance(formats, dict) or tuple(formats.keys()) != FORMAT_KEYS:
            errors.append(f"tools/products.json: {product_id}: formats attendus dans l'ordre 25, 50, 100")
            continue
        prices = {size: decimal_value(formats[size]) for size in FORMAT_KEYS}
        if any(value is None for value in prices.values()):
            errors.append(f"tools/products.json: {product_id}: prix numériques invalides")
            continue
        expected = {"25": Decimal("3.00"), "50": Decimal("5.00"), "100": Decimal("8.50")}
        if prices != expected:
            errors.append(f"tools/products.json: {product_id}: prix requis 25=3.00 / 50=5.00 / 100=8.50")
        normalized[product_id] = {"name": name, "page": page, "image": image, "formats": prices}
    if "poire" not in normalized:
        errors.append("tools/products.json: produit poire requis")
    return normalized


def validate_js_products(products: dict[str, dict[str, object]], errors: list[str]) -> None:
    js_path = ROOT / "js" / "main.js"
    if not js_path.is_file():
        errors.append("js/main.js: fichier introuvable")
        return
    actual = parse_products_js(js_path.read_text(encoding="utf-8"), errors)
    if set(actual) != set(products):
        errors.append(f"js/main.js: IDs PRODUCTS {sorted(actual)} != products.json {sorted(products)}")
    for product_id in sorted(set(actual) & set(products)):
        for field in ("name", "page", "image"):
            if actual[product_id][field] != products[product_id][field]:
                errors.append(f"js/main.js: PRODUCTS.{product_id}.{field} incohérent avec products.json")
        if actual[product_id]["formats"] != products[product_id]["formats"]:
            errors.append(f"js/main.js: PRODUCTS.{product_id}.formats incohérent avec products.json")


def extract_catalog_prices(text: str) -> dict[str, Decimal]:
    result: dict[str, Decimal] = {}
    pattern = re.compile(
        r'<span\s+class="p"[^>]*>\s*<span\s+class="size"[^>]*>\s*(\d+)\s*cl\s*</span>'
        r'\s*<span\s+class="amount"[^>]*>\s*CHF\s*([0-9]+(?:\.[0-9]+)?)\s*</span>\s*</span>',
        re.I,
    )
    for size, price in pattern.findall(text):
        result[size] = Decimal(price)
    return result


def extract_pill_prices(text: str) -> list[tuple[str, Decimal]]:
    pattern = re.compile(
        r'<label\s+class="format-pill"[^>]*>\s*<input\b[^>]*\bvalue="(\d+)"[^>]*>'
        r'\s*<span>\s*\d+\s*cl\s*<b>\s*CHF\s*([0-9]+(?:\.[0-9]+)?)\s*</b>',
        re.I,
    )
    return [(size, Decimal(price)) for size, price in pattern.findall(text)]


def validate_product_surfaces(
    products: dict[str, dict[str, object]],
    texts: dict[str, str],
    parsers: dict[str, SiteParser],
    jsonld_nodes: dict[str, list[dict[str, object]]],
    errors: list[str],
) -> None:
    catalog_page = "produits.html"
    catalog_prices = extract_catalog_prices(texts.get(catalog_page, ""))
    expected_common = {size: products[next(iter(products))]["formats"][size] for size in FORMAT_KEYS} if products else {}
    if catalog_prices != expected_common:
        add_error(errors, catalog_page, f"bannière prix {catalog_prices} incohérente avec products.json {expected_common}")
    for product_id, product in products.items():
        page = str(product["page"])
        if page not in texts:
            continue
        parser = parsers[page]
        data_product = re.findall(r'<main\b[^>]*\bdata-product="([^"]+)"', texts[page], re.I)
        if data_product != [product_id]:
            add_error(errors, page, f"data-product attendu {product_id!r}, trouvé {data_product}")
        h1 = re.findall(r"<h1\b[^>]*>(.*?)</h1>", texts[page], re.I | re.S)
        h1_text = re.sub(r"<[^>]+>", "", h1[0]).strip() if h1 else ""
        if html.unescape(h1_text) != product["name"]:
            add_error(errors, page, f"nom du h1 incohérent avec products.json: {html.unescape(h1_text)!r}")
        pills = extract_pill_prices(texts[page])
        expected_pills = [(size, product["formats"][size]) for size in FORMAT_KEYS]
        if len(pills) != 3 or pills != expected_pills:
            add_error(errors, page, f"exactement 3 format pills attendues {expected_pills}, trouvé {pills}")
        product_nodes = [node for node in jsonld_nodes[page] if "Product" in schema_types(node.get("@type"))]
        if len(product_nodes) != 1:
            add_error(errors, page, f"exactement un objet JSON-LD Product requis, trouvé: {len(product_nodes)}")
            continue
        node = product_nodes[0]
        accepted_names = {str(product["name"]), "ThéCol " + str(product["name"])}
        if node.get("name") not in accepted_names:
            add_error(errors, page, "JSON-LD Product.name incohérent avec products.json")
        image_value = node.get("image")
        images = image_value if isinstance(image_value, list) else [image_value]
        if not any(isinstance(item, str) and urlsplit(item).path.endswith("/" + str(product["image"])) for item in images):
            add_error(errors, page, "JSON-LD Product.image incohérent avec products.json")
        offers = node.get("offers")
        if isinstance(offers, dict):
            offers = [offers]
        if not isinstance(offers, list) or len(offers) != 3:
            add_error(errors, page, "JSON-LD Product.offers doit contenir exactement 3 offres")
            continue
        actual_offers: dict[str, Decimal] = {}
        for offer in offers:
            if not isinstance(offer, dict) or "Offer" not in schema_types(offer.get("@type")):
                add_error(errors, page, "chaque offre JSON-LD doit être de type Offer")
                continue
            if offer.get("priceCurrency") != "CHF":
                add_error(errors, page, "chaque offre JSON-LD doit utiliser priceCurrency CHF")
            labels = " ".join(str(offer.get(key, "")) for key in ("sku", "name"))
            sizes = re.findall(r"(?<!\d)(25|50|100)(?!\d)", labels)
            price = decimal_value(offer.get("price"))
            if len(set(sizes)) != 1 or price is None:
                add_error(errors, page, f"offre JSON-LD sans format/prix exploitable: {offer}")
                continue
            actual_offers[sizes[0]] = price
        if actual_offers != product["formats"]:
            add_error(errors, page, f"prix/formats JSON-LD {actual_offers} incohérents avec products.json {product['formats']}")
        canonical = parser.canonicals[0] if len(parser.canonicals) == 1 else ""
        if canonical and not urlsplit(canonical).path.endswith("/" + page):
            add_error(errors, page, "canonical ne correspond pas à la page déclarée dans products.json")


def main() -> int:
    errors: list[str] = []
    try:
        raw_products = json.loads(PRODUCTS_FILE.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print("ERREUR tools/products.json: fichier introuvable")
        return 1
    except json.JSONDecodeError as exc:
        print(f"ERREUR tools/products.json: JSON invalide: {exc}")
        return 1
    products = validate_products_file(raw_products, errors)

    expected_set = set(EXPECTED_PAGES)
    actual_set = {path.name for path in ROOT.glob("*.html")}
    for page in sorted(expected_set - actual_set):
        errors.append(f"{page}: page HTML attendue introuvable")
    for page in sorted(actual_set - expected_set):
        errors.append(f"{page}: page HTML inattendue (liste contractuelle = 10 pages)")
    if len(actual_set) != 10:
        errors.append(f"racine: exactement 10 pages HTML requises, trouvé: {len(actual_set)}")

    texts: dict[str, str] = {}
    parsers: dict[str, SiteParser] = {}
    jsonld_by_page: dict[str, list[dict[str, object]]] = {}
    for page in EXPECTED_PAGES:
        path = ROOT / page
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        parser = SiteParser()
        try:
            parser.feed(text)
            parser.close()
        except Exception as exc:
            add_error(errors, page, f"analyse HTML impossible: {exc}")
        texts[page] = text
        parsers[page] = parser
        jsonld_by_page[page] = validate_page(page, path, parser, errors)

    if "index.html" in jsonld_by_page:
        validate_required_schema("index.html", jsonld_by_page["index.html"], {"Organization", "FAQPage"}, errors)
    for product in products.values():
        page = str(product["page"])
        if page in jsonld_by_page:
            validate_required_schema(page, jsonld_by_page[page], {"Product", "BreadcrumbList"}, errors)

    validate_js_products(products, errors)
    validate_product_surfaces(products, texts, parsers, jsonld_by_page, errors)

    checks = (
        "10 pages HTML attendues",
        "liens et fichiers locaux href/src/srcset",
        "IDs, h1 et alt des images",
        "canonical, Open Graph et Twitter",
        "JSON-LD et types Schema.org requis",
        "catalogue/prix cohérents avec tools/products.json",
    )
    print("Validation du site ThéCol")
    print(f"Racine : {ROOT}")
    print(f"Source de vérité produits : {PRODUCTS_FILE.relative_to(ROOT)} ({len(products)} produits)")
    print(f"Pages analysées : {len(parsers)}/{len(EXPECTED_PAGES)}")
    if errors:
        print(f"\nÉCHEC — {len(errors)} erreur(s)")
        for error in errors:
            print(f"ERREUR {error}")
        return 1
    print("\nContrôles réussis :")
    for check in checks:
        print(f"OK {check}")
    print(f"\nSUCCÈS — 0 erreur, {len(parsers)} pages et {len(products)} produits validés.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
