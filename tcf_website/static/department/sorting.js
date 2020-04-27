const sort = (cmp) => {
    $("ul.course-list").each(function (a) {
        var li = $(this).children("li");
        li.detach().sort(cmp);
        $(this).append(li);
    });
}

const sort_by_rating_D = (a, b) => {
    ratingA = a.querySelectorAll(".mb-0.info")[0].innerHTML.trim();
    ratingB = b.querySelectorAll(".mb-0.info")[0].innerHTML.trim();

    if (ratingA === '—' | ratingB === '—') {
        return 1;
    }

    if (ratingA > ratingB) {
        return -1;
    } else if (ratingB > ratingA) {
        return 1;
    } else {
        return 0;
    }
};

const sort_by_rating_A = (a, b) => {
    ratingA = a.querySelectorAll(".mb-0.info")[0].innerHTML.trim();
    ratingB = b.querySelectorAll(".mb-0.info")[0].innerHTML.trim();

    if (ratingA === '—' | ratingB === '—') {
        return 1;
    }

    if (ratingA > ratingB) {
        return 1;
    } else if (ratingB > ratingA) {
        return -1;
    } else {
        return 0;
    }
};

const sort_by_difficulty_D = (a, b) => {
    difficultyA = a.querySelectorAll(".mb-0.info")[1].innerHTML.trim();
    difficultyB = b.querySelectorAll(".mb-0.info")[1].innerHTML.trim();

    if (difficultyA === '—' | difficultyB === '—') {
        return 1;
    }

    if (difficultyA > difficultyB) {
        return -1;
    } else if (difficultyB > difficultyA) {
        return 1;
    } else {
        return 0;
    }
};

const sort_by_difficulty_A = (a, b) => {
    difficultyA = a.querySelectorAll(".mb-0.info")[1].innerHTML.trim();
    difficultyB = b.querySelectorAll(".mb-0.info")[1].innerHTML.trim();

    if (difficultyA === '—' | difficultyB === '—') {
        return 1;
    }

    if (difficultyA > difficultyB) {
        return 1;
    } else if (difficultyB > difficultyA) {
        return -1;
    } else {
        return 0;
    }
};

const sort_by_gpa_D = (a, b) => {
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

const sort_by_gpa_A = (a, b) => {
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

const sort_by_number_D = (a, b) => {
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

const sort_by_number_A = (a, b) => {
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