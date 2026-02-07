/**
 * Modal Manager
 * =============
 * Handles modal open/close, backdrop clicks, and keyboard navigation.
 */

(function() {
  'use strict';

  const BACKDROP_CLASS = 'modal-backdrop';
  const MODAL_CLASS = 'modal';
  const OPEN_CLASS = 'is-open';
  const BODY_OPEN_CLASS = 'modal-open';

  let activeModal = null;
  let previouslyFocused = null;

  /**
   * Open a modal by ID.
   */
  function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (!modal) return;

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
    const focusable = modal.querySelector('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
    if (focusable) {
      setTimeout(() => focusable.focus(), 100);
    }
    
    // Dispatch event
    modal.dispatchEvent(new CustomEvent('modal:open'));
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
    activeModal.dispatchEvent(new CustomEvent('modal:close'));
    
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
   * Initialize modal triggers.
   */
  function initModalTriggers() {
    // Open triggers
    document.querySelectorAll('[data-modal-open]').forEach(trigger => {
      trigger.addEventListener('click', (e) => {
        e.preventDefault();
        const modalId = trigger.getAttribute('data-modal-open');
        openModal(modalId);
      });
    });

    // Close triggers
    document.querySelectorAll('[data-modal-close]').forEach(trigger => {
      trigger.addEventListener('click', (e) => {
        e.preventDefault();
        closeModal();
      });
    });

    // Backdrop click to close
    document.querySelectorAll(`.${BACKDROP_CLASS}`).forEach(backdrop => {
      backdrop.addEventListener('click', closeModal);
    });

    // Close button inside modals
    document.querySelectorAll('.modal__close').forEach(closeBtn => {
      closeBtn.addEventListener('click', (e) => {
        e.preventDefault();
        closeModal();
      });
    });
  }

  /**
   * Handle keyboard events.
   */
  function initKeyboardHandler() {
    document.addEventListener('keydown', (e) => {
      if (!activeModal) return;

      // Close on Escape
      if (e.key === 'Escape') {
        e.preventDefault();
        closeModal();
        return;
      }

      // Trap focus within modal
      if (e.key === 'Tab') {
        const focusableElements = activeModal.querySelectorAll(
          'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
        );
        
        const firstFocusable = focusableElements[0];
        const lastFocusable = focusableElements[focusableElements.length - 1];

        if (e.shiftKey) {
          if (document.activeElement === firstFocusable) {
            e.preventDefault();
            lastFocusable.focus();
          }
        } else {
          if (document.activeElement === lastFocusable) {
            e.preventDefault();
            firstFocusable.focus();
          }
        }
      }
    });
  }

  // Initialize on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      initModalTriggers();
      initKeyboardHandler();
    });
  } else {
    initModalTriggers();
    initKeyboardHandler();
  }

  // Expose API globally
  window.modal = {
    open: openModal,
    close: closeModal,
    closeById: closeModalById
  };
})();
