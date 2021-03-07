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
    Remove the arrows from all other buttons as well
    Use selectOrderOfSort to sort and toggle correct ascending/descneding button
*/
const sortByNumber = () => {
    activeSort = "title";

    // Updating looks and sorting order
    if (!$("#number-sort-btn").hasClass("active")) {
        $("#rating-sort-btn").removeClass("active");
        $("#diff-sort-btn").removeClass("active");
        $("#gpa-sort-btn").removeClass("active");
        $("#rating-sort-btn").html("Rating");
        $("#diff-sort-btn").html("Difficulty");
        $("#gpa-sort-btn").html("GPA");
        $("#number-sort-btn").addClass("active");
        // Choose default order
    } else { // Already selected so simply reverse the order of sorting (ascending vs descending)
        sortNumberAsc *= -1;
    }
    selectOrderOfSort(sortNumberAsc, "#number-sort-btn", "Course ID");
};

const sortByRating = () => {
    activeSort = "rating";
    if (!$("#rating-sort-btn").hasClass("active")) {
        $("#number-sort-btn").removeClass("active");
        $("#diff-sort-btn").removeClass("active");
        $("#gpa-sort-btn").removeClass("active");
        $("#number-sort-btn").html("Course ID");
        $("#diff-sort-btn").html("Difficulty");
        $("#gpa-sort-btn").html("GPA");
        $("#rating-sort-btn").addClass("active");
    } else {
        sortRatingAsc *= -1;
    }
    selectOrderOfSort(sortRatingAsc, "#rating-sort-btn", "Rating");
};

const sortByDifficulty = () => {
    activeSort = "difficulty";
    if (!$("#diff-sort-btn").hasClass("active")) {
        $("#number-sort-btn").removeClass("active");
        $("#rating-sort-btn").removeClass("active");
        $("#gpa-sort-btn").html("GPA");
        $("#number-sort-btn").html("Course ID");
        $("#rating-sort-btn").html("Rating");
        $("#gpa-sort-btn").removeClass("active");

        $("#diff-sort-btn").addClass("active");
    } else {
        sortDifficultyAsc *= -1;
    }
    selectOrderOfSort(sortDifficultyAsc, "#diff-sort-btn", "Difficulty");
};

const sortByGpa = () => {
    activeSort = "gpa";
    if (!$("#gpa-sort-btn").hasClass("active")) {
        $("#number-sort-btn").removeClass("active");
        $("#rating-sort-btn").removeClass("active");
        $("#diff-sort-btn").removeClass("active");
        $("#number-sort-btn").html("Course ID");
        $("#rating-sort-btn").html("Rating");
        $("#diff-sort-btn").html("Difficulty");
        $("#gpa-sort-btn").addClass("active");
    } else {
        sortGpaAsc *= -1;
    }
    selectOrderOfSort(sortGpaAsc, "#gpa-sort-btn", "GPA");
};

/* Helper function used by all sort functions to:
   -Compute the relevant sort based on what sort button is active
   -Select the relevant ascending/descending arrow and add it as text
*/
const selectOrderOfSort = (asc, id, sortName) => {
    /* sortClasses takes in a comparing function (defined below) and reorders the classes appropriately
       comparator needed for both ascending and descending as any classes with null values should be at the end of the list either order
    */
    var arrow = "";
    sortClasses(cmpByProp(activeSort, asc));
    if (asc === 1) {
        arrow = " &#11014;"; // Up arrow (dummy Unicode value replace with the real one)
    } else {
        arrow = " &#11015;"; // Down arrow (dummy Unicode value replace with the real one)
    }
    $(id).html(sortName + arrow);
};

const sortClasses = (cmp) => {
    $("ul.course-list").each(function(a) {
        var li = $(this).children("li");
        li.detach().sort(cmp);
        $(this).append(li);
    });
};

export { sortByNumber, sortByRating, sortByDifficulty, sortByGpa };
