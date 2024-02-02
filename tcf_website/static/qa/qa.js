function handleQAVote(elementID, isQuestion, isUpvote) {
    let elem;
    let otherElem;
    let endpoint;
    let newUpvoteCount;
    let newDownvoteCount;

    let upvoteCountElem;
    let downvoteCountElem;
    let totalCountElem;

    if (isQuestion) {
        upvoteCountElem = $(`#question${elementID} .upvoteCount`);
        downvoteCountElem = $(`#question${elementID} .downvoteCount`);
        totalCountElem = $(`#question${elementID} #question-vote-count`);

        if (isUpvote) {
            elem = $(`#question${elementID} .upvoteQuestion`);
            otherElem = $(`#question${elementID} .downvoteQuestion`);
            endpoint = `/questions/${elementID}/upvote/`;
        } else {
            elem = $(`#question${elementID} .downvoteQuestion`);
            otherElem = $(`#question${elementID} .upvoteQuestion`);
            endpoint = `/questions/${elementID}/downvote/`;
        }
    } else {
        upvoteCountElem = $(`#answer${elementID} .upvoteCount`);
        downvoteCountElem = $(`#answer${elementID} .downvoteCount`);
        totalCountElem = $(`#answer${elementID} #answer-vote-count`);

        if (isUpvote) {
            elem = $(`#answer${elementID} .upvoteAnswer`);
            otherElem = $(`#answer${elementID} .downvoteAnswer`);
            endpoint = `/answers/${elementID}/upvote/`;
        } else {
            elem = $(`#answer${elementID} .downvoteAnswer`);
            otherElem = $(`#answer${elementID} .upvoteAnswer`);
            endpoint = `/answers/${elementID}/downvote/`;
        }
    }

    const upvoteCount = parseInt(upvoteCountElem.text());
    const downvoteCount = parseInt(downvoteCountElem.text());

    if (isUpvote) {
    // If already upvoted, subtract 1.
        if (elem.hasClass("active")) {
            newUpvoteCount = upvoteCount - 1;
            newDownvoteCount = downvoteCount;
            // If already downvoted, add 1 to upvote and subtract 1 from downvote.
        } else if (otherElem.hasClass("active")) {
            newUpvoteCount = upvoteCount + 1;
            newDownvoteCount = downvoteCount - 1;
            // Otherwise add 1.
        } else {
            newUpvoteCount = upvoteCount + 1;
            newDownvoteCount = downvoteCount;
        }
    } else {
    // If already downvoted, add 1.
        if (elem.hasClass("active")) {
            newDownvoteCount = downvoteCount - 1;
            newUpvoteCount = upvoteCount;
            // If already upvoted, add 1 to downvote and subtract 1 from upvote.
        } else if (otherElem.hasClass("active")) {
            newDownvoteCount = downvoteCount + 1;
            newUpvoteCount = upvoteCount - 1;
            // Otherwise subtract 1.
        } else {
            newDownvoteCount = downvoteCount + 1;
            newUpvoteCount = upvoteCount;
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
    totalCountElem.text(newUpvoteCount - newDownvoteCount);

    if (elem.hasClass("active")) {
        elem.removeClass("active");
    } else {
        elem.addClass("active");
        otherElem.removeClass("active");
    }
}

export { handleQAVote };
