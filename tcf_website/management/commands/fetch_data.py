"""Download the course-data snapshot. This command does not call SIS.

Usage:
docker compose exec devcontainer uv run python manage.py fetch_data "<year>_<season>"

The <year>_<season> argument is accepted so existing commands keep working.
It is unused until the data repo stores one file per semester.
"""

import json
import subprocess
from pathlib import Path

from django.core.management.base import BaseCommand

# Personal stand-in used to test the data-repo flow.
# Replace this URL with the theCourseForum course-data repository when it exists.
# That repo's two-hour SIS schedule is written and commented out.
# Uncomment it when the workflow moves to the real theCourseForum data repo.
# This command only downloads the committed file.
COURSE_DATA_REPO_URL = "https://github.com/richardhe789/tcf-course-data.git"
# File the data-repo bot commits. One class-search page, not a load_semester CSV.
COURSE_DATA_GIT_PATH = "data/1268.json"

REPO_ROOT = Path(__file__).resolve().parents[3]
DEST_DIR = REPO_ROOT / "fetched"


class Command(BaseCommand):
    """Download the snapshot the data-repo bot committed."""

    help = (
        "Download the course-data snapshot. Does not call SIS. "
        "The <year>_<season> argument is unused until the data repo "
        "stores one file per semester. load_semester cannot import this JSON."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "semester",
            type=str,
            help=(
                "Semester in format <year>_<season> (e.g. 2024_spring). "
                "Accepted for compatibility and currently ignored."
            ),
        )

    def handle(self, *args, **options):
        semester = options["semester"]
        elements = semester.split("_")
        if (
            len(elements) != 2
            or not elements[0].isdigit()
            or len(elements[0]) != 4
            or elements[1].lower() not in {"fall", "spring", "summer", "january"}
        ):
            self.stdout.write(
                self.style.ERROR(
                    "Argument given in improper format. "
                    "Give an argument in format: <year>_<season>"
                )
            )
            return

        self.stdout.write(
            f"Semester argument {semester} is ignored. "
            f"Downloading {COURSE_DATA_GIT_PATH} from the data repo."
        )
        fetch = subprocess.run(
            ["git", "fetch", COURSE_DATA_REPO_URL, "master"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        if fetch.returncode != 0:
            self.stdout.write(self.style.ERROR(fetch.stderr.strip() or "git fetch failed"))
            return

        show = subprocess.run(
            ["git", "show", f"FETCH_HEAD:{COURSE_DATA_GIT_PATH}"],
            cwd=REPO_ROOT,
            capture_output=True,
        )
        if show.returncode != 0:
            self.stdout.write(
                self.style.ERROR(show.stderr.decode().strip() or "git show failed")
            )
            return

        DEST_DIR.mkdir(exist_ok=True)
        dest = DEST_DIR / "1268.json"
        dest.write_bytes(show.stdout)
        data = json.loads(dest.read_text(encoding="utf-8"))
        first = data["classes"][0]
        preview = (
            f"term {data['term']}\n"
            f"classes {len(data['classes'])}\n"
            f"pages {data['pageCount']}\n"
            f"first {first['subject']} {first['catalog_nbr']}\n"
            f"enrollment {first['enrollment_total']}\n"
        )
        (DEST_DIR / "preview.txt").write_text(preview, encoding="utf-8", newline="\n")
        self.stdout.write(self.style.SUCCESS(f"Wrote {dest}"))
        self.stdout.write(preview)
