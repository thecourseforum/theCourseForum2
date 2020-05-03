let number_A = true;
let rating_A = false;
let difficulty_A = true;
let gpa_A = false;

/*
    Each method sort_by_... is the same format as outline below
    sort_classes takes in a comparing function (defined below) and reorders the classes appropriately
    comparator needed for both ascending and decending as any classes with null values should be at the end of the list either order
*/
const sort_by_number = () => {
    // Updating looks and sorting order
    if (!$('#number-sort-btn').hasClass('active')) {
        $('#rating-sort-btn').removeClass('active')
        $('#diff-sort-btn').removeClass('active')
        $('#gpa-sort-btn').removeClass('active')
        $('#number-sort-btn').addClass('active')
    } else {               // Already selected so simply reverse the order of sorting (ascending vs descending)
        number_A = !number_A;
    }

    // Actual sorting
    if (number_A) {
        sort_classes(cmp_by_number_A)
    } else {
        sort_classes(cmp_by_number_D)
    }
}

const sort_by_rating = () => {
    if (!$('#rating-sort-btn').hasClass('active')) {
        $('#number-sort-btn').removeClass('active')
        $('#diff-sort-btn').removeClass('active')
        $('#gpa-sort-btn').removeClass('active')
        $('#rating-sort-btn').addClass('active')
    } else {
        rating_A = !rating_A;
    }

    if (rating_A) {
        sort_classes(cmp_by_rating_A)
    } else {
        sort_classes(cmp_by_rating_D)
    }
}

const sort_by_difficulty = () => {
    if (!$('#diff-sort-btn').hasClass('active')) {
        $('#number-sort-btn').removeClass('active')
        $('#rating-sort-btn').removeClass('active')
        $('#gpa-sort-btn').removeClass('active')
        $('#diff-sort-btn').addClass('active')
    } else {
        difficulty_A = !difficulty_A;
    }

    if (difficulty_A) {
        sort_classes(cmp_by_difficulty_A)
    } else {
        sort_classes(cmp_by_difficulty_D)
    }
}

const sort_by_gpa = () => {
    if (!$('#gpa-sort-btn').hasClass('active')) {
        $('#number-sort-btn').removeClass('active')
        $('#rating-sort-btn').removeClass('active')
        $('#diff-sort-btn').removeClass('active')
        $('#gpa-sort-btn').addClass('active')
    } else {
        gpa_A = !gpa_A;
    }

    if (gpa_A) {
        sort_classes(cmp_by_gpa_A)
    } else {
        sort_classes(cmp_by_gpa_D)
    }
}


const sort_classes = (cmp) => {
    $("ul.course-list").each(function (a) {
        var li = $(this).children("li");
        li.detach().sort(cmp);
        $(this).append(li);
    });
}

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