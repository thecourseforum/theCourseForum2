/**
 * Render Django-style flash messages into the global strip (same markup as _messages.html).
 */
(function (global) {
  function alertClass(tags) {
    const t = tags || "";
    if (t.indexOf("error") !== -1) {
      return "alert alert--danger";
    }
    if (t.indexOf("success") !== -1) {
      return "alert alert--success";
    }
    if (t.indexOf("warning") !== -1) {
      return "alert alert--warning";
    }
    return "alert alert--info";
  }

  function showFromJson(messageRows) {
    if (!messageRows || !messageRows.length) {
      return;
    }
    const section = document.getElementById("tcf-flash-messages");
    const inner = document.getElementById("tcf-flash-messages-inner");
    if (!section || !inner) {
      return;
    }
    inner.textContent = "";
    messageRows.forEach(function (row) {
      const text = typeof row === "string" ? row : row.message;
      const tags = (typeof row === "object" && row && row.tags) || "";
      const wrap = document.createElement("div");
      wrap.className = alertClass(tags);
      const content = document.createElement("div");
      content.className = "alert__content";
      const p = document.createElement("p");
      p.className = "alert__description";
      p.textContent = text;
      content.appendChild(p);
      wrap.appendChild(content);
      inner.appendChild(wrap);
    });
    section.hidden = false;
  }

  global.TcfFlashMessages = { showFromJson };
})(window);
