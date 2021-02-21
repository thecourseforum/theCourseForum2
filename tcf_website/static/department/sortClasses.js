import { cmpByProp } from "../common/sorting.js";

// Default way to sort each category
let sortNumberAsc = 1;
let sortRatingAsc = -1;
let sortDifficultyAsc = 1;
let sortGpaAsc = -1;

// Used to track which button is active for the ascending/descending order buttons
let activeSort = "title";

/*
    Each method sort_by_... is the same format as outline below
    If not currently active, make it active and all other sort buttons inactive
    Use selectOrderOfSort to sort and toggle correct ascending/descneding button
*/
const sortByNumber = () => {
    activeSort = "title";
    // Updating looks and sorting order
    if (!$("#number-sort-btn").hasClass("active")) {
        $("#rating-sort-btn").removeClass("active");
        $("#diff-sort-btn").removeClass("active");
        $("#gpa-sort-btn").removeClass("active");
        $("#number-sort-btn").addClass("active");
        // Choose default order
        selectOrderOfSort(sortNumberAsc);
    } else { // Already selected so simply reverse the order of sorting (ascending vs descending)
        sortNumberAsc *= -1;
        selectOrderOfSort(sortNumberAsc);
    }
};

const sortByRating = () => {
    activeSort = "rating";
    if (!$("#rating-sort-btn").hasClass("active")) {
        $("#number-sort-btn").removeClass("active");
        $("#diff-sort-btn").removeClass("active");
        $("#gpa-sort-btn").removeClass("active");
        $("#rating-sort-btn").addClass("active");
        selectOrderOfSort(sortRatingAsc);
    } else {
        sortRatingAsc *= -1;
        selectOrderOfSort(sortRatingAsc);
    }
};

const sortByDifficulty = () => {
    activeSort = "difficulty";
    if (!$("#diff-sort-btn").hasClass("active")) {
        $("#number-sort-btn").removeClass("active");
        $("#rating-sort-btn").removeClass("active");
        $("#gpa-sort-btn").removeClass("active");
        $("#diff-sort-btn").addClass("active");
        selectOrderOfSort(sortDifficultyAsc);
    } else {
        sortDifficultyAsc *= -1;
        selectOrderOfSort(sortDifficultyAsc);
    }
};

const sortByGpa = () => {
    activeSort = "gpa";
    if (!$("#gpa-sort-btn").hasClass("active")) {
        $("#number-sort-btn").removeClass("active");
        $("#rating-sort-btn").removeClass("active");
        $("#diff-sort-btn").removeClass("active");
        $("#gpa-sort-btn").addClass("active");
        selectOrderOfSort(sortGpaAsc);
    } else {
        sortGpaAsc *= -1;
        selectOrderOfSort(sortGpaAsc);
    }
};

// Simply here for the ascending order button to bind to
const ascendingOrder = () => {
    selectOrderOfSort(1);
};

// Simply here for the descending order button to bind to
const descendingOrder = () => {
    selectOrderOfSort(-1);
};

/* Helper function used by all sort functions to:
   -Compute the relevant sort based on what sort button is active
   -Select the relevant ascending/descending button
*/
const selectOrderOfSort = (asc) => {
    /* sortClasses takes in a comparing function (defined below) and reorders the classes appropriately
       comparator needed for both ascending and decending as any classes with null values should be at the end of the list either order
    */
    sortClasses(cmpByProp(activeSort, asc));

    if (asc === -1 && !$("#descending-order-btn").hasClass("active")) {
        $("#ascending-order-btn").removeClass("active");
        $("#descending-order-btn").addClass("active");
    } else if (asc === 1 && !$("#ascending-order-btn").hasClass("active")) {
        $("#descending-order-btn").removeClass("active");
        $("#ascending-order-btn").addClass("active");
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
