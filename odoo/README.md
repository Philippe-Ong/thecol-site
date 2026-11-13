# Portage vers Odoo (éditeur HTML/SCSS)

Ce dossier contient le code prêt à coller dans l'éditeur de code du site Odoo
(**Site Web → Modifier → ⋯ → Éditeur HTML/SCSS**). Tester d'abord sur la base
**neutralisée** (copie de test), puis refaire les mêmes collages sur la production.

| Fichier | Où le coller |
|---|---|
| `thecol.scss` | Menu déroulant **SCSS (CSS)** → fichier `user_custom_rules.scss` |
| `accueil.xml` | Menu déroulant **XML (HTML)** → vue `Home` (`website.homepage`) |
| `distributeurs.scss` | `user_custom_rules.scss`, **à la suite** de `thecol.scss` |
| `distributeurs.js` | Menu déroulant **JS** → `user_custom_javascript.js` |
| `produits.scss` | `user_custom_rules.scss`, à la suite des blocs précédents |
| `produits.xml` | Nouvelle page `/nos-produits` (Site → Nouveau → Page) : **XML (HTML)**, garder la 1re ligne, remplacer le reste |
| `contact.scss` | `user_custom_rules.scss`, à la suite des blocs précédents |
| `contact.xml` | Page `/contactus` : **XML (HTML)**, garder tout jusqu'à la ligne `<div id="wrap"` exclue, remplacer de `<div id="wrap"` jusqu'à la fin |
| `a-propos.scss` | `user_custom_rules.scss`, à la suite des blocs précédents |
| `a-propos.xml` | Page `/about-us` : **XML (HTML)**, remplacer de `<div id="wrap"` jusqu'à la fin |
| `entete-pied.scss` | `user_custom_rules.scss`, à la suite des blocs précédents (habille l'en-tête Odoo) |
| `pied-de-page.xml` | Vue du pied de page (celle qui contient `<div id="footer"`) : garder cette ligne, remplacer tout ce qui suit jusqu'à `</xpath>` exclu |
| `contact-cgv.xml` | Page `/contactus` : remplace la section `id="cgv"` (CGV officielles reprises de l'ancien pied de page) |
| `boutique.scss` | `user_custom_rules.scss`, à la suite des blocs précédents (liste `/shop` + fiches produit, CSS uniquement) |
| `fiche-produit.scss` | `user_custom_rules.scss`, après `boutique.scss` (fiche produit façon prototype, couleur par saveur ; le bloc de saveur est ajouté par `fiches-saveurs.js`) |
| `pages-odoo.scss` | `user_custom_rules.scss`, en dernier (pages natives d'Odoo : panier, commande, connexion, CGV `/terms`, 404 — fond crème et polices du site) |
| `prix-formats.js` | `user_custom_javascript.js`, à la suite (prix complet sous chaque pilule 25/50/100 cl ; la ligne `var PRICES` est resynchronisée avec `tools/products.json` par `tools/deploy_odoo.py`. Retient aussi un clic sur « Ajouter au panier » donné pendant le changement de format, sinon l'ancien format part au panier) |
| `fiches-saveurs.js` | `user_custom_javascript.js`, à la suite : sous-titre, paragraphes et pastilles de chaque saveur (reconnue d'après le nom du produit) |
| `distributeurs.xml` | **XML (HTML)** → vue de la page `/distributeurs` : garder la 1re ligne `<t name=… t-name=…>`, remplacer tout le reste |

Pour copier un fichier entier dans le presse-papiers (PowerShell, accents conservés) :

```powershell
Get-Content odoo\distributeurs.xml -Raw -Encoding UTF8 | Set-Clipboard
```

## Procédure

1. **Styles d'abord.** Ouvrir l'éditeur, choisir **SCSS (CSS)**, sélectionner
   `user_custom_rules.scss`, coller **tout** le contenu de `thecol.scss` à la suite
   de ce qui existe, puis **Sauvegarder**. Si Odoo affiche une erreur de compilation,
   rien n'est appliqué : corriger et resauvegarder.
2. **Page d'accueil.** Choisir **XML (HTML)**, vue **Home**, tout sélectionner
   (Ctrl+A) et remplacer par le contenu de `accueil.xml`, puis **Sauvegarder**.
   L'ancien carrousel est écrasé. Odoo garde l'historique de la vue, et vous pouvez aussi
   copier l'ancien code dans un fichier avant de coller.
3. Recharger la page et vérifier en desktop et en mobile (icône téléphone de la barre Odoo).

## Conventions

- Chaque section porte la classe `tc` et toutes les classes custom commencent par `tc-`
  pour éviter tout conflit avec Bootstrap et le thème Odoo.
- Les boutons gardent la classe Bootstrap `btn` (`class="btn tc-btn"`) pour que
  l'éditeur glisser-déposer les reconnaisse comme boutons.
- XML strict : pas de `&nbsp;` (utiliser `&#160;`), balises fermées (`<br/>`, `<img/>`),
  pas de `<div/>` vide auto-fermant (écrire `<div></div>`).
- SCSS compilé par **libsass** : ne pas utiliser `min()` / `max()` avec des unités
  mixtes (ex. `min(340px, 84%)`), sinon la compilation plante. `clamp()` fonctionne.
- Le JSON-LD FAQ est placé **hors** de `#wrap` pour que l'éditeur visuel ne le supprime pas.
- Aucun JavaScript : FAQ en `<details>`, apparition au scroll en CSS pur
  (`animation-timeline`, ignoré sans risque par les navigateurs qui ne le gèrent pas).

## Page Distributeurs

- La **liste** est du HTML statique : on ajoute un distributeur en dupliquant une carte
  dans l'éditeur Odoo. Chaque carte porte `data-canton` et `data-loc` (onglet XML).
- La **carte, la recherche et les filtres** sont dessinés par `distributeurs.js`
  à partir de cette liste. Une nouvelle localité n'apparaît sur la carte que si elle
  existe dans `GEO.loc` (coordonnées générées par `tools/build_map.py`).
- Le **filtre par type de commerce** (`<select id="tc-pos-type">`) est rempli par
  `distributeurs.js` à partir du libellé de chaque carte (`.tc-pos-type span`). Les types
  sont regroupés par famille dans `TYPE_GROUPS` ; un type inconnu tombe dans
  « Fermes & boucheries », donc aucune carte ne disparaît. Pour une nouvelle famille,
  ajouter une entrée à `TYPE_GROUPS`.
- Le **JSON-LD** (`ItemList` de `Store`, utile au référencement local) est construit
  par le script depuis les cartes, adresse au format « Rue 1, 1700 Ville ».
- Le script **ne s'exécute pas dans l'éditeur/aperçu Odoo** (iframe) : ce qu'il ajoute
  n'est donc jamais enregistré dans la page. Pour voir la carte, ouvrir
  `/distributeurs` dans un onglet normal.
- `prix-formats.js` et `fiches-saveurs.js` ne s'exécutent pas non plus dans l'éditeur :
  connecté, Odoo affiche le site dans une iframe et leurs observateurs se relançaient
  avec ceux de l'éditeur (page figée).
- Le fichier JS doit rester en JavaScript « classique » (pas de gabarits `` ` ``,
  pas d'`import`) : Odoo le minifie comme un script ordinaire.

## Images et polices

Dans les fichiers de ce dossier, les images, `montagne.svg` et les polices Fraunces/Outfit
pointent vers `https://philippe-ong.github.io/thecol-site/assets/`. `tools/deploy_odoo.py`
(étape `assets`) les téléverse dans la médiathèque d'Odoo et réécrit ces URL en
`/web/image/...` ou `/web/content/...` : le site déployé ne dépend plus de GitHub Pages.

En collage manuel, il faut faire ce rapatriement à la main :

- **Images** : en mode Modifier, double-cliquer sur chaque image → *Remplacer* →
  téléverser le fichier depuis `assets/web/`.
- **Polices et `montagne.svg`** : les téléverser dans la médiathèque, puis remplacer
  `$tc-assets` / les `url(...)` dans `user_custom_rules.scss` par les URL `/web/content/...`.
  Éviter Google Fonts (panneau *Thème*) : chaque visite enverrait l'adresse IP à Google.

Le **thème Odoo** est réglé sur « polices système » (étape `styles`, `THEME_FONTS`) : par défaut
il charge Inter et Inter Tight chez Google sur chaque page. Ne pas choisir de police Google dans
*Thème → Polices* ; Fraunces et Outfit viennent de `thecol.scss`.

Les `<img>` portent `width`/`height` (place réservée avant le chargement) et, quand une variante
plus petite existe dans `assets/web/`, un `srcset`. L'image du haut de l'accueil garde
`loading="eager"` : sans cet attribut, Odoo ajoute `loading="lazy"` à toutes les images.

## Réglages de la base (étapes `header`, `site` et `products` de `tools/deploy_odoo.py`)

- **Icône d'onglet** (`icon-192.png`) et **image de partage** par défaut (`photo-groupe.jpg`),
  comme sur le site statique.
- **Base de test** : balise `noindex, nofollow` dans le `<head>` de toutes les pages. Elle est
  retirée quand le script est lancé avec `--production`.
- **Fiches produit** : URL sans accents (`/shop/mures-sauvages-4`) ; l'ancienne adresse redirige.
  La **taxe de vente par défaut** de la société devient « 2.6% TTC » (un produit créé à la main
  ne part plus avec 8,1 % hors taxe).
- **Sujet de l'e-mail de confirmation de commande** traduit (« … : commande S000xx »).

- **Nom du site** « ThéCol » (suffixe des titres d'onglet) et, si la société porte encore
  le nom technique de la base (`thecol-test`), **nom de société** « ThéCol Sàrl »
  (« Copyright © » du pied de page, e-mails de commande).
- **Titres SEO des pages d'Odoo** (boutique, panier, commande, connexion, 404, recherche,
  CGV) : sans eux, l'onglet affiche le nom interne anglais du gabarit (« Products »,
  « Shopping Cart »…). Les fiches produit reprennent le titre des pages `produit-*.html`.
- **Traductions** qu'Odoo 20 n'a pas encore en français (« Name », « Company », « Search... »…).
- **`/terms`** : la page des conditions générales de la société (Comptabilité → Paramètres)
  reçoit les CGV de la section `id="cgv"` de `contact.xml`, à la place du texte d'exemple
  d'Odoo. Modifier les CGV dans `contact.xml`, puis relancer `--steps pages,site`.
- **`/privacy`** (page vide créée par Odoo) est dépubliée. Une vraie déclaration de
  protection des données (nLPD) pourra y être publiée plus tard.

## Livraison (étape `livraison` de `tools/deploy_odoo.py`)

Les modes proposés au moment de commander reprennent les CGV (« Livraison et transport ») :

| Mode | Où | Prix |
|---|---|---|
| Envoi postal (La Poste), 3 à 5 jours | toute la Suisse | paliers `POSTAL_TIERS` selon le montant TTC |
| Livraison par nos soins, 3 à 5 jours | canton de Fribourg | gratuite |
| Livraison par nos soins (tournée régionale), 30 jours max. | VD, GE, VS, NE, JU | gratuite |

- **Paliers provisoires** : moins de CHF 30 → 9.00 ; moins de 60 → 12.00 ; moins de 100 → 15.00 ;
  dès 100 → offert. Mettre les vrais tarifs dans `POSTAL_TIERS`, puis relancer `--steps livraison`
  (le texte « offerte dès CHF … » suit le dernier palier).
- Chaque mode a son produit de livraison (`LIV-POSTE`, `LIV-FRIBOURG`, `LIV-TOURNEE`) : c'est par
  cette référence que le script le retrouve. Les frais de port portent la TVA « 2.6% TTC » des thés.
- Odoo a chaque canton en une fiche par langue (« Freiburg » FR, « Fribourg » FR-FR,
  « Friburgo » FR-IT) : les modes par canton visent toutes les variantes. Ne pas renommer ces fiches
  (on créerait des doublons dans la liste du formulaire d'adresse).
- Le canton devient **obligatoire** dans les adresses en Suisse : sans canton, un client de
  Fribourg ne verrait que l'envoi postal.
- « Livraison standard » (créée par Odoo, gratuite, tous pays) est retirée du site mais reste
  utilisable pour les commandes saisies au bureau.
- Hors de Suisse, aucun mode n'est proposé : la commande ne peut pas aboutir.

## Liens utilisés (pages existantes d'Odoo)

| Ancien fichier statique | URL Odoo |
|---|---|
| `produits.html` | `/nos-produits` |
| `produit-*.html` | fiche produit `/shop/<saveur>-<id>` |
| `points-de-vente.html` | `/distributeurs` |
| `a-propos.html` | `/about-us` |
| `contact.html` | `/contactus` |

Les liens vers une fiche produit s'écrivent `href="tc-produit:hibiscus"` (clé de
`tools/products.json`) dans `accueil.xml` et `produits.xml` : l'URL contient l'id Odoo,
différent d'une base à l'autre, et `tools/deploy_odoo.py` la lit dans la base visée.
En collage manuel, remplacer ces repères par l'URL de la fiche (bouton *Aller au site*
du produit). Le menu n'a plus d'entrée « Boutique » : on commande depuis la fiche.

## Étapes suivantes

- [x] Page d'accueil
- [x] En-tête (SCSS) et pied de page (nouveau contenu + SCSS)
- [x] Page Distributeurs (liste + carte)
- [x] Page vitrine « Nos produits » (`/nos-produits`)
- [x] Page À propos (`/about-us`)
- [x] Page Contact (formulaire Odoo natif conservé tel quel, habillé en CSS)
- [x] Style de la boutique `/shop` et des fiches produit (SCSS uniquement)
- [ ] Fiches produit : créer 5 produits à variantes « Format » (25/50/100 cl) et archiver les 15 anciens
- [x] Rapatrier images et polices dans Odoo (étape `assets` du script)
- [x] Modes de livraison des CGV (étape `livraison`), paliers postaux provisoires
- [ ] Vrais paliers de l'envoi postal dans `POSTAL_TIERS`
- [ ] Paiement (carte Visa/MasterCard et PayPal selon les CGV) : aucun moyen publié, une commande
      ne peut pas encore aboutir
