(function () {
    "use strict";

    var toggle = document.querySelector("[data-password-toggle]");
    if (!toggle) {
        return;
    }

    var password = document.getElementById(toggle.dataset.passwordToggle);
    if (!password) {
        return;
    }

    toggle.addEventListener("click", function () {
        var isVisible = password.type === "text";
        password.type = isVisible ? "password" : "text";
        toggle.textContent = isVisible ? "Show" : "Hide";
        toggle.setAttribute("aria-pressed", String(!isVisible));
    });
}());