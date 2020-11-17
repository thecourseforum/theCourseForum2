// let loadData = async url => {
//   if (url) {
//     const data = await fetch(url).then(res => res.json())
//     if (data.detail === "Not found.") {
//       console.log("NOTFOUND")
//     } else {
//     }
//
//
//   }
// }

var subjectObject = {
  "Front-end": {
    "HTML": ["Links", "Images", "Tables", "Lists"],
    "CSS": ["Borders", "Margins", "Backgrounds", "Float"],
    "JavaScript": ["Variables", "Operators", "Functions", "Conditions"]
  },
  "Back-end": {
    "PHP": ["Variables", "Strings", "Arrays"],
    "SQL": ["SELECT", "UPDATE", "DELETE"]
  }
}

window.onload = function() {
  var subjectSel = document.getElementById("subject");
  var courseSel = document.getElementById("courseID");
  var instrSel = document.getElementById("instructor");
  for (var x in subjectObject) {
    subjectSel.options[subjectSel.options.length] = new Option(x, x);
  }
  subjectSel.onchange = function() {
    //display correct values
    for (var y in subjectObject[this.value]) {
      courseSel.options[courseSel.options.length] = new Option(y, y);
    }
  }
  topicSel.onchange = function() {
    //display correct values
    var z = subjectObject[subjectSel.value][this.value];
    for (var i = 0; i < z.length; i++) {
      instrSel.options[instrSel.options.length] = new Option(z[i], z[i]);
    }
  }
}


var ddlCountries = document.getElementById("ddlCountries");
var ddlCities = document.getElementById("ddlCities");
var data = []; // your json array
var defaultCountry = data[0];
loadAllCountries();
loadDefaultCities();

function loadAllCountries() {
   for (var i = 0; i < data.length; i++) {
        var currentCountry = data[i];
            addCountry(currentCountry);
    }
}
function loadDefaultCities() {
    addCities(defaultCountry.cities, defaultCountry);
}
function addCountry(currentCountry) {
    var option = document.createElement("option");
    option.text = currentCountry.name;
    option.value = currentCountry.id;
    ddlCountries.appendChild(option);
}
function addCities(cities, currentCountry) {
    for (var i = 0; i < cities.length; i++) {
        var option = document.createElement("option");
        option.text = cities[i].name;
        option.value = cities[i].id;
        ddlCities.appendChild(option);
        ddlCities.selectedIndex = 0;
    }
}
function onChange() {
    var selectedCountry = data.find(findById);
    clearDropdownlist(ddlCities);
    addCities(selectedCountry.cities, selectedCountry);
}
function findById(country) {
    return country.id == ddlCountries.value;
}
function clearDropdownlist(ddl) {
    while (ddl.firstChild) {
        ddl.removeChild(ddl.firstChild);
    }
}
