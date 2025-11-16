import Quill from "quill";
import QuillCursors from "quill-cursors";
import { createClient } from "@liveblocks/client";
import LiveblocksProvider from "@liveblocks/yjs";
import * as Y from "yjs";

function init() {
  const editorEl = document.getElementById("editor");
  if (!editorEl) {
    console.error("#editor element not found");
    return;
  }
  const roomId = editorEl.dataset.roomId || "studyguide-default";
  const userName = editorEl.dataset.userDisplay || "anonymous";

  // Register cursors module BEFORE creating the editor
  try {
    Quill.register("modules/cursors", QuillCursors);
  } catch (_) {}

  // Initialize Quill with cursors module enabled
  const quill = new Quill("#editor", {
    theme: "snow",
    modules: {
      toolbar: "#editor-toolbar",
      cursors: {
        hideDelay: 500,
        transformOnTextChange: true,
        selectionChangeSource: null,
      },
    },
  });

  try {
    const client = createClient({ authEndpoint: "/api/liveblocks-auth" });
    const entered = typeof client.enterRoom === "function"
      ? client.enterRoom(roomId, { initialPresence: {} })
      : typeof client.enter === "function"
        ? client.enter(roomId, { initialPresence: {} })
        : null;
    if (!entered || !entered.room) {
      throw new Error("Failed to enter Liveblocks room; client API mismatch");
    }
    const { room } = entered;

    const doc = new Y.Doc();
    const provider = new LiveblocksProvider(room, doc);
    const ytext = doc.getText("quill");
    const awareness = provider.awareness;

    // Deterministic color per user to identify who is writing
    const stringToColor = (str) => {
      let h = 0;
      for (let i = 0; i < (str || "").length; i++) h = (h << 5) - h + str.charCodeAt(i);
      const hue = Math.abs(h) % 360;
      return `hsl(${hue}, 70%, 55%)`;
    };

    // Presence: local user info
    awareness.setLocalStateField("user", {
      name: userName || "anonymous",
      color: stringToColor(userName || "anonymous"),
    });

    // Cursors
    const cursors = quill.getModule("cursors");
    if (cursors) {
      const upsertCursor = (id, state) => {
        const key = String(id);
        if (!state || !state.cursor || !state.user) {
          try { cursors.removeCursor(key); } catch (_) {}
          return;
        }
        const { name = "anonymous", color = "#00AAFF" } = state.user || {};
        try { cursors.createCursor(key, name, color); } catch (_) {}
        try { cursors.moveCursor(key, state.cursor); } catch (_) {}
      };

      quill.on("selection-change", (range, _old, source) => {
        if (source === "user") {
          const cursor = range ? { index: range.index, length: range.length } : null;
          awareness.setLocalStateField("cursor", cursor);
        }
      });

      awareness.on("update", ({ added, updated, removed }) => {
        const states = awareness.getStates();
        [...added, ...updated].forEach((id) => upsertCursor(id, states.get(id)));
        removed.forEach((id) => {
          try { cursors.removeCursor(String(id)); } catch (_) {}
        });
      });

      awareness.getStates().forEach((state, id) => upsertCursor(id, state));
    }

    // Content initialization: rely solely on Yjs document state.
    // Do NOT seed from localStorage to avoid duplication on refresh.
    // As the provider syncs, ytext.observe will bring content into Quill.

    // Remote -> Quill (ignore local transactions to prevent echo/duplication)
    ytext.observe((event) => {
      try {
        if (event && event.transaction && event.transaction.local) return;
        if (event.delta) {
          quill.updateContents(event.delta);
        } else if (typeof event.changes === "object" && event.changes.delta) {
          quill.updateContents(event.changes.delta);
        } else {
          const full = ytext.toDelta ? ytext.toDelta() : null;
          if (full) quill.setContents(full);
        }
      } catch (_) {}
    });

    // Quill -> Yjs (apply within a local transaction to mark origin)
    quill.on("text-change", (delta, _oldDelta, source) => {
      if (source !== "user") return;
      try {
        doc.transact(() => {
          if (typeof ytext.applyDelta === "function") {
            ytext.applyDelta(delta.ops);
          } else {
            let index = 0;
            (delta.ops || []).forEach((op) => {
              if (op.retain) index += op.retain;
              if (op.insert) {
                ytext.insert(index, typeof op.insert === "string" ? op.insert : "\uFFFC");
                index += typeof op.insert === "string" ? op.insert.length : 1;
              }
              if (op.delete) {
                ytext.delete(index, op.delete);
              }
            });
          }
        }, "quill");
      } catch (e) {
        console.warn("Failed to apply local delta to Yjs", e);
      }
    });

    // Local autosave (write-only; avoid reading to prevent duplication)
    const storageKey = `studyguide:${roomId}`;
    quill.on("text-change", () => {
      try {
        const contents = quill.getContents();
        window.localStorage.setItem(storageKey, JSON.stringify(contents));
      } catch (_) {}
    });
  } catch (err) {
    console.error("Failed to initialize Quill + Liveblocks:", err);
  }
}

if (document.readyState === "complete" || document.readyState === "interactive") {
  init();
} else {
  document.addEventListener("DOMContentLoaded", init);
}