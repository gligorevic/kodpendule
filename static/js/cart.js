/** Cart requests run in order: concurrent writes can otherwise lose session changes. */
(function () {
    "use strict";
    var queue = Promise.resolve();
    var pending = 0;
    var drawer;
    var page;
    var drawerOpener;
    var confirmationTimer;
    var confirmationOpener;
    var rowSelector = "[data-cart-line], [data-cart-drawer-line]";

    function label(key) { return drawer ? drawer.getAttribute("data-i18n-" + key) || "" : ""; }
    function escapeHtml(value) {
        return String(value == null ? "" : value).replace(/&/g, "&amp;").replace(/</g, "&lt;")
            .replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#39;");
    }
    function csrf() {
        var token = document.querySelector('meta[name="csrf-token"]');
        return token ? token.content : "";
    }
    function enqueue(work) {
        var next = queue.then(work);
        queue = next.catch(function () {});
        return next;
    }
    function request(url, body) {
        return fetch(url, {
            method: body ? "POST" : "GET", body: body,
            credentials: "same-origin", cache: "no-store",
            headers: { Accept: "application/json", "X-Requested-With": "XMLHttpRequest" }
        }).then(function (response) {
            return response.json().then(function (data) { return { ok: response.ok && data.ok, data: data }; });
        });
    }
    function announce(message) {
        var region = drawer && drawer.classList.contains("show")
            ? drawer.querySelector("[data-cart-status]") : document.querySelector("[data-cart-page] [data-cart-status]");
        if (region) { region.textContent = ""; window.setTimeout(function () { region.textContent = message; }, 20); }
    }
    function hideConfirmation(restoreFocus) {
        var notice = document.querySelector("[data-cart-confirmation]");
        window.clearTimeout(confirmationTimer);
        if (notice) notice.hidden = true;
        if (restoreFocus && confirmationOpener && confirmationOpener.isConnected) confirmationOpener.focus();
    }
    function scheduleConfirmationHide() {
        window.clearTimeout(confirmationTimer);
        confirmationTimer = window.setTimeout(function () {
            var notice = document.querySelector("[data-cart-confirmation]");
            if (notice && !notice.contains(document.activeElement) && !notice.matches(":hover")) notice.hidden = true;
        }, 6500);
    }
    function showAdded(data, opener) {
        confirmationOpener = opener;
        var notice = document.querySelector("[data-cart-confirmation]");
        if (!notice) return;
        notice.querySelector("[data-cart-confirmation-message]").textContent = data.message;
        notice.querySelector("[data-cart-confirmation-total]").textContent = data.subtotal_display;
        var line = data.lines.find(function (item) { return String(item.product_id) === String(data.product_id); });
        var image = notice.querySelector("img");
        image.hidden = !line || !line.image_url;
        if (line && line.image_url) image.src = line.image_url;
        notice.hidden = false;
        scheduleConfirmationHide();
    }
    function cancelRemoval(form) {
        var confirmation = form.querySelector("[data-cart-remove-confirm]");
        if (confirmation) confirmation.remove();
        var trigger = form.querySelector("button[type=submit]");
        if (trigger) { trigger.hidden = false; trigger.focus(); }
    }
    function confirmRemoval(form) {
        if (form.querySelector("[data-cart-remove-confirm]")) return;
        var panel = document.createElement("div");
        panel.className = "cart-remove-confirm"; panel.setAttribute("data-cart-remove-confirm", "");
        panel.innerHTML = '<span>' + escapeHtml(label("remove-question")) + '</span><div>' +
            '<button type="button" data-cart-remove-cancel>' + escapeHtml(label("keep")) + '</button>' +
            '<button type="button" data-cart-remove-yes>' + escapeHtml(label("remove")) + '</button></div>';
        form.querySelector("button[type=submit]").hidden = true;
        form.appendChild(panel); panel.querySelector("[data-cart-remove-cancel]").focus();
    }
    function clearError(container) {
        var error = container.querySelector("[data-cart-error]"); if (error) error.remove();
    }
    function showError(container, message) {
        clearError(container);
        var error = document.createElement("p"); error.className = "shop-cart-error";
        error.setAttribute("data-cart-error", ""); error.setAttribute("role", "alert");
        error.textContent = message; container.appendChild(error);
    }
    function updateStepper(wrap) {
        var input = wrap.querySelector('input[name="quantity"]');
        var min = Number(input.min || 1), max = Number(input.max);
        var busy = !!wrap.closest('[aria-busy="true"]');
        wrap.querySelector("[data-cart-dec]").disabled = busy || Number(input.value) <= min;
        wrap.querySelector("[data-cart-inc]").disabled = busy || Number(input.value) >= max;
    }
    function setBusy(container, busy) {
        container.setAttribute("aria-busy", String(busy)); container.classList.toggle("is-updating", busy);
        container.querySelectorAll("button, input:not([type=hidden])").forEach(function (el) {
            if (busy) { el.dataset.cartWasDisabled = String(el.disabled); el.disabled = true; }
            else { el.disabled = el.dataset.cartWasDisabled === "true"; delete el.dataset.cartWasDisabled; }
        });
        container.querySelectorAll("[data-cart-qty]").forEach(updateStepper);
    }
    function syncCheckoutLink() {
        document.querySelectorAll("[data-cart-checkout]").forEach(function (link) {
            link.setAttribute("aria-disabled", String(pending > 0));
        });
    }
    function drawerRow(line) {
        var row = document.createElement("li"); row.className = "shop-cart-drawer-line";
        row.setAttribute("data-cart-drawer-line", ""); row.dataset.productId = String(line.product_id);
        var name = escapeHtml(line.name), token = '<input type="hidden" name="csrfmiddlewaretoken" value="' + escapeHtml(csrf()) + '">';
        row.innerHTML = '<a class="shop-cart-drawer-line__media" href="' + escapeHtml(line.url) + '" tabindex="-1" aria-hidden="true">' +
            (line.image_url ? '<img src="' + escapeHtml(line.image_url) + '" alt="" loading="lazy">' : '<span class="shop-cart-drawer-line__placeholder"></span>') + '</a>' +
            '<div class="shop-cart-drawer-line__body"><a class="shop-cart-drawer-line__name" href="' + escapeHtml(line.url) + '">' + name + '</a>' +
            '<p class="shop-cart-drawer-line__unit">' + escapeHtml(line.unit_price_display) + '</p>' +
            '<form method="post" action="' + escapeHtml(line.update_url) + '" data-cart-quantity-form>' + token +
            '<div class="shop-qty shop-qty--compact" data-cart-qty><button type="button" class="shop-qty__btn" data-cart-dec aria-label="' + escapeHtml(label("dec")) + ': ' + name + '">−</button>' +
            '<input class="shop-qty__input" type="number" name="quantity" min="1" step="1" inputmode="numeric" aria-label="' + escapeHtml(label("qty")) + ': ' + name + '">' +
            '<button type="button" class="shop-qty__btn" data-cart-inc aria-label="' + escapeHtml(label("inc")) + ': ' + name + '">+</button></div></form>' +
            '<div class="shop-cart-drawer-line__bottom"><strong class="shop-cart-drawer-line__total" data-cart-line-total></strong>' +
            '<form method="post" action="' + escapeHtml(line.remove_url) + '" class="shop-cart-drawer-line__remove-form" data-cart-remove-form>' + token +
            '<button type="submit" class="shop-btn shop-btn--ghost shop-btn--sm" aria-label="' + escapeHtml(label("remove")) + ': ' + name + '">' + '<svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"><path d="M4 7h16M9 7V4h6v3M6 7l1 13h10l1-13M10 10v7m4-7v7"/></svg><span>' + escapeHtml(label("remove")) + '</span></button></form></div></div>';
        return row;
    }
    function syncRows(root, lines, current, create, previousFocus) {
        var active = previousFocus && document.activeElement === document.body ? previousFocus : document.activeElement;
        var activeRow = active && active.closest(rowSelector);
        var rows = Array.from(root.querySelectorAll(rowSelector));
        var focusedIndex = rows.indexOf(activeRow);
        var byId = {};
        lines.forEach(function (line) { byId[String(line.product_id)] = line; });
        rows.forEach(function (row) {
            if (!byId[row.dataset.productId]) row.remove();
        });
        lines.forEach(function (line) {
            var row = root.querySelector('[data-product-id="' + line.product_id + '"]');
            if (!row && create) { row = drawerRow(line); root.appendChild(row); }
            if (!row || (row.getAttribute("aria-busy") === "true" && row !== current)) return;
            var input = row.querySelector('input[name="quantity"]');
            input.value = String(line.quantity); input.dataset.confirmedQuantity = String(line.quantity); input.max = String(line.stock);
            row.querySelector("[data-cart-line-total]").textContent = line.line_total_display;
            var unit = row.querySelector(".shop-cart-line__unit, .shop-cart-drawer-line__unit");
            if (unit) unit.textContent = line.unit_price_display;
            var name = row.querySelector(".shop-cart-line__name, .shop-cart-drawer-line__name");
            if (name) { name.textContent = line.name; name.href = line.url; }
            var media = row.querySelector(".shop-cart-line__media, .shop-cart-drawer-line__media");
            if (media) {
                media.href = line.url;
                var image = media.querySelector("img");
                if (line.image_url) {
                    if (!image) { image = document.createElement("img"); image.alt = ""; image.loading = "lazy"; media.replaceChildren(image); }
                    image.src = line.image_url;
                } else if (image) image.remove();
            }
            [["[data-cart-dec]", "dec"], ["[data-cart-inc]", "inc"], ['input[name="quantity"]', "qty"], ["[data-cart-remove-form] button", "remove"]].forEach(function (control) {
                var el = row.querySelector(control[0]);
                if (el) el.setAttribute("aria-label", label(control[1]) + ": " + line.name);
            });
            row.querySelectorAll("[data-cart-qty]").forEach(updateStepper);
        });
        if (focusedIndex >= 0 && activeRow && !activeRow.isConnected) {
            var remaining = root.querySelectorAll(rowSelector);
            var next = remaining[Math.min(focusedIndex, remaining.length - 1)];
            var target = next ? next.querySelector("[data-cart-remove-form] button") :
                (root.closest("[data-cart-drawer]") ? drawer.querySelector("[data-bs-dismiss]") : page.querySelector("[data-cart-empty] a"));
            // The empty state is made visible by applyState before the next frame.
            if (target) window.requestAnimationFrame(function () { target.focus(); });
        }
    }
    function applyState(data, current, previousFocus) {
        if (!Array.isArray(data.lines)) return;
        document.querySelectorAll("[data-cart-header-count]").forEach(function (badge) {
            badge.textContent = String(data.item_count); badge.hidden = !data.item_count;
        });
        if (data.item_count_label) {
            document.querySelectorAll(".shop-header__cart, .shop-header-panel__cart").forEach(function (link) {
                link.setAttribute("aria-label", data.item_count_label);
            });
        }
        var fab = document.getElementById("shopCartFab");
        if (fab) {
            var visible = data.item_count > 0 && !document.querySelector(".shop-page--cart, .shop-page--checkout");
            fab.hidden = !visible; fab.classList.toggle("is-visible", visible);
            if (data.item_count_label) fab.setAttribute("aria-label", data.item_count_label);
        }
        if (drawer) {
            syncRows(drawer.querySelector("[data-cart-drawer-lines]"), data.lines, current, true, previousFocus);
            drawer.querySelector("[data-cart-drawer-empty]").hidden = !!data.lines.length;
            drawer.querySelector("[data-cart-drawer-footer]").hidden = !data.lines.length;
            drawer.querySelector("[data-cart-drawer-subtotal]").textContent = data.subtotal_display;
        }
        if (page) {
            syncRows(page, data.lines, current, false, previousFocus);
            page.querySelector("[data-cart-content]").hidden = !data.lines.length;
            page.querySelector("[data-cart-empty]").hidden = !!data.lines.length;
            page.querySelector("[data-cart-header-summary]").textContent = data.item_count_label;
            var subtotal = page.querySelector("[data-cart-subtotal]"); if (subtotal) subtotal.textContent = data.subtotal_display;
        }
    }
    function mutate(form) {
        var row = form.closest(rowSelector), container = row || form;
        if (container.getAttribute("aria-busy") === "true") return;
        var input = form.querySelector('input[name="quantity"]');
        if (input && !input.checkValidity()) { input.reportValidity(); return; }
        var body = new FormData(form); // Capture before disabling controls.
        var add = form.hasAttribute("data-shop-add-cart");
        var focused = document.activeElement;
        if (!add) {
            drawer.querySelector("[data-cart-added]").hidden = true;
            drawer.querySelectorAll(".is-just-added").forEach(function (line) { line.classList.remove("is-just-added"); });
        }
        clearError(container); setBusy(container, true); pending += 1; syncCheckoutLink();
        enqueue(function () {
            return request(form.action, body).then(function (result) {
                applyState(result.data, row, focused);
                if (!result.ok) { showError(container, result.data.error || label("error")); return; }
                if (add) showAdded(result.data, focused); else announce(result.data.message || label("updated"));
            }).catch(function () {
                // A lost response may follow a successful write; read back, never repeat the POST.
                return request(drawer.getAttribute("data-cart-state-url")).then(function (result) {
                    if (result.ok) applyState(result.data, row, focused);
                }).catch(function () {
                    if (input && input.dataset.confirmedQuantity) input.value = input.dataset.confirmedQuantity;
                }).finally(function () { showError(container.isConnected ? container : (page || drawer), label("error")); });
            }).finally(function () {
                setBusy(container, false); pending -= 1; syncCheckoutLink();
                if (focused && focused.isConnected && document.activeElement === document.body) focused.focus();
            });
        });
    }
    function loadDrawer() {
        var loading = drawer.querySelector("[data-cart-drawer-loading]");
        var error = drawer.querySelector("[data-cart-load-error]");
        loading.hidden = false; error.hidden = true;
        enqueue(function () {
            return request(drawer.getAttribute("data-cart-state-url")).then(function (result) {
                if (!result.ok) throw new Error("cart-state");
                applyState(result.data);
            }).catch(function () { error.hidden = false; })
                .finally(function () { loading.hidden = true; });
        });
    }
    function init() {
        drawer = document.querySelector("[data-cart-drawer]"); page = document.querySelector("[data-cart-page]");
        if (!drawer || !window.fetch || !window.FormData) return;
        document.querySelectorAll("[data-cart-qty]").forEach(function (wrap) {
            var input = wrap.querySelector('input[name="quantity"]'); input.dataset.confirmedQuantity = input.value; updateStepper(wrap);
        });
        document.querySelectorAll("[data-cart-save]").forEach(function (button) { button.hidden = true; });
        var fab = document.getElementById("shopCartFab");
        if (fab && document.querySelector(".shop-page--cart, .shop-page--checkout")) { fab.hidden = true; fab.classList.remove("is-visible"); }
        drawer.addEventListener("show.bs.offcanvas", function (event) { drawerOpener = event.relatedTarget || document.activeElement; hideConfirmation(); });
        drawer.addEventListener("shown.bs.offcanvas", loadDrawer);
        drawer.addEventListener("hidden.bs.offcanvas", function () {
            drawer.querySelector("[data-cart-added]").hidden = true;
            drawer.querySelectorAll(".is-just-added").forEach(function (row) { row.classList.remove("is-just-added"); });
            if (drawerOpener && drawerOpener.isConnected && drawerOpener.getClientRects().length) drawerOpener.focus();
            // The floating opener disappears when the last item is removed.
            if (drawerOpener && (!drawerOpener.isConnected || !drawerOpener.getClientRects().length)) {
                var fallback = document.querySelector(".shop-header__cart");
                if (fallback) fallback.focus();
            }
        });
        drawer.querySelector("[data-cart-retry]").addEventListener("click", loadDrawer);
        var confirmation = document.querySelector("[data-cart-confirmation]");
        if (confirmation) {
            confirmation.addEventListener("mouseenter", function () { window.clearTimeout(confirmationTimer); });
            confirmation.addEventListener("mouseleave", scheduleConfirmationHide);
            confirmation.addEventListener("focusin", function () { window.clearTimeout(confirmationTimer); });
            confirmation.addEventListener("focusout", scheduleConfirmationHide);
        }
        document.addEventListener("click", function (event) {
            if (event.target.closest("[data-cart-confirmation-close]")) { hideConfirmation(true); return; }
            var preview = event.target.closest("[data-cart-preview]");
            if (preview && !event.ctrlKey && !event.metaKey && !event.shiftKey && !event.altKey && window.bootstrap && window.bootstrap.Offcanvas) {
                event.preventDefault(); window.bootstrap.Offcanvas.getOrCreateInstance(drawer).show(preview); return;
            }
            var headerCart = event.target.closest(".shop-header__cart");
            if (headerCart && !page && !event.ctrlKey && !event.metaKey && !event.shiftKey && !event.altKey && window.bootstrap && window.bootstrap.Offcanvas) {
                event.preventDefault(); window.bootstrap.Offcanvas.getOrCreateInstance(drawer).show(headerCart); return;
            }
            var cancel = event.target.closest("[data-cart-remove-cancel]");
            if (cancel) { cancelRemoval(cancel.closest("form")); return; }
            var remove = event.target.closest("[data-cart-remove-yes]");
            if (remove) { mutate(remove.closest("form")); return; }
            var checkout = event.target.closest("[data-cart-checkout]");
            if (checkout && pending) { event.preventDefault(); announce(label("saving")); }
            var button = event.target.closest("[data-cart-dec], [data-cart-inc]");
            if (!button || button.disabled) return;
            var input = button.closest("[data-cart-qty]").querySelector('input[name="quantity"]');
            var current = Number(input.value || input.min);
            input.value = String(Math.max(Number(input.min), Math.min(Number(input.max), current + (button.hasAttribute("data-cart-inc") ? 1 : -1))));
            input.dispatchEvent(new Event("change", { bubbles: true }));
        });
        document.addEventListener("keydown", function (event) {
            if (event.key === "Escape" && event.target.closest("[data-cart-remove-confirm]")) {
                event.preventDefault(); event.stopPropagation(); cancelRemoval(event.target.closest("form"));
            }
        }, true);
        document.addEventListener("change", function (event) {
            if (event.target.matches('[data-cart-qty] input[name="quantity"]')) mutate(event.target.form);
        });
        document.addEventListener("submit", function (event) {
            var form = event.target;
            if (!form.matches("[data-shop-add-cart], [data-cart-quantity-form], [data-cart-remove-form]")) return;
            event.preventDefault();
            if (form.hasAttribute("data-cart-remove-form")) confirmRemoval(form); else mutate(form);
        });
    }
    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init); else init();
})();
