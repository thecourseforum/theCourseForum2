"""Expected structure of the SIS data ``fetch_data`` reads; a mismatch fails the fetch."""

SECTION_FIELDS = frozenset(
    {
        "class_nbr",
        "subject",
        "catalog_nbr",
        "class_section",
        "component",
        "units",
        "descr",
        "topic",
        "enrl_stat_descr",
        "enrollment_total",
        "class_capacity",
        "wait_tot",
        "wait_cap",
        "crse_attr_value",
        "crse_id",
        "crse_offer_nbr",
        "instructors",
        "meetings",
    }
)
NESTED_FIELDS = {
    "instructors": frozenset({"name"}),
    "meetings": frozenset(
        {"instructor", "days", "start_time", "end_time", "room", "start_dt", "end_dt"}
    ),
}
DESCRIPTION_PATH = ("section_info", "catalog_descr", "crse_catalog_description")


def section_errors(course):
    """List every way one SIS section differs from the structure ``fetch_data`` reads."""
    if not isinstance(course, dict):
        return ["section is not an object"]
    errors = [f"missing {key}" for key in sorted(SECTION_FIELDS - course.keys())]
    for field, expected in NESTED_FIELDS.items():
        items = course.get(field, [])
        if not isinstance(items, list):
            errors.append(f"{field} is not a list")
            continue
        for index, item in enumerate(items):
            if not isinstance(item, dict):
                errors.append(f"{field}[{index}] is not an object")
                continue
            errors += [
                f"missing {field}[{index}].{key}"
                for key in sorted(expected - item.keys())
            ]
    return errors


def validate_sis_courses(courses):
    """Raise ValueError on the first SIS section whose structure is unexpected."""
    for course in courses:
        errors = section_errors(course)
        if errors:
            class_nbr = (
                course.get("class_nbr", "?") if isinstance(course, dict) else "?"
            )
            raise ValueError(
                f"SIS section {class_nbr} has an unexpected structure: {'; '.join(errors)}."
            )


def catalog_description(details, class_nbr):
    """Return the description in a SIS ClassDetails response; empty text is allowed.

    A missing field raises ValueError, so a SIS format change fails the fetch
    instead of quietly blanking every description.
    """
    value = details
    for key in DESCRIPTION_PATH:
        if not isinstance(value, dict) or key not in value:
            raise ValueError(
                f"SIS details for section {class_nbr} have an unexpected structure: missing {key}."
            )
        value = value[key]
    return value if value and value.strip() else ""
