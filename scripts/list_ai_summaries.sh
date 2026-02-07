#!/bin/bash
# List course/instructor AI summaries with ids and last updated timestamps.
# Usage (docker): docker compose exec web ./scripts/list_ai_summaries.sh
set -euo pipefail

python3 - <<'PY'
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tcf_core.settings.dev")
django.setup()

from tcf_website.models import ReviewLLMSummary  # pylint: disable=import-outside-toplevel

summaries = (
    ReviewLLMSummary.objects.filter(club__isnull=True)
    .select_related("course", "instructor")
    .order_by("-updated_at", "-id")
)

if not summaries.exists():
    print("No course/instructor summaries found.")
    raise SystemExit(0)

total = summaries.count()

header = (
    f"{'summary_id':>10}  {'course_id':>9}  {'instructor_id':>13}  "
    f"{'reviews':>7}  {'course':<12}  {'instructor':<28}  {'updated_at'}"
)
print(header)
print("-" * len(header))

for summary in summaries:
    course = summary.course
    instructor = summary.instructor
    course_code = course.code() if course else "-"
    instructor_name = instructor.full_name if instructor else "-"
    print(
        f"{summary.id:>10}  {summary.course_id:>9}  "
        f"{summary.instructor_id:>13}  {summary.source_review_count:>7}  "
        f"{course_code:<12}  "
        f"{instructor_name:<28}  {summary.updated_at.date()}"
    )

print(f"Total summaries: {total}")
PY
