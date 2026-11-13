/* ==========================================================================
   ThéCol — prix complet sous chaque format (25 / 50 / 100 cl) sur la fiche
   produit (à coller À LA SUITE dans user_custom_javascript.js).

   Odoo 20 n'affiche plus le supplément dans les pilules : on part du prix
   affiché pour le format choisi (TVA et liste de prix comprises) et on en
   déduit les autres au prorata de PRICES. Recalculé quand Odoo met le prix
   à jour.
   Le script ne tourne PAS dans l'éditeur Odoo (iframe) : ses observateurs
   et ceux de l'éditeur se relanceraient l'un l'autre sans fin.

   Il retient aussi un clic sur « Ajouter au panier » donné pendant qu'Odoo
   change de format (~200 à 450 ms) : sans cela, c'est l'ancien format qui
   part au panier. Le clic est rejoué dès que le nouveau prix est affiché.
   JavaScript « classique » : pas de gabarits `...`, pas d'import.
   ========================================================================== */
(function () {
  "use strict";

  // Prix de chaque format, par produit (nom sans accents, en minuscules).
  // Ligne réécrite par tools/deploy_odoo.py d'après tools/products.json.
  var PRICES = {"hibiscus": {"25 cl": 3.0, "50 cl": 5.0, "100 cl": 8.5}, "mures sauvages": {"25 cl": 3.0, "50 cl": 5.0, "100 cl": 8.5}, "fleur de sureau": {"25 cl": 3.0, "50 cl": 5.0, "100 cl": 8.5}, "herbes des alpes": {"25 cl": 3.0, "50 cl": 5.0, "100 cl": 8.5}, "poire a botzi": {"25 cl": 3.0, "50 cl": 5.0, "100 cl": 8.5}};

  function start() {
    try {
      initFormatPrices();
    } catch (err) {
      if (window.console) console.error("ThéCol prix des formats :", err);
    }
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start);
  else start();

  function norm(s) {
    return String(s || "").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").trim();
  }
  // « CHF 2,00 », « 2.00 CHF », « 1'234,50 » → 2 / 1234.5
  function parseAmount(text) {
    var m = String(text || "").replace(/[\s'’]/g, "").match(/-?\d+(?:[.,]\d+)?/);
    return m ? parseFloat(m[0].replace(",", ".")) : 0;
  }

  function initFormatPrices() {
    if (window.self !== window.top) return; // éditeur / aperçu Odoo
    var wrap = document.querySelector("#wrap.o_wsale_product_page");
    if (!wrap) return;
    var title = wrap.querySelector("#product_details h1");
    var prices = title && PRICES[norm(title.textContent)];
    if (!prices) return;
    var pills = wrap.querySelectorAll(".o_variant_pills");
    if (!pills.length) return;
    var PRICE = ".o_wsale_product_details_content_section_price .oe_price";
    var target = wrap.querySelector(PRICE);
    if (!target) return;

    function formatOf(pill) {
      var input = pill.querySelector("input");
      return input ? input.getAttribute("data-value-name") : null;
    }

    function update() {
      var checked = wrap.querySelector(".o_variant_pills input:checked");
      var active = checked ? checked.closest(".o_variant_pills") : wrap.querySelector(".o_variant_pills.active");
      var ref = active && prices[formatOf(active)];
      var priceEl = wrap.querySelector(PRICE + " .oe_currency_value");
      var shown = priceEl ? priceEl.textContent : "";
      var amount = parseAmount(shown);
      if (!ref || !amount) return;
      var comma = shown.indexOf(",") !== -1;
      Array.prototype.forEach.call(pills, function (pill) {
        var own = prices[formatOf(pill)];
        if (!own) return;
        var label = pill.querySelector(".o_variant_pills_input_value") || pill;
        var out = label.querySelector(".tc-pill-price");
        if (!out) {
          out = document.createElement("span");
          out.className = "tc-pill-price";
          label.appendChild(out);
        }
        var txt = "CHF " + (amount * own / ref).toFixed(2);
        if (comma) txt = txt.replace(".", ",");
        // N'écrire que si le texte change : pas de mutation inutile à observer.
        if (out.textContent !== txt) out.textContent = txt;
      });
    }

    // ---------- Format en cours de changement : « Ajouter au panier » attend ----------
    var pending = false, queued = null, timer = null;
    function settle() {
      if (!pending) return;
      pending = false;
      clearTimeout(timer);
      var btn = queued;
      queued = null;
      if (btn) {
        btn.classList.remove("tc-cart-wait");
        btn.removeAttribute("aria-busy");
        btn.click();
      }
    }
    wrap.addEventListener("change", function (e) {
      if (!e.target.closest || !e.target.closest(".o_variant_pills")) return;
      pending = true;
      clearTimeout(timer);
      timer = setTimeout(settle, 3000); // filet si le prix ne change pas
    }, true);
    // Phase de capture : le clic est arrêté avant d'atteindre le gestionnaire d'Odoo.
    wrap.addEventListener("click", function (e) {
      if (!pending || !e.target.closest) return;
      var btn = e.target.closest('[name="add_to_cart"]');
      if (!btn) return;
      e.preventDefault();
      e.stopImmediatePropagation();
      queued = btn;
      btn.classList.add("tc-cart-wait");
      btn.setAttribute("aria-busy", "true");
    }, true);

    update();
    // Odoo réécrit le prix après chaque changement de format : on suit. Le format
    // retenu par Odoo est à jour dans le même traitement, d'où le court délai.
    new MutationObserver(function () {
      update();
      if (pending) setTimeout(settle, 60);
    }).observe(target, { childList: true, characterData: true, subtree: true });
  }
})();
