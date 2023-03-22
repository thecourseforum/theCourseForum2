import { sortHTML } from "../common/sorting.js";

function makeQAActive(htmlTag, label) {
    $(".dropdown-item").removeClass("active");
    $(htmlTag).addClass("active");
    $("#qa-sort-select").html(label);
}

function sortQA(btnID) {
    const htmlTag = "#".concat(btnID);
    let label = "";
    let prop = "";
    const asc = -1;
    switch (btnID) {
    case "qa-votes-sort-btn":
        label = "Most Helpful";
        prop = "question-vote-count";
        break;
    case "qa-recent-sort-btn":
        label = "Most Recent";
        prop = "date";
        break;
    default:
        console.log("error");
        return;
    }
    if (!$(htmlTag).hasClass("active")) {
        makeQAActive(htmlTag, label);
        sortAnswers(".answer-container");
        sortHTML(".qa", ".question-container", prop, asc);
    }
}

// TODO: Need to test!
function sortAnswers(containerClass) {
    var ids = $(containerClass).map(function(_, x) { return "#".concat(x.id); }).get();
    ids.forEach((item) => sortHTML(item, item.concat(" .answer"), "answer-vote-count", -1));
}

sortQA("qa-votes-sort-btn");
document.getElementById("qa-votes-sort-btn").addEventListener("click", () => sortQA("qa-votes-sort-btn"));
document.getElementById("qa-recent-sort-btn").addEventListener("click", () => sortQA("qa-recent-sort-btn"));
