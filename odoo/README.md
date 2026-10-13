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
| `prix-formats.js` | `user_custom_javascript.js`, à la suite (prix complet sous chaque pilule 25/50/100 cl) |
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
- Le script **ne s'exécute pas dans l'éditeur/aperçu Odoo** (iframe) : ce qu'il ajoute
  n'est donc jamais enregistré dans la page. Pour voir la carte, ouvrir
  `/distributeurs` dans un onglet normal.
- Le fichier JS doit rester en JavaScript « classique » (pas de gabarits `` ` ``,
  pas d'`import`) : Odoo le minifie comme un script ordinaire.

## Provisoire : images et polices sur GitHub Pages

Les images, `montagne.svg` et les polices Fraunces/Outfit sont chargées depuis
`https://philippe-ong.github.io/thecol-site/assets/`. C'est suffisant pour tester, mais
**avant la mise en production** il faut les rapatrier dans Odoo :

- **Images** : en mode Modifier, double-cliquer sur chaque image → *Remplacer* →
  téléverser le fichier depuis `assets/web/`.
- **Polices et `montagne.svg`** : les téléverser dans la médiathèque, puis remplacer
  `$tc-assets` / les `url(...)` dans `user_custom_rules.scss` par les URL `/web/content/...`.
  Autre option pour les polices : les ajouter via Google Fonts dans le panneau
  *Thème* d'Odoo.

## Liens utilisés (pages existantes d'Odoo)

| Ancien fichier statique | URL Odoo |
|---|---|
| `produits.html`, `produit-*.html` | `/shop`, `/shop?search=<saveur>` |
| `points-de-vente.html` | `/distributeurs` |
| `a-propos.html` | `/about-us` |
| `contact.html` | `/contactus` |

La Poire à Botzi n'est pas encore dans la boutique Odoo : sa carte pointe vers `/shop`.

## Étapes suivantes

- [x] Page d'accueil
- [x] En-tête (SCSS) et pied de page (nouveau contenu + SCSS)
- [x] Page Distributeurs (liste + carte)
- [x] Page vitrine « Nos produits » (`/nos-produits`)
- [x] Page À propos (`/about-us`)
- [x] Page Contact (formulaire Odoo natif conservé tel quel, habillé en CSS)
- [x] Style de la boutique `/shop` et des fiches produit (SCSS uniquement)
- [ ] Fiches produit : créer 5 produits à variantes « Format » (25/50/100 cl) et archiver les 15 anciens
- [ ] Rapatrier images et polices dans Odoo
