"""Benchmark Fall 2026, acad_org=CS: original versus optimized HoosList/SIS descriptions."""

import csv
import sys
from collections import Counter
from difflib import SequenceMatcher
from functools import partial
from pathlib import Path
from time import perf_counter
from unittest.mock import patch

import requests

WHITESPACE_MAPPING = str.maketrans(
    {" ": "·", "\xa0": "⍽", "\n": "↵", "\r": "␍", "\t": "⇥"}
)


def send_timed_request(send, intervals, session, request, **kwargs):
    start = perf_counter()
    try:
        return send(session, request, **kwargs)
    finally:
        if "IScript_ClassDetails" in request.url:
            intervals.append((start, perf_counter()))


def compare_csvs(old_path, new_path, description_sources=None):
    with old_path.open() as old_file, new_path.open() as new_file:
        old_reader, new_reader = csv.DictReader(old_file), csv.DictReader(new_file)
        old_rows, new_rows = list(old_reader), list(new_reader)
        same_headers = old_reader.fieldnames == new_reader.fieldnames
        fields = list(
            dict.fromkeys(
                [*(old_reader.fieldnames or []), *(new_reader.fieldnames or [])]
            )
        )
    old = {r["ClassNumber"]: r for r in old_rows}
    new = {r["ClassNumber"]: r for r in new_rows}
    differences = []
    for key in sorted(old.keys() | new.keys()):
        course = old.get(key) or new[key]
        for field in fields:
            original, deviated = (
                old.get(key, {}).get(field),
                new.get(key, {}).get(field),
            )
            if original == deviated:
                continue
            before, after = original or "", deviated or ""
            compact_before, compact_after = (
                "".join(text.split()) for text in (before, after)
            )
            category = (
                "other"
                if original is None or deviated is None
                else "spacing"
                if compact_before == compact_after
                else "capitalization"
                if before.casefold() == after.casefold()
                else "spacing&capitalization"
                if compact_before.casefold() == compact_after.casefold()
                else "other"
            )
            highlights = ([], [])
            for tag, i1, i2, j1, j2 in SequenceMatcher(
                None, before, after, autojunk=False
            ).get_opcodes():
                for parts, text in zip(
                    highlights, (before[i1:i2], after[j1:j2]), strict=True
                ):
                    if tag != "equal":
                        text = "⟦" + text.translate(WHITESPACE_MAPPING) + "⟧"
                    parts.append(text)
            differences.append(
                {
                    "ClassNumber": key,
                    "Course": f"{course.get('Mnemonic', '')} {course.get('Number', '')}".strip(),
                    "Section": course.get("Section", ""),
                    "DeviationType": field,
                    "Difference": category,
                    "true_source": ""
                    if key not in new
                    else (description_sources or {}).get(key, "unknown")
                    if field == "Description"
                    else "sis",
                    "Change": "extra class"
                    if key not in old
                    else "missing class"
                    if key not in new
                    else "extra field"
                    if original is None
                    else "missing field"
                    if deviated is None
                    else "changed value",
                    "OriginalHighlighted": "".join(highlights[0]),
                    "DeviatedHighlighted": "".join(highlights[1]),
                    "Original": original,
                    "Deviated": deviated,
                }
            )
    difference_path = new_path.with_name(
        f"differences-{new_path.stem.removeprefix('optimized-')}.csv"
    )
    if differences:
        with difference_path.open("w", newline="", encoding="utf-8-sig") as stream:
            writer = csv.DictWriter(
                stream,
                fieldnames=[
                    "ClassNumber",
                    "Course",
                    "Section",
                    "DeviationType",
                    "Difference",
                    "true_source",
                    "Change",
                    "OriginalHighlighted",
                    "DeviatedHighlighted",
                    "Original",
                    "Deviated",
                ],
            )
            writer.writeheader()
            writer.writerows(differences)
        print(f"Saved {len(differences)} field differences: {difference_path}")
    else:
        difference_path.unlink(missing_ok=True)
    return {
        "same_headers": same_headers,
        "old_rows": len(old_rows),
        "new_rows": len(new_rows),
        "old_duplicate_ids": len(old_rows) - len(old),
        "new_duplicate_ids": len(new_rows) - len(new),
        "missing_ids": sorted(old.keys() - new.keys()),
        "extra_ids": sorted(new.keys() - old.keys()),
        "raw_field_differences": dict(
            Counter(row["DeviationType"] for row in differences)
        ),
    }


def main():
    from tcf_website.management.commands import fetch_data as optimized
    from tcf_website.management.commands import fetch_data_old as legacy

    root = Path(__file__).resolve().parent / "semester_data" / "benchmark_data"
    root.mkdir(parents=True, exist_ok=True)
    # The original fetcher appends, so start each benchmark with fresh files.
    for filename in (
        "old.csv",
        "optimized-hooslist.csv",
        "optimized-sis.csv",
        "differences-hooslist.csv",
        "differences-sis.csv",
    ):
        (root / filename).unlink(missing_ok=True)
    report = {}
    for name in ("old", "hooslist", "sis"):
        print(f"Running {name}: Fall 2026, acad_org=CS -> {root}")
        intervals = []
        description_sources = {}
        start = perf_counter()
        # Apply the same organization to the original's unchanged requests.
        with (
            patch.dict(legacy.session.params, {"acad_org": "CS"}),
            patch.object(
                requests.Session,
                "send",
                autospec=True,
                side_effect=partial(
                    send_timed_request, requests.Session.send, intervals
                ),
            ) as sent,
        ):
            if name == "old":
                legacy.retrieve_and_write_semester_courses(
                    str(root / "old.csv"), "1268"
                )
                # Count overlapping detail requests once, as elapsed description time.
                description_seconds, end = 0, 0
                for started, finished in sorted(intervals):
                    description_seconds += max(0, finished - max(started, end))
                    end = max(end, finished)
            else:
                command = optimized.Command()
                command.handle(
                    semester="2026_fall",
                    subjects=None,
                    timeout=optimized.TIMEOUT,
                    acad_org="CS",
                    output=root / f"optimized-{name}.csv",
                    description_source=name,
                )
                description_seconds = command.description_seconds
                description_sources = command.description_sources
        report[name] = {
            "seconds": perf_counter() - start,
            "description_seconds": description_seconds,
            "description_sources": description_sources,
            "http_calls_excluding_retries": len(sent.call_args_list),
        }
    print("\nComparison: Fall 2026, acad_org=CS")
    for name, stats in report.items():
        print(
            f"{name.title()}: {stats['seconds']:.3f}s, "
            f"{stats['http_calls_excluding_retries']} HTTP calls excluding retries"
        )
        seconds = stats["description_seconds"]
        percent = 100 * seconds / stats["seconds"] if stats["seconds"] else 0
        print(
            f"  Descriptions: {seconds:.1f}s ({percent:.1f}%); everything else: "
            f"{stats['seconds'] - seconds:.1f}s ({100 - percent:.1f}%)"
        )
    print(
        "Old description time counts class-detail requests, including their other fields."
    )
    for name in ("hooslist", "sis"):
        print(f"\nOptimized ({name} descriptions) vs original:")
        comparison = compare_csvs(
            root / "old.csv",
            root / f"optimized-{name}.csv",
            report[name]["description_sources"],
        )
        same_scope = (
            comparison["same_headers"]
            and comparison["old_rows"] > 0
            and not any(
                comparison[k]
                for k in (
                    "missing_ids",
                    "extra_ids",
                    "old_duplicate_ids",
                    "new_duplicate_ids",
                )
            )
        )
        if same_scope and report[name]["seconds"]:
            print(f"Speedup: {report['old']['seconds'] / report[name]['seconds']:.2f}x")
        else:
            print(
                "Speedup unavailable: export scope differs, is empty, or timing is zero."
            )
        for label, value in comparison.items():
            if isinstance(value, dict):
                value = (
                    ", ".join(f"{field}: {count}" for field, count in value.items())
                    or "none"
                )
            elif isinstance(value, list):
                value = ", ".join(value) or "none"
            print(f"{label.replace('_', ' ').capitalize()}: {value}")
    print(f"Saved CSVs: {root}")


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
    main()
