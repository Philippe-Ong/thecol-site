/* ThéCol — interactions du site */
(function () {
  "use strict";

  /* ---------- Utilitaires ---------- */
  function focusableSelector() {
    return 'a[href], area[href], input:not([disabled]):not([type="hidden"]),' +
      ' select:not([disabled]), textarea:not([disabled]), button:not([disabled]),' +
      ' iframe, object, embed, [tabindex]:not([tabindex="-1"]), [contenteditable="true"]';
  }

  /* ---------- Header : état scroll + menu mobile ---------- */
  var header = document.querySelector(".site-header");
  var toggle = document.querySelector(".nav-toggle");
  var navEl = document.querySelector(".main-nav");
  var mobileNav = window.matchMedia("(max-width: 860px)");

  function onScroll() {
    if (header) header.classList.toggle("scrolled", window.scrollY > 10);
  }
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  function setToggleState(isOpen) {
    if (!toggle) return;
    toggle.setAttribute("aria-expanded", isOpen ? "true" : "false");
    toggle.setAttribute("aria-label", isOpen ? "Fermer le menu" : "Ouvrir le menu");
  }

  function setMenuOpen(isOpen) {
    document.body.classList.toggle("nav-open", isOpen);
    setToggleState(isOpen);
    if (isOpen && navEl) {
      var first = navEl.querySelector(focusableSelector());
      if (first) first.focus();
    }
  }

  if (toggle) {
    // État initial explicite
    setToggleState(false);

    toggle.addEventListener("click", function () {
      var open = !document.body.classList.contains("nav-open");
      setMenuOpen(open);
    });

    var navLinks = document.querySelectorAll(".main-nav a");
    navLinks.forEach(function (a) {
      a.addEventListener("click", function () {
        setMenuOpen(false);
      });
    });

    // Le bouton de fermeture et les liens partagent le même cycle clavier.
    mobileNav.addEventListener("change", function () {
      var active = document.activeElement;
      setMenuOpen(false);
      if (mobileNav.matches && navEl && navEl.contains(active)) toggle.focus();
      if (!mobileNav.matches && active === toggle && navEl) {
        var first = navEl.querySelector(focusableSelector());
        if (first) first.focus();
      }
    });
    document.addEventListener("keydown", function (e) {
      if (!mobileNav.matches || !document.body.classList.contains("nav-open")) return;
      if (e.key === "Escape") {
        setMenuOpen(false);
        toggle.focus();
        return;
      }
      if (e.key !== "Tab" || !navEl) return;
      var focusables = navEl.querySelectorAll(focusableSelector());
      if (!focusables.length) return;
      var first = focusables[0];
      var last = focusables[focusables.length - 1];
      var active = document.activeElement;
      if (active === toggle || !navEl.contains(active)) {
        e.preventDefault();
        (e.shiftKey ? last : first).focus();
      } else if ((e.shiftKey && active === first) || (!e.shiftKey && active === last)) {
        e.preventDefault();
        toggle.focus();
      }
    });
  }

  /* ---------- Skip link + main landmark id stable ---------- */
  (function setupSkipLinkAndMain() {
    var main = document.querySelector("main");
    if (main && !main.id) main.id = "main-content";
    var hasSkip = document.querySelector(".skip-link, [href='#main-content'][class*='skip']");
    if (!hasSkip && main) {
      var skip = document.createElement("a");
      skip.className = "skip-link";
      skip.href = "#main-content";
      skip.textContent = "Aller au contenu";
      document.body.insertBefore(skip, document.body.firstChild);
    }
  })();

  /* ---------- aria-current sur le lien actif ---------- */
  (function applyAriaCurrent() {
    var navLinks = document.querySelectorAll(".main-nav a");
    if (!navLinks.length) return;
    var path = (location.pathname || "").toLowerCase();
    var currentPage = path.substring(path.lastIndexOf("/") + 1) || "index.html";

    function matches(linkHref) {
      if (!linkHref) return false;
      var href = linkHref.toLowerCase();
      if (href.indexOf("#") === 0) return false; // ancres internes
      var file = href.substring(href.lastIndexOf("/") + 1);
      if (file === currentPage) return true;
      if (currentPage === "" && (href === "index.html" || href === "./" || href === "/")) return true;
      return false;
    }

    var currentSet = false;
    navLinks.forEach(function (a) {
      var href = a.getAttribute("href") || "";
      if (matches(href)) {
        a.setAttribute("aria-current", "page");
        currentSet = true;
      } else {
        a.removeAttribute("aria-current");
      }
    });
    // Si aucun href ne matche mais que .active existe déjà dans le HTML, on en déduit l'actif
    if (!currentSet) {
      var activeByClass = document.querySelector(".main-nav a.active");
      if (activeByClass) activeByClass.setAttribute("aria-current", "page");
    }
  })();

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
    { n: "Au Bon Moment", a: "Route de Fribourg 17, 1723 Marly", c: "Fribourg", loc: "Marly", t: "Épicerie" },
    { n: "Audiopur", a: "Rue de Lausanne 12, 1700 Fribourg", c: "Fribourg", loc: "Fribourg", t: "Boutique" },
    { n: "Café de la Marionnette", a: "Derrière les Jardins 2, 1700 Fribourg", c: "Fribourg", loc: "Fribourg", t: "Café" },
    { n: "Terre d'elles", a: "Route du Barrage 14, 1733 Treyvaux", c: "Fribourg", loc: "Treyvaux", t: "Épicerie" },
    { n: "L'ART'isan Pâtissier", a: "Route de Fribourg 12, 1746 Prez-vers-Noréaz", c: "Fribourg", loc: "Prez-vers-Noréaz", t: "Pâtisserie" },
    { n: "1.2.3. Bocal", a: "Route de Fribourg 7A, 1784 Courtepin", c: "Fribourg", loc: "Courtepin", t: "Épicerie vrac" },
    { n: "La Vracrie", a: "Route Principale 90, 1788 Praz (Vully)", c: "Fribourg", loc: "Praz (Vully)", t: "Épicerie vrac" },
    { n: "Piccand Vins & Boissons", a: "Route des Grandseys 81, 1564 Domdidier", c: "Fribourg", loc: "Domdidier", t: "Caviste" },
    { n: "L'épicerie Papiy", a: "Grand-Rue 64, 1618 Châtel-Saint-Denis", c: "Fribourg", loc: "Châtel-Saint-Denis", t: "Épicerie" },
    { n: "Boulangerie Didier Ecoffey", a: "Grand-Rue 4, 1680 Romont", c: "Fribourg", loc: "Romont", t: "Boulangerie" },
    { n: "Fromagerie de Rossens", a: "Route du Barrage 100, 1728 Rossens", c: "Fribourg", loc: "Rossens", t: "Fromagerie" },
    { n: "Fromagerie de Ponthaux", a: "Au Village 13, 1772 Ponthaux", c: "Fribourg", loc: "Ponthaux", t: "Fromagerie" },
    { n: "Au Petit Marché", a: "Rue de la Neuveville 68, 1700 Fribourg", c: "Fribourg", loc: "Fribourg", t: "Épicerie" },
    { n: "Au Bocal du Coin", a: "Grand-Rue 26, 1680 Romont", c: "Fribourg", loc: "Romont", t: "Épicerie vrac" },
    { n: "Fromagerie de Villaz-St-Pierre", a: "Route de Fuyens 14, 1690 Villaz-St-Pierre", c: "Fribourg", loc: "Villaz-St-Pierre", t: "Fromagerie" },
    { n: "La Ferme du Ferrage", a: "Route du Ferrage 21, 1695 Rueyres-St-Laurent", c: "Fribourg", loc: "Rueyres-St-Laurent", t: "Ferme" },
    { n: "Moi Aussi", a: "Rue de la Neuveville 52, 1700 Fribourg", c: "Fribourg", loc: "Fribourg", t: "Épicerie" },
    { n: "Aux Pains d'Ependes", a: "Au Village 8, 1731 Ependes", c: "Fribourg", loc: "Ependes", t: "Boulangerie" },
    { n: "Fromagerie de Neyruz", a: "Route du Puits 2, 1740 Neyruz", c: "Fribourg", loc: "Neyruz", t: "Fromagerie" },
    { n: "Boulangerie Les Arcades", a: "Route de Belfaux 2, 1762 Givisiez", c: "Fribourg", loc: "Givisiez", t: "Boulangerie" },
    { n: "Boucherie Yerly", a: "Route du Barrage 73, 1728 Rossens", c: "Fribourg", loc: "Rossens", t: "Boucherie" },
    { n: "Epi'Vrac", a: "Rue du Centre 22, 1637 Charmey", c: "Fribourg", loc: "Charmey", t: "Épicerie vrac" },
    { n: "Assemblage", a: "Place de l'Ancienne Papeterie 4, 1723 Marly", c: "Fribourg", loc: "Marly", t: "Épicerie" },
    { n: "Laiterie de Belfaux", a: "Route du Centre 30, 1782 Belfaux", c: "Fribourg", loc: "Belfaux", t: "Laiterie" },
    { n: "Self des Pralies", a: "Route du Crêt 1, 1697 La Joux", c: "Fribourg", loc: "La Joux", t: "Restaurant" },
    { n: "Le Sarrazin", a: "Route des Sarrazins 115, 1782 Lossy", c: "Fribourg", loc: "Lossy", t: "Épicerie" },
    { n: "Laiterie d'Arconciel", a: "Au Village 50, 1732 Arconciel", c: "Fribourg", loc: "Arconciel", t: "Laiterie" },
    { n: "Le Local Hauterive", a: "Route de la Ria 3, 1725 Posieux", c: "Fribourg", loc: "Posieux", t: "Épicerie" },
    { n: "Le Biergarten", a: "Impasse de la Sous-Station 3, 1700 Fribourg", c: "Fribourg", loc: "Fribourg", t: "Bar / Café" },
    { n: "L'éco des saisons", a: "Route de Payerne 5, 1482 Cugy", c: "Fribourg", loc: "Cugy", t: "Épicerie" },
    { n: "Les Bièrosophes", a: "Rue du Valentin 7, 1400 Yverdon-les-Bains", c: "Vaud", loc: "Yverdon-les-Bains", t: "Caviste" },
    { n: "L'Esprit du Fruit", a: "Rue d'Yverdon 19, 1023 Crissier", c: "Vaud", loc: "Crissier", t: "Boutique" },
    { n: "L'antre d'Eux", a: "Route de Champoussin 22, 1873 Champoussin", c: "Valais", loc: "Champoussin", t: "Restaurant" },
    { n: "Shop de la Communance", a: "Rue Victor Helg 8, 2800 Delémont", c: "Jura", loc: "Delémont", t: "Épicerie" }
  ];

  var CANTONS = ["Fribourg", "Vaud", "Valais", "Jura", "Genève", "Neuchâtel"];
  var EMPTY_MSG = "Pas trop vite ! Notre petite entreprise se développe à son rythme. " +
    "Nous n'avons malheureusement pas encore de distributeurs dans le canton de ";

  // Mapping canton name → ID de canton dans THECOL_GEO.cantons
  var CANTON_TO_ID = {
    "Fribourg": "FR", "Vaud": "VD", "Valais": "VS", "Jura": "JU",
    "Genève": "GE", "Neuchâtel": "NE",
    "Zurich": "ZH", "Berne": "BE", "Lucerne": "LU", "Uri": "UR",
    "Schwyz": "SZ", "Obwald": "OW", "Nidwald": "NW", "Glaris": "GL",
    "Zoug": "ZG", "Soleure": "SO", "Bâle-Ville": "BS", "Bâle-Campagne": "BL",
    "Schaffhouse": "SH", "Appenzell Rhodes-Extérieures": "AR",
    "Appenzell Rhodes-Intérieures": "AI", "Saint-Gall": "SG", "Grisons": "GR",
    "Argovie": "AG", "Thurgovie": "TG", "Tessin": "TI"
  };
  var SOON_CANTONS = { "Genève": "GE", "Neuchâtel": "NE" };
  var HAS_POS_CANTONS = { "Fribourg": true, "Vaud": true, "Valais": true, "Jura": true };
  // Index inverse ID → nom pour les classes has-pos / soon
  var ID_TO_CANTON = {};
  Object.keys(CANTON_TO_ID).forEach(function (k) { ID_TO_CANTON[CANTON_TO_ID[k]] = k; });

  // Icône SVG inline par type de commerce
  function typeIcon(t) {
    var s = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">';
    if (t === "Épicerie" || t === "Épicerie vrac" || t === "Boutique") {
      s += '<path d="M3 9h18l-1.5 11a2 2 0 0 1-2 1.8H6.5a2 2 0 0 1-2-1.8L3 9Z"/><path d="M8 9V6a4 4 0 0 1 8 0v3"/>';
    } else if (t === "Fromagerie" || t === "Laiterie") {
      s += '<path d="M4 11h16v3a6 6 0 0 1-6 6h-4a6 6 0 0 1-6-6v-3Z"/><path d="M4 11c0-3 2-5 4-5s4 2 4 5"/><path d="M12 6c0-2 1.5-3 4-3s4 1 4 3"/>';
    } else if (t === "Boulangerie" || t === "Pâtisserie") {
      s += '<path d="M5 22h14"/><path d="M6 18c0-3 1-5 3-7 1 2 2 3 3 3s2-1 3-3c2 2 3 4 3 7"/><path d="M7 11c0-3 2-5 5-5s5 2 5 5"/>';
    } else if (t === "Café" || t === "Bar / Café" || t === "Restaurant") {
      s += '<path d="M17 8h1a3 3 0 0 1 0 6h-1"/><path d="M3 8h14v8a4 4 0 0 1-4 4H7a4 4 0 0 1-4-4V8Z"/><path d="M7 4v2M11 4v2M15 4v2"/>';
    } else if (t === "Caviste") {
      s += '<path d="M8 22h8"/><path d="M9 22V11l3-7 3 7v11"/><path d="M9 14h6"/>';
    } else if (t === "Ferme") {
      s += '<path d="M11 20A7 7 0 0 1 4 13c0-3 1.5-4.5 3-6 0 2 1 3 2 3 0-2 1-3 2-4 1 1 2 2 2 4 1 0 2-1 2-3 1.5 1.5 3 3 3 6a7 7 0 0 1-7 7Z"/>';
    } else if (t === "Boucherie") {
      s += '<path d="M15 4c1.5 0 3 1.5 3 4s-1.5 4-3 4"/><path d="M9 4c-1.5 0-3 1.5-3 4s1.5 4 3 4"/><path d="M9 12v8M15 12v8"/><path d="M9 4h6"/>';
    } else {
      s += '<path d="M4 8h16l-1 3H5L4 8Z"/><path d="M5 11v10h14V11"/><path d="M9 21v-6h6v6"/>';
    }
    return s + '</svg>';
  }

  var posRoot = document.getElementById("pos-root");
  if (posRoot) {
    var chipRow = document.getElementById("pos-chips");
    var searchInput = document.getElementById("pos-search");
    var totalEl = document.getElementById("pos-total");
    var countEl = document.getElementById("pos-count");
    var activeCanton = "Tous";
    var reduceMotion = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    if (totalEl) totalEl.textContent = POS.length;

    // Garde-fou : le conteneur #pos-root ne doit jamais être une zone
    // aria-live, sinon chaque re-render serait dicté intégralement par les
    // lecteurs d'écran. On retire systématiquement tout attribut aria-live
    // et l'état busy/atomic qui auraient pu être ajoutés dans le HTML ou
    // ailleurs. Une seule zone concise #pos-live-status annonce les résultats.
    posRoot.removeAttribute("aria-live");
    posRoot.removeAttribute("aria-busy");
    posRoot.removeAttribute("aria-atomic");

    // Zone aria-live concise, séparée de la zone de résultats : seule cette
    // zone annonce les changements (le conteneur #pos-root reste muet pour
    // éviter que chaque re-render ne soit dicté intégralement).
    var liveStatus = document.getElementById("pos-live-status");
    if (!liveStatus) {
      liveStatus = document.createElement("p");
      liveStatus.id = "pos-live-status";
      liveStatus.className = "visually-hidden";
      liveStatus.setAttribute("aria-live", "polite");
      liveStatus.setAttribute("aria-atomic", "true");
      posRoot.parentNode.insertBefore(liveStatus, posRoot);
    }

    function norm(s) {
      return s.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
    }

    function mapsUrl(p) {
      return "https://www.google.com/maps/search/?api=1&query=" +
        encodeURIComponent(p.n + ", " + p.a);
    }

    function splitAddress(a) {
      var idx = a.lastIndexOf(",");
      if (idx === -1) return [a, ""];
      var street = a.substring(0, idx).trim();
      var city = a.substring(idx + 1).trim();
      return [street, "<b>" + city + "</b>"];
    }

    function escapeAttr(s) {
      return String(s || "").replace(/&/g, "&amp;").replace(/"/g, "&quot;").replace(/</g, "&lt;");
    }

    function cardHtml(p, i) {
      var parts = splitAddress(p.a);
      var street = parts[0];
      var cityHtml = parts[1];
      var locEsc = escapeAttr(p.loc);
      var locLabel = escapeAttr(p.loc || "ce commerce");
      return '<article class="pos-card" data-loc="' + locEsc +
        '" style="--i:' + (i || 0) + '">' +
        '<div class="pos-card-top">' +
        '<span class="pos-type">' + typeIcon(p.t) + '<span>' + p.t + '</span></span>' +
        '<button class="pos-locate" type="button" data-loc="' + locEsc +
        '" aria-label="Voir ' + locLabel + ' sur la carte">' +
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 21s-7-7.5-7-12a7 7 0 0 1 14 0c0 4.5-7 12-7 12Z"/><circle cx="12" cy="9" r="2.5"/></svg>' +
        '</button>' +
        '</div>' +
        "<h3>" + p.n + "</h3>" +
        '<address><span class="street">' + street + '</span> ' + cityHtml + '</address>' +
        '<a class="link-arrow" href="' + mapsUrl(p) + '" target="_blank" rel="noopener">' +
        'Itinéraire <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M7 17 17 7M8 7h9v9"/></svg></a>' +
        "</article>";
    }

    function totalShown() {
      return posRoot.querySelectorAll(".pos-card").length;
    }

    function announce(count, cantonLabel) {
      var label = cantonLabel && cantonLabel !== "Tous" ? cantonLabel : "tous les cantons";
      liveStatus.textContent = count + " point" + (count > 1 ? "s" : "") + " de vente trouvé" + (count > 1 ? "s" : "") + " — " + label + ".";
    }

    /* ---------- Module carte (gated par #pos-map + window.THECOL_GEO) ---------- */
    var mapModule = null;

    var mapStage = document.getElementById("pos-map");
    var mapBand = mapStage ? mapStage.closest(".map-band") : null;
    var mapTip = document.getElementById("pos-map-tip");
    var mapLegend = document.getElementById("map-legend");
    var geo = window.THECOL_GEO;

    // La tooltip est créée par JS (pas dans le HTML) pour rester enfant de #pos-map
    // et garder le même offsetParent (.map-stage, position:relative) que les pins,
    // afin que left/top calculés via getBoundingClientRect soient cohérents.
    if (mapStage && !mapTip) {
      mapTip = document.createElement("div");
      mapTip.id = "pos-map-tip";
      mapTip.className = "map-tip";
      mapTip.setAttribute("role", "tooltip");
      mapTip.setAttribute("aria-hidden", "true");
      mapStage.appendChild(mapTip);
    }

    if (!geo || !geo.cantons || !geo.loc || !mapStage) {
      if (mapBand) mapBand.style.display = "none";
    } else {
      // Si la tooltip existe (créée ci-dessus ou laissée par du HTML legacy),
      // on s'assure qu'elle est enfant direct de #pos-map.
      if (mapTip && mapTip.parentNode !== mapStage) {
        mapStage.appendChild(mapTip);
      }

        mapModule = (function () {
        var VIEW_W = 1000, VIEW_H = 700;
        var SVG_NS = "http://www.w3.org/2000/svg";
        var FR = "Fribourg";
        var ZOOM_VB = (geo.zoom && geo.zoom.viewBox) ? geo.zoom.viewBox.split(/\s+/).map(Number) : null;
        var cropX = ZOOM_VB ? ZOOM_VB[0] : 0;
        var cropY = ZOOM_VB ? ZOOM_VB[1] : 0;
        var cropW = ZOOM_VB ? ZOOM_VB[2] : VIEW_W;
        var cropH = ZOOM_VB ? ZOOM_VB[3] : VIEW_H;

        var frLocs = [];
        POS.forEach(function (p) {
          if (p.c === FR && geo.loc[p.loc] && frLocs.indexOf(p.loc) === -1) frLocs.push(p.loc);
        });
        var peripheralLocs = [];
        POS.forEach(function (p) {
          if (p.c !== FR && geo.loc[p.loc] && peripheralLocs.indexOf(p.loc) === -1) peripheralLocs.push(p.loc);
        });

        var byLoc = {};
        POS.forEach(function (p) {
          if (!p.loc || !geo.loc[p.loc]) return;
          if (!byLoc[p.loc]) byLoc[p.loc] = [];
          byLoc[p.loc].push(p);
        });

        var svg = document.createElementNS(SVG_NS, "svg");
        svg.setAttribute("viewBox", geo.viewBox || ("0 0 " + VIEW_W + " " + VIEW_H));
        svg.setAttribute("xmlns", SVG_NS);
        svg.setAttribute("aria-hidden", "true");
        svg.setAttribute("role", "presentation");

        Object.keys(geo.cantons).forEach(function (id) {
          var p = document.createElementNS(SVG_NS, "path");
          p.setAttribute("d", geo.cantons[id]);
          var klass = "canton";
          if (HAS_POS_CANTONS[ID_TO_CANTON[id]]) klass += " has-pos";
          if (SOON_CANTONS[ID_TO_CANTON[id]]) klass += " soon";
          p.setAttribute("class", klass);
          p.setAttribute("data-canton-id", id);
          svg.appendChild(p);
        });

        if (ZOOM_VB) {
          var zr = document.createElementNS(SVG_NS, "rect");
          zr.setAttribute("x", cropX);
          zr.setAttribute("y", cropY);
          zr.setAttribute("width", cropW);
          zr.setAttribute("height", cropH);
          zr.setAttribute("rx", 6);
          zr.setAttribute("class", "zoom-rect");
          svg.appendChild(zr);
        }

        var fallbackLabels = {
          "VD": [110, 410], "VS": [320, 470], "JU": [245, 235],
          "GE": [60, 510], "NE": [155, 310]
        };
        var labels = [
          { id: "VD", name: "Vaud" },
          { id: "VS", name: "Valais" },
          { id: "JU", name: "Jura" },
          { id: "GE", name: "Genève", soon: true },
          { id: "NE", name: "Neuchâtel", soon: true }
        ];
        labels.forEach(function (lb) {
          var pos = (geo.labels && geo.labels[lb.id]) || fallbackLabels[lb.id];
          var x = pos[0], y = pos[1];
          var t = document.createElementNS(SVG_NS, "text");
          t.setAttribute("x", x);
          t.setAttribute("y", y);
          t.setAttribute("text-anchor", "middle");
          t.setAttribute("class", "canton-label");
          t.textContent = lb.name;
          svg.appendChild(t);
          if (lb.soon) {
            var s = document.createElementNS(SVG_NS, "text");
            s.setAttribute("x", x);
            s.setAttribute("y", y + 14);
            s.setAttribute("text-anchor", "middle");
            s.setAttribute("class", "soon-label");
            s.textContent = "Bientôt";
            svg.appendChild(s);
          }
        });

        mapStage.appendChild(svg);

        var pins = {};
        var clusterBtn = null;

        peripheralLocs.forEach(function (loc, idx) {
          var pos = geo.loc[loc];
          var count = byLoc[loc].length;
          var btn = document.createElement("button");
          btn.type = "button";
          btn.className = "map-pin";
          btn.style.left = (pos[0] / VIEW_W * 100) + "%";
          btn.style.top = (pos[1] / VIEW_H * 100) + "%";
          btn.style.setProperty("--d", (idx * 0.06).toFixed(2) + "s");
          btn.setAttribute("data-loc", loc);
          btn.setAttribute("data-count", String(count));
          btn.setAttribute("aria-label", loc + " — " + count + " commerce" + (count > 1 ? "s" : ""));
          btn.setAttribute("aria-describedby", "pos-map-tip");
          var dot = document.createElement("span");
          dot.className = "dot";
          dot.setAttribute("aria-hidden", "true");
          btn.appendChild(dot);
          if (count > 1) {
            var badge = document.createElement("span");
            badge.className = "badge";
            badge.setAttribute("aria-hidden", "true");
            badge.textContent = String(count);
            btn.appendChild(badge);
          }
          mapStage.appendChild(btn);
          pins[loc] = { btn: btn, stage: mapStage };
        });

        if (frLocs.length && geo.loc[FR]) {
          var cpos = geo.loc[FR];
          clusterBtn = document.createElement("button");
          clusterBtn.type = "button";
          clusterBtn.className = "map-pin cluster";
          clusterBtn.style.left = (cpos[0] / VIEW_W * 100) + "%";
          clusterBtn.style.top = (cpos[1] / VIEW_H * 100) + "%";
          clusterBtn.style.setProperty("--d", "0s");
          clusterBtn.setAttribute("data-loc", "__cluster_fr__");
          clusterBtn.setAttribute("data-count", String(frLocs.length));
          clusterBtn.setAttribute("aria-label", "Canton de Fribourg — " + frLocs.length + " localités, voir le zoom");
          clusterBtn.setAttribute("aria-describedby", "pos-map-tip");
          var cdot = document.createElement("span");
          cdot.className = "dot";
          cdot.setAttribute("aria-hidden", "true");
          clusterBtn.appendChild(cdot);
          var cbadge = document.createElement("span");
          cbadge.className = "badge";
          cbadge.setAttribute("aria-hidden", "true");
          cbadge.textContent = String(frLocs.length);
          clusterBtn.appendChild(cbadge);
          mapStage.appendChild(clusterBtn);
          pins["__cluster_fr__"] = { btn: clusterBtn, stage: mapStage };
        }

        var insetMap = document.getElementById("pos-inset-map");
        var insetSVG = null;
        if (insetMap && ZOOM_VB) {
          insetSVG = document.createElementNS(SVG_NS, "svg");
          insetSVG.setAttribute("viewBox", geo.zoom.viewBox);
          insetSVG.setAttribute("xmlns", SVG_NS);
          insetSVG.setAttribute("aria-hidden", "true");
          insetSVG.setAttribute("role", "presentation");

          Object.keys(geo.cantons).forEach(function (id) {
            var p = document.createElementNS(SVG_NS, "path");
            p.setAttribute("d", geo.cantons[id]);
            var klass = "canton";
            if (HAS_POS_CANTONS[ID_TO_CANTON[id]]) klass += " has-pos";
            if (SOON_CANTONS[ID_TO_CANTON[id]]) klass += " soon";
            p.setAttribute("class", klass);
            p.setAttribute("data-canton-id", id);
            insetSVG.appendChild(p);
          });
          insetMap.appendChild(insetSVG);

          frLocs.forEach(function (loc, idx) {
            var pos = geo.loc[loc];
            var count = byLoc[loc] ? byLoc[loc].length : 0;
            var leftPct = (pos[0] - cropX) / cropW * 100;
            var topPct = (pos[1] - cropY) / cropH * 100;
            var btn = document.createElement("button");
            btn.type = "button";
            btn.className = "map-pin";
            btn.style.left = leftPct + "%";
            btn.style.top = topPct + "%";
            btn.style.setProperty("--d", (idx * 0.06).toFixed(2) + "s");
            btn.setAttribute("data-loc", loc);
            btn.setAttribute("data-count", String(count));
            btn.setAttribute("aria-label", loc + " — " + count + " commerce" + (count > 1 ? "s" : ""));
            btn.setAttribute("aria-describedby", "pos-inset-tip");
            var dot = document.createElement("span");
            dot.className = "dot";
            dot.setAttribute("aria-hidden", "true");
            btn.appendChild(dot);
            if (count > 1) {
              var badge = document.createElement("span");
              badge.className = "badge";
              badge.setAttribute("aria-hidden", "true");
              badge.textContent = String(count);
              btn.appendChild(badge);
            }
            insetMap.appendChild(btn);
            pins[loc] = { btn: btn, stage: insetMap };
          });

          var insetTip = document.createElement("div");
          insetTip.id = "pos-inset-tip";
          insetTip.className = "map-tip";
          insetTip.setAttribute("role", "tooltip");
          insetTip.setAttribute("aria-hidden", "true");
          insetMap.appendChild(insetTip);
        }

        if (mapLegend) {
          var perCanton = {};
          POS.forEach(function (p) { perCanton[p.c] = (perCanton[p.c] || 0) + 1; });
          var orderedC = [];
          CANTONS.forEach(function (c) {
            if (perCanton[c]) orderedC.push({ name: c, n: perCanton[c] });
          });
          var soonNames = Object.keys(SOON_CANTONS);
          if (soonNames.length) orderedC.push({ name: "Bientôt (" + soonNames.join(", ") + ")", n: 0 });
          mapLegend.innerHTML = orderedC.map(function (c) {
            return '<span class="leg"><span class="dot"></span>' + c.name +
              (c.n ? ' <span class="cnt">' + c.n + '</span>' : '') + '</span>';
          }).join("");
        }

        function tipFor(stageEl) {
          if (!stageEl) return null;
          return stageEl.querySelector(".map-tip");
        }
        function showTipFor(stageEl, loc, anchor) {
          var tip = tipFor(stageEl);
          if (!tip) return;
          var html;
          if (loc === "__cluster_fr__") {
            html = '<b>Canton de Fribourg</b>' +
              '<div class="tip-canton">' + frLocs.length + ' localités</div>' +
              '<p style="margin:6px 0 0;color:var(--ink-soft);font-size:.82rem;">Cliquez pour voir le zoom détaillé.</p>';
          } else {
            var items = byLoc[loc] || [];
            var canton = items.length ? items[0].c : "";
            html = '<b>' + loc + '</b>' +
              '<div class="tip-canton">' + canton + '</div>' +
              '<ul>' + items.map(function (it) { return '<li>' + it.n + '</li>'; }).join("") + '</ul>';
          }
          tip.innerHTML = html;
          var stageRect = stageEl.getBoundingClientRect();
          var anchorRect = anchor.getBoundingClientRect();
          var x = anchorRect.left - stageRect.left + anchorRect.width / 2;
          var y = anchorRect.top - stageRect.top;
          tip.style.left = x + "px";
          tip.style.top = y + "px";
          tip.classList.remove("flip");
          var flipThresh = (stageEl === insetMap) ? stageRect.height * 0.45 : 110;
          if (y < flipThresh) tip.classList.add("flip");
          tip.classList.add("show");
          tip.setAttribute("aria-hidden", "false");
        }
        function hideTipFor(stageEl) {
          var tip = tipFor(stageEl);
          if (!tip) return;
          tip.classList.remove("show");
          tip.setAttribute("aria-hidden", "true");
        }

        Object.keys(pins).forEach(function (loc) {
          var entry = pins[loc];
          var btn = entry.btn;
          var stage = entry.stage;
          btn.addEventListener("mouseenter", function () { showTipFor(stage, loc, btn); });
          btn.addEventListener("focus", function () { showTipFor(stage, loc, btn); });
          btn.addEventListener("mouseleave", function () { hideTipFor(stage); });
          btn.addEventListener("blur", function () { hideTipFor(stage); });
        });

        function hideAllTips() {
          hideTipFor(mapStage);
          if (insetMap) hideTipFor(insetMap);
        }
        mapStage.addEventListener("keydown", function (e) {
          if (e.key === "Escape") {
            hideAllTips();
            var a = document.activeElement;
            if (a && pins[a.getAttribute("data-loc") || ""]) a.blur();
          }
        });
        if (insetMap) {
          insetMap.addEventListener("keydown", function (e) {
            if (e.key === "Escape") {
              hideAllTips();
              var a = document.activeElement;
              if (a && pins[a.getAttribute("data-loc") || ""]) a.blur();
            }
          });
        }

        function setHiPin(loc, on) {
          var entry = pins[loc];
          if (entry) entry.btn.classList.toggle("hi", !!on);
        }
        function setDimPin(loc, dim) {
          var entry = pins[loc];
          if (entry) entry.btn.classList.toggle("dim", !!dim);
        }
        function clearCantonLit() {
          svg.querySelectorAll(".canton.lit").forEach(function (el) { el.classList.remove("lit"); });
          if (insetSVG) insetSVG.querySelectorAll(".canton.lit").forEach(function (el) { el.classList.remove("lit"); });
        }
        function lightCanton(canton) {
          clearCantonLit();
          if (!canton || canton === "Tous") return;
          var id = CANTON_TO_ID[canton];
          if (!id) return;
          var p1 = svg.querySelector('[data-canton-id="' + id + '"]');
          if (p1) p1.classList.add("lit");
          if (insetSVG) {
            var p2 = insetSVG.querySelector('[data-canton-id="' + id + '"]');
            if (p2) p2.classList.add("lit");
          }
        }

        function isFrLoc(loc) { return frLocs.indexOf(loc) !== -1; }
        posRoot.addEventListener("mouseover", function (e) {
          var card = e.target.closest && e.target.closest(".pos-card");
          if (!card) return;
          var loc = card.getAttribute("data-loc");
          if (!loc) return;
          if (isFrLoc(loc)) { setHiPin("__cluster_fr__", true); setHiPin(loc, true); }
          else setHiPin(loc, true);
        });
        posRoot.addEventListener("mouseout", function (e) {
          var card = e.target.closest && e.target.closest(".pos-card");
          if (!card) return;
          var loc = card.getAttribute("data-loc");
          if (!loc) return;
          if (isFrLoc(loc)) { setHiPin("__cluster_fr__", false); setHiPin(loc, false); }
          else setHiPin(loc, false);
        });
        posRoot.addEventListener("focusin", function (e) {
          var card = e.target.closest && e.target.closest(".pos-card");
          if (!card) return;
          var loc = card.getAttribute("data-loc");
          if (!loc) return;
          if (isFrLoc(loc)) { setHiPin("__cluster_fr__", true); setHiPin(loc, true); }
          else setHiPin(loc, true);
        });
        posRoot.addEventListener("focusout", function (e) {
          var card = e.target.closest && e.target.closest(".pos-card");
          if (!card) return;
          var loc = card.getAttribute("data-loc");
          if (!loc) return;
          if (isFrLoc(loc)) { setHiPin("__cluster_fr__", false); setHiPin(loc, false); }
          else setHiPin(loc, false);
        });

        posRoot.addEventListener("click", function (e) {
          var btn = e.target.closest && e.target.closest(".pos-locate");
          if (!btn) return;
          var loc = btn.getAttribute("data-loc");
          if (!loc) return;
          var card = posRoot.querySelector('.pos-card[data-loc="' + (loc || "").replace(/"/g, "\\\"") + '"]');
          if (card) {
            try { card.scrollIntoView({ behavior: reduceMotion ? "auto" : "smooth", block: "center" }); } catch (err) {}
            card.classList.add("flash");
            setTimeout(function () { card.classList.remove("flash"); }, 1800);
          }
          if (isFrLoc(loc)) {
            setHiPin("__cluster_fr__", true); setHiPin(loc, true);
            setTimeout(function () { setHiPin("__cluster_fr__", false); setHiPin(loc, false); }, 1800);
          } else {
            setHiPin(loc, true);
            setTimeout(function () { setHiPin(loc, false); }, 1800);
          }
        });

        function clickPin(loc) {
          var targetLocs = (loc === "__cluster_fr__") ? frLocs.slice() : [loc];
          var firstCard = null;
          var allCards = [];
          targetLocs.forEach(function (l) {
            var cs = posRoot.querySelectorAll('.pos-card[data-loc="' + (l || "").replace(/"/g, "\\\"") + '"]');
            cs.forEach(function (c) { allCards.push(c); if (!firstCard) firstCard = c; });
          });
          if (firstCard) {
            try { firstCard.scrollIntoView({ behavior: reduceMotion ? "auto" : "smooth", block: "center" }); } catch (err) {}
            allCards.forEach(function (c) {
              c.classList.add("flash");
              if (!c.hasAttribute("tabindex")) c.setAttribute("tabindex", "-1");
              setTimeout(function () { c.classList.remove("flash"); }, 1800);
            });
            try { firstCard.focus({ preventScroll: true }); } catch (err) {}
          }
          if (liveStatus) {
            var n = allCards.length;
            if (loc === "__cluster_fr__") {
              liveStatus.textContent = n + " commerces répartis sur " + frLocs.length + " localités fribourgeoises mis en évidence.";
            } else {
              liveStatus.textContent = n + " commerce" + (n > 1 ? "s" : "") + " à " + loc + " mis en évidence.";
            }
          }
        }
        function clickCluster() {
          var inset = document.getElementById("pos-inset");
          if (inset) {
            inset.classList.remove("flash");
            void inset.offsetWidth;
            inset.classList.add("flash");
            setTimeout(function () { inset.classList.remove("flash"); }, 1200);
            var r = inset.getBoundingClientRect();
            if (r.top > window.innerHeight || r.bottom < 0) {
              try { inset.scrollIntoView({ behavior: reduceMotion ? "auto" : "smooth", block: "center" }); } catch (err) {}
            }
          }
          clickPin("__cluster_fr__");
        }
        Object.keys(pins).forEach(function (loc) {
          var entry = pins[loc];
          entry.btn.addEventListener("click", function () {
            if (loc === "__cluster_fr__") clickCluster();
            else clickPin(loc);
          });
        });

        if (!reduceMotion && "IntersectionObserver" in window) {
          var pinIO = new IntersectionObserver(function (entries) {
            entries.forEach(function (e) {
              if (e.isIntersecting) {
                mapStage.classList.add("pins-in");
                if (insetMap) insetMap.classList.add("pins-in");
                pinIO.unobserve(e.target);
              }
            });
          }, { threshold: 0.18 });
          pinIO.observe(mapStage);
        } else {
          mapStage.classList.add("pins-in");
          if (insetMap) insetMap.classList.add("pins-in");
        }

        return {
          syncVisible: function (visibleLocs) {
            Object.keys(pins).forEach(function (loc) {
              if (loc === "__cluster_fr__") {
                var anyFr = frLocs.some(function (l) { return visibleLocs.indexOf(l) !== -1; });
                setDimPin("__cluster_fr__", !anyFr);
              } else {
                setDimPin(loc, visibleLocs.indexOf(loc) === -1);
              }
            });
          },
          lightCanton: lightCanton
        };
      })();

    }

    (function setupCountUp() {
      var els = document.querySelectorAll(".pos-stats b[data-countup]");
      if (!els.length) return;
      var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      function animate(el) {
        if (reduce) return;
        var target = parseInt(el.getAttribute("data-countup"), 10) || parseInt(el.textContent, 10) || 0;
        var dur = 1200;
        var t0 = null;
        function step(t) {
          if (!t0) t0 = t;
          var p = Math.min(1, (t - t0) / dur);
          var eased = 1 - Math.pow(1 - p, 3);
          el.textContent = Math.round(target * eased);
          if (p < 1) requestAnimationFrame(step);
        }
        requestAnimationFrame(step);
      }
      if ("IntersectionObserver" in window && !reduce) {
        var io = new IntersectionObserver(function (entries) {
          entries.forEach(function (e) {
            if (e.isIntersecting) {
              animate(e.target);
              io.unobserve(e.target);
            }
          });
        }, { threshold: 0.4 });
        els.forEach(function (el) { io.observe(el); });
      }
    })();

    function render() {
      var q = searchInput ? norm(searchInput.value.trim()) : "";
      var html = "";
      var cantonsToShow = activeCanton === "Tous" ? CANTONS : [activeCanton];

      cantonsToShow.forEach(function (canton) {
        var items = POS.filter(function (p) {
          return p.c === canton && (!q || norm(p.n + " " + p.a + " " + (p.loc || "")).indexOf(q) !== -1);
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
        html += '<div class="pos-grid anim">' + items.map(function (p, i) { return cardHtml(p, i); }).join("") + "</div>";
      });

      if (!html) {
        html = '<div class="empty-canton"><b>Aucun résultat.</b> Essayez un autre nom de commerce ou de localité.</div>';
      }
      posRoot.innerHTML = html;

      var n = totalShown();
      announce(n, activeCanton);

      if (countEl) {
        countEl.textContent = n + " adresse" + (n > 1 ? "s" : "");
      }

      if (mapModule) {
        var visibleLocs = {};
        posRoot.querySelectorAll(".pos-card").forEach(function (card) {
          var l = card.getAttribute("data-loc");
          if (l) visibleLocs[l] = true;
        });
        mapModule.syncVisible(Object.keys(visibleLocs));
        mapModule.lightCanton(activeCanton);
      }
    }

    if (chipRow) {
      var counts = {};
      CANTONS.forEach(function (c) {
        counts[c] = POS.filter(function (p) { return p.c === c; }).length;
      });
      var chips = ["Tous"].concat(CANTONS);
      chipRow.innerHTML = chips.map(function (c) {
        var count = c === "Tous" ? POS.length : counts[c];
        var pressed = c === "Tous" ? "true" : "false";
        return '<button class="chip' + (c === "Tous" ? " active" : "") +
          '" type="button" data-canton="' + c + '" aria-pressed="' + pressed + '">' +
          c + ' <span class="count">' + count + "</span></button>";
      }).join("");
      chipRow.addEventListener("click", function (e) {
        var btn = e.target.closest(".chip");
        if (!btn) return;
        activeCanton = btn.dataset.canton;
        chipRow.querySelectorAll(".chip").forEach(function (ch) {
          var isActive = ch === btn;
          ch.classList.toggle("active", isActive);
          ch.setAttribute("aria-pressed", isActive ? "true" : "false");
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
    var formFeedback = document.getElementById("contact-feedback");

    // Bouton principal : détecté par son type (submit explicite) ou, à défaut,
    // premier bouton du formulaire (HTML5 default <button> = type="submit").
    var submitBtn = form.querySelector('button[type="submit"]') || form.querySelector("button");
    var submitLabel = submitBtn ? (submitBtn.textContent || "").trim() || "Ouvrir ma messagerie" : "Ouvrir ma messagerie";

    // Bouton de copie du message préparé. Priorité : un bouton déjà présent
    // dans le DOM (#contact-copy), sinon injection. Toujours inséré APRÈS le
    // bouton principal pour rester accessible au clavier.
    var copyEl = document.getElementById("contact-copy");
    if (!copyEl && submitBtn && submitBtn.parentNode) {
      copyEl = document.createElement("button");
      copyEl.type = "button";
      copyEl.id = "contact-copy";
      copyEl.className = "btn ghost small";
      copyEl.textContent = "Copier le message";
      submitBtn.parentNode.insertBefore(copyEl, submitBtn.nextSibling);
    }

    if (!formFeedback) {
      formFeedback = document.createElement("p");
      formFeedback.id = "contact-feedback";
      formFeedback.className = "form-hint";
      formFeedback.setAttribute("role", "status");
      formFeedback.setAttribute("aria-live", "polite");
      form.appendChild(formFeedback);
    }

    function buildMessage() {
      var get = function (id) { return (document.getElementById(id) || {}).value || ""; };
      var nom = get("f-nom"), mail = get("f-email"), soc = get("f-societe");
      var sujet = get("f-sujet"), question = get("f-question");
      return {
        body: "Nom : " + nom + "\nE-mail : " + mail +
          (soc ? "\nSociété : " + soc : "") + "\n\n" + question,
        subject: "[thecol.ch] " + sujet,
        to: "commande@thecol.ch"
      };
    }

    function setFeedback(msg, isError) {
      formFeedback.textContent = msg;
      formFeedback.style.color = isError ? "var(--red)" : "var(--green-700)";
    }

    // Listener unique sur "submit" : le navigateur ne déclenche l'event que si
    // tous les champs requis sont valides (validation HTML native). On n'a donc
    // jamais à court-circuiter un champ invalide : si quoi que ce soit est
    // invalide, le navigateur affiche les bulles natives et l'event n'arrive
    // pas ici. preventDefault évite la soumission GET native (recharge avec
    // paramètres en query string), puis on ouvre une seule URL mailto.
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var m = buildMessage();
      formFeedback.textContent = "";
      window.location.href = "mailto:" + m.to +
        "?subject=" + encodeURIComponent(m.subject) +
        "&body=" + encodeURIComponent(m.body);
    });

    if (copyEl) {
      copyEl.addEventListener("click", function () {
        if (!form.checkValidity()) {
          setFeedback("Merci de remplir les champs requis avant de copier le message.", true);
          // Focalise le premier champ invalide pour faciliter la correction
          var firstInvalid = form.querySelector(":invalid");
          if (firstInvalid) firstInvalid.focus();
          return;
        }
        var m = buildMessage();
        var text = "À : " + m.to + "\nObjet : " + m.subject + "\n\n" + m.body;
        var done = function (ok) {
          if (ok) {
            setFeedback("Message copié dans le presse-papiers. Vous pouvez le coller (Ctrl/Cmd+V) dans votre messagerie avant de l'envoyer.", false);
          } else {
            // Libellé du bouton principal lu sur le DOM pour rester synchro.
            setFeedback("Copie impossible dans ce navigateur. Utilisez le bouton « " + submitLabel + " » pour ouvrir votre messagerie.", true);
          }
        };
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(text).then(function () { done(true); }, function () { fallbackCopy(text, done); });
        } else {
          fallbackCopy(text, done);
        }
      });
    }
  }

  function fallbackCopy(text, cb) {
    try {
      var ta = document.createElement("textarea");
      ta.value = text;
      ta.setAttribute("readonly", "");
      ta.style.position = "fixed";
      ta.style.top = "-1000px";
      ta.style.opacity = "0";
      document.body.appendChild(ta);
      ta.select();
      var ok = false;
      try { ok = document.execCommand("copy"); } catch (e) { ok = false; }
      document.body.removeChild(ta);
      cb(ok);
    } catch (e) {
      cb(false);
    }
  }

  /* ==================================================================
     Boutique : catalogue, panier (localStorage) et fiche produit
     ================================================================== */

  var PRODUCTS = {
    hibiscus: { name: "Hibiscus", img: "assets/web/produit-hibiscus.jpg", page: "produit-hibiscus.html", formats: { 25: 3.0, 50: 5.0, 100: 8.5 } },
    mures:    { name: "Mûres sauvages", img: "assets/web/produit-mures.jpg", page: "produit-mures.html", formats: { 25: 3.0, 50: 5.0, 100: 8.5 } },
    sureau:   { name: "Fleur de Sureau", img: "assets/web/produit-sureau.jpg", page: "produit-sureau.html", formats: { 25: 3.0, 50: 5.0, 100: 8.5 } },
    herbes:   { name: "Herbes des Alpes", img: "assets/web/produit-herbes.jpg", page: "produit-herbes.html", formats: { 25: 3.0, 50: 5.0, 100: 8.5 } },
    poire:    { name: "Poire à Botzi", img: "assets/web/produit-poire.jpg", page: "produit-poire.html", formats: { 25: 3.0, 50: 5.0, 100: 8.5 } }
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

  /* Tiroir : injecté une fois dans chaque page.
     Texte : "Demande de commande par e-mail" — pas une commande confirmée.
     Le mailto déclenche la messagerie, sans message de confirmation mensonger. */
  var CART_TITLE_ID = "cart-title";
  var drawerHtml =
    '<div class="cart-overlay" id="cart-overlay" hidden></div>' +
    '<aside class="cart-drawer" id="cart-drawer" role="dialog" aria-modal="true"' +
    ' aria-labelledby="' + CART_TITLE_ID + '">' +
    '  <div class="cart-head"><h3 id="' + CART_TITLE_ID + '">Demande de commande par e-mail</h3>' +
    '  <button class="cart-close" id="cart-close" aria-label="Fermer le panier" type="button">&times;</button></div>' +
    '  <div class="cart-items" id="cart-items"></div>' +
    '  <div class="cart-foot" id="cart-foot">' +
    '    <div class="cart-total">Total <b id="cart-total">CHF 0.00</b></div>' +
    '    <button class="btn" id="cart-checkout" type="button">Envoyer la demande par e-mail</button>' +
    '    <a class="btn ghost small cart-online" id="cart-online" href="https://www.thecol.ch/shop" target="_blank" rel="noopener">Acheter et payer en ligne</a>' +
    '    <p class="cart-note">Cette action ouvre votre messagerie avec un message prérempli à commande@thecol.ch&nbsp;: aucune commande n’est confirmée tant que nous n’avons pas répondu. Pour payer directement par carte ou PayPal, utilisez le bouton « Acheter et payer en ligne » ci-dessus (paiement sécurisé géré dans Odoo).</p>' +
    '  </div>' +
    '</aside>';
  document.body.insertAdjacentHTML("beforeend", drawerHtml);

  var drawer = document.getElementById("cart-drawer");
  var drawerItems = document.getElementById("cart-items");
  var drawerFoot = document.getElementById("cart-foot");
  var drawerTotal = document.getElementById("cart-total");
  var drawerOverlay = document.getElementById("cart-overlay");

  // État d'ouverture et mémorisation du déclencheur
  var lastCartTrigger = null;
  function isCartOpen() { return document.body.classList.contains("cart-open"); }

  function lockScroll() {
    if (document.body.dataset.scrollLocked === "1") return;
    // Compensation pour la disparition de la scrollbar afin d'éviter tout décalage
    var sbw = window.innerWidth - document.documentElement.clientWidth;
    if (sbw > 0) document.body.style.paddingRight = sbw + "px";
    document.body.style.overflow = "hidden";
    document.body.dataset.scrollLocked = "1";
  }
  function unlockScroll() {
    if (document.body.dataset.scrollLocked !== "1") return;
    document.body.style.overflow = "";
    document.body.style.paddingRight = "";
    delete document.body.dataset.scrollLocked;
  }

  function setBackgroundInert(inert) {
    // Tout sauf le tiroir et son overlay
    var siblings = document.body.children;
    for (var i = 0; i < siblings.length; i++) {
      var el = siblings[i];
      if (el === drawer || el === drawerOverlay) continue;
      if (inert) {
        if ("inert" in el) {
          try { el.inert = true; } catch (e) {}
        } else {
          el.setAttribute("aria-hidden", "true");
        }
      } else {
        if ("inert" in el) {
          try { el.inert = false; } catch (e) {}
        } else {
          el.removeAttribute("aria-hidden");
        }
      }
    }
  }

  function focusableInDrawer() {
    return Array.prototype.slice.call(drawer.querySelectorAll(focusableSelector()))
      .filter(function (el) { return !el.disabled && el.offsetParent !== null; });
  }

  function trapTab(e) {
    if (e.key !== "Tab") return;
    var items = focusableInDrawer();
    if (!items.length) {
      e.preventDefault();
      drawer.focus();
      return;
    }
    var first = items[0];
    var last = items[items.length - 1];
    var active = document.activeElement;
    if (e.shiftKey && (active === first || !drawer.contains(active))) {
      e.preventDefault();
      last.focus();
    } else if (!e.shiftKey && (active === last || !drawer.contains(active))) {
      e.preventDefault();
      first.focus();
    }
  }

  function cartOpen() {
    if (isCartOpen()) return;
    lastCartTrigger = document.activeElement;
    setMenuOpen(false);
    document.body.classList.add("cart-open");
    drawerOverlay.hidden = false;
    lockScroll();
    setBackgroundInert(true);
    // Focus sur le bouton de fermeture dès l'ouverture
    setTimeout(function () {
      var closeBtn = document.getElementById("cart-close");
      if (closeBtn) closeBtn.focus();
    }, 0);
  }

  function cartClose() {
    if (!isCartOpen()) return;
    document.body.classList.remove("cart-open");
    drawerOverlay.hidden = true;
    unlockScroll();
    setBackgroundInert(false);
    // Retour du focus sur l'élément déclencheur
    var t = lastCartTrigger;
    lastCartTrigger = null;
    if (t && typeof t.focus === "function") {
      try { t.focus(); } catch (e) {}
    }
  }

  drawerOverlay.addEventListener("click", cartClose);
  document.getElementById("cart-close").addEventListener("click", cartClose);

  // Escape : seulement si le tiroir est ouvert, et on ferme le panier même si le focus est ailleurs
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && isCartOpen()) {
      e.preventDefault();
      cartClose();
      return;
    }
    if (isCartOpen()) trapTab(e);
  });

  // Liens internes du tiroir : on s'assure que la fermeture ne laisse pas l'état inaccessible
  drawer.addEventListener("click", function (e) {
    var link = e.target.closest && e.target.closest("a[href]");
    if (!link) return;
    // Liens externes (target=_blank) ou mailto : laisser le comportement natif, mais on ferme quand même
    cartClose();
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
    var body = "Bonjour,\n\nJe souhaite passer commande des articles suivants :\n" + lines.join("\n") +
      "\n\nTotal indicatif : " + chf(cartTotal(items)) +
      "\n\nMerci de me confirmer la disponibilité, les frais de livraison et les modalités de paiement.\n\nNom :\nAdresse de livraison :\nTéléphone (facultatif) :";
    // Simple déclenchement du client mail, sans message de confirmation serveur.
    window.location.href = "mailto:commande@thecol.ch" +
      "?subject=" + encodeURIComponent("[thecol.ch] Demande de commande") +
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
        '<button data-ci-dec="' + i + '" aria-label="Réduire la quantité" type="button">&minus;</button>' +
        '<input type="number" value="' + it.qty + '" readonly aria-label="Quantité">' +
        '<button data-ci-inc="' + i + '" aria-label="Augmenter la quantité" type="button">+</button>' +
        "</div></div>" +
        '<div class="ci-right"><span class="ci-price">' + chf(p.formats[it.size] * it.qty) + "</span>" +
        '<button class="ci-remove" data-ci-rm="' + i + '" type="button">Retirer</button></div>' +
        "</div>";
    }).join("");
  }

  drawerItems.addEventListener("click", function (e) {
    var items = cartLoad();
    var t = e.target;
    if (!t || !t.dataset) return;
    if (t.dataset.ciDec !== undefined) {
      var d = items[+t.dataset.ciDec];
      if (d) { d.qty -= 1; if (d.qty <= 0) items.splice(+t.dataset.ciDec, 1); }
    } else if (t.dataset.ciInc !== undefined) {
      var inc = items[+t.dataset.ciInc];
      if (inc) inc.qty = Math.min(99, inc.qty + 1);
    } else if (t.dataset.ciRm !== undefined) {
      items.splice(+t.dataset.ciRm, 1);
    } else { return; }
    var action = t.hasAttribute("data-ci-dec") ? "data-ci-dec" :
      t.hasAttribute("data-ci-inc") ? "data-ci-inc" : "data-ci-rm";
    var focusIndex = Math.min(+t.getAttribute(action), items.length - 1);
    cartSave(items);
    // Le rendu remplace le bouton activé : retrouver le même contrôle, ou
    // l'article voisin après suppression, puis le lien du panier vide.
    var nextFocus = drawerItems.querySelector('[' + action + '="' + focusIndex + '"]') ||
      drawerItems.querySelector(".cart-empty a") || document.getElementById("cart-close");
    nextFocus.focus();
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
