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

function collapseAnswers(numberShown) {
    var ids = $(".answer-container").map(function(_, x) { return x.id; }).get();
    for (const id of ids) {
        collapseQuestionAnswer(numberShown, parseInt(id.substring(16)));
    }
}

function collapseQuestionAnswer(numberShown, questionID) {
    const answerContainerID = "#answer-container" + questionID;
    const showAnswerContainer = "#answerShow" + questionID;
    const collapseAnswerContainer = "#answerCollapse" + questionID;

    var answerIDs = $(answerContainerID.concat(" .answer")).map(function(_, x) { return "#".concat(x.id); }).get();

    for (const [index, id] of answerIDs.entries()) {
        var detachedID = $(id).detach();
        if (index < numberShown) {
            $(showAnswerContainer).append(detachedID);
        } else {
            $(collapseAnswerContainer).append(detachedID);
        }
    }
}

function sortAnswers(containerClass) {
    var ids = $(containerClass).map(function(_, x) { return "#".concat(x.id); }).get();
    ids.forEach((item) => sortHTML(item, item.concat(" .answer"), "answer-vote-count", -1));
    collapseAnswers(1);
}

sortQA("qa-votes-sort-btn");
document.getElementById("qa-votes-sort-btn").addEventListener("click", () => sortQA("qa-votes-sort-btn"));
document.getElementById("qa-recent-sort-btn").addEventListener("click", () => sortQA("qa-recent-sort-btn"));

// collapse QA functionality
document.getElementById("collapse-qa-button").addEventListener("click", function() {
    if ($("#collapse-qa-button").val() === "hide") {
        $("#collapse-qa-button").val("show");
        $("#collapse-chevron").removeClass("fa-chevron-up");
        $("#collapse-chevron").addClass("fa-chevron-down");
        // $("#collapse-qa-button p").html("Show All Questions");
    } else {
        $("#collapse-qa-button").val("hide");
        $("#collapse-chevron").removeClass("fa-chevron-down");
        $("#collapse-chevron").addClass("fa-chevron-up");
        // $("#collapse-qa-button p").html("Hide Questions");
    }
});

function clickCollapseAnswer(collapseID) {
    const questionID = parseInt(collapseID.substring(22));
    const collapseButton = "#collapse-answer-button" + questionID;
    // const collapseChevron = "#collapse-answer-chevron" + questionID;

    console.log("in clickCollapseAnswer()");
    if ($(collapseButton).val() === "hide") {
        $(collapseButton).val("show");
        // $(collapseChevron).removeClass("fa-chevron-up");
        // $(collapseChevron).addClass("fa-chevron-down");
    } else {
        $(collapseButton).val("hide");
        // $(collapseChevron).removeClass("fa-chevron-down");
        // $(collapseChevron).addClass("fa-chevron-up");
    }
}

$(function() {
    var ids = $(".collapse-answer-button").map(function(_, x) { return x.id; }).get();
    ids.forEach((item) => document.getElementById(item).addEventListener("click", () => clickCollapseAnswer(item)));
});
