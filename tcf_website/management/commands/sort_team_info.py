import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

TEAM_INFO_PATH = (
    Path(__file__).resolve().parents[2] / "data" / "about" / "team_info.json"
)
EXEC_SECTION = "executive_team"


def _member_sort_key(member: dict) -> tuple[str, str, str]:
    name = member.get("name", "").strip()
    last_name = name.split()[-1] if name else ""
    return (member.get("class", ""), last_name.lower(), name.lower())


def sort_team_info(team_info: dict) -> dict:
    exec_order = {
        member["name"]: index
        for index, member in enumerate(team_info.get(EXEC_SECTION, []))
    }
    sorted_info = {}
    for section, members in team_info.items():
        if section == EXEC_SECTION:
            sorted_info[section] = members
            continue
        execs = sorted(
            (member for member in members if member["name"] in exec_order),
            key=lambda member: exec_order[member["name"]],
        )
        others = sorted(
            (member for member in members if member["name"] not in exec_order),
            key=_member_sort_key,
        )
        sorted_info[section] = execs + others
    return sorted_info


def dump_team_info(team_info: dict) -> str:
    return json.dumps(team_info, indent=2, ensure_ascii=False) + "\n"


class Command(BaseCommand):
    help = (
        "Sort team_info.json sections: execs first, then by grad year and last "
        "name. The executive_team section keeps its order."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--check",
            action="store_true",
            help="Fail if team_info.json is not sorted instead of rewriting it",
        )

    def handle(self, *args, **options):
        current = TEAM_INFO_PATH.read_text(encoding="UTF-8")
        expected = dump_team_info(sort_team_info(json.loads(current)))

        if current == expected:
            self.stdout.write("team_info.json is already sorted.")
            return

        if options["check"]:
            raise CommandError(
                "team_info.json is not sorted. Run `python manage.py sort_team_info`."
            )

        TEAM_INFO_PATH.write_text(expected, encoding="UTF-8")
        self.stdout.write("Sorted team_info.json.")
