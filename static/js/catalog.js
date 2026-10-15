/* Progressive enhancement: native GET forms continue to work without JavaScript. */
(function () {
    "use strict";
    var form = document.getElementById("shop-search");
    var controls = document.querySelector(".shop-catalog-controls");
    var results = document.getElementById("catalog-results");
    if (!form || !controls || !form.requestSubmit) return;
    var apply = controls.querySelector("[data-catalog-apply]");
    var help = document.getElementById("catalog-auto-help");
    if (apply) apply.hidden = true;
    if (help) help.hidden = false;
    controls.querySelectorAll("[data-catalog-control]").forEach(function (input) {
        input.setAttribute("aria-describedby", "catalog-auto-help");
        input.addEventListener("change", function () { form.requestSubmit(); });
    });
    form.addEventListener("submit", function () {
        if (results) results.setAttribute("aria-busy", "true");
    });
    window.addEventListener("pageshow", function () {
        if (results) results.removeAttribute("aria-busy");
    });
    // Pagination/filter navigation lands below the sticky header and puts
    // keyboard and screen-reader users at the refreshed product list.
    if (location.hash === "#catalog-results" && results) {
        results.focus({ preventScroll: true });
    }
})();
