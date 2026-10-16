/* Keep the listing URL in real links; storage only enhances scroll restoration. */
(function () {
    "use strict";
    var key = "shop-catalog-position", restoreKey = "shop-catalog-restore";
    function read(name) { try { return JSON.parse(sessionStorage.getItem(name)); } catch (_) { return null; } }
    function write(name, value) { try { sessionStorage.setItem(name, JSON.stringify(value)); } catch (_) {} }
    function localPath(url) { var target = new URL(url, location.href); return target.pathname + target.search; }
    document.addEventListener("click", function (event) {
        var link = event.target.closest("a");
        if (!link) return;
        if (link.hasAttribute("data-product-link") && document.getElementById("catalog-results")) {
            write(key, { url: location.pathname + location.search, y: window.scrollY, time: Date.now() });
        }
        if (link.hasAttribute("data-catalog-back")) {
            var saved = read(key);
            if (saved && saved.url === localPath(link.href) && Date.now() - saved.time < 1800000) write(restoreKey, saved);
        }
    });
    window.addEventListener("pageshow", function () {
        if (!document.getElementById("catalog-results")) return;
        var saved = read(restoreKey);
        if (!saved || saved.url !== location.pathname + location.search || Date.now() - saved.time >= 1800000) return;
        try { sessionStorage.removeItem(restoreKey); } catch (_) {}
        window.requestAnimationFrame(function () { window.scrollTo({ top: saved.y, behavior: "instant" }); });
    });
})();
