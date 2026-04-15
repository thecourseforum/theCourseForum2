/**
 * Modal Manager
 * =============
 * Handles modal open/close, backdrop clicks, and keyboard navigation.
 * Open/close uses a single delegated document listener so dynamically injected
 * markup (e.g. schedule flow modal body) works without per-element binding.
 */

(function () {
  "use strict";

  const BACKDROP_CLASS = "modal-backdrop";
  const OPEN_CLASS = "is-open";
  const BODY_OPEN_CLASS = "modal-open";
  const FOCUSABLE_SELECTOR =
    'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"]):not([disabled])';

  let activeModal = null;
  let previouslyFocused = null;

  const LOGIN_MODAL_ID = "loginModal";

  /**
   * Optional short hint above the login modal body (data-login-modal-message on the trigger).
   */
  function setLoginModalMessage(text) {
    const el = document.getElementById("loginModalHint");
    if (!el) return;
    const trimmed = text && String(text).trim();
    if (trimmed) {
      el.textContent = trimmed;
      el.classList.remove("hidden");
    } else {
      el.textContent = "";
      el.classList.add("hidden");
    }
  }

  /**
   * Open a modal by ID.
   * @param {string} modalId
   * @param {{ skipLoginMessageReset?: boolean }} [options] - When opening loginModal from a trigger that already called setLoginModalMessage, pass { skipLoginMessageReset: true }.
   */
  function openModal(modalId, options) {
    if (modalId === LOGIN_MODAL_ID && !options?.skipLoginMessageReset) {
      setLoginModalMessage(null);
    }

    const modal = document.getElementById(modalId);
    if (!modal) return;

    if (activeModal) {
      closeModal();
    }

    const backdrop = modal.previousElementSibling;

    // Store currently focused element
    previouslyFocused = document.activeElement;

    // Prevent body scroll
    document.body.classList.add(BODY_OPEN_CLASS);

    // Show modal and backdrop
    if (backdrop && backdrop.classList.contains(BACKDROP_CLASS)) {
      backdrop.classList.add(OPEN_CLASS);
    }
    modal.classList.add(OPEN_CLASS);

    activeModal = modal;

    // Focus first focusable element
    const focusable = modal.querySelector(FOCUSABLE_SELECTOR);
    if (focusable) {
      setTimeout(() => focusable.focus(), 100);
    }

    // Dispatch event
    modal.dispatchEvent(new CustomEvent("modal:open"));
  }

  /**
   * Close the currently active modal.
   */
  function closeModal() {
    if (!activeModal) return;

    const backdrop = activeModal.previousElementSibling;

    // Hide modal and backdrop
    activeModal.classList.remove(OPEN_CLASS);
    if (backdrop && backdrop.classList.contains(BACKDROP_CLASS)) {
      backdrop.classList.remove(OPEN_CLASS);
    }

    // Restore body scroll
    document.body.classList.remove(BODY_OPEN_CLASS);

    // Restore focus
    if (previouslyFocused) {
      previouslyFocused.focus();
    }

    // Dispatch event
    activeModal.dispatchEvent(new CustomEvent("modal:close"));

    activeModal = null;
    previouslyFocused = null;
  }

  /**
   * Close modal by ID.
   */
  function closeModalById(modalId) {
    const modal = document.getElementById(modalId);
    if (modal && modal === activeModal) {
      closeModal();
    }
  }

  /**
   * True if target's close element is the active modal's backdrop (sibling) or inside the modal.
   */
  function isActiveModalCloseTarget(target) {
    if (!activeModal) return false;
    const closeEl = target.closest("[data-modal-close]");
    if (!closeEl) return false;
    if (activeModal.contains(closeEl)) return true;
    const backdrop = activeModal.previousElementSibling;
    return (
      Boolean(backdrop) &&
      backdrop.classList.contains(BACKDROP_CLASS) &&
      closeEl === backdrop
    );
  }

  /**
   * Single delegated click handler (capture) for open and close triggers.
   */
  function handleDelegatedModalClick(e) {
    const openTrig = e.target.closest("[data-modal-open]");
    if (openTrig) {
      e.preventDefault();
      const modalId = openTrig.getAttribute("data-modal-open");
      if (modalId === LOGIN_MODAL_ID) {
        const raw = openTrig.getAttribute("data-login-modal-message");
        setLoginModalMessage(raw && raw.trim() ? raw.trim() : null);
        openModal(modalId, { skipLoginMessageReset: true });
      } else {
        openModal(modalId);
      }
      return;
    }

    if (isActiveModalCloseTarget(e.target)) {
      e.preventDefault();
      closeModal();
    }
  }

  function initModalTriggers() {
    document.addEventListener("click", handleDelegatedModalClick, true);
  }

  /**
   * Handle keyboard events.
   */
  function initKeyboardHandler() {
    document.addEventListener("keydown", (e) => {
      if (!activeModal) return;

      // Close on Escape
      if (e.key === "Escape") {
        e.preventDefault();
        closeModal();
        return;
      }

      // Trap focus within modal
      if (e.key === "Tab") {
        const focusableElements =
          activeModal.querySelectorAll(FOCUSABLE_SELECTOR);

        const firstFocusable = focusableElements[0];
        const lastFocusable = focusableElements[focusableElements.length - 1];

        if (e.shiftKey) {
          if (document.activeElement === firstFocusable) {
            e.preventDefault();
            lastFocusable.focus();
          }
        } else if (document.activeElement === lastFocusable) {
          e.preventDefault();
          firstFocusable.focus();
        }
      }
    });
  }

  // Initialize on DOM ready
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => {
      initModalTriggers();
      initKeyboardHandler();
    });
  } else {
    initModalTriggers();
    initKeyboardHandler();
  }

  // Expose API globally
  window.modal = {
    open: (modalId) => openModal(modalId),
    close: closeModal,
    closeById: closeModalById,
  };
})();
