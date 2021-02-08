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
        // Ascending order is the default
        $("#descending-order-btn").removeClass("active");
        $("#ascending-order-btn").addClass("active");
    } else { // Already selected so simply reverse the order of sorting (ascending vs descending)
        sortNumberAsc *= -1;
        if ($("#ascending-order-btn").hasClass("active")) {
            $("#ascending-order-btn").removeClass("active");
            $("#descending-order-btn").addClass("active");
        } else {
            $("#descending-order-btn").removeClass("active");
            $("#ascending-order-btn").addClass("active");
        }
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
        $("#descending-order-btn").removeClass("active");
        $("#ascending-order-btn").addClass("active");
    } else {
        sortRatingAsc *= -1;
        if ($("#ascending-order-btn").hasClass("active")) {
            $("#ascending-order-btn").removeClass("active");
            $("#descending-order-btn").addClass("active");
        } else {
            $("#descending-order-btn").removeClass("active");
            $("#ascending-order-btn").addClass("active");
        }
    }

    sortClasses(cmpByProp("rating", sortRatingAsc));
};

const sortByDifficulty = () => {
    if (!$("#diff-sort-btn").hasClass("active")) {
        $("#number-sort-btn").removeClass("active");
        $("#rating-sort-btn").removeClass("active");
        $("#gpa-sort-btn").removeClass("active");
        $("#diff-sort-btn").addClass("active");
        $("#descending-order-btn").removeClass("active");
        $("#ascending-order-btn").addClass("active");
    } else {
        sortDifficultyAsc *= -1;
        if ($("#ascending-order-btn").hasClass("active")) {
            $("#ascending-order-btn").removeClass("active");
            $("#descending-order-btn").addClass("active");
        } else {
            $("#descending-order-btn").removeClass("active");
            $("#ascending-order-btn").addClass("active");
        }
    }

    sortClasses(cmpByProp("difficulty", sortDifficultyAsc));
};

const sortByGpa = () => {
    if (!$("#gpa-sort-btn").hasClass("active")) {
        $("#number-sort-btn").removeClass("active");
        $("#rating-sort-btn").removeClass("active");
        $("#diff-sort-btn").removeClass("active");
        $("#gpa-sort-btn").addClass("active");
        $("#descending-order-btn").removeClass("active");
        $("#ascending-order-btn").addClass("active");
    } else {
        sortGpaAsc *= -1;
        if ($("#ascending-order-btn").hasClass("active")) {
            $("#ascending-order-btn").removeClass("active");
            $("#descending-order-btn").addClass("active");
        } else {
            $("#descending-order-btn").removeClass("active");
            $("#ascending-order-btn").addClass("active");
        }
    }

    sortClasses(cmpByProp("gpa", sortGpaAsc));
};

const ascendingOrder = () => {
    if (!$("#ascending-order-btn").hasClass("active")) {
        $("#descending-order-btn").removeClass("active");
        $("#ascending-order-btn").addClass("active");
        // Check which sort is currently selected and compute that sort
        if ($("#number-sort-btn").hasClass("active")) {
            sortClasses(cmpByProp("title", 1));
        } else if ($("#rating-sort-btn").hasClass("active")) {
            sortClasses(cmpByProp("rating", -1));
        } else if ($("#diff-sort-btn").hasClass("active")) {
            sortClasses(cmpByProp("difficulty", 1));
        } else if ($("#gpa-sort-btn").hasClass("active")) {
            sortClasses(cmpByProp("gpa", -1));
        }
    }
};

const descendingOrder = () => {
    if (!$("#descending-order-btn").hasClass("active")) {
        $("#ascending-order-btn").removeClass("active");
        $("#descending-order-btn").addClass("active");
        // Check which sort is currently selected and compute that sort
        if ($("#number-sort-btn").hasClass("active")) {
            sortClasses(cmpByProp("title", -1));
        } else if ($("#rating-sort-btn").hasClass("active")) {
            sortClasses(cmpByProp("rating", 1));
        } else if ($("#diff-sort-btn").hasClass("active")) {
            sortClasses(cmpByProp("difficulty", -1));
        } else if ($("#gpa-sort-btn").hasClass("active")) {
            sortClasses(cmpByProp("gpa", 1));
        }
    }
};

const sortClasses = (cmp) => {
    $("ul.course-list").each(function(a) {
        var li = $(this).children("li");
        li.detach().sort(cmp);
        $(this).append(li);
    });
};

export { sortByNumber, sortByRating, sortByDifficulty, sortByGpa, ascendingOrder, descendingOrder };
