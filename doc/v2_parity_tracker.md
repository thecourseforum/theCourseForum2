# V2 Parity Tracker (Legacy to V2)

Last updated: 2026-02-07  
Scope owner: Codex + Jay  
Status: In progress

## Scope
Goal: achieve function-level and page-level parity between legacy UI and v2 UI, including the v2 schedule builder migration.

## Explicit Exclusions
- Schedule-page course search/autocomplete (planned for later and intended to be reused by v2 new-review).

## Product Decisions (Intentional Divergence)
- Q&A is removed from v2 course-instructor page by request.
- Course cards in department view show only `Rating` and `GPA`.
- Instructor cards in course view show only `Rating` and `GPA`.
- v2 will not restore legacy day/time filter controls.
- v2 course-instructor will not include legacy instructor switcher dropdown.
- Legacy landing-only sections were intentionally retired.

## Parity Criteria
1. Data parity: same underlying query/model outputs for the same page context.
2. Action parity: same mutations and side effects (create, vote, delete, update).
3. Navigation parity: v2 links keep users in v2 when an equivalent v2 page exists.
4. Auth parity: same login requirements and protected actions.
5. UX parity: no unnecessary full-page redirects for in-page operations (sorting/voting).

## Route Coverage Matrix
| Legacy Route | V2 Route | Status | Notes |
| --- | --- | --- | --- |
| `/` | `/v2/` | Partial | Core landing exists, but legacy landing has additional content/flows not yet mirrored (see page checklist). |
| `/about/` | `/v2/about/` | Done | Team/history/contributors/sponsors flows present. |
| `/browse/` | `/v2/browse/` | Done | Courses/clubs mode supported. |
| `/department/<id>/` | `/v2/department/<id>/` | Done | Sorting, recency, pagination preserved. |
| `/department/<id>/<course_recency>/` | `/v2/department/<id>/<course_recency>/` | Done | Recency route parity present. |
| `/course/<mnemonic>/<number>/` | `/v2/course/<mnemonic>/<number>/` | Done | Core data/actions preserved; schedule action excluded by scope. |
| `/course/<course_id>/<instructor_id>/` | `/v2/course/<course_id>/<instructor_id>/` | Done | Reviews, ratings, grades, and sections parity complete for approved v2 scope. |
| `/course/<course_id>/<instructor_id>/sort=<method>` | `/v2/course/<course_id>/<instructor_id>/sort=<method>` | Done | Supported; v2 also supports non-redirect sort query UX. |
| `/instructor/<id>/` | `/v2/instructor/<id>/` | Done | Aggregates and course history present. |
| `/search/` | `/v2/search/` | Done | Core search parity present; legacy day/time filters intentionally not brought to v2. |
| `/reviews/new/` | `/v2/reviews/new/` | Partial | Review creation parity present; edge-case redirect/mode behavior still open. |
| `/reviews/` | `/v2/reviews/` | Done | Stats, list, vote, delete, pagination present. |
| `/profile/` | `/v2/profile/` | Done | Edit/delete flow works; v2 delete now supplies v2-safe next destination. |
| `/schedule/` | `/v2/schedule/` | Partial | v2 schedule builder page, calendar view, and core actions implemented; legacy modal editor parity intentionally not copied. |
| `/club-category/<slug>/` | `/v2/club-category/<slug>/` | Done | Added and linked from v2 browse/search. |
| Legacy club detail via `/course/<slug>/<id>/?mode=clubs` | `/v2/club/<slug>/<id>/` | Done | Added dedicated v2 club detail page with review flows. |
| `/terms/` | `/v2/terms/` | Done | Added dedicated v2 terms page and updated v2 links. |
| `/privacy/` | `/v2/privacy/` | Done | Added dedicated v2 privacy page and updated v2 links. |

## Page-Level Parity Checklist
| Page | Legacy Source | V2 Source | Status | Evaluation |
| --- | --- | --- | --- | --- |
| Landing | `tcf_website/templates/landing/landing.html` | `tcf_website/templates/v2/pages/landing.html` | Partial | Core hero/search/features/FAQ exist, but legacy-specific sections (feedback/historical modal flows) are not fully mirrored. |
| About | `tcf_website/templates/about/about.html` | `tcf_website/templates/v2/pages/about.html` | Done | Tabs and people/history/sponsors content mapped; image-path logic implemented in v2 member cards. |
| Browse | `tcf_website/templates/browse/browse.html` | `tcf_website/templates/v2/pages/browse.html` | Done | Departments and club categories supported. |
| Department | `tcf_website/templates/department/department.html` | `tcf_website/templates/v2/pages/department.html` | Done | Recency, sorting, pagination, course cards present. |
| Course | `tcf_website/templates/course/course.html` | `tcf_website/templates/v2/pages/course.html` | Done | Description and instructor listing parity preserved (with approved metric simplification). |
| Course Instructor | `tcf_website/templates/course/course_professor.html` | `tcf_website/templates/v2/pages/course_instructor.html` | Done | Q&A and instructor switcher intentionally removed; workload breakdown added in Ratings panel. |
| Instructor | `tcf_website/templates/instructor/instructor.html` | `tcf_website/templates/v2/pages/instructor.html` | Done | Stats + grouped courses + links preserved. |
| Search Results | `tcf_website/templates/search/search.html` | `tcf_website/templates/v2/pages/search.html` | Done | Result grouping/tabs parity complete for current v2 scope; day/time filters intentionally omitted. |
| New Review | `tcf_website/templates/reviews/new_review.html` | `tcf_website/templates/v2/pages/review.html` | Partial | Validation and backend checks are present; UI fallback modals are still simple alerts/confirms. |
| My Reviews | `tcf_website/templates/reviews/user_reviews.html` | `tcf_website/templates/v2/pages/reviews.html` | Done | Stats, review cards, voting, delete, pagination all present. |
| Profile | `tcf_website/templates/profile/profile.html` | `tcf_website/templates/v2/pages/profile.html` | Done | CRUD parity works; delete action now passes v2 next destination. |
| Schedule Builder | `tcf_website/templates/schedule/user_schedules.html` | `tcf_website/templates/v2/pages/schedule.html` | Partial | v2 schedule list/detail/actions + reusable weekly calendar exist; legacy modal editing flow intentionally replaced by simpler v2 forms. |
| Add Course to Schedule | legacy schedule modal flow from course page | `tcf_website/templates/v2/pages/schedule_add_course.html` | Done | v2 course page now routes to a dedicated add-to-schedule flow (lecture-only options, conflict checks, login-protected). |
| Club Category | `tcf_website/templates/club/category.html` | `tcf_website/templates/v2/pages/club_category.html` | Done | Pagination + breadcrumb + links implemented. |
| Club Detail | `tcf_website/templates/club/club.html` | `tcf_website/templates/v2/pages/club.html` | Done | Reviews, sorting, voting, add-review flow implemented. |
| Terms | `tcf_website/templates/about/terms.html` | `tcf_website/templates/v2/pages/terms.html` | Done | Shared legal content partial now rendered in v2 shell. |
| Privacy | `tcf_website/templates/about/privacy.html` | `tcf_website/templates/v2/pages/privacy.html` | Done | Shared legal content partial now rendered in v2 shell. |

## Function-Level Parity Checklist
| Function Pair | Status | Evidence | Notes |
| --- | --- | --- | --- |
| `browse` / `browse_v2` | Done | `tcf_website/views/browse.py:40`, `tcf_website/views/browse.py:89` | Same data branches for clubs/courses. |
| `department` / `department_v2` | Done | `tcf_website/views/browse.py:135`, `tcf_website/views/browse.py:186` | Same sorting/recency/pagination logic. |
| `course_view` / `course_view_v2` | Done | `tcf_website/views/browse.py:348`, `tcf_website/views/browse.py:453` | Same core course/instructor retrieval with v2 rendering tweaks. |
| `course_instructor` / `course_instructor_v2` | Done | `tcf_website/views/browse.py:522`, `tcf_website/views/browse.py:685` | Core review/grade/section logic present; workload breakdown added and approved divergences documented. |
| `instructor_view` / `instructor_view_v2` | Done | `tcf_website/views/browse.py:816`, `tcf_website/views/browse.py:868` | Same aggregate and grouping behavior. |
| `club_category` / `club_category_v2` | Done | `tcf_website/views/browse.py:929`, `tcf_website/views/browse.py:968` | Equivalent category listing/pagination. |
| Legacy club detail branch / `club_view_v2` | Done | `tcf_website/views/browse.py:364`, `tcf_website/views/browse.py:1001` | Shared helper context used for parity. |
| `new_review` / `new_review_v2` | Partial | `tcf_website/views/review.py:126`, `tcf_website/views/review.py:384` | Backend validation parity good; missing-context redirects should preserve explicit mode in v2. |
| `profile` / `profile_v2` | Done | `tcf_website/views/profile.py:55`, `tcf_website/views/profile.py:85` | Same form fields and save behavior. |
| `reviews` / `reviews_v2` | Done | `tcf_website/views/profile.py:102`, `tcf_website/views/profile.py:109` | Same stats source + paginated review list in v2. |
| `search` (legacy + v2 template switch) | Done | `tcf_website/views/search.py:70`, `tcf_website/views/search.py:145` | Backend parity exists; v2 omits day/time filter controls by product decision. |
| Review vote endpoints | Done | `tcf_website/views/review.py:91`, `tcf_website/views/review.py:109` | v2 uses shared protected vote endpoint and updates UI in place. |
| `view_schedules` / `view_schedules_v2` | Partial | `tcf_website/views/schedule.py` | Shared schedule aggregates preserved; v2 uses new calendar/context and simplified form actions. |
| Course-page add flow / `schedule_add_course_v2` | Done | `tcf_website/views/schedule.py` | v2 add flow is login-protected, lecture-only, and includes server-side duplicate/conflict checks. |

## Navigation Parity Audit (V2 Template Links)
Current v2 templates mainly route to v2 pages where available. Remaining non-v2 links are expected legacy/shared routes:
- Shared auth routes: `login`, `logout`.
- Shared mutation routes: `delete_review`, `delete_profile`.
- Shared schedule mutation routes reused by v2 forms: `new_schedule`, `delete_schedule`, `edit_schedule`, `duplicate_schedule`.

## Open Gaps Backlog
Priority P0:
- [x] Add detailed workload breakdown (reading/writing/group/other) to v2 course-instructor ratings area.
- [ ] Update `new_review_v2` missing-context redirects to preserve explicit mode semantics (`mode=courses` or `mode=clubs`). (Deferred by request)
- [ ] Finish schedule-builder parity for any remaining legacy-only behaviors not intentionally retired.

Priority P1:
- [x] Make post-delete profile redirect v2-aware (avoid dropping users onto legacy route).
- [x] Switch terms/privacy to v2 routes and templates.
- [x] Confirm legacy landing-only features are intentionally retired.

Priority P2:
- [ ] Replace review-form duplicate/zero-hour alert/confirm fallbacks with v2-styled modal UX. (Deferred: full review form redesign planned)
- [ ] Add an automated parity smoke test checklist (view render + key action endpoints).

## Smoke Test Checklist (Manual)
- [ ] `v2` landing renders and search submits in both course/club modes.
- [ ] `v2` browse -> department -> course -> course-instructor navigation stays in v2.
- [ ] `v2` course -> add-to-schedule flow adds lecture section to selected schedule and handles conflict/duplicate states.
- [ ] `v2` schedule page renders schedule list, course list, and weekly calendar consistently.
- [ ] Course-instructor ratings panel renders workload breakdown values/bars.
- [ ] Review sort updates in-place and retains `#reviews`.
- [ ] Review voting updates score/state without full reload.
- [ ] My reviews page supports delete + vote and links to v2 detail pages.
- [ ] Profile save and profile delete flows work; delete lands on v2 browse.
- [ ] Terms/privacy links from v2 footer and login modal open v2 pages.
- [ ] Club mode: browse category -> club detail -> add review flow works in v2.

## Validation Commands
- `DJANGO_SETTINGS_MODULE=tcf_core.settings.ci .venv/bin/python manage.py check`
- `rg -n "path\\(" tcf_website/urls.py`
- `rg -n "\\{% url '" tcf_website/templates/v2`

## Audit Log
- 2026-02-07: Completed initial route/page/function parity inventory and classified current gaps.
- 2026-02-07: Confirmed v2 club category/detail pages are wired and linked in browse/search/reviews.
- 2026-02-07: Confirmed Q&A removal from v2 course-instructor is intentional and tracked as a product divergence.
- 2026-02-07: Added workload breakdown rows in v2 course-instructor Ratings panel.
- 2026-02-07: Added v2 terms/privacy routes and templates; updated v2 footer/login policy links.
- 2026-02-07: Added v2-safe `next` handling for profile deletion flow.
- 2026-02-07: Added v2 schedule builder page (`/v2/schedule/`) with reusable weekly calendar component.
- 2026-02-07: Added dedicated v2 add-to-schedule flow from course page (lecture sections only) with server-side conflict checks.
