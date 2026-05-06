(function () {
    const projectRoute = "/app/projects";
    const loginPaths = new Set(["/login", "/login/"]);

    if (!loginPaths.has(window.location.pathname)) {
        return;
    }

    const url = new URL(window.location.href);
    if (url.searchParams.has("redirect-to")) {
        url.searchParams.delete("redirect-to");
        window.history.replaceState({}, document.title, url.pathname + url.search + url.hash);
    }

    try {
        localStorage.removeItem("last_visited");
    } catch (e) {
        // Ignore storage restrictions in private browsing or locked-down browsers.
    }

    window.reva_erp_login_home_page = projectRoute;
})();
