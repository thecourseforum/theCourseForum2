/* For reply upvote/downvote functionality */
function handleReplyVote(replyID, isUpvote) {
  const upvoteCountElem = $(`#reply${replyID} .reply-upvote-count`);
  const downvoteCountElem = $(`#reply${replyID} .reply-downvote-count`);
  const upvoteCount = parseInt(upvoteCountElem.text());
  const downvoteCount = parseInt(downvoteCountElem.text());

  let elem;
  let otherElem;
  let endpoint;
  let newUpvoteCount = upvoteCount;
  let newDownvoteCount = downvoteCount;

  if (isUpvote) {
    elem = $(`#reply${replyID} .reply-upvote`);
    otherElem = $(`#reply${replyID} .reply-downvote`);
    endpoint = `/reviews/reply/${replyID}/upvote/`;

    if (elem.hasClass("active")) {
      newUpvoteCount = upvoteCount - 1;
    } else if (otherElem.hasClass("active")) {
      newUpvoteCount = upvoteCount + 1;
      newDownvoteCount = downvoteCount - 1;
    } else {
      newUpvoteCount = upvoteCount + 1;
    }
  } else {
    elem = $(`#reply${replyID} .reply-downvote`);
    otherElem = $(`#reply${replyID} .reply-upvote`);
    endpoint = `/reviews/reply/${replyID}/downvote/`;

    if (elem.hasClass("active")) {
      newDownvoteCount = downvoteCount - 1;
    } else if (otherElem.hasClass("active")) {
      newDownvoteCount = downvoteCount + 1;
      newUpvoteCount = upvoteCount - 1;
    } else {
      newDownvoteCount = downvoteCount + 1;
    }
  }

  fetch(endpoint, {
    method: "post",
    headers: { "X-CSRFToken": getCookie("csrftoken") },
  });

  upvoteCountElem.text(newUpvoteCount);
  downvoteCountElem.text(newDownvoteCount);

  if (elem.hasClass("active")) {
    elem.removeClass("active");
  } else {
    elem.addClass("active");
    otherElem.removeClass("active");
  }
}

export { handleReplyVote };