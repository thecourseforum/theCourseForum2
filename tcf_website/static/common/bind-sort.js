import { sortByNumber, sortByRating, sortByDifficulty, sortByGpa, sortByRecency, sortByRecencyOnce } from "./sortClasses.js";

if ($("#number-sort-btn").length) {
    document.getElementById("number-sort-btn").addEventListener("click", sortByNumber, false);
}
if ($("#recency-sort-btn").length) {
    document.getElementById("recency-sort-btn").addEventListener("click", sortByRecency, false);
    document.getElementById("show-btn").addEventListener("click", sortByRecencyOnce, false);
}
document.getElementById("rating-sort-btn").addEventListener("click", sortByRating, false);
document.getElementById("diff-sort-btn").addEventListener("click", sortByDifficulty, false);
document.getElementById("gpa-sort-btn").addEventListener("click", sortByGpa, false);
