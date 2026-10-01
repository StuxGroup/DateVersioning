/* Date Versioning - shared behaviour. Copyright (c) 2026 Stux.Group. All rights reserved. */
(function () {
  "use strict";

  // Dev-only banner in the shared site-banner component (dev-server forces DEV_MODE on);
  // ?banner=soon,maintenance,site previews the other styles.
  if (window.DEV_MODE) {
    var copy = {
      maintenance: ["Maintenance", "Date Versioning is being updated and will be back shortly."],
      soon: ["Coming soon", "Date Versioning is launching soon."],
      dev: ["Dev mode", "Local preview of Date Versioning. Run <code>dev-server.sh --no-dev-mode</code> to see it as production does."],
      site: ["Notice", "A site notice for Date Versioning appears here."]
    };
    var want = (new URLSearchParams(location.search).get("banner") || "").split(",");
    var box = document.createElement("div");
    box.className = "site-banners";
    box.setAttribute("data-site-banners", "");
    ["maintenance", "soon", "dev", "site"].forEach(function (v) {
      if (v !== "dev" && want.indexOf(v) < 0) return;
      var d = document.createElement("div");
      d.className = "site-banner site-banner--" + v;
      d.setAttribute("role", "note");
      d.innerHTML = '<span class="site-banner-label"></span><span class="site-banner-text">' + copy[v][1] + "</span>";
      d.firstChild.textContent = copy[v][0];
      box.appendChild(d);
    });
    document.body.insertBefore(box, document.body.firstChild);
    document.documentElement.classList.add("has-site-banner");
    var bs = document.createElement("script");
    bs.src = "/assets/js/site-banner.js";
    document.body.appendChild(bs);
  }

  // Copyright years: CURRENT alone if the start year is the current year, otherwise START-CURRENT.
  var year = new Date().getFullYear();
  document.querySelectorAll("[data-year]").forEach(function (el) {
    var start = parseInt(el.getAttribute("data-year-start"), 10);
    el.textContent = start && start < year ? start + "–" + year : String(year);
  });

  // Copy buttons: data-copy-from="<element id>" copies that element's text.
  document.querySelectorAll("[data-copy-from]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var src = document.getElementById(btn.getAttribute("data-copy-from"));
      if (!src) return;
      var text = src.textContent;
      var done = function () {
        var old = btn.textContent;
        btn.textContent = "Copied";
        setTimeout(function () { btn.textContent = old; }, 1400);
      };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(done, function () {});
        return;
      }
      var ta = document.createElement("textarea");
      ta.value = text;
      ta.setAttribute("readonly", "");
      ta.style.position = "fixed";
      ta.style.opacity = "0";
      document.body.appendChild(ta);
      ta.select();
      try { document.execCommand("copy"); done(); } catch (e) {}
      document.body.removeChild(ta);
    });
  });

  // Table of contents: highlight the section being read.
  var tocLinks = Array.prototype.slice.call(document.querySelectorAll(".toc a[href^='#']"));
  if (tocLinks.length && "IntersectionObserver" in window) {
    var byId = {};
    tocLinks.forEach(function (a) { byId[decodeURIComponent(a.getAttribute("href").slice(1))] = a; });
    var current = null;
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (!e.isIntersecting) return;
        var a = byId[e.target.id];
        if (!a || a === current) return;
        if (current) current.classList.remove("active");
        a.classList.add("active");
        current = a;
      });
    }, { rootMargin: "-90px 0px -70% 0px" });
    Object.keys(byId).forEach(function (id) {
      var el = document.getElementById(id);
      if (el) io.observe(el);
    });
  }
})();
