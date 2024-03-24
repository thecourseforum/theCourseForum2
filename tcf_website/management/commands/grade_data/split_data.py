"""
The data came from UVA was 2009-2020, but that's bulky and we want it to come
in semester-by-semester files. This script probably won't ever be run again, but
may come in handy if we ever need to break up a big data file by semester.
"""

from sys import argv

from pandas import read_csv

raw_data = read_csv(argv[1], encoding="ISO-8859-1")
# Default is utf-8, which breaks on certain characters (probably prof names)

grouped_data = raw_data.groupby(
    "Term Desc"
)  # What semesters are called in the data

for group in grouped_data.groups:
    semester = (
        group.lower().strip().replace(" ", "_")
    )  # Format semester name e.g. 2020_fall

    semester_data = grouped_data.get_group(group)
    semester_data.to_csv(f"csv/{semester}.csv", index=False)
