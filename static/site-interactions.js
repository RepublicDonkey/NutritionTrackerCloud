const loadingScreen = document.createElement("div");
loadingScreen.className = "loading-screen";
loadingScreen.setAttribute("role", "status");
loadingScreen.setAttribute("aria-live", "polite");
loadingScreen.setAttribute("aria-hidden", "true");
loadingScreen.innerHTML = `
    <div class="loading-panel">
        <span class="loading-spinner" aria-hidden="true"></span>
        <span>Loading…</span>
    </div>
`;
document.body.appendChild(loadingScreen);
//Loading Screen is displayed after 250ms to avoid flickering on fast page loads
let loadingTimer;

function scheduleLoadingScreen() {
    window.clearTimeout(loadingTimer);
    loadingScreen.classList.add("is-visible");
    loadingScreen.setAttribute("aria-hidden", "false");
}

// Hides the loading screen and clears the timer if it hasn't been displayed yet
function hideLoadingScreen() {
    window.clearTimeout(loadingTimer);
    loadingScreen.classList.remove("is-visible");
    loadingScreen.setAttribute("aria-hidden", "true");
}

document.querySelectorAll("form").forEach((form) => {
    form.addEventListener("submit", scheduleLoadingScreen);
});

document.addEventListener("click", (event) => {
    const link = event.target.closest("a[href]");

    if (
        !link ||
        event.button !== 0 ||
        event.ctrlKey ||
        event.metaKey ||
        event.shiftKey ||
        event.altKey ||
        link.target === "_blank" ||
        link.hasAttribute("download")
    ) {
        return;
    }

    const destination = new URL(link.href, window.location.href);
    const currentPage = new URL(window.location.href);
    const isSamePageAnchor =
        destination.pathname === currentPage.pathname &&
        destination.search === currentPage.search &&
        destination.hash;

    if (destination.origin === currentPage.origin && !isSamePageAnchor) {
        scheduleLoadingScreen();
    }
});
// Hide the loading screen when the page is shown (including when navigating back to it)
window.addEventListener("pageshow", hideLoadingScreen);

document.querySelectorAll("[data-password-toggle]").forEach((toggle) => {
    const passwordField = document.getElementById(toggle.dataset.passwordToggle);

    if (!passwordField) {
        return;
    }

    toggle.addEventListener("click", () => {
        const showPassword = passwordField.type === "password";

        passwordField.type = showPassword ? "text" : "password";
        toggle.classList.toggle("is-visible", showPassword);
        toggle.setAttribute("aria-pressed", String(showPassword));
        toggle.setAttribute(
            "aria-label",
            showPassword ? "Hide password" : "Show password",
        );
        passwordField.focus({ preventScroll: true });
    });
});

const successNotification = document.querySelector(
    "[data-success-notification]",
);

if (successNotification) {
    let notificationTimer;
    const notificationUrl = new URL(window.location.href);

    if (notificationUrl.searchParams.get("registered") === "1") {
        notificationUrl.searchParams.delete("registered");
        window.history.replaceState({}, "", notificationUrl);
    }

    function dismissNotification() {
        window.clearTimeout(notificationTimer);
        successNotification.classList.add("is-hiding");
        window.setTimeout(() => successNotification.remove(), 180);
    }

    successNotification
        .querySelector("[data-notification-close]")
        .addEventListener("click", dismissNotification);

    notificationTimer = window.setTimeout(dismissNotification, 5000);
}
