# Club event list — iteration 1

Owner: Hani Moudarres (`HaniMoudarres`). This branch implements the public event
list from the approved theClubForum design. Month view and calendar downloads
are visible but disabled with a “Coming soon” explanation. Following clubs,
expanded club profiles, real data ingestion, and email updates are outside scope.

## Run locally

Use the existing environment in [dev.md](dev.md), including PostgreSQL, Valkey,
and local static/media storage. Run these commands in that environment:

```sh
python manage.py migrate
python manage.py load_sample_club_events
python manage.py collectstatic --noinput
python manage.py runserver 0.0.0.0:8000
```

Open `/club-events/?mode=clubs&from=2026-11-01&to=2026-11-30`. The explicit dates
keep the design examples visible after November 2026. Without date parameters,
the list defaults to the current Eastern calendar month; blank dates remove
that boundary. Choose Events from the existing header while in Clubs mode.

The loader uses 18 club examples and 21 event occurrences from OpenDesign's
“Project As Complete Opendesign Design System” (`assets/js/data.js`). Twenty
events appear with canceled events hidden. Sample data is labeled in the list
and details, and sample source links are suppressed. The loader:

- Runs only with `TCF_ENV=local` or `ci`; it never runs automatically at startup.
- Reuses `load_clubs.Command.get_or_create_category` and existing Club records.
- Preserves existing club descriptions, categories, and other profile fields.
- Creates missing sample club profiles with a visible sample description.
- Updates only its `sample:<design-event-id>` occurrences, keeping their IDs
  stable and deduplicating co-hosts. Re-running it does not duplicate records.
- Runs in one transaction and refuses to overwrite a non-sample occurrence.

## Reused UI and Django behavior

The pages extend `site/common/base.html` and reuse the header, footer, advertising
placement, theme tokens, browse layout, input/select/button styles, shared
pagination template, `paginate`, `querystring`, and `mode_url`. The existing
`modal.js` owns focus trapping, Escape, backdrop dismissal, and focus restoration.
`TcfPartialHtml` handles partial requests; ordinary GET forms and event-detail
links remain usable when JavaScript is disabled. Existing course-mode navigation
retains Schedule; club mode has public Events navigation.

Only event rows, filters, results, and detail templates/styles are new. GET
requests preserve filter values in URLs; pagination uses 15 occurrences per
page. Loading keeps prior results in place. Failed requests retain input and
offer retry; empty and invalid-filter states offer clear next steps.

## Event contract for teammates

- `ClubEvent` is one occurrence with a unique, stable `source_key`; future
  importers should namespace external occurrence IDs and upsert by that key.
  There is no Engage/Presence fetcher in this branch.
- `hosts` is a many-to-many relationship with existing `Club`. `category` is
  the event's category. `interests` is a JSON list of names; this does not add
  a club categorization pipeline or expanded profile fields.
- Store timezone-aware `starts_at` and `ends_at`, with `end > start`. The end
  is exclusive. All-day boundaries are Eastern midnights; the sample loader
  converts the design's inclusive end date to the next midnight. Call
  `full_clean()` before saving imported data, as the sample command does.
- `is_public` governs both list and detail access; hostless events are hidden.
  Canceled events are omitted unless requested. Real source links accept only
  HTTP(S); missing location and description have explicit fallbacks.
- Reuse `ClubEventFilterForm`, `filtered_events`, and `public_events` from
  `tcf_website/clubs/events.py` for later calendar/export work. Filtering
  intersects keyword, category, host club, interest, and inclusive local date
  range. Date queries include overlapping and overnight occurrences and handle
  daylight-saving changes. Co-host joins cannot duplicate an occurrence.
- Routes: `club_events` (`/club-events/`) and `club_event_detail`
  (`/club-events/<event_id>/`). XHR requests may add `partial=results` or
  `partial=details`. These return HTML, not a new public JSON API.

## Verification

Verified November 9, 2026: all 309 Django tests passed, including 31 new
event-list tests. Ruff, formatting, type, template, migration, and Django checks
passed. ESLint passed with one pre-existing unused-disable warning in
`review_votes.js`; the new event script has no warnings.

Tests were written and observed failing before each model/query, page, and
sample-command implementation. Run the complete suite with `python manage.py
test`, or the 31 focused tests with:

```sh
python manage.py test tcf_website.tests.test_club_events \
  tcf_website.tests.test_club_event_views \
  tcf_website.tests.test_sample_club_events
```

Coverage includes public/private visibility, combined filters, deduplication,
Eastern/DST boundaries, inclusive date overlap, all-day and overnight events,
safe detail URLs, escaped text, preserved pagination filters, invalid input,
and repeatable sample loading without overwriting real club data.

Browser acceptance checks use Playwright MCP with Brave's executable in an
isolated profile. Verify desktop and mobile layouts, light/dark themes, filter
and browser-history persistence, pagination scroll position, keyboard modal
behavior, loading/error/retry states, and JavaScript-disabled navigation. Only
third-party ad/analytics/WAF scripts are stubbed in these local browser checks;
the Django event pages, queries, static assets, and interactions are real.
