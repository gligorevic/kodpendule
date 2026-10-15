(function () {
    "use strict";
    document.addEventListener("DOMContentLoaded", function () {
        var form = document.getElementById("shop-checkout-form");
        if (!form) return;
        var errorSummary = form.querySelector("[data-checkout-errors]");
        if (errorSummary) {
            errorSummary.focus();
            errorSummary.addEventListener("click", function (event) {
                var link = event.target.closest('a[href^="#checkout-field-"]');
                if (!link) return;
                var field = document.getElementById(link.hash.slice(1));
                var input = field && field.querySelector("input:not([type=hidden]):not(:disabled), select, textarea");
                if (input) { event.preventDefault(); input.focus(); input.scrollIntoView({ block: "center" }); }
            });
        }
        var submitting = false;
        var submitButtons = document.querySelectorAll('#shop-checkout-form button[type="submit"], button[form="shop-checkout-form"]');
        var saving = form.querySelector("[data-checkout-saving]");
        function resetSubmit() {
            submitting = false; form.removeAttribute("aria-busy"); saving.hidden = true;
            submitButtons.forEach(function (button) { button.disabled = false; button.classList.remove("is-loading"); });
        }
        form.addEventListener("submit", function (event) {
            if (submitting) { event.preventDefault(); return; }
            submitting = true; form.setAttribute("aria-busy", "true"); saving.hidden = false;
            submitButtons.forEach(function (button) { button.disabled = true; button.classList.add("is-loading"); });
        });
        window.addEventListener("pageshow", resetSubmit);

        var summary = document.querySelector("[data-checkout-subtotal]");
        var city = document.getElementById("id_shipping_city");
        var date = document.getElementById("id_requested_delivery_date");
        var dateRow = document.getElementById("shop-delivery-date-row");
        var hint = document.getElementById("checkout-shipping-hint");
        var subtotal = Number(summary.dataset.checkoutSubtotal);
        var cities, today;
        try {
            cities = JSON.parse(document.getElementById("city-delivery-data").textContent);
            today = JSON.parse(document.getElementById("checkout-today-data").textContent);
        } catch (error) { return; } // Keep the server-rendered form usable if pricing data is unavailable.
        var currency = summary.dataset.currency || "RSD";
        function amount(value) {
            return Number(value).toLocaleString("sr-RS", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
        }
        function money(value) { return amount(value) + " " + currency; }
        function refresh() {
            var selected = form.querySelector('input[name="delivery_timing"]:checked');
            var scheduled = selected && selected.value === "scheduled";
            dateRow.hidden = !scheduled; date.disabled = !scheduled; date.required = !!scheduled;
            var validDate = scheduled && date.value > today && date.checkValidity();
            var rules = cities[city.value];
            var shipping = null, hintText = "";
            if (rules && (!scheduled || validDate)) {
                if (scheduled) {
                    shipping = 0; hintText = hint.dataset.msgScheduledFree || "";
                } else {
                    shipping = Number(rules.base);
                    var threshold = Number(rules.threshold);
                    if (threshold > 0 && subtotal >= threshold) {
                        if (rules.threshold_shipping_mode === "free") {
                            shipping = 0; hintText = hint.dataset.msgFree || "";
                        } else if (rules.discounted_shipping_price !== "") {
                            shipping = Number(rules.discounted_shipping_price);
                            hintText = hint.dataset.msgDiscounted || "";
                        }
                    } else if (threshold > subtotal) {
                        hintText = (hint.dataset.msgRemaining || "").replace("__AMOUNT__", amount(threshold - subtotal));
                    }
                }
            }
            var known = shipping !== null && Number.isFinite(shipping) && Number.isFinite(subtotal);
            var pendingText = !rules ? summary.dataset.cityPending : summary.dataset.datePending;
            document.querySelectorAll(".js-shipping-price").forEach(function (el) { el.textContent = known ? money(shipping) : pendingText; });
            document.querySelectorAll("[data-checkout-total]").forEach(function (el) {
                el.textContent = known ? money(subtotal + shipping) : summary.dataset.totalPending;
                el.classList.toggle("is-pending", !known);
            });
            hint.textContent = hintText; hint.hidden = !hintText;
        }
        city.addEventListener("change", refresh); date.addEventListener("change", refresh);
        form.querySelectorAll('input[name="delivery_timing"]').forEach(function (radio) { radio.addEventListener("change", refresh); });
        refresh();
    });
})();
