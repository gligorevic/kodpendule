/**
 * Kod Pendule admin navigation helpers
 */
(function () {
    "use strict";

    var MOBILE_MQ = "(max-width: 1023px)";
    var DESKTOP_MQ = "(min-width: 1024px)";

    /* Django's nav_sidebar.js also binds the toggle; replace node to avoid double-toggle on mobile. */
    (function resetToggleButton() {
        var toggle = document.getElementById("toggle-nav-sidebar");
        if (toggle && toggle.parentNode) {
            toggle.parentNode.replaceChild(toggle.cloneNode(true), toggle);
        }
        if (window.matchMedia(MOBILE_MQ).matches) {
            var mobileToggle = document.getElementById("toggle-nav-sidebar");
            var label = mobileToggle && mobileToggle.querySelector(".kp-nav-toggle__label");
            if (label && mobileToggle) {
                label.textContent =
                    mobileToggle.getAttribute("data-label-open") || "Open menu";
            }
        }
    })();

    function getMain() {
        return document.getElementById("main");
    }

    function getSidebar() {
        return document.getElementById("nav-sidebar");
    }

    function getToggle() {
        return document.getElementById("toggle-nav-sidebar");
    }

    function isMobile() {
        return window.matchMedia(MOBILE_MQ).matches;
    }

    function setStickyToggleLabel(open) {
        var toggle = getToggle();
        if (!toggle) {
            return;
        }
        toggle.setAttribute("aria-expanded", open ? "true" : "false");
        var label = toggle.querySelector(".kp-nav-toggle__label");
        if (!label) {
            return;
        }
        if (isMobile()) {
            /* Sticky bar always says "Open menu"; close only in the drawer. */
            label.textContent = toggle.getAttribute("data-label-open") || "Open menu";
            return;
        }
        var openText = toggle.getAttribute("data-label-open") || "Open menu";
        var closeText = toggle.getAttribute("data-label-close") || "Close menu";
        label.textContent = open ? closeText : openText;
    }

    function setSidebarOpen(open) {
        var main = getMain();
        var sidebar = getSidebar();
        if (!main || !sidebar) {
            return;
        }
        main.classList.toggle("shifted", open);
        sidebar.setAttribute("aria-expanded", open ? "true" : "false");
        sidebar.inert = !open;
        document.body.classList.toggle("kp-admin-nav-open", open);
        setStickyToggleLabel(open);
        try {
            localStorage.setItem("kp.admin.navSidebarIsOpen", open ? "true" : "false");
        } catch (e) {
            /* ignore */
        }
    }

    function openSidebarOnDesktop() {
        var main = getMain();
        var sidebar = getSidebar();
        if (!main || isMobile()) {
            return;
        }
        if (window.matchMedia(DESKTOP_MQ).matches) setSidebarOpen(true);
    }

    function initMobileSidebarState() {
        if (!isMobile()) {
            document.body.classList.remove("kp-admin-nav-open");
            return;
        }
        /* Drawer always starts closed on mobile (desktop localStorage would break layout). */
        setSidebarOpen(false);
    }

    function initMobileNav() {
        var main = getMain();
        var sidebar = getSidebar();
        var toggle = getToggle();
        if (!main || !sidebar) {
            return;
        }

        initMobileSidebarState();

        window.matchMedia(MOBILE_MQ).addEventListener("change", function () {
            if (isMobile()) {
                initMobileSidebarState();
            } else {
                document.body.classList.remove("kp-admin-nav-open");
                openSidebarOnDesktop();
            }
        });

        if (toggle) {
            toggle.addEventListener("click", function (event) {
                event.stopPropagation();
                var open = !main.classList.contains("shifted");
                setSidebarOpen(open);
                if (open && isMobile()) sidebar.querySelector("button, a, input").focus();
            });
        }

        var drawerClose = document.getElementById("kp-nav-drawer-close");
        if (drawerClose) {
            drawerClose.addEventListener("click", function (event) {
                event.stopPropagation();
                setSidebarOpen(false);
                if (toggle) toggle.focus();
            });
        }

        document.addEventListener("click", function (event) {
            if (!isMobile() || !document.body.classList.contains("kp-admin-nav-open")) {
                return;
            }
            if (event.target.closest("#nav-sidebar, #toggle-nav-sidebar")) {
                return;
            }
            setSidebarOpen(false);
        });

        sidebar.querySelectorAll("a").forEach(function (link) {
            link.addEventListener("click", function () {
                if (isMobile()) {
                    setSidebarOpen(false);
                }
            });
        });

        document.addEventListener("keydown", function (event) {
            if (event.key === "Escape" && isMobile() && main.classList.contains("shifted")) {
                setSidebarOpen(false);
                if (toggle) toggle.focus();
            }
            if (event.key === "Tab" && isMobile() && main.classList.contains("shifted")) {
                var items = Array.from(sidebar.querySelectorAll("a, button, input")).filter(function (el) { return el.getClientRects().length; });
                var first = items[0], last = items[items.length - 1];
                if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
                else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
            }
        });
    }

    function enhanceNavFilter() {
        var input = document.getElementById("nav-filter");
        var sidebar = getSidebar();
        if (!input || !sidebar) {
            return;
        }

        input.addEventListener("input", function () {
            var query = input.value.trim().toLowerCase();
            var sections = sidebar.querySelectorAll(".kp-admin-nav__section");
            sections.forEach(function (section) {
                var visibleItems = 0;
                section.querySelectorAll(".kp-admin-nav__item").forEach(function (item) {
                    var label = item.textContent.toLowerCase();
                    var match = !query || label.indexOf(query) !== -1;
                    item.classList.toggle("is-hidden", !match);
                    if (match) {
                        visibleItems += 1;
                    }
                });
                section.classList.toggle("is-hidden", query.length > 0 && visibleItems === 0);
            });
        });
    }

    document.addEventListener("DOMContentLoaded", function () {
        initMobileNav();
        openSidebarOnDesktop();
        enhanceNavFilter();
    });
})();
