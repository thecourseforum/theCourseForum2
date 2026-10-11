"""Download one semester snapshot from the course-data repository.

This command does not call SIS.

Usage:
docker compose exec devcontainer uv run python manage.py fetch_data
docker compose exec devcontainer uv run python manage.py fetch_data "<year>_<season>"

With no argument, the semester comes from today's date.

The snapshot lives in https://github.com/thecourseforum/tCF-data on branch
dev, as data/<year>_<season>.csv. COURSE_DATA_REPO_URL and
COURSE_DATA_REPO_BRANCH override that.
"""

import csv
import os
import subprocess
from pathlib import Path

from django.core.management.base import BaseCommand

from tcf_website.utils import current_semester, sis_term_code

# Production course-data repository. Fall 2026 is data/2026_fall.csv on branch dev.
COURSE_DATA_REPO_URL = "https://github.com/thecourseforum/tCF-data.git"
COURSE_DATA_REPO_BRANCH = "dev"

REPO_ROOT = Path(__file__).resolve().parents[3]
DEST_DIR = REPO_ROOT / "fetched"


class Command(BaseCommand):
    """Download the snapshot the data-repo bot committed for one semester."""

    help = (
        "Download data/<year>_<season>.csv from thecourseforum/tCF-data "
        "(branch dev). Does not call SIS. "
        "load_semester reads this file from fetched/ when it is present."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "semester",
            nargs="?",
            type=str,
            help=(
                "Semester in format <year>_<season> (e.g. 2026_fall). "
                "Defaults to the semester for today's date."
            ),
        )

    def handle(self, *args, **options):
        semester = options["semester"] or current_semester()
        term = sis_term_code(semester)
        if term is None:
            self.stdout.write(
                self.style.ERROR(
                    "Argument given in improper format. "
                    "Give an argument in format: <year>_<season>"
                )
            )
            return

        repo_url = (
            os.environ.get("COURSE_DATA_REPO_URL", "").strip() or COURSE_DATA_REPO_URL
        )
        branch = (
            os.environ.get("COURSE_DATA_REPO_BRANCH", "").strip()
            or COURSE_DATA_REPO_BRANCH
        )
        year, _, season = semester.partition("_")
        filename = f"{year}_{season.lower()}.csv"
        git_path = f"data/{filename}"

        self.stdout.write(
            f"Downloading {git_path} from thecourseforum/tCF-data ({branch})."
        )
        fetch = subprocess.run(
            ["git", "fetch", repo_url, branch],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        if fetch.returncode != 0:
            self.stdout.write(
                self.style.ERROR(fetch.stderr.strip() or "git fetch failed")
            )
            return

        show = subprocess.run(
            ["git", "show", f"FETCH_HEAD:{git_path}"],
            cwd=REPO_ROOT,
            capture_output=True,
        )
        if show.returncode != 0:
            self.stdout.write(
                self.style.ERROR(show.stderr.decode().strip() or "git show failed")
            )
            return

        DEST_DIR.mkdir(exist_ok=True)
        dest = DEST_DIR / filename
        dest.write_bytes(show.stdout)
        with dest.open(encoding="utf-8", newline="") as handle:
            row_count = sum(1 for _ in csv.DictReader(handle))
        self.stdout.write(self.style.SUCCESS(f"Wrote {dest}"))
        self.stdout.write(f"term {term}\nsections {row_count}\n")
