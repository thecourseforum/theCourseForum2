document.addEventListener('DOMContentLoaded', function() {
  // Initialize all search bars independently
  document.querySelectorAll('.search-bar-container').forEach(container => {
    const toggle = container.querySelector('.search-bar__filter-trigger');
    const dropdown = container.querySelector('.search-filters');
    const form = container.querySelector('form');
    const clearBtn = container.querySelector('.btn--ghost'); // Assuming clean button has this class or add ID-like class
    const gpaSlider = container.querySelector('input[name="min_gpa"]');
    const gpaValue = container.querySelector('#gpaValue') || container.querySelector('.gpa-value-display'); 
    // note: IDs inside template are still problem if not unique. 
    // We should use classes for gpaValue finding or scoped query.
    
    // 1. Toggle Dropdown
    if (toggle && dropdown) {
      toggle.addEventListener('click', (e) => {
        e.stopPropagation();
        
        // Close other open dropdowns first? Valid UX but optional.
        document.querySelectorAll('.search-filters.is-open').forEach(d => {
            if (d !== dropdown) {
                d.classList.remove('is-open');
                // Remove active state from their toggles
                // (Need to find the toggle for that dropdown... simplifying: just close)
            }
        });

        dropdown.classList.toggle('is-open');
        toggle.classList.toggle('is-active');
      });

      // Close when clicking outside
      document.addEventListener('click', (e) => {
        if (dropdown.classList.contains('is-open') && 
            !dropdown.contains(e.target) && 
            !toggle.contains(e.target)) {
          dropdown.classList.remove('is-open');
          toggle.classList.remove('is-active');
        }
      });
      
      // Prevent closing when clicking inside
      dropdown.addEventListener('click', (e) => {
         // e.stopPropagation(); 
      });
    }

    // 2. GPA Slider
    if (gpaSlider) {
       // Find value display relative to slider
       const valueDisplay = gpaSlider.parentElement.querySelector('span'); // Simple relative find
       if (valueDisplay) {
         gpaSlider.addEventListener('input', () => {
           valueDisplay.textContent = parseFloat(gpaSlider.value).toFixed(1);
         });
       }
    }

    // 3. List Filtering (Subjects/Disciplines)
    // Scope inputs to this container
    const searchInputs = container.querySelectorAll('[data-filter-list]');
    searchInputs.forEach(input => {
      input.addEventListener('keyup', () => {
        const targetId = input.dataset.filterList; 
        // IDs are still used for lists. Since lists are inside the unique dropdown, 
        // using ID is risky if duplicate components exist.
        // We should traverse DOM or use scoped naming? 
        // For now, assume only one open filter or that lists are structurally found.
        
        // Better: Find the list sibling or child of parent
        const listContainer = input.closest('.filter-list-container').querySelector('.filter-list');
        
        if (!listContainer) return;
        
        const filterText = input.value.toLowerCase();
        const items = listContainer.querySelectorAll('.filter-item');
        items.forEach(item => {
          const text = item.textContent.toLowerCase();
          if (text.includes(filterText)) {
            item.style.display = 'flex';
          } else {
            item.style.display = 'none';
          }
        });
      });
    });

    // 4. Clear Filters
    // Add specific class to clear button in template to find it reliably
    const clearButton = container.querySelector('.search-filters .btn--ghost'); 
    if (clearButton && form) {
      clearButton.addEventListener('click', () => {
        form.reset();
        
        // Update GPA display
        if (gpaSlider) {
            const val = gpaSlider.parentElement.querySelector('span');
            if (val) val.textContent = "0.0";
        }
        
        // Trigger list reset
        searchInputs.forEach(input => {
          input.value = '';
          input.dispatchEvent(new Event('keyup'));
        });
      });
    }
    // 5. Active State Highlighting (Live)
    const updateActiveState = () => {
        let hasActiveFilters = false;
        
        // Check Checkboxes (Days, Open Sections, Lists)
        const checkboxes = container.querySelectorAll('input[type="checkbox"]');
        checkboxes.forEach(cb => {
            if (cb.checked) hasActiveFilters = true;
        });
        
        // Check Time Inputs
        const timeInputs = container.querySelectorAll('input[type="time"]');
        timeInputs.forEach(input => {
            if (input.value) hasActiveFilters = true;
        });
        
        // Check GPA (val > 0)
        if (gpaSlider && parseFloat(gpaSlider.value) > 0) {
            hasActiveFilters = true;
        }

        if (toggle) {
            if (hasActiveFilters) {
                toggle.classList.add('is-active-filter');
            } else {
                toggle.classList.remove('is-active-filter');
            }
        }
    };

    // Attach listeners for active state
    if (form) {
        form.addEventListener('change', updateActiveState);
        form.addEventListener('input', updateActiveState);
    }
    
    // Initial check on load
    updateActiveState();

  });
});
