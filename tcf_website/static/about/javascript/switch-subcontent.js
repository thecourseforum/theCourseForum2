/*
    This javascript is used to select between
    history, current team, and past contributors
    when loading the about page subcontent on theCourseForum.

    Author: Bradley Knaysi
*/

const showCurrentTeam = () => {
    // Hide subcontent
    $(".tCF-past-contributors").removeClass("shown");
    $(".tCF-history").removeClass("shown");
    $(".tCF-sponsors").removeClass("shown");

    // Show subcontent
    $(".tCF-current-team").addClass("shown");

    // Show user the current selection
    $("#tCF-current-team-btn").addClass("active");
    $("#tCF-history-btn").removeClass("active");
    $("#tCF-past-contributors-btn").removeClass("active");
    $("#tCF-sponsors-btn").removeClass("active");
};

const showHistory = () => {
    // Hide subcontent
    $(".tCF-past-contributors").removeClass("shown");
    $(".tCF-current-team").removeClass("shown");
    $(".tCF-sponsors").removeClass("shown");

    // Show subcontent
    $(".tCF-history").addClass("shown");

    // Show user the current selection
    $("#tCF-history-btn").addClass("active");
    $("#tCF-current-team-btn").removeClass("active");
    $("#tCF-past-contributors-btn").removeClass("active");
    $("#tCF-sponsors-btn").removeClass("active");
};

const showPastContributors = () => {
    // Hide subcontent
    $(".tCF-current-team").removeClass("shown");
    $(".tCF-history").removeClass("shown");
    $(".tCF-sponsors").removeClass("shown");

    // Show subcontent
    $(".tCF-past-contributors").addClass("shown");

    // Show user the current selection
    $("#tCF-past-contributors-btn").addClass("active");
    $("#tCF-history-btn").removeClass("active");
    $("#tCF-current-team-btn").removeClass("active");
    $("#tCF-sponsors-btn").removeClass("active");
};

const showSponsors = () => {
    // Hide subcontent
    $(".tCF-current-team").removeClass("shown");
    $(".tCF-history").removeClass("shown");
    $(".tCF-past-contributors").removeClass("shown");

    // Show subcontent
    $(".tCF-sponsors").addClass("shown");

    // Show user the current selection
    $("#tCF-sponsors-btn").addClass("active");
    $("#tCF-history-btn").removeClass("active");
    $("#tCF-current-team-btn").removeClass("active");
    $("#tCF-past-contributors-btn").removeClass("active");
};

export { showCurrentTeam, showHistory, showPastContributors, showSponsors };
