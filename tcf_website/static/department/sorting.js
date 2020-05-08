let sortNumberAsc = true;
let sortRatingAsc = false;
let sortDifficultyAsc = true;
let sortGpaAsc = false;

/*
    Each method sort_by_... is the same format as outline below
    sort_classes takes in a comparing function (defined below) and reorders the classes appropriately
    comparator needed for both ascending and decending as any classes with null values should be at the end of the list either order
*/
const sortByNumber = () => {
    // Updating looks and sorting order
    if (!$('#number-sort-btn').hasClass('active')) {
        $('#rating-sort-btn').removeClass('active')
        $('#diff-sort-btn').removeClass('active')
        $('#gpa-sort-btn').removeClass('active')
        $('#number-sort-btn').addClass('active')
    } else {               // Already selected so simply reverse the order of sorting (ascending vs descending)
        sortNumberAsc = !sortNumberAsc;
    }

    // Actual sorting
    sortClasses(compareByPartial(3, sortNumberAsc));
}

const sortByRating = () => {
    if (!$('#rating-sort-btn').hasClass('active')) {
        $('#number-sort-btn').removeClass('active')
        $('#diff-sort-btn').removeClass('active')
        $('#gpa-sort-btn').removeClass('active')
        $('#rating-sort-btn').addClass('active')
    } else {
        sortRatingAsc = !sortRatingAsc;
    }

    sortClasses(compareByPartial(0, sortRatingAsc));
}

const sortByDifficulty = () => {
    if (!$('#diff-sort-btn').hasClass('active')) {
        $('#number-sort-btn').removeClass('active')
        $('#rating-sort-btn').removeClass('active')
        $('#gpa-sort-btn').removeClass('active')
        $('#diff-sort-btn').addClass('active')
    } else {
        sortDifficultyAsc = !sortDifficultyAsc;
    }

    sortClasses(compareByPartial(1, sortDifficultyAsc));
}

const sortByGpa = () => {
    if (!$('#gpa-sort-btn').hasClass('active')) {
        $('#number-sort-btn').removeClass('active')
        $('#rating-sort-btn').removeClass('active')
        $('#diff-sort-btn').removeClass('active')
        $('#gpa-sort-btn').addClass('active')
    } else {
        sortGpaAsc = !sortGpaAsc;
    }

    sortClasses(compareByPartial(2, sortGpaAsc));
}


const sortClasses = (cmp) => {
    $("ul.course-list").each(function (a) {
        var li = $(this).children("li");
        li.detach().sort(cmp);
        $(this).append(li);
    });
}

const compareByPartial = (attribute, ascending) => {

    const compareByAttribute = (a, b) => {
        let attributeA = "";
        let attributeB = "";
        switch (attribute) {
            case 0:                                                                                 // Rating
            case 1:                                                                                 // Difficulty
            case 2:                                                                                 // GPA
                attributeA = a.querySelectorAll(".mb-0.info")[attribute].innerHTML.trim();    // If any of these three cases,
                attributeB = b.querySelectorAll(".mb-0.info")[attribute].innerHTML.trim();    // getting value is the same
                break;
            case 3:                                                                                 // Number
                attributeA = a.getElementsByTagName("h3")[0].innerHTML.split(" ").pop();
                attributeB = b.getElementsByTagName("h3")[0].innerHTML.split(" ").pop();
                break;
            default:
                console.log('Sorting Error')            
        }
        

        if (isNaN(attributeA)) {               // This ensures that NaN elements are at the end of the list
            return 1;
        } else if (isNaN(attributeB)) {
            return -1;
        }

        if (attributeA > attributeB) {
            return ascending ? 1 : -1;
        } else if (attributeB > attributeA) {
            return ascending ? -1 : 1;
        } else {
            return 0;
        }
    }

    return compareByAttribute;
}


/*
const cmp_by_rating_D = (a, b) => {
    ratingA = a.querySelectorAll(".mb-0.info")[0].innerHTML.trim();
    ratingB = b.querySelectorAll(".mb-0.info")[0].innerHTML.trim();

    if (ratingA === '—') {
        return 1;
    } else if (ratingB === '—') {
        return -1;
    }

    if (ratingA > ratingB) {
        return -1;
    } else if (ratingB > ratingA) {
        return 1;
    } else {
        return 0;
    }
};

const cmp_by_rating_A = (a, b) => {
    ratingA = a.querySelectorAll(".mb-0.info")[0].innerHTML.trim();
    ratingB = b.querySelectorAll(".mb-0.info")[0].innerHTML.trim();

    if (ratingA === '—') {
        return 1;
    } else if (ratingB === '—') {
        return -1;
    }

    if (ratingA > ratingB) {
        return 1;
    } else if (ratingB > ratingA) {
        return -1;
    } else {
        return 0;
    }
};

const cmp_by_difficulty_D = (a, b) => {
    difficultyA = a.querySelectorAll(".mb-0.info")[1].innerHTML.trim();
    difficultyB = b.querySelectorAll(".mb-0.info")[1].innerHTML.trim();

    if (difficultyA === '—') {
        return 1;
    } else if (difficultyB === '—') {
        return -1;
    }

    if (difficultyA > difficultyB) {
        return -1;
    } else if (difficultyB > difficultyA) {
        return 1;
    } else {
        return 0;
    }
};

const cmp_by_difficulty_A = (a, b) => {
    difficultyA = a.querySelectorAll(".mb-0.info")[1].innerHTML.trim();
    difficultyB = b.querySelectorAll(".mb-0.info")[1].innerHTML.trim();

    if (difficultyA === '—') {
        return 1;
    } else if (difficultyB === '—') {
        return -1;
    }

    if (difficultyA > difficultyB) {
        return 1;
    } else if (difficultyB > difficultyA) {
        return -1;
    } else {
        return 0;
    }
};

const cmp_by_gpa_D = (a, b) => {
    gpaA = a.querySelectorAll(".mb-0.info")[2].innerHTML.trim();
    gpaB = b.querySelectorAll(".mb-0.info")[2].innerHTML.trim();

    if (gpaA > gpaB) {
        return -1;
    } else if (gpaB > gpaA) {
        return 1;
    } else {
        return 0;
    }
};

const cmp_by_gpa_A = (a, b) => {
    gpaA = a.querySelectorAll(".mb-0.info")[2].innerHTML.trim();
    gpaB = b.querySelectorAll(".mb-0.info")[2].innerHTML.trim();

    if (gpaA > gpaB) {
        return 1;
    } else if (gpaB > gpaA) {
        return -1;
    } else {
        return 0;
    }
};

const cmp_by_number_D = (a, b) => {
    numberA = a.getElementsByTagName("h3")[0].innerHTML;
    numberB = b.getElementsByTagName("h3")[0].innerHTML;

    if (numberA > numberB) {
        return -1;
    } else if (numberB > numberA) {
        return 1;
    } else {
        return 0;
    }
};

const cmp_by_number_A = (a, b) => {
    numberA = a.getElementsByTagName("h3")[0].innerHTML;
    numberB = b.getElementsByTagName("h3")[0].innerHTML;

    if (numberA > numberB) {
        return 1;
    } else if (numberB > numberA) {
        return -1;
    } else {
        return 0;
    }
};
*/