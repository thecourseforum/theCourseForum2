/**
 * Render Django-style flash messages into the global strip (same markup as _messages.html).
 */
(function (global) {
  function alertClass(tags) {
    var t = tags || "";
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
    var section = document.getElementById("tcf-flash-messages");
    var inner = document.getElementById("tcf-flash-messages-inner");
    if (!section || !inner) {
      return;
    }
    inner.textContent = "";
    messageRows.forEach(function (row) {
      var text = typeof row === "string" ? row : row.message;
      var tags = (typeof row === "object" && row && row.tags) || "";
      var wrap = document.createElement("div");
      wrap.className = alertClass(tags);
      var content = document.createElement("div");
      content.className = "alert__content";
      var p = document.createElement("p");
      p.className = "alert__description";
      p.textContent = text;
      content.appendChild(p);
      wrap.appendChild(content);
      inner.appendChild(wrap);
    });
    section.hidden = false;
  }

  global.TcfFlashMessages = { showFromJson: showFromJson };
})(window);
