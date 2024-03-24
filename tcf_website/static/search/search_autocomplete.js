const autocompleteResults = document.getElementById("autocomplete-results");
const searchInput = document.getElementById("search-input");
let latestRequestTime, currentRequestTime;

function adjustAutocompleteWidth() {
  const searchInputWidth = searchInput.offsetWidth;

  const autocompleteWidth = searchInputWidth;
  autocompleteResults.style.width = autocompleteWidth + "px";
}

document.addEventListener("DOMContentLoaded", function () {
  adjustAutocompleteWidth();

  searchInput.addEventListener("input", adjustAutocompleteWidth);
  window.addEventListener("resize", adjustAutocompleteWidth);

  let onCooldown = false;
  let debounceTimeout;
  searchInput.addEventListener("input", function () {
    const latestRequestTime = Date.now();
    currentRequestTime = latestRequestTime;
    const query = searchInput.value;

    if (debounceTimeout !== undefined) {
      clearTimeout(debounceTimeout);
    }
    debounceTimeout = setTimeout(function () {
      if (query.length >= 1 && !onCooldown) {
        fetch("/autocomplete/?q=" + encodeURIComponent(query))
          .then((response) => response.json())
          .then((data) => {
            if (
              data &&
              Array.isArray(data.results) &&
              currentRequestTime === latestRequestTime
            ) {
              displayAutocompleteResults(data.results);
            }
          })
          .catch((error) => console.error("Error:", error));
        onCooldown = true;
        setTimeout(function () {
          onCooldown = false;
        }, 100);
      } else {
        autocompleteResults.innerHTML = "";
      }
    }, 100);
  });
});

function displayAutocompleteResults(results) {
  autocompleteResults.innerHTML = "";

  if (results.length === 0) {
    autocompleteResults.innerHTML =
      '<div class="autocomplete-result">No results found</div>';
    return;
  }

  results.forEach(function (result) {
    const resultElement = document.createElement("div");
    resultElement.classList.add("autocomplete-result");
    resultElement.setAttribute("tabindex", "0");
    resultElement.textContent = result.title;
    resultElement.addEventListener("click", function () {
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
    });
    autocompleteResults.appendChild(resultElement);
  });
}
