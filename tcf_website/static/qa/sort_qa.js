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

    // collapse QA
    collapseQA(3);
}

function collapseQA(numberShown) {
    var ids = $(".question-container").map(function(_, x) { return "#".concat(x.id); }).get();
    for (const [index, id] of ids.entries()) {
        var detachedID = $(id).detach();
        if (index < numberShown) {
            $("#questionShow").append(detachedID);
        } else {
            $("#questionCollapse").append(detachedID);
        }
    }
}

function sortAnswers(containerClass) {
    var ids = $(containerClass).map(function(_, x) { return "#".concat(x.id); }).get();
    ids.forEach((item) => sortHTML(item, item.concat(" .answer"), "answer-vote-count", -1));
}

sortQA("qa-votes-sort-btn");
document.getElementById("qa-votes-sort-btn").addEventListener("click", () => sortQA("qa-votes-sort-btn"));
document.getElementById("qa-recent-sort-btn").addEventListener("click", () => sortQA("qa-recent-sort-btn"));

// collapse QA functionality
document.getElementById("collapse-qa-button").addEventListener("click", function() {
    if ($("#collapse-qa-button").val() === "hide") {
        $("#collapse-qa-button").val("show");
        $("#collapse-qa-button").html("Show All Questions");
    } else {
        $("#collapse-qa-button").val("hide");
        $("#collapse-qa-button").html("Hide Questions");
    }
});
