/* Quantity controls for product cards/details, plus gallery selection feedback. */
(function () {
    "use strict";

    document.addEventListener("DOMContentLoaded", function () {
        document.querySelectorAll("[data-shop-qty]").forEach(function (wrap) {
            var input = wrap.querySelector("input[type='number']");
            var inc = wrap.querySelector("[data-shop-qty-inc]");
            var dec = wrap.querySelector("[data-shop-qty-dec]");
            if (!input || !inc || !dec) return;

            var min = Number(input.min || 1);
            var max = Number(input.max || 9999);
            function value() {
                var number = Number(input.value);
                return Number.isFinite(number) ? Math.min(max, Math.max(min, Math.floor(number))) : min;
            }
            function updateButtons() {
                var current = value();
                dec.disabled = current <= min;
                inc.disabled = current >= max;
            }
            function commit(next) {
                input.value = String(Math.min(max, Math.max(min, next)));
                input.dispatchEvent(new Event("change", { bubbles: true }));
            }
            inc.addEventListener("click", function () { commit(value() + 1); });
            dec.addEventListener("click", function () { commit(value() - 1); });
            // Let people clear and type multi-digit quantities before normalization.
            input.addEventListener("input", updateButtons);
            input.addEventListener("change", function () {
                input.value = String(value());
                updateButtons();
            });
            updateButtons();
        });

        var gallery = document.getElementById("productGallery");
        if (gallery) {
            gallery.addEventListener("slid.bs.carousel", function (event) {
                document.querySelectorAll(".shop-thumb[data-bs-slide-to]").forEach(function (thumb) {
                    var active = Number(thumb.dataset.bsSlideTo) === event.to;
                    thumb.classList.toggle("is-active", active);
                    if (active) thumb.setAttribute("aria-current", "true");
                    else thumb.removeAttribute("aria-current");
                });
            });
        }
    });
})();
