# UI Parity Tracker

Last updated: 2026-02-07

## Scope
- Goal: full page-level and function-level parity between legacy templates and the current production templates.
- Out of scope: schedule-page course autocomplete for now.

## Route Status
| Route | Status | Notes |
| --- | --- | --- |
| `/` | Done | Landing uses current template set. |
| `/about/` | Done | Team/contributors/sponsors/history tabs supported. |
| `/privacy/` | Done | Current template wired. |
| `/terms/` | Done | Current template wired. |
| `/browse/` | Done | Courses and clubs modes supported. |
| `/department/<id>/` | Done | Sorting, recency, pagination maintained. |
| `/course/<mnemonic>/<number>/` | Done | Instructor list, ratings/GPA, add-to-schedule preserved. |
| `/course/<course_id>/<instructor_id>/` | Done | Ratings, reviews, grade distribution, sections panel preserved. |
| `/instructor/<id>/` | Done | Aggregates and grouped course history preserved. |
| `/search/` | Done | Search grouping, pagination, mode handling preserved. |
| `/reviews/new/` | Partial | Full backend flow works; planned UI refinement remains. |
| `/reviews/` | Done | User stats, pagination, vote/delete actions preserved. |
| `/profile/` | Done | Edit and delete profile flows preserved. |
| `/schedule/` | Done | Builder list/detail/actions and weekly calendar available. |
| `/course/<id>/add-to-schedule/` | Done | Course-to-schedule flow with conflict/duplicate checks preserved. |
| `/club-category/<slug>/` | Done | Category listing and pagination preserved. |
| `/club/<slug>/<id>/` | Done | Club reviews, sorting, voting, add review supported. |

## Feature Parity Checklist
- [x] Shared header/footer/nav behavior
- [x] Shared flash messages across all pages
- [x] Shared top leaderboard ad on all non-landing pages
- [x] Adblock detection via ad script `onerror`
- [x] Review voting parity (up/down/toggle)
- [x] Sort controls on instructor reviews without page-level UX regressions
- [x] Course and instructor metric cards aligned with current product decisions
- [x] Lecture/other section display rules and scroll behavior
- [x] Schedule conflict detection and duplicate prevention
- [x] Terms/privacy flow in current styling
- [ ] New review form UI redesign (deferred)
- [ ] Schedule-page course autocomplete (deferred)

## QA Smoke Test Matrix
- [ ] Anonymous browse/search/course navigation
- [ ] Authenticated add review (course + club)
- [ ] Authenticated vote review (my reviews + instructor page)
- [ ] Profile edit and delete
- [ ] Schedule create, rename, duplicate, delete
- [ ] Add section to schedule + conflict path
- [ ] Remove scheduled course
- [ ] Club category and club detail review flow

## Notes
- No backward-compatibility route layer is required.
- Canonical routes now serve the current template set.
