// Searchable dropdowns (.combo). Requires search_bar.js (defines window.addArrowKeyNav).
document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".combo").forEach((combo) => {
    const input = combo.querySelector(".combo__input");
    const list = combo.querySelector(".combo__list");
    const hidden = combo.querySelector('input[type="hidden"]');
    const options = Array.from(list.querySelectorAll(".combo__option"));
    const mnemonicSearch = input.hasAttribute("data-mnemonic-search");

    const preselected = options.find(
      (o) => o.hasAttribute("data-selected") && o.dataset.value !== "",
    );
    if (preselected) input.value = preselected.textContent.trim();

    let suppressShow = false;

    function showList() {
      if (suppressShow) return;
      list.hidden = false;
      options.forEach((o) => {
        o.hidden = false;
      });
      if (mnemonicSearch)
        options.forEach((o) => {
          list.appendChild(o);
        });
    }

    function hideList() {
      list.hidden = true;
    }

    input.addEventListener("focus", () => {
      showList();
      if (hidden.value && !suppressShow) setTimeout(() => input.select(), 0);
    });
    input.addEventListener("click", showList);
    input.addEventListener("input", () => {
      list.hidden = false;
      hidden.value = "";
      const q = input.value.toLowerCase();
      if (!q) {
        options.forEach((o) => {
          o.hidden = false;
        });
        if (mnemonicSearch)
          options.forEach((o) => {
            list.appendChild(o);
          });
        return;
      }
      if (mnemonicSearch) {
        const exact = [];
        const primary = [];
        const secondary = [];
        options.forEach((o) => {
          const text = o.textContent.trim().toLowerCase();
          const mnemonic = text.split(" - ")[0].trim();
          if (mnemonic === q) {
            o.hidden = false;
            exact.push(o);
          } else if (mnemonic.includes(q)) {
            o.hidden = false;
            primary.push(o);
          } else if (text.includes(q)) {
            o.hidden = false;
            secondary.push(o);
          } else {
            o.hidden = true;
          }
        });
        [...exact, ...primary, ...secondary].forEach((o) => {
          list.appendChild(o);
        });
      } else {
        options.forEach((o) => {
          o.hidden = !o.textContent.toLowerCase().includes(q);
        });
      }
    });

    function selectOption(opt) {
      hidden.value = opt.dataset.value;
      input.value = opt.dataset.value ? opt.textContent.trim() : "";
      hidden.dispatchEvent(new Event("change", { bubbles: true }));
      suppressShow = true;
      hideList();
      input.focus();
      suppressShow = false;
      if (combo.hasAttribute("data-submit-on-select")) {
        const parentForm = combo.closest("form");
        if (parentForm && typeof parentForm.requestSubmit === "function") {
          parentForm.requestSubmit();
        } else {
          parentForm?.submit();
        }
      }
    }

    list.addEventListener("mousedown", (e) => {
      const opt = e.target.closest(".combo__option");
      if (!opt) return;
      e.preventDefault();
      selectOption(opt);
    });

    input.addEventListener("blur", (e) => {
      if (list.contains(e.relatedTarget)) return;
      if (hidden.value) {
        const sel = options.find(
          (o) => String(o.dataset.value) === String(hidden.value),
        );
        if (sel) input.value = sel.textContent.trim();
      } else {
        input.value = "";
      }
      hideList();
    });
    list.addEventListener("focusout", (e) => {
      if (e.relatedTarget === input || list.contains(e.relatedTarget)) return;
      hideList();
    });

    list.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        const focused = list.querySelector(".combo__option:focus");
        if (!focused) return;
        e.preventDefault();
        selectOption(focused);
      } else if (e.key === "Escape") {
        suppressShow = true;
        hideList();
        input.focus();
        suppressShow = false;
      }
    });
    input.addEventListener("keydown", (e) => {
      if (e.key === "Escape") hideList();
    });

    window.addArrowKeyNav(input, list, ".combo__option:not([hidden])", {
      upLoops: false,
      downLoops: false,
    });
  });
});
