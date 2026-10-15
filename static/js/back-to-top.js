(function () {
    "use strict";

    function initBackToTop() {
        var button = document.getElementById("shop-back-to-top");
        if (!button) {
            return;
        }

        button.addEventListener("click", function () {
            window.scrollTo({ top: 0, behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" });
        });

        /* Storefront: scroll reveal is driven together with menu FAB in header.js */
        if (
            !document.getElementById("shopHeaderFab") &&
            typeof window.shopInitScrollFloatControls === "function"
        ) {
            window.shopInitScrollFloatControls([{ el: button, manageAria: false }]);
        }
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initBackToTop);
    } else {
        initBackToTop();
    }
})();
