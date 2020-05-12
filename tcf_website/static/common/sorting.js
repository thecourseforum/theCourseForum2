/*
 * sorting functions for sorting reviews and classes
 */

// prop is html id of property to be sorted by
// asc = 1 for ascending, asc = -1 for descending
function sortHTML(container, items, prop, asc=1){
    cmp = cmp_prop(prop, asc);
    var objs = $(items);
    objs.detach().sort(cmp);
    $(container).append(objs);
}

function cmp_prop(prop, asc) {
    return function(a, b) {
      id = '#'.concat(prop)
      valA = a.querySelector(id).innerHTML.trim();
      valB = b.querySelector(id).innerHTML.trim();

      if(prop=='date'){ //convert date string to int
        valA = dateToInt(valA);
        valB = dateToInt(valB);
      }else{ //extract number from string
        valA = valA.match(/[\d\.]+/)[0];
        valB = valB.match(/[\d\.]+/)[0];
      }

      if (isNaN(valA)) {  // ensures that NaN elements are at the end of the list
        return 1;
      } else if (isNaN(valB)) {
        return -1;
      }

      if (valA > valB) {
        return -1*asc;
      } else if (valA < valB) {
        return 1*asc;
      } else {
        return 0;
      }
    }
}
