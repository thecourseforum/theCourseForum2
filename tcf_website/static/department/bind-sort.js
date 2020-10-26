import { sortByNumber, sortByRating, sortByDifficulty, sortByGpa } from "./sortClasses.js";

document.getElementById("number-sort-btn").addEventListener("click", sortByNumber, false);
document.getElementById("rating-sort-btn").addEventListener("click", sortByRating, false);
document.getElementById("diff-sort-btn").addEventListener("click", sortByDifficulty, false);
document.getElementById("gpa-sort-btn").addEventListener("click", sortByGpa, false);
