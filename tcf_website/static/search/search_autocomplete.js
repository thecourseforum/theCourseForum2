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

  $searchInput.on("input", function () {
    const latestRequestTime = Date.now();
    currentRequestTime = latestRequestTime;
    const query = $(this).val();

    setTimeout(function () {
      if (query.length >= 1) {
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
      } else {
        $autocompleteResults.html("");
      }
    }, 50);
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
          $searchInput.val(result.title);
          $autocompleteResults.empty();
          $searchInput.closest("form").submit();
        },
      });
      $autocompleteResults.append($resultElement);
    });
  }
});
