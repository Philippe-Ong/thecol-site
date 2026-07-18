# ThéCol — site remasterisé

Refonte statique multi-pages de [thecol.ch](https://www.thecol.ch), avec le même contenu
(textes, produits, 34 points de vente, FAQ, CGV) et les nouvelles images du dossier `assets/`.

**Site en ligne : <https://philippe-ong.github.io/thecol-site/>** (GitHub Pages, branche `main`).
Chaque `git push` sur `main` redéploie automatiquement le site en ~1 minute.
Les images sources (`assets/Membre`, `image deco`, `image produit`, `logo`) restent locales
(voir `.gitignore`) — seules les versions optimisées `assets/web/` sont publiées.

## Pages

| Fichier | Page |
| --- | --- |
| `index.html` | Accueil — hero, chiffres clés, origines, piliers, aperçu de la gamme, FAQ |
| `produits.html` | Nos produits — catalogue des 5 saveurs, prix, commander |
| `produit-hibiscus.html` etc. | Fiches produit (×5) — galerie photo, description, format, quantité, ajout au panier |
| `points-de-vente.html` | Points de vente — 34 distributeurs, recherche + filtre par canton |
| `a-propos.html` | À propos — valeurs, fabrication, équipe, chronologie, galerie |
| `contact.html` | Contact — formulaire (mailto), coordonnées, CGV |

## Boutique

Chaque saveur a sa fiche (`produit-<saveur>.html`) avec galerie à vignettes, description,
sélecteur de format (25/50/100 cl) et quantité. Le panier vit dans le `localStorage` du
navigateur (`js/main.js`, objet `PRODUCTS` + fonctions `cart*`) et s'ouvre en tiroir latéral
depuis l'icône du header, présente sur toutes les pages.

Le bouton « Commander par e-mail » compose un e-mail prérempli (articles, total, champs
nom/adresse) vers `commande@thecol.ch` — aucun backend requis. Pour brancher un vrai
paiement en ligne, remplacer ce bouton par le tunnel Odoo/Stripe de votre choix dans
`js/main.js` (listener `cart-checkout`).

## Lancer le site en local

```
python -m http.server 8123
```

puis ouvrir <http://localhost:8123>. (Ou n'importe quel serveur statique — aucun build nécessaire.)

## Structure

- `css/style.css` — feuille de style unique (palette tirée du logo : `#29a151`, `#49bd58`, menthe `#dbfee0`)
- `js/main.js` — menu mobile, animations d'apparition, données + filtres des points de vente, formulaire
- `assets/fonts/` — polices auto-hébergées (Fraunces pour les titres, Outfit pour le texte)
- `assets/web/` — images optimisées pour le web (générées depuis les originaux, ~2 Mo au total au lieu de 209 Mo)
- `assets/logo`, `assets/image produit`, `assets/image deco`, `assets/Membre` — originaux, non utilisés directement par le site

## À ajuster si besoin

- **Poire à Botzi** : affichée comme « Nouveauté » en 50 cl à CHF 5.00 (aligné sur le prix des autres 50 cl).
  Adapter `produits.html` si d'autres formats arrivent.
- **Formulaire de contact** : il ouvre la messagerie du visiteur (mailto vers `commande@thecol.ch`).
  Pour un envoi direct, brancher un service type Formspree ou le backend Odoo existant (`js/main.js`, bloc `contact-form`).
- **Boutique en ligne** : les boutons « Boutique en ligne » pointent vers l'actuel shop Odoo (`www.thecol.ch/shop`).
- **Points de vente** : la liste vit dans `js/main.js` (tableau `POS`) — ajouter/retirer une entrée suffit.
- Des découpes de bouteilles supplémentaires (`assets/web/cut-*.png`) sont prêtes si vous voulez varier le hero.
