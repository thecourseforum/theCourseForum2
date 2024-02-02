import {
    sortByNumber,
    sortByRating,
    sortByDifficulty,
    sortByGpa,
    sortByRecency
} from "./sortClasses.js";

// Conditionals present as toolbar is reused across departments/courses pages but with different functionality
if ($("#number-sort-btn").length) {
    document
        .getElementById("number-sort-btn")
        .addEventListener("click", sortByNumber, false);
}
if ($("#recency-sort-btn").length) {
    // Binds multi-directional sort function
    document
        .getElementById("recency-sort-btn")
        .addEventListener("click", (event) => sortByRecency(event, false), false);
    // Binds single sort function
    document
        .getElementById("show-btn")
        .addEventListener("click", (event) => sortByRecency(event, true), false);
}
document
    .getElementById("rating-sort-btn")
    .addEventListener("click", sortByRating, false);
document
    .getElementById("diff-sort-btn")
    .addEventListener("click", sortByDifficulty, false);
document
    .getElementById("gpa-sort-btn")
    .addEventListener("click", sortByGpa, false);
