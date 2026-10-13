/* ==========================================================================
   ThéCol — contenu « prototype » des fiches produit (à coller À LA SUITE
   dans user_custom_javascript.js).

   La saveur est reconnue d'après le nom du produit (Hibiscus, Mûres…).
   On insère juste sous le titre : sous-titre, paragraphes et pastilles.
   Le champ « Description ecommerce » d'Odoo reste affiché en dessous
   (ingrédients, valeurs nutritionnelles) et se modifie normalement.
   Le bloc est ajouté À CÔTÉ du titre, hors des zones modifiables : il n'est
   jamais enregistré dans la fiche produit.
   JavaScript « classique » : pas de gabarits `...`, pas d'import.
   ========================================================================== */
(function () {
  "use strict";

  var COMMON = [
    "Comme toute la gamme, il est brassé artisanalement en petites séries à Fribourg — sans arômes, ni extraits, ni concentrés, ni colorants, ni conservateurs. Simplement goûtu, rafraîchissant et pas trop sucré.",
    "Bouteille fermée, il se conserve 6 mois à l'abri de la lumière et de la chaleur, sans frigo. Une fois ouverte, gardez-la au frais — et finissez-la sans tarder\u00a0!"
  ];
  var FEATS = ["Sans arômes ni conservateurs", "Pas trop sucré", "Bouteille en verre réutilisable"];

  // Mots-clés cherchés dans le nom du produit (sans accents, en minuscules)
  var FLAVORS = [
    { key: "hibiscus", words: ["hibiscus"],
      sub: "La fleur qui voit rouge.",
      intro: "L'infusion de fleurs d'hibiscus lui donne sa robe rouge éclatante et son acidité typique. Le thé froid qui ne passe pas inaperçu." },
    { key: "mures", words: ["mure"],
      sub: "Le goût des balades en forêt.",
      intro: "Aussi fruité et gourmand que les mûres des jardins de nos grands-mères. Rafraîchissant et tout en légèreté." },
    { key: "sureau", words: ["sureau"],
      sub: "Le classique du terroir, en plus frais.",
      intro: "Un thé floral tout en rondeur. À savourer sans modération." },
    { key: "herbes", words: ["herbes", "alpes"],
      sub: "Un air d'alpage en bouteille.",
      intro: "Une infusion herbacée redoutablement délicieuse. L'esprit de nos montagnes en bouteille." },
    { key: "poire", words: ["poire", "botzi"],
      sub: "La poire AOP de chez nous.",
      intro: "Doux, fruité et délicat : un grand classique de nos régions revisité en thé froid. Comme un début d'automne à déguster toute l'année." }
  ];

  function start() {
    try {
      initFlavorPage();
    } catch (err) {
      if (window.console) console.error("ThéCol fiches saveurs :", err);
    }
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start);
  else start();

  function norm(s) {
    return String(s || "").toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
  }
  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    return e;
  }

  function initFlavorPage() {
    var wrap = document.querySelector("#wrap.o_wsale_product_page");
    if (!wrap || wrap.querySelector(".tc-pd")) return;
    var title = wrap.querySelector("#product_details h1");
    if (!title) return;

    var name = norm(title.textContent);
    var flavor = null;
    for (var i = 0; i < FLAVORS.length && !flavor; i++) {
      for (var j = 0; j < FLAVORS[i].words.length; j++) {
        if (name.indexOf(FLAVORS[i].words[j]) !== -1) { flavor = FLAVORS[i]; break; }
      }
    }
    if (!flavor) return;

    var block = el("div", "tc-pd tc-pd-" + flavor.key);
    block.appendChild(el("p", "tc-pd-sub", flavor.sub));
    var desc = el("div", "tc-pd-desc");
    [flavor.intro].concat(COMMON).forEach(function (t) { desc.appendChild(el("p", null, t)); });
    block.appendChild(desc);
    var feats = el("div", "tc-pd-feats");
    feats.appendChild(el("span", "tc-pd-feat tc-pd-swiss", "Swiss made"));
    FEATS.forEach(function (t) { feats.appendChild(el("span", "tc-pd-feat", t)); });
    block.appendChild(feats);

    title.parentNode.insertBefore(block, title.nextSibling);
  }
})();
