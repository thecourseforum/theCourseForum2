// Ad blocker detection
window.addEventListener("DOMContentLoaded", function () {
  // 'adsbygoogle' is the global variable used by Google AdSense
  setTimeout(() => {
    if (!window.adsbygoogle || !window.adsbygoogle.loaded) {
      $("#adblockModal").modal({
        backdrop: "static",
        keyboard: false,
      });
      $("#adblockModal").modal("show");
    }
  }, 1000);
});
