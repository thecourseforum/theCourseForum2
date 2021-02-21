/* For review upvote/downvote functionality */
function handleVote(reviewID, isUpvote) {
    const voteCountElem = $(`#review${reviewID} .voteCount`);
    const voteCount = parseInt(voteCountElem.text());

    let elem;
    let otherElem;
    let endpoint;
    let newVoteCount;

    if (isUpvote) {
        elem = $(`#review${reviewID} .upvote`);
        otherElem = $(`#review${reviewID} .downvote`);
        endpoint = `/reviews/${reviewID}/upvote`;

        // If already upvoted, subtract 1.
        if (elem.hasClass("active")) {
            newVoteCount = voteCount - 1;
        // If already downvoted, add 2.
        } else if (otherElem.hasClass("active")) {
            newVoteCount = voteCount + 2;
        // Otherwise add 1.
        } else {
            newVoteCount = voteCount + 1;
        }
    } else {
        elem = $(`#review${reviewID} .downvote`);
        otherElem = $(`#review${reviewID} .upvote`);
        endpoint = `/reviews/${reviewID}/downvote`;

        // If already downvoted, add 1.
        if (elem.hasClass("active")) {
            newVoteCount = voteCount + 1;
        // If already upvoted, subtract 2.
        } else if (otherElem.hasClass("active")) {
            newVoteCount = voteCount - 2;
        // Otherwise subtract 1.
        } else {
            newVoteCount = voteCount - 1;
        }
    }

    // POST to upvote or downvote endpoint.
    fetch(endpoint, {
        method: "post",
        headers: { "X-CSRFToken": getCookie("csrftoken") }
    });

    // Update vote text.
    voteCountElem.text(newVoteCount);

    // Only one option can be active
    if (elem.hasClass("active")) {
        elem.removeClass("active");
    } else {
        elem.addClass("active");
        otherElem.removeClass("active");
    }
}

export { handleVote };

/* For review text collapse/expand functionality */
$(window).resize(function() {
    // On browser window resize, refresh collapser threshold for each review card
    $(".review").each(function(i, review) {
        var visibleReviewBody = $(this).find("div.review-text-body");
        var fullReviewText = $(this).find("p.review-text-full");
        var reviewCollapseLink = $(this).find("a.review-collapse-link");

        // Long review
        if (visibleReviewBody.height() < fullReviewText.height()) {
            // Show "See More" expander only for long reviews
            reviewCollapseLink.show();
        } else { // Short review
            reviewCollapseLink.hide();
            visibleReviewBody.css("height", "auto"); // Remove static blurb height
        }
    });
});
