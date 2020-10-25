import { cmpByProp } from "../common/sorting.js";

let sortNumberAsc = 1;
let sortRatingAsc = -1;
let sortDifficultyAsc = 1;
let sortGpaAsc = -1;

/*
    Each method sort_by_... is the same format as outline below
    sort_classes takes in a comparing function (defined below) and reorders the classes appropriately
    comparator needed for both ascending and decending as any classes with null values should be at the end of the list either order
*/
const sortByNumber = () => {
    // Updating looks and sorting order
    if (!$("#number-sort-btn").hasClass("active")) {
        $("#rating-sort-btn").removeClass("active");
        $("#diff-sort-btn").removeClass("active");
        $("#gpa-sort-btn").removeClass("active");
        $("#number-sort-btn").addClass("active");
    } else { // Already selected so simply reverse the order of sorting (ascending vs descending)
        sortNumberAsc *= -1;
    }

    // Actual sorting
    sortClasses(cmpByProp("title", sortNumberAsc));
};

const sortByRating = () => {
    if (!$("#rating-sort-btn").hasClass("active")) {
        $("#number-sort-btn").removeClass("active");
        $("#diff-sort-btn").removeClass("active");
        $("#gpa-sort-btn").removeClass("active");
        $("#rating-sort-btn").addClass("active");
    } else {
        sortRatingAsc *= -1;
    }

    sortClasses(cmpByProp("rating", sortRatingAsc));
};

const sortByDifficulty = () => {
    if (!$("#diff-sort-btn").hasClass("active")) {
        $("#number-sort-btn").removeClass("active");
        $("#rating-sort-btn").removeClass("active");
        $("#gpa-sort-btn").removeClass("active");
        $("#diff-sort-btn").addClass("active");
    } else {
        sortDifficultyAsc *= -1;
    }

    sortClasses(cmpByProp("difficulty", sortDifficultyAsc));
};

const sortByGpa = () => {
    if (!$("#gpa-sort-btn").hasClass("active")) {
        $("#number-sort-btn").removeClass("active");
        $("#rating-sort-btn").removeClass("active");
        $("#diff-sort-btn").removeClass("active");
        $("#gpa-sort-btn").addClass("active");
    } else {
        sortGpaAsc *= -1;
    }

    sortClasses(cmpByProp("gpa", sortGpaAsc));
};

const sortClasses = (cmp) => {
    $("ul.course-list").each(function(a) {
        var li = $(this).children("li");
        li.detach().sort(cmp);
        $(this).append(li);
    });
};

export { sortByNumber, sortByRating, sortByDifficulty, sortByGpa };
