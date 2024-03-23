var autocompleteResults = document.getElementById('autocomplete-results');
var searchInput = document.getElementById("search-input");
var latestRequestTime, currentRequestTime;

function adjustAutocompleteWidth() {
  var searchInputWidth = searchInput.offsetWidth;

  var autocompleteWidth = searchInputWidth
  autocompleteResults.style.width = autocompleteWidth + 'px';
}


document.addEventListener('DOMContentLoaded', function () {

  adjustAutocompleteWidth();

  searchInput.addEventListener('input', adjustAutocompleteWidth);
  window.addEventListener('resize', adjustAutocompleteWidth);

  var onCooldown = false;
  var debounceTimeout = undefined;
  searchInput.addEventListener('input', function () {
    var latestRequestTime = Date.now();
    currentRequestTime = latestRequestTime;
    var query = searchInput.value;

    if (debounceTimeout !== undefined) {
      clearTimeout(debounceTimeout);
    }
    debounceTimeout = setTimeout(function () {
      if (query.length >= 1 && !onCooldown) {
        fetch('/autocomplete/?q=' + encodeURIComponent(query))
          .then(response => response.json())
          .then(data => {
            if (data && Array.isArray(data.results) && currentRequestTime == latestRequestTime) {
              displayAutocompleteResults(data.results);
            }
          })
          .catch(error => console.error('Error:', error));
        onCooldown = true;
        setTimeout(function () {
          onCooldown = false;
        }, 100);
      } else {
        autocompleteResults.innerHTML = '';
      }
    }, 100);
  });
});

function displayAutocompleteResults(results) {
  autocompleteResults.innerHTML = '';

  if (results.length === 0) {
    autocompleteResults.innerHTML = '<div class="autocomplete-result">No results found</div>';
    return;
  }

  results.forEach(function (result) {
    var resultElement = document.createElement('div');
    resultElement.classList.add('autocomplete-result');
    resultElement.setAttribute('tabindex', '0');
    resultElement.textContent = result.title;
    resultElement.addEventListener('click', function () {
      if (result.mnemonic === undefined) {
        window.location.replace(window.location.origin + '/instructor/' + result.id);
      } else {
        window.location.replace(window.location.origin + '/course/' + result.mnemonic.replace(' ', '/'));
      }
    });
    autocompleteResults.appendChild(resultElement);
  });
}