"""Course/club row dicts and grouping for search and browse results."""

from ..models import Subdepartment


def course_to_row_dict(course, *, include_similarity: bool = False) -> dict:
    """Build a course dict for grouping/templates; search adds trigram score when present."""
    row = {
        "id": course.id,
        "title": course.title,
        "number": course.number,
        "mnemonic": course.mnemonic,
        "description": course.description,
        "average_rating": course.average_rating,
        "average_difficulty": course.average_difficulty,
        "average_gpa": course.average_gpa,
        "semester_last_taught": str(course.semester_last_taught),
    }
    if include_similarity:
        row["max_similarity"] = course.max_similarity
    return row


def group_by_dept(courses: list[dict]) -> dict:
    """Group courses by department mnemonic; one Subdepartment query for labels."""
    mnemonics = {course["mnemonic"] for course in courses}
    subdepts = {
        s.mnemonic: s
        for s in Subdepartment.objects.filter(mnemonic__in=mnemonics).only(
            "mnemonic", "name", "department_id"
        )
    }
    grouped: dict = {}
    for course in courses:
        mnemonic = course["mnemonic"]
        if mnemonic not in grouped:
            subdept = subdepts[mnemonic]
            grouped[mnemonic] = {
                "subdept_name": subdept.name,
                "dept_id": subdept.department_id,
                "courses": [],
            }
        grouped[mnemonic]["courses"].append(course)
    return grouped


def club_to_row_dict(club) -> dict:
    """Build a club dict for grouping/templates (matches fetch_clubs / group_by_club_category)."""
    return {
        "id": club.id,
        "name": club.name,
        "description": club.description,
        "category_slug": club.category.slug,
        "category_name": club.category.name,
    }


def group_by_club_category(clubs: list[dict]) -> dict:
    """Group clubs by category slug."""
    grouped: dict = {}
    for club in clubs:
        slug = club["category_slug"]
        if slug not in grouped:
            grouped[slug] = {
                "category_name": club["category_name"],
                "category_slug": slug,
                "clubs": [],
            }
        grouped[slug]["clubs"].append(club)
    return grouped
