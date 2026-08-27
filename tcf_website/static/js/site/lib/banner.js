/**
 * Interest Meeting Banner
 * ========================
 * Handles dismissing the interest meeting announcement banner,
 * persisting the dismissal in localStorage.
 */

(function () {
  "use strict";

  function storageKey(banner) {
    return "bannerDismissed:" + banner.dataset.bannerId;
  }

  function isDismissed(banner) {
    return localStorage.getItem(storageKey(banner)) === "true";
  }

  function dismissBanner(banner) {
    localStorage.setItem(storageKey(banner), "true");
    banner.hidden = true;
  }

  function initBanner() {
    const banner = document.getElementById("tcf-interest-meeting");
    if (!banner) return;

    if (isDismissed(banner)) {
      banner.hidden = true;
      return;
    }

    const closeButton = banner.querySelector("[data-banner-dismiss]");
    if (closeButton) {
      closeButton.addEventListener("click", () => dismissBanner(banner));
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initBanner);
  } else {
    initBanner();
  }
})();