import { sortByNumber, sortByRating, sortByDifficulty, sortByGpa, ascendingOrder, descendingOrder } from "./sortClasses.js";

document.getElementById("number-sort-btn").addEventListener("click", sortByNumber, false);
document.getElementById("rating-sort-btn").addEventListener("click", sortByRating, false);
document.getElementById("diff-sort-btn").addEventListener("click", sortByDifficulty, false);
document.getElementById("gpa-sort-btn").addEventListener("click", sortByGpa, false);
document.getElementById("ascending-order-btn").addEventListener("click", ascendingOrder, false);
document.getElementById("descending-order-btn").addEventListener("click", descendingOrder, false);
