import { sortByNumber, sortByRating, sortByDifficulty, sortByGpa, sortByLastTaught, sortByLastTaughtOnce } from "./sortClasses.js";

if ($("#number-sort-btn").length) {
    document.getElementById("number-sort-btn").addEventListener("click", sortByNumber, false);
}
document.getElementById("rating-sort-btn").addEventListener("click", sortByRating, false);
document.getElementById("diff-sort-btn").addEventListener("click", sortByDifficulty, false);
document.getElementById("gpa-sort-btn").addEventListener("click", sortByGpa, false);
if ($("#last-taught-sort-btn").length) {
    document.getElementById("last-taught-sort-btn").addEventListener("click", sortByLastTaught, false);
    document.getElementById("show-btn").addEventListener("click", sortByLastTaughtOnce, false);
}
