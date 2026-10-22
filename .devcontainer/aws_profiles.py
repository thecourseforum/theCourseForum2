#!/usr/bin/env python3
import os
import re
import sys
from pathlib import Path

SOURCE = Path(__file__).parent / "aws-config"
DEST = Path(os.environ.get("AWS_CONFIG_FILE") or Path.home() / ".aws" / "config")

SECTION_HEADER = re.compile(r"^\s*\[(.+)\]")


def section_name(line):
    match = SECTION_HEADER.match(line)
    if match is None:
        return None
    return " ".join(match.group(1).split())


def existing_sections(path):
    names = (section_name(line) for line in path.read_text().splitlines())
    return {name for name in names if name is not None}


def missing_blocks(source, existing):
    blocks = []
    seen = set()
    keep = False
    for line in source.read_text().splitlines():
        name = section_name(line)
        if name is not None:
            if name in seen:
                sys.exit(f"aws-profiles: duplicate section [{name}] in {source}")
            seen.add(name)
            keep = name not in existing
        if keep:
            blocks.append(line)
    return blocks


def append_lines(path, lines):
    current = path.read_text()
    separator = ""
    if current:
        separator = ("" if current.endswith("\n") else "\n") + "\n"
    with path.open("a") as file:
        file.write(separator + "\n".join(lines) + "\n")


def main():
    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.touch()

    lines = missing_blocks(SOURCE, existing_sections(DEST))
    if lines:
        append_lines(DEST, lines)


if __name__ == "__main__":
    main()
