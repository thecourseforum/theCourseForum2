"""Download one semester snapshot from the course-data repository.

This command does not call SIS.

Usage:
docker compose exec devcontainer uv run python manage.py fetch_data
docker compose exec devcontainer uv run python manage.py fetch_data "<year>_<season>"

With no argument, the semester comes from today's date.

The snapshot lives in https://github.com/thecourseforum/tCF-data on branch
main, as data/<year>_<season>.csv. COURSE_DATA_REPO_URL and
COURSE_DATA_REPO_BRANCH override that.
"""

import csv
import os
import re
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse, urlunparse
from urllib.request import Request, urlopen

from django.core.management.base import BaseCommand, CommandError

from tcf_website.utils import current_semester, sis_term_code

# Production course-data repository. Fall 2026 is data/2026_fall.csv on branch main.
COURSE_DATA_REPO_URL = "https://github.com/thecourseforum/tCF-data.git"
COURSE_DATA_REPO_BRANCH = "main"
_ALLOWED_BRANCHES = frozenset({"main"})

REPO_ROOT = Path(__file__).resolve().parents[3]
DEST_DIR = REPO_ROOT / "fetched"

_GITHUB_REPO = re.compile(
    r"(?:github\.com[:/]|github\.com/)(?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?/?$"
)


def _redact_repo_url(repo_url: str) -> str:
    """Strip userinfo so tokens never appear in logs."""
    parsed = urlparse(repo_url)
    if not parsed.username and not parsed.password:
        return repo_url
    host = parsed.hostname or "github.com"
    if parsed.port:
        host = f"{host}:{parsed.port}"
    return urlunparse(parsed._replace(netloc=host))


def _raw_download(repo_url: str, branch: str, git_path: str) -> bytes:
    """Fetch one file from a GitHub repo over HTTPS (no local .git, no git binary)."""
    parsed = urlparse(repo_url)
    token = None
    if parsed.password:
        token = parsed.password
    elif parsed.username and parsed.username != "git":
        token = parsed.username

    match = _GITHUB_REPO.search(repo_url)
    if match is None:
        raise CommandError(
            "COURSE_DATA_REPO_URL must be a github.com URL "
            f"(got {_redact_repo_url(repo_url)!r})"
        )
    owner, repo = match.group("owner"), match.group("repo")
    raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{git_path}"
    headers = {"User-Agent": "theCourseForum2-fetch_data"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(raw_url, headers=headers)
    try:
        with urlopen(request, timeout=60) as response:
            return response.read()
    except HTTPError as error:
        raise CommandError(f"download failed ({error.code}): {raw_url}") from error
    except URLError as error:
        raise CommandError(f"download failed: {error.reason}") from error


class Command(BaseCommand):
    """Download the snapshot the data-repo bot committed for one semester."""

    help = (
        "Download data/<year>_<season>.csv from thecourseforum/tCF-data "
        "(branch main). Does not call SIS. "
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
            raise CommandError(
                "Argument given in improper format. "
                "Give an argument in format: <year>_<season>"
            )

        repo_url = (
            os.environ.get("COURSE_DATA_REPO_URL", "").strip() or COURSE_DATA_REPO_URL
        )
        branch = (
            os.environ.get("COURSE_DATA_REPO_BRANCH", "").strip()
            or COURSE_DATA_REPO_BRANCH
        )
        if branch not in _ALLOWED_BRANCHES:
            raise CommandError(
                f"COURSE_DATA_REPO_BRANCH {branch!r} is not allowed "
                f"(allowed: {', '.join(sorted(_ALLOWED_BRANCHES))})"
            )
        year, _, season = semester.partition("_")
        filename = f"{year}_{season.lower()}.csv"
        git_path = f"data/{filename}"

        self.stdout.write(
            f"Downloading {git_path} from thecourseforum/tCF-data ({branch})."
        )
        payload = _raw_download(repo_url, branch, git_path)

        DEST_DIR.mkdir(exist_ok=True)
        dest = DEST_DIR / filename
        tmp = DEST_DIR / f".{filename}.tmp"
        try:
            tmp.write_bytes(payload)
            with tmp.open(encoding="utf-8", newline="") as handle:
                row_count = sum(1 for _ in csv.DictReader(handle))
            if row_count == 0:
                raise CommandError(
                    f"{git_path} has no usable sections "
                    "(empty or header-only CSV); left existing snapshot alone"
                )
            tmp.replace(dest)
        finally:
            if tmp.exists():
                tmp.unlink()

        self.stdout.write(self.style.SUCCESS(f"Wrote {dest}"))
        self.stdout.write(f"term {term}\nsections {row_count}\n")
