/* For review upvote/downvote functionality */
function handleVote(reviewID, isUpvote) {
    const upvoteCountElem = $(`#review${reviewID} .upvoteCount`);
    const downvoteCountElem = $(`#review${reviewID} .downvoteCount`);
    const upvoteCount = parseInt(upvoteCountElem.text());
    const downvoteCount = parseInt(downvoteCountElem.text());

    let elem;
    let otherElem;
    let endpoint;
    let newUpvoteCount;
    let newDownvoteCount;

    if (isUpvote) {
        elem = $(`#review${reviewID} .upvote`);
        otherElem = $(`#review${reviewID} .downvote`);
        endpoint = `/reviews/${reviewID}/upvote/`;

        // If already upvoted, subtract 1.
        if (elem.hasClass("active")) {
            newUpvoteCount = upvoteCount - 1;
            // If already downvoted, add 1 to upvote and subtract 1 from downvote.
        } else if (otherElem.hasClass("active")) {
            newUpvoteCount = upvoteCount + 1;
            newDownvoteCount = downvoteCount - 1;
            // Otherwise add 1.
        } else {
            newUpvoteCount = upvoteCount + 1;
        }
    } else {
        elem = $(`#review${reviewID} .downvote`);
        otherElem = $(`#review${reviewID} .upvote`);
        endpoint = `/reviews/${reviewID}/downvote/`;

        // If already downvoted, add 1.
        if (elem.hasClass("active")) {
            newDownvoteCount = downvoteCount - 1;
            // If already upvoted, add 1 to downvote and subtract 1 from upvote.
        } else if (otherElem.hasClass("active")) {
            newDownvoteCount = downvoteCount + 1;
            newUpvoteCount = upvoteCount - 1;
            // Otherwise subtract 1.
        } else {
            newDownvoteCount = downvoteCount + 1;
        }
    }

    // POST to upvote or downvote endpoint.
    fetch(endpoint, {
        method: "post",
        headers: { "X-CSRFToken": getCookie("csrftoken") }
    });

    // Update vote text.
    upvoteCountElem.text(newUpvoteCount);
    downvoteCountElem.text(newDownvoteCount);

    if (elem.hasClass("active")) {
        elem.removeClass("active");
    } else {
        elem.addClass("active");
        otherElem.removeClass("active");
    }
}

export { handleVote };

/* For review text collapse/expand functionality */
$(function() {
    // On browser window resize, refresh collapser threshold for each review card
    $(".review").each(function(i, review) {
        const visibleReviewBody = $(this).find("div.review-text-body");
        const fullReviewText = $(this).find("p.review-text-full");
        const reviewCollapseLink = $(this).find("a.review-collapse-link");

        // Long review
        if (visibleReviewBody.height() < fullReviewText.height()) {
            // Show "See More" expander only for long reviews
            reviewCollapseLink.show();
        } else {
            // Short review
            reviewCollapseLink.hide();
            visibleReviewBody.css("height", "auto"); // Remove static blurb height
        }
    });
});
