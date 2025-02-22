import { handleVote } from "./review";

document.addEventListener("DOMContentLoaded", function () {
    const currentPage = 1;
    const courseId = document.getElementById("reviews-container").dataset.courseId;
    const instructorId = document.getElementById("reviews-container").dataset.instructorId;

    function fetchReviews(page) {
        $.ajax({
            url: `/reviews/paginated/${courseId}/${instructorId}?page=${page}`,
            type: "GET",
            dataType: "json",
            success: function (data) {
                $("#reviews-container").html(data.reviews_html);

                // update pagination buttons
                $(".pagination-button").off("click").on("click", function (event) {
                    event.preventDefault();
                    fetchReviews($(this).data("page"));
                });

                // reattach voting event handlers
                attachVoteHandlers();

            },
            error: function () {
                console.error("Failed to load reviews.");
            }
        });
    }

    function attachVoteHandlers() {
        $(".upvote").each(function () {
            $(this).off("click").on("click", function () {
                handleVote(this.id.substring(6), true);
            });
        });

        $(".downvote").each(function () {
            $(this).off("click").on("click", function () {
                handleVote(this.id.substring(8), false);
            });
        });
    }

    // initial fetch
    fetchReviews(currentPage);
});
