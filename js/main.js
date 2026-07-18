/* ThéCol — interactions du site */
(function () {
  "use strict";

  /* ---------- Header : état scroll + menu mobile ---------- */
  var header = document.querySelector(".site-header");
  var toggle = document.querySelector(".nav-toggle");

  function onScroll() {
    if (header) header.classList.toggle("scrolled", window.scrollY > 10);
  }
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  if (toggle) {
    toggle.addEventListener("click", function () {
      var open = document.body.classList.toggle("nav-open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
    document.querySelectorAll(".main-nav a").forEach(function (a) {
      a.addEventListener("click", function () {
        document.body.classList.remove("nav-open");
        toggle.setAttribute("aria-expanded", "false");
      });
    });
  }

  /* ---------- Révélation au scroll ---------- */
  var revealEls = document.querySelectorAll(".reveal");
  if ("IntersectionObserver" in window && revealEls.length) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) {
          e.target.classList.add("in");
          io.unobserve(e.target);
        }
      });
    }, { threshold: 0.12, rootMargin: "0px 0px -40px 0px" });
    revealEls.forEach(function (el) { io.observe(el); });
  } else {
    revealEls.forEach(function (el) { el.classList.add("in"); });
  }

  /* ---------- Année du footer ---------- */
  document.querySelectorAll("[data-year]").forEach(function (el) {
    el.textContent = new Date().getFullYear();
  });

  /* ---------- Points de vente : données + filtres ---------- */
  var POS = [
    { n: "Au Bon Moment", a: "Route de Fribourg 17, 1723 Marly", c: "Fribourg" },
    { n: "Audiopur", a: "Rue de Lausanne 12, 1700 Fribourg", c: "Fribourg" },
    { n: "Café de la Marionnette", a: "Derrière les Jardins 2, 1700 Fribourg", c: "Fribourg" },
    { n: "Terre d'elles", a: "Route du Barrage 14, 1733 Treyvaux", c: "Fribourg" },
    { n: "L'ART'isan Pâtissier", a: "Route de Fribourg 12, 1746 Prez-vers-Noréaz", c: "Fribourg" },
    { n: "1.2.3. Bocal", a: "Route de Fribourg 7A, 1784 Courtepin", c: "Fribourg" },
    { n: "La Vracrie", a: "Route Principale 90, 1788 Praz (Vully)", c: "Fribourg" },
    { n: "Piccand Vins & Boissons", a: "Route des Grandseys 81, 1564 Domdidier", c: "Fribourg" },
    { n: "L'épicerie Papiy", a: "Grand-Rue 64, 1618 Châtel-Saint-Denis", c: "Fribourg" },
    { n: "Boulangerie Didier Ecoffey", a: "Grand-Rue 4, 1680 Romont", c: "Fribourg" },
    { n: "Fromagerie de Rossens", a: "Route du Barrage 100, 1728 Rossens", c: "Fribourg" },
    { n: "Fromagerie de Ponthaux", a: "Au Village 13, 1772 Ponthaux", c: "Fribourg" },
    { n: "Au Petit Marché", a: "Rue de la Neuveville 68, 1700 Fribourg", c: "Fribourg" },
    { n: "Au Bocal du Coin", a: "Grand-Rue 26, 1680 Romont", c: "Fribourg" },
    { n: "Fromagerie de Villaz-St-Pierre", a: "Route de Fuyens 14, 1690 Villaz-St-Pierre", c: "Fribourg" },
    { n: "La Ferme du Ferrage", a: "Route du Ferrage 21, 1695 Rueyres-St-Laurent", c: "Fribourg" },
    { n: "Moi Aussi", a: "Rue de la Neuveville 52, 1700 Fribourg", c: "Fribourg" },
    { n: "Aux Pains d'Ependes", a: "Au Village 8, 1731 Ependes", c: "Fribourg" },
    { n: "Fromagerie de Neyruz", a: "Route du Puits 2, 1740 Neyruz", c: "Fribourg" },
    { n: "Boulangerie Les Arcades", a: "Route de Belfaux 2, 1762 Givisiez", c: "Fribourg" },
    { n: "Boucherie Yerly", a: "Route du Barrage 73, 1728 Rossens", c: "Fribourg" },
    { n: "Epi'Vrac", a: "Rue du Centre 22, 1637 Charmey", c: "Fribourg" },
    { n: "Assemblage", a: "Place de l'Ancienne Papeterie 4, 1723 Marly", c: "Fribourg" },
    { n: "Laiterie de Belfaux", a: "Route du Centre 30, 1782 Belfaux", c: "Fribourg" },
    { n: "Self des Pralies", a: "Route du Crêt 1, 1697 La Joux", c: "Fribourg" },
    { n: "Le Sarrazin", a: "Route des Sarrazins 115, 1782 Lossy", c: "Fribourg" },
    { n: "Laiterie d'Arconciel", a: "Au Village 50, 1732 Arconciel", c: "Fribourg" },
    { n: "Le Local Hauterive", a: "Route de la Ria 3, 1725 Posieux", c: "Fribourg" },
    { n: "Le Biergarten", a: "Impasse de la Sous-Station 3, 1700 Fribourg", c: "Fribourg" },
    { n: "L'éco des saisons", a: "Route de Payerne 5, 1482 Cugy", c: "Fribourg" },
    { n: "Les Bièrosophes", a: "Rue du Valentin 7, 1400 Yverdon-les-Bains", c: "Vaud" },
    { n: "L'Esprit du Fruit", a: "Rue d'Yverdon 19, 1023 Crissier", c: "Vaud" },
    { n: "L'antre d'Eux", a: "Route de Champoussin 22, 1873 Champoussin", c: "Valais" },
    { n: "Shop de la Communance", a: "Rue Victor Helg 8, 2800 Delémont", c: "Jura" }
  ];

  var CANTONS = ["Fribourg", "Vaud", "Valais", "Jura", "Genève", "Neuchâtel"];
  var EMPTY_MSG = "Pas trop vite ! Notre petite entreprise se développe à son rythme. " +
    "Nous n'avons malheureusement pas encore de distributeurs dans le canton de ";

  var posRoot = document.getElementById("pos-root");
  if (posRoot) {
    var chipRow = document.getElementById("pos-chips");
    var searchInput = document.getElementById("pos-search");
    var totalEl = document.getElementById("pos-total");
    var activeCanton = "Tous";

    if (totalEl) totalEl.textContent = POS.length;

    function norm(s) {
      return s.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "");
    }

    function mapsUrl(p) {
      return "https://www.google.com/maps/search/?api=1&query=" +
        encodeURIComponent(p.n + ", " + p.a);
    }

    function cardHtml(p) {
      return '<article class="pos-card">' +
        "<h3>" + p.n + "</h3>" +
        "<address>" + p.a + "</address>" +
        '<a class="link-arrow" href="' + mapsUrl(p) + '" target="_blank" rel="noopener">' +
        'Itinéraire <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M7 17 17 7M8 7h9v9"/></svg></a>' +
        "</article>";
    }

    function render() {
      var q = searchInput ? norm(searchInput.value.trim()) : "";
      var html = "";
      var cantonsToShow = activeCanton === "Tous" ? CANTONS : [activeCanton];

      cantonsToShow.forEach(function (canton) {
        var items = POS.filter(function (p) {
          return p.c === canton && (!q || norm(p.n + " " + p.a).indexOf(q) !== -1);
        });
        var all = POS.filter(function (p) { return p.c === canton; });

        if (all.length === 0) {
          if (activeCanton === canton || (activeCanton === "Tous" && !q)) {
            html += '<div class="canton-title"><h2>' + canton + '</h2><span class="count-pill">0</span></div>';
            html += '<div class="empty-canton"><b>Pas trop vite !</b> ' +
              EMPTY_MSG.replace("Pas trop vite ! ", "").replace(/^Notre/, "Notre") + canton + ".&nbsp;" +
              'Vous connaissez l’adresse idéale&nbsp;? <a class="link-arrow" href="contact.html">Proposez-nous un point de vente</a></div>';
          }
          return;
        }
        if (items.length === 0) return;

        html += '<div class="canton-title"><h2>' + canton + '</h2><span class="count-pill">' + items.length + "</span></div>";
        html += '<div class="pos-grid">' + items.map(cardHtml).join("") + "</div>";
      });

      if (!html) {
        html = '<div class="empty-canton"><b>Aucun résultat.</b> Essayez un autre nom de commerce ou de localité.</div>';
      }
      posRoot.innerHTML = html;
    }

    if (chipRow) {
      var counts = {};
      CANTONS.forEach(function (c) {
        counts[c] = POS.filter(function (p) { return p.c === c; }).length;
      });
      var chips = ["Tous"].concat(CANTONS);
      chipRow.innerHTML = chips.map(function (c) {
        var count = c === "Tous" ? POS.length : counts[c];
        return '<button class="chip' + (c === "Tous" ? " active" : "") + '" data-canton="' + c + '">' +
          c + ' <span class="count">' + count + "</span></button>";
      }).join("");
      chipRow.addEventListener("click", function (e) {
        var btn = e.target.closest(".chip");
        if (!btn) return;
        activeCanton = btn.dataset.canton;
        chipRow.querySelectorAll(".chip").forEach(function (ch) {
          ch.classList.toggle("active", ch === btn);
        });
        render();
      });
    }
    if (searchInput) searchInput.addEventListener("input", render);
    render();
  }

  /* ---------- Formulaire de contact (ouvre la messagerie) ---------- */
  var form = document.getElementById("contact-form");
  if (form) {
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var get = function (id) { return (document.getElementById(id) || {}).value || ""; };
      var nom = get("f-nom"), mail = get("f-email"), soc = get("f-societe");
      var sujet = get("f-sujet"), question = get("f-question");
      var body = "Nom : " + nom + "\nE-mail : " + mail +
        (soc ? "\nSociété : " + soc : "") + "\n\n" + question;
      window.location.href = "mailto:commande@thecol.ch" +
        "?subject=" + encodeURIComponent("[thecol.ch] " + sujet) +
        "&body=" + encodeURIComponent(body);
    });
  }

  /* ==================================================================
     Boutique : catalogue, panier (localStorage) et fiche produit
     ================================================================== */

  var PRODUCTS = {
    hibiscus: { name: "Hibiscus", img: "assets/web/produit-hibiscus.jpg", page: "produit-hibiscus.html", formats: { 25: 3.0, 50: 5.0, 100: 8.5 } },
    mures:    { name: "Mûres sauvages", img: "assets/web/produit-mures.jpg", page: "produit-mures.html", formats: { 25: 3.0, 50: 5.0, 100: 8.5 } },
    sureau:   { name: "Fleur de Sureau", img: "assets/web/produit-sureau.jpg", page: "produit-sureau.html", formats: { 25: 3.0, 50: 5.0, 100: 8.5 } },
    herbes:   { name: "Herbes des Alpes", img: "assets/web/produit-herbes.jpg", page: "produit-herbes.html", formats: { 25: 3.0, 50: 5.0, 100: 8.5 } },
    poire:    { name: "Poire à Botzi", img: "assets/web/produit-poire.jpg", page: "produit-poire.html", formats: { 50: 5.0 } }
  };

  var CART_KEY = "thecol-cart";

  function chf(n) { return "CHF " + n.toFixed(2); }

  function cartLoad() {
    try {
      var items = JSON.parse(localStorage.getItem(CART_KEY)) || [];
      return items.filter(function (it) {
        return PRODUCTS[it.id] && PRODUCTS[it.id].formats[it.size] && it.qty > 0;
      });
    } catch (e) { return []; }
  }
  function cartSave(items) {
    try { localStorage.setItem(CART_KEY, JSON.stringify(items)); } catch (e) {}
    cartRender();
  }
  function cartAdd(id, size, qty) {
    var items = cartLoad();
    var hit = items.find(function (it) { return it.id === id && it.size === size; });
    if (hit) { hit.qty = Math.min(99, hit.qty + qty); }
    else { items.push({ id: id, size: size, qty: qty }); }
    cartSave(items);
  }
  function cartTotal(items) {
    return items.reduce(function (sum, it) {
      return sum + PRODUCTS[it.id].formats[it.size] * it.qty;
    }, 0);
  }

  /* Tiroir : injecté une fois dans chaque page */
  var drawerHtml =
    '<div class="cart-overlay" id="cart-overlay"></div>' +
    '<aside class="cart-drawer" id="cart-drawer" role="dialog" aria-modal="true" aria-label="Panier">' +
    '  <div class="cart-head"><h3>Votre panier</h3>' +
    '  <button class="cart-close" id="cart-close" aria-label="Fermer le panier">&times;</button></div>' +
    '  <div class="cart-items" id="cart-items"></div>' +
    '  <div class="cart-foot" id="cart-foot">' +
    '    <div class="cart-total">Total <b id="cart-total">CHF 0.00</b></div>' +
    '    <button class="btn" id="cart-checkout">Commander par e-mail</button>' +
    '    <p class="cart-note">Nous confirmons la commande, la livraison (3–5 jours) et le paiement par retour d’e-mail. Vous pouvez aussi commander sur la <a href="https://www.thecol.ch/shop" target="_blank" rel="noopener">boutique en ligne actuelle</a>.</p>' +
    '  </div>' +
    '</aside>';
  document.body.insertAdjacentHTML("beforeend", drawerHtml);

  var drawerItems = document.getElementById("cart-items");
  var drawerFoot = document.getElementById("cart-foot");
  var drawerTotal = document.getElementById("cart-total");

  function cartOpen() { document.body.classList.add("cart-open"); }
  function cartClose() { document.body.classList.remove("cart-open"); }

  document.getElementById("cart-overlay").addEventListener("click", cartClose);
  document.getElementById("cart-close").addEventListener("click", cartClose);
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") cartClose();
  });
  document.querySelectorAll(".cart-btn").forEach(function (b) {
    b.addEventListener("click", cartOpen);
  });

  document.getElementById("cart-checkout").addEventListener("click", function () {
    var items = cartLoad();
    if (!items.length) return;
    var lines = items.map(function (it) {
      var p = PRODUCTS[it.id];
      return "• " + it.qty + " × " + p.name + " " + it.size + " cl — " + chf(p.formats[it.size] * it.qty);
    });
    var body = "Bonjour,\n\nJe souhaite commander :\n" + lines.join("\n") +
      "\n\nTotal : " + chf(cartTotal(items)) +
      "\n\nNom :\nAdresse de livraison :\nTéléphone (facultatif) :\n\nMerci !";
    window.location.href = "mailto:commande@thecol.ch" +
      "?subject=" + encodeURIComponent("[thecol.ch] Commande en ligne") +
      "&body=" + encodeURIComponent(body);
  });

  function cartRender() {
    var items = cartLoad();
    var count = items.reduce(function (s, it) { return s + it.qty; }, 0);

    document.querySelectorAll("[data-cart-count]").forEach(function (el) {
      el.textContent = count;
      el.hidden = count === 0;
    });

    if (!items.length) {
      drawerItems.innerHTML =
        '<div class="cart-empty"><p>Votre panier est vide.</p>' +
        '<a class="btn small" href="produits.html">Découvrir nos saveurs</a></div>';
      drawerFoot.style.display = "none";
      return;
    }
    drawerFoot.style.display = "";
    drawerTotal.textContent = chf(cartTotal(items));
    drawerItems.innerHTML = items.map(function (it, i) {
      var p = PRODUCTS[it.id];
      return '<div class="cart-item">' +
        '<a href="' + p.page + '"><img src="' + p.img + '" alt="' + p.name + '"></a>' +
        '<div><div class="ci-name">' + p.name + "</div>" +
        '<div class="ci-size">' + it.size + " cl · " + chf(p.formats[it.size]) + "</div>" +
        '<div class="qty sm">' +
        '<button data-ci-dec="' + i + '" aria-label="Réduire la quantité">&minus;</button>' +
        '<input type="number" value="' + it.qty + '" readonly aria-label="Quantité">' +
        '<button data-ci-inc="' + i + '" aria-label="Augmenter la quantité">+</button>' +
        "</div></div>" +
        '<div class="ci-right"><span class="ci-price">' + chf(p.formats[it.size] * it.qty) + "</span>" +
        '<button class="ci-remove" data-ci-rm="' + i + '">Retirer</button></div>' +
        "</div>";
    }).join("");
  }

  drawerItems.addEventListener("click", function (e) {
    var items = cartLoad();
    var t = e.target;
    if (t.dataset.ciDec !== undefined) {
      var d = items[+t.dataset.ciDec];
      if (d) { d.qty -= 1; if (d.qty <= 0) items.splice(+t.dataset.ciDec, 1); }
    } else if (t.dataset.ciInc !== undefined) {
      var inc = items[+t.dataset.ciInc];
      if (inc) inc.qty = Math.min(99, inc.qty + 1);
    } else if (t.dataset.ciRm !== undefined) {
      items.splice(+t.dataset.ciRm, 1);
    } else { return; }
    cartSave(items);
  });

  cartRender();

  /* ---------- Fiche produit ---------- */
  var pd = document.querySelector("[data-product]");
  if (pd) {
    var pid = pd.dataset.product;
    var product = PRODUCTS[pid];
    var qtyInput = pd.querySelector("#pd-qty");
    var totalEl = pd.querySelector("#pd-total");
    var addBtn = pd.querySelector("#pd-add");

    function selectedSize() {
      var r = pd.querySelector('input[name="format"]:checked');
      return r ? +r.value : +Object.keys(product.formats)[0];
    }
    function refresh() {
      var qty = Math.max(1, Math.min(99, parseInt(qtyInput.value, 10) || 1));
      qtyInput.value = qty;
      totalEl.textContent = chf(product.formats[selectedSize()] * qty);
    }
    pd.querySelectorAll('input[name="format"]').forEach(function (r) {
      r.addEventListener("change", refresh);
    });
    pd.querySelector("#pd-minus").addEventListener("click", function () {
      qtyInput.value = (parseInt(qtyInput.value, 10) || 1) - 1; refresh();
    });
    pd.querySelector("#pd-plus").addEventListener("click", function () {
      qtyInput.value = (parseInt(qtyInput.value, 10) || 1) + 1; refresh();
    });
    qtyInput.addEventListener("change", refresh);
    addBtn.addEventListener("click", function () {
      cartAdd(pid, selectedSize(), parseInt(qtyInput.value, 10) || 1);
      cartOpen();
    });
    refresh();

    /* Galerie : clic sur vignette */
    var mainImg = pd.querySelector("#pd-main-img");
    pd.querySelectorAll(".pd-thumb").forEach(function (th) {
      th.addEventListener("click", function () {
        var img = th.querySelector("img");
        mainImg.src = img.src;
        mainImg.alt = img.alt;
        pd.querySelectorAll(".pd-thumb").forEach(function (o) { o.classList.remove("active"); });
        th.classList.add("active");
      });
    });
  }
})();
