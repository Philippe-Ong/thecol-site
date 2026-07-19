# ThéCol — site statique multi-pages

Refonte statique multi-pages du site de [ThéCol](https://www.thecol.ch), hébergée sur **GitHub Pages**
(branche `main`, déploiement automatique à chaque `git push`).

> **URL temporaire utilisée pour le SEO** (canonical, OG, Twitter, JSON-LD, robots, sitemap) :
> **<https://philippe-ong.github.io/thecol-site/>**
> Avant de migrer vers le domaine définitif, toutes les références absolues pointent ici.

---

## Migrer vers `https://www.thecol.ch/`

Quand le domaine définitif est prêt, remplacer **toutes** les occurrences de l'URL temporaire
par `https://www.thecol.ch` dans les fichiers suivants :

| Fichier | À modifier |
|---|---|
| `index.html`, `produits.html`, `produit-*.html`, `points-de-vente.html`, `a-propos.html`, `contact.html` | `<link rel="canonical">` — `<meta property="og:url">` — `<meta name="twitter:url">` — `<meta property="og:image">` — `<meta name="twitter:image">` — JSON-LD (`"url"`, `"image"`, `"item"` des BreadcrumbList) |
| `robots.txt` | Ligne `Sitemap:` |
| `sitemap.xml` | Tous les `<loc>` |

Procédure recommandée :

1. **Rechercher** `philippe-ong.github.io/thecol-site` dans tout le dépôt.
2. **Remplacer** par `www.thecol.ch`.
3. **Valider** avec :
   ```
   python tools/validate_site.py
   ```
   (le validateur vérifie que les canonical, OG, Twitter et JSON-LD utilisent une URL absolue).

Aucune autre modification n'est nécessaire : tous les liens internes sont relatifs (`href="produits.html"`, etc.).

---

## Pages

| Fichier | Page |
|---|---|
| `index.html` | Accueil — hero, chiffres clés, origines, piliers, gamme, FAQ + JSON-LD (Organization, FAQPage) |
| `produits.html` | Nos produits — catalogue des 5 saveurs, prix, formats |
| `produit-hibiscus.html` etc. | Fiches produit (×5) — galerie, description, sélecteur de format, ajout au panier, JSON-LD (Product, BreadcrumbList) |
| `points-de-vente.html` | Points de vente — 34 distributeurs, recherche + filtre par canton, carte interactive à deux niveaux : carte Suisse complète (pin cluster agrégé pour Fribourg + pins individuels Yverdon/Crissier/Champoussin/Delémont + rectangle de zoom en pointillés) et inset « Canton de Fribourg — zoom ×3 » flottant en bas à droite (empilé sous la carte sur mobile) avec les 23 localités fribourgeoises à leur position réelle ; synchronisation bidirectionnelle carte↔liste sur les deux niveaux |
| `a-propos.html` | À propos — valeurs, fabrication, équipe, chronologie, galerie |
| `contact.html` | Contact — formulaire (mailto), coordonnées, CGV expliquant les deux parcours |

---

## Deux parcours d'achat distincts

Le site propose deux façons de commander, clairement différenciées dans l'UI et les CGV :

### 1. Demande locale par e-mail (sur ce site)

- Le panier vit dans `localStorage` (`js/main.js` : objet `PRODUCTS` + fonctions `cart*`).
- Tiroir latéral ouvert depuis l'icône panier du header, présent sur toutes les pages.
- Le bouton **« Envoyer la demande par e-mail »** compose un mailto: prérempli (articles, totaux,
  champs nom/adresse) vers `commande@thecol.ch` — **aucun paiement n'est encaissé sur ce site**.
- Aucune commande n'est confirmée tant que l'équipe ThéCol n'a pas répondu par retour d'e-mail.

### 2. Achat et paiement en ligne (via Odoo)

- Un lien direct **« Acheter et payer en ligne »** (toujours visible dans le tiroir panier) redirige
  vers la boutique Odoo existante : **<https://www.thecol.ch/shop>**.
- Le paiement en ligne s'effectue par **carte bancaire (Visa, MasterCard) ou PayPal** — c'est le seul
  parcours où un paiement est réellement encaissé.
- Les CGV (`contact.html`) détaillent cette distinction.

> **Important** : les descriptions JSON-LD Product incluent les 3 offres (25/50/100 cl) en CHF,
> mais le site n'est pas une boutique e-commerce au sens transactionnel ; il sert de vitrine et
> de générateur de demande par e-mail.

---

## Produits : source de vérité unique

**`tools/products.json`** est l'unique source de vérité pour le catalogue (5 identifiants, noms,
pages, images, formats et prix). Chaque modification du catalogue (prix, formats, nouveau produit)
doit être répercutée dans **tous** les endroits suivants, faute de quoi le validateur échoue :

| Cible | Ce qui doit être cohérent |
|---|---|
| `tools/products.json` | Identifiants, noms, images, pages, formats, prix |
| `js/main.js` | Tableau `PRODUCTS` (var) — identifiants, noms, images, pages, formats, prix |
| Chaque page `produit-*.html` | `data-product="<id>"` sur `<main>`, `<h1>`, `format-pill` (prix), galerie |
| `produits.html` | Bannière des prix (25/50/100 cl) |
| JSON-LD embarqué dans chaque `produit-*.html` | `Product.name`, `Product.image`, `Product.offers[].price`, `Product.offers[].sku` |

Le validateur (`tools/validate_site.py`) compare automatiquement toutes ces surfaces :
```
python tools/validate_site.py
```

### Cas particulier : Poire à Botzi

Depuis la refonte, la Poire à Botzi est alignée sur les 4 autres saveurs : **3 formats (25, 50, 100 cl)
aux mêmes prix** (CHF 3.00 / 5.00 / 8.50). Plus de dérogation « 50 cl seulement ».

---

## Lancer le site en local

Aucun build ni dépendance requis — le site est du HTML/CSS/JS statique.

```powershell
python -m http.server 8123
```

Ouvrir <http://localhost:8123>. (Ou n'importe quel serveur statique.)

---

## Validation

Le validateur est écrit en **Python standard** (aucune dépendance externe).

```powershell
python tools/validate_site.py
```

Il vérifie :

- Les 10 pages HTML attendues sont présentes
- Liens et fichiers locaux (href/src/srcset) — existants et dans la racine
- IDs uniques, exactement 1 `<h1>` par page, `alt` non vides sur les images
- Balises **canonical**, **Open Graph** (og:title, og:description, og:url, og:image, og:type)
  et **Twitter Cards** (twitter:card, twitter:title, twitter:description, twitter:url, twitter:image)
- **JSON-LD** : syntaxe valide, types requis (Organization, FAQPage, Product, BreadcrumbList)
- **Cohérence des prix** : produits.html, fiches produit, format-pills, JSON-LD Product.offers
- **Cohérence js/main.js** : objet PRODUCTS identique à tools/products.json

---

## Images et WebP

- Les images optimisées pour le web sont dans **`assets/web/`**.
- Le script `tools/build_webp.py` génère des variantes WebP redimensionnées (qualité 82) depuis
  les JPEG/PNG de `assets/web/` :
  - `<base>-sm.webp` (~480 px) et `<base>-lg.webp` (~960 px) pour les photos produit
  - Tailles variables pour les photos de contenu (600–720 px / 1100–1280 px)
- Les originaux JPEG/PNG sont conservés comme fallback.
- Les petits fichiers (icônes, cut-*.png, logo-header, photos d'équipe) ne sont pas convertis.
- Les **sources originales** (`assets/logo`, `assets/image produit`, `assets/image deco`,
  `assets/Membre`) sont ignorées par `.gitignore` — ne pas y toucher.

```powershell
# Voir le plan sans écrire
python tools/build_webp.py --dry-run

# Générer les WebP (nécessite Pillow)
python tools/build_webp.py
```

---

## Structure

- `css/style.css` — feuille de style unique (palette : `#29a151`, `#49bd58`, menthe `#dbfee0` ;
  variables accessibles `--btn-grad-from`, `--btn-grad-to`, `--badge-red`, `--focus-ring`)
- `js/main.js` — menu mobile, aria-current, animations au scroll, données + filtres des points de
  vente, module carte (gated par `window.THECOL_GEO`), formulaire de contact, panier (localStorage,
  mailto), piège de focus et inert
- `js/map-suisse.js` — `window.THECOL_GEO` : données géographiques de la carte (viewBox, chemins
  SVG simplifiés des 26 cantons, coordonnées des 27 localités, ancres de labels, zoom.viewBox
  pour le cadre de l'inset Fribourg). Généré par `tools/build_map.py` à partir de
  « Suisse cantons.svg » (Pymouss44, CC BY-SA 4.0)
- `assets/fonts/` — polices auto-hébergées (Fraunces pour les titres, Outfit pour le texte)
- `assets/web/` — images optimisées (JPEG/PNG + WebP), icônes
- `robots.txt` / `sitemap.xml` — SEO (pointent vers l'URL temporaire GitHub Pages)
- `tools/` — utilitaires Python (validation `validate_site.py`, images WebP `build_webp.py`,
  carte interactive `build_map.py` : anti-chevauchement doux des localités + calcul automatique
  du cadre de zoom pour l'inset Fribourg)

---

## À ajuster si besoin

- **Points de vente** : la liste et les cantons vivent dans `js/main.js` (tableaux `POS`, `CANTONS`).
  Ajouter/retirer une entrée suffit ; le compteur et les chips sont automatiques. La **carte
  interactive** (`js/map-suisse.js`) comporte deux niveaux : la carte Suisse complète (pin cluster
  agrégé pour Fribourg + pins individuels Yverdon/Crissier/Champoussin/Delémont + rectangle de zoom
  en pointillés) et un **inset « Canton de Fribourg — zoom ×3 »** flottant en bas à droite (empilé
  sous la carte sur mobile) avec les 23 localités fribourgeoises à leur position géographique réelle
  (écart max ~1,6 km). Chaque entrée `POS` doit fournir deux champs :
  - `loc` : clé de localité dans `window.THECOL_GEO.loc` (parmi les 27 existantes, ou après ajout
    des coordonnées dans le script puis régénération de la carte)
  - `t` : type de commerce (détermine l'icône / le pill sur la carte).
  Les positions sont calculées par projection géographique ; un anti-chevauchement doux
  (distance min 10 unités, déplacement max ~2 km) les ajuste automatiquement. Pour ajouter
  une localité inédite, éditer les coordonnées dans `js/map-suisse.js` puis régénérer la carte
  avec la commande suivante (Python standard, aucune dépendance) — le cadre de zoom de l'inset
  est recalculé automatiquement :
  ```
  python tools/build_map.py
  ```
- **Formulaire de contact** : ouvre la messagerie du visiteur (mailto: vers `commande@thecol.ch`) —
  aucun backend. Un bouton « Copier le message » permet de copier le texte manuellement.
- **Boutique en ligne** : le lien « Acheter et payer en ligne » dans le tiroir panier et dans les
  fiches produit pointe vers `https://www.thecol.ch/shop` (Odoo).
- **Découpes de bouteilles** : `assets/web/cut-*.png` sont prêtes pour varier le visuel du hero.
- **CGV** : les conditions générales de vente sont dans `contact.html` ; chaque section distingue
  le parcours « demande par e-mail (ce site) » du parcours « achat en ligne (Odoo) ».
