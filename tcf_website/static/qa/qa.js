/* For question upvote/downvote functionality */
function handleQuestionVote(questionID, isUpvote) {
    const upvoteCountElem = $(`#question${questionID} .upvoteCount`);
    const downvoteCountElem = $(`#question${questionID} .downvoteCount`);
    const totalCountElem = $(`#question${questionID} #question-vote-count`);
    const upvoteCount = parseInt(upvoteCountElem.text());
    const downvoteCount = parseInt(downvoteCountElem.text());

    let elem;
    let otherElem;
    let endpoint;
    let newUpvoteCount;
    let newDownvoteCount;

    if (isUpvote) {
        elem = $(`#question${questionID} .upvoteQuestion`);
        otherElem = $(`#question${questionID} .downvoteQuestion`);
        endpoint = `/questions/${questionID}/upvote/`;

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
        elem = $(`#question${questionID} .downvoteQuestion`);
        otherElem = $(`#question${questionID} .upvoteQuestion`);
        endpoint = `/questions/${questionID}/downvote/`;

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

/* For answer upvote/downvote functionality */
function handleAnswerVote(answerID, isUpvote) {
    const upvoteCountElem = $(`#answer${answerID} .upvoteCount`);
    const downvoteCountElem = $(`#answer${answerID} .downvoteCount`);
    const totalCountElem = $(`#answer${answerID} #answer-vote-count`);
    const upvoteCount = parseInt(upvoteCountElem.text());
    const downvoteCount = parseInt(downvoteCountElem.text());

    let elem;
    let otherElem;
    let endpoint;
    let newUpvoteCount;
    let newDownvoteCount;

    if (isUpvote) {
        elem = $(`#answer${answerID} .upvoteAnswer`);
        otherElem = $(`#answer${answerID} .downvoteAnswer`);
        endpoint = `/answers/${answerID}/upvote/`;

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
        elem = $(`#answer${answerID} .downvoteAnswer`);
        otherElem = $(`#answer${answerID} .upvoteAnswer`);
        endpoint = `/answers/${answerID}/downvote/`;

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

export { handleQuestionVote, handleAnswerVote };
