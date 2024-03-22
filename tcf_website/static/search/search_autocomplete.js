$(document).ready(function () {
  const $autocompleteResults = $("#autocomplete-results");
  const $searchInput = $("#search-input");
  let currentRequestTime;

  function adjustAutocompleteWidth() {
    const searchInputWidth = $searchInput.outerWidth();
    $autocompleteResults.width(searchInputWidth);
  }

  adjustAutocompleteWidth();
  $(window).on("resize", adjustAutocompleteWidth);
  $searchInput.on("input", adjustAutocompleteWidth);

  let onCooldown = false;
  let debounceTimeout = undefined;

  $searchInput.on("input", function () {
    const latestRequestTime = Date.now();
    currentRequestTime = latestRequestTime;
    const query = $(this).val();

    if (debounceTimeout !== undefined) {
      clearTimeout(debounceTimeout);
    }
    debounceTimeout = setTimeout(function () {
      if (query.length >= 1 && !onCooldown) {
        $.ajax({
          url: "/autocomplete/?q=" + encodeURIComponent(query),
          type: "GET",
          dataType: "json",
          success: function (data) {
            if (
              data &&
              Array.isArray(data.results) &&
              currentRequestTime === latestRequestTime
            ) {
              displayAutocompleteResults(data.results);
            }
          },
          error: function (error) {
            console.error("Error:", error);
          },
        });
        onCooldown = true;
        setTimeout(function () {
          onCooldown = false;
        }, 100);
      } else {
        $autocompleteResults.html("");
      }
    }, 100);
  });

  function displayAutocompleteResults(results) {
    console.log(results);
    $autocompleteResults.empty();

    if (results.length === 0) {
      $autocompleteResults.html(
        '<div class="autocomplete-result">No results found</div>',
      );
      return;
    }

    $.each(results, function (i, result) {
      const $resultElement = $("<div></div>", {
        class: "autocomplete-result",
        tabindex: "0",
        text: result.title,
        click: function () {
          if (result.mnemonic === undefined) {
            window.location.replace(
              window.location.origin + "/instructor/" + result.id,
            );
          } else {
            window.location.replace(
              window.location.origin +
                "/course/" +
                result.mnemonic.replace(" ", "/"),
            );
          }
        },
      });
      $autocompleteResults.append($resultElement);
    });
  }
});
