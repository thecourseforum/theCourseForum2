/*
 * sorting functions for sorting reviews and classes
 */

// prop is html id of property to be sorted by
// asc = 1 for ascending, asc = -1 for descending
function sortHTML(container, items, prop, asc = 1) {
    const cmp = cmpByProp(prop, asc);
    var objs = $(items);
    objs.detach().sort(cmp);
    $(container).append(objs);
}

function cmpByProp(prop, asc) {
    return function(a, b) {
        const id = "#".concat(prop);
        let valA = a.querySelector(id).innerHTML.trim();
        let valB = b.querySelector(id).innerHTML.trim();

        if (prop === "date") { // convert date string to int
            valA = dateToInt(valA);
            valB = dateToInt(valB);
        } else { // extract number from string
            try {
                valA = parseFloat(valA.match(/-?[0-9]\d*(\.\d+)?/)[0]);
            } catch (err) {
                return 1;
            }
            try {
                valB = parseFloat(valB.match(/-?[0-9]\d*(\.\d+)?/)[0]);
            } catch (err) {
                return -1;
            }
        }

        if (valA > valB) {
            return asc;
        } else if (valA < valB) {
            return -1 * asc;
        } else {
            return 0;
        }
    };
}

function dateToInt(dateStr) {
    const date = new Date(dateStr);
    return date.getTime();
}

export { cmpByProp, sortHTML };
