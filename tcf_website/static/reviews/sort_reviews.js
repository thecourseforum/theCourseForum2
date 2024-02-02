import { sortHTML } from "../common/sorting.js";

function makeActive(htmlTag, label) {
    $(".dropdown-item").removeClass("active");
    $(htmlTag).addClass("active");
    $("#review-sort-select").html(label);
}

function sortReviews(btnID) {
    const htmlTag = "#".concat(btnID);
    let label = "";
    let prop = "";
    let asc = -1;
    switch (btnID) {
    case "votes-sort-btn":
        label = "Most Helpful";
        prop = "vote-count";
        break;
    case "recent-sort-btn":
        label = "Most Recent";
        prop = "date";
        break;
    case "highrating-sort-btn":
        label = "Highest Rating";
        prop = "review-average";
        break;
    case "lowrating-sort-btn":
        label = "Lowest Rating";
        prop = "review-average";
        asc = 1;
        break;
    default:
        console.log("error");
        return;
    }
    if (!$(htmlTag).hasClass("active")) {
        makeActive(htmlTag, label);
        sortHTML(".reviews", ".review", prop, asc);
    }
}

sortReviews("votes-sort-btn");
document
    .getElementById("votes-sort-btn")
    .addEventListener("click", () => sortReviews("votes-sort-btn"), false);
document
    .getElementById("recent-sort-btn")
    .addEventListener("click", () => sortReviews("recent-sort-btn"), false);
document
    .getElementById("highrating-sort-btn")
    .addEventListener("click", () => sortReviews("highrating-sort-btn"), false);
document
    .getElementById("lowrating-sort-btn")
    .addEventListener("click", () => sortReviews("lowrating-sort-btn"), false);
