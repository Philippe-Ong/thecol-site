/* ==========================================================================
   ThéCol — prix complet sous chaque format (25 / 50 / 100 cl) sur la fiche
   produit (à coller À LA SUITE dans user_custom_javascript.js).

   Odoo n'affiche que le supplément « (+ CHF 2,00) ». On calcule le prix de
   base (prix affiché − supplément du format choisi), puis on écrit le prix
   de chaque format dans sa pilule. Recalculé quand Odoo met le prix à jour.
   JavaScript « classique » : pas de gabarits `...`, pas d'import.
   ========================================================================== */
(function () {
  "use strict";

  function start() {
    try {
      initFormatPrices();
    } catch (err) {
      if (window.console) console.error("ThéCol prix des formats :", err);
    }
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start);
  else start();

  // « CHF 2,00 », « 2.00 CHF », « 1'234,50 » → 2 / 1234.5
  function parseAmount(text) {
    var m = String(text || "").replace(/[\s'’]/g, "").match(/-?\d+(?:[.,]\d+)?/);
    return m ? parseFloat(m[0].replace(",", ".")) : 0;
  }

  function initFormatPrices() {
    var wrap = document.querySelector("#wrap.o_wsale_product_page");
    if (!wrap) return;
    var pills = wrap.querySelectorAll(".o_variant_pills");
    if (!pills.length) return;
    var priceEl = wrap.querySelector(".o_wsale_product_details_content_section_price .oe_price .oe_currency_value");
    if (!priceEl) return;

    function extraOf(pill) {
      var el = pill.querySelector(".variant_price_extra");
      if (!el) return 0;
      var sign = pill.querySelector(".sign_badge_price_extra");
      var v = parseAmount(el.textContent);
      return sign && sign.textContent.indexOf("-") !== -1 ? -v : v;
    }

    function update() {
      var checked = wrap.querySelector(".o_variant_pills input:checked");
      var active = checked ? checked.closest(".o_variant_pills") : wrap.querySelector(".o_variant_pills.active");
      var shown = priceEl.textContent;
      var base = parseAmount(shown) - (active ? extraOf(active) : 0);
      var comma = shown.indexOf(",") !== -1;
      Array.prototype.forEach.call(pills, function (pill) {
        var label = pill.querySelector(".o_variant_pills_input_value") || pill;
        var out = label.querySelector(".tc-pill-price");
        if (!out) {
          out = document.createElement("span");
          out.className = "tc-pill-price";
          label.appendChild(out);
        }
        var txt = "CHF " + (base + extraOf(pill)).toFixed(2);
        out.textContent = comma ? txt.replace(".", ",") : txt;
      });
    }

    update();
    // Odoo réécrit le prix après chaque changement de format : on suit.
    var target = priceEl.closest(".oe_price") || priceEl;
    new MutationObserver(update).observe(target, { childList: true, characterData: true, subtree: true });
    wrap.addEventListener("change", function (e) {
      if (e.target && e.target.closest && e.target.closest(".o_variant_pills")) setTimeout(update, 0);
    });
  }
})();
