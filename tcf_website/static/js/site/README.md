# Site JavaScript layout

Scripts live under feature folders plus `lib/` for shared utilities. Paths are relative to `static/js/site/`.

## Directories

| Directory | Scripts |
|-----------|---------|
| `lib/` | `tcf_http.js`, `partial_html.js`, `modal.js`, `flash_messages.js`, `theme.js`, `combo_dropdown.js`, `search_bar.js` |
| `schedule/` | `schedule_grid_refresh.js`, `schedule_builder.js`, `schedule_flow_modal.js` |
| `review/` | `review_votes.js`, `review_cascade.js`, `reviews_sort_fetch.js` |
| `browse/` | `browse_live_results.js` |

## Global load order (from `templates/site/common/base.html`)

The builder and search UI depend on this order:

1. `lib/theme.js`
2. `lib/modal.js`
3. `lib/flash_messages.js`
4. `lib/tcf_http.js` — shared `fetch` helpers (`TcfHttp`)
5. `lib/partial_html.js` — HTML fragment injection
6. `schedule/schedule_grid_refresh.js` — grid partial refresh + abortable requests
7. `schedule/schedule_flow_modal.js` — new schedule / add-course modals (uses `TcfHttp`, partial HTML, modal)
8. `lib/search_bar.js`
9. `lib/combo_dropdown.js`

**Schedule page** additionally loads `schedule/schedule_builder.js` after the base stack (see `templates/site/schedule/schedule.html`).

**Review** pages load `review/*.js` as needed on top of the base stack; `review_cascade.js` uses XHR endpoints for semester/instructor options.

**Browse** loads `browse/browse_live_results.js` after base scripts.
