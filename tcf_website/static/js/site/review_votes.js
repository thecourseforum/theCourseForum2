/**
 * Review Vote Manager
 * ===================
 * Handles secure in-place voting updates for review cards.
 */

(function () {
  "use strict";

  function getCookie(name) {
    const cookie = document.cookie
      .split(";")
      .map((part) => part.trim())
      .find((part) => part.startsWith(`${name}=`));
    return cookie
      ? decodeURIComponent(cookie.split("=").slice(1).join("="))
      : "";
  }

  function openLoginModal() {
    if (window.modal && typeof window.modal.open === "function") {
      window.modal.open("loginModal");
    }
  }

  function isAuthenticated() {
    return document.body?.dataset.userAuthenticated === "true";
  }

  async function submitVote(button) {
    const reviewId = button.dataset.review;
    const action = button.dataset.action === "upvote" ? "up" : "down";
    const voteContainer = button.closest(".review-card__votes");
    if (!reviewId || !voteContainer) {
      return;
    }

    if (!isAuthenticated()) {
      openLoginModal();
      return;
    }

    const csrfToken = getCookie("csrftoken");
    const buttons = voteContainer.querySelectorAll(".vote-btn");
    buttons.forEach((item) => {
      item.disabled = true;
    });

    try {
      const response = await fetch(`/reviews/${reviewId}/vote/`, {
        method: "POST",
        credentials: "same-origin",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
          "X-CSRFToken": csrfToken,
          "X-Requested-With": "XMLHttpRequest",
        },
        body: new URLSearchParams({ action }).toString(),
      });

      if (!response.ok) {
        throw new Error("Vote request failed.");
      }

      const payload = await response.json();
      const upvoteButton = voteContainer.querySelector(
        '[data-action="upvote"]',
      );
      const downvoteButton = voteContainer.querySelector(
        '[data-action="downvote"]',
      );
      const scoreElement = upvoteButton?.querySelector("span");

      if (scoreElement && typeof payload.sum_votes === "number") {
        scoreElement.textContent = String(payload.sum_votes);
      }

      upvoteButton?.classList.toggle("is-active", payload.user_vote > 0);
      downvoteButton?.classList.toggle("is-active", payload.user_vote < 0);
    } catch (error) {
      // Keep this intentionally quiet to avoid noisy UI errors.
      // eslint-disable-next-line no-console
      console.error(error);
    } finally {
      buttons.forEach((item) => {
        item.disabled = false;
      });
    }
  }

  function initVotes() {
    document
      .querySelectorAll(".review-card__votes")
      .forEach((voteContainer) => {
        if (voteContainer.dataset.voteInit === "true") {
          return;
        }
        voteContainer.dataset.voteInit = "true";
        voteContainer.addEventListener("click", (event) => {
          const button = event.target.closest(".vote-btn");
          if (!button) {
            return;
          }
          event.preventDefault();
          submitVote(button);
        });
      });
  }

  function initLoginButtons() {
    document.querySelectorAll('[data-action="login"]').forEach((trigger) => {
      if (trigger.dataset.loginInit === "true") {
        return;
      }
      trigger.dataset.loginInit = "true";
      trigger.addEventListener("click", (event) => {
        event.preventDefault();
        openLoginModal();
      });
    });
  }

  function init() {
    initVotes();
    initLoginButtons();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  window.reviewVotes = { init };
})();
