/**
 * Kod Pendule — storefront UX polish (form submit feedback)
 */
(function () {
    "use strict";

    document.addEventListener("DOMContentLoaded", function () {
        document.querySelectorAll("form").forEach(function (form) {
            if (
                form.hasAttribute("data-shop-add-cart")
                || form.hasAttribute("data-cart-quantity-form")
                || form.hasAttribute("data-cart-remove-form")
                || form.closest(".shop-header")
                || form.closest(".shop-offcanvas")
                || form.closest(".shop-header-panel")
            ) {
                return;
            }
            form.addEventListener(
                "submit",
                function () {
                    var btn = form.querySelector(
                        'button[type="submit"].shop-btn, button[type="submit"].btn-primary, button[type="submit"].btn'
                    );
                    if (!btn || btn.disabled || btn.classList.contains("is-loading")) {
                        return;
                    }
                    btn.classList.add("is-loading");
                    btn.setAttribute("aria-busy", "true");
                },
                { once: false }
            );
        });
    });
})();
