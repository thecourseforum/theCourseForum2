"""Expected structure of the SIS data ``fetch_data`` reads; a mismatch fails the fetch."""

ANY = object
TEXT = str
OPTIONAL_TEXT = (str, type(None))  # fetch_data reads None as empty text.

# Every field fetch_data reads, mapped to the types it can handle.
SECTION_FIELDS = {
    "class_nbr": ANY,
    "subject": ANY,
    "catalog_nbr": ANY,
    "class_section": ANY,
    "component": ANY,
    "units": ANY,
    "descr": ANY,
    "topic": ANY,
    "enrl_stat_descr": ANY,
    "enrollment_total": ANY,
    "class_capacity": ANY,
    "wait_tot": ANY,
    "wait_cap": ANY,
    "crse_attr_value": OPTIONAL_TEXT,
    "crse_id": ANY,
    "crse_offer_nbr": ANY,
    "instructors": list,
    "meetings": list,
}
NESTED_FIELDS = {
    "instructors": {"name": TEXT},
    "meetings": {
        "instructor": TEXT,
        "days": ANY,
        "start_time": OPTIONAL_TEXT,
        "end_time": OPTIONAL_TEXT,
        "room": ANY,
        "start_dt": ANY,
        "end_dt": ANY,
    },
}
DESCRIPTION_PATH = ("section_info", "catalog_descr", "crse_catalog_description")
ATTRIBUTES_PATH = ("section_info", "enrollment_information", "class_attributes")


def field_errors(record, fields, prefix=""):
    """List the ``fields`` a SIS record lacks or holds with an unexpected type."""
    return [
        f"missing {prefix}{key}"
        if key not in record
        else f"{prefix}{key} has unexpected type {type(record[key]).__name__}"
        for key, types in sorted(fields.items())
        if key not in record or not isinstance(record[key], types)
    ]


def section_errors(course):
    """List every way one SIS section differs from the structure ``fetch_data`` reads."""
    if not isinstance(course, dict):
        return ["section is not an object"]
    errors = field_errors(course, SECTION_FIELDS)
    for field, fields in NESTED_FIELDS.items():
        items = course.get(field)
        if not isinstance(items, list):
            continue  # Already reported as missing or with an unexpected type.
        for index, item in enumerate(items):
            label = f"{field}[{index}]"
            if isinstance(item, dict):
                errors += field_errors(item, fields, f"{label}.")
            else:
                errors.append(f"{label} is not an object")
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


def details_field(details, path, types, class_nbr):
    """Return the value at ``path`` in a SIS ClassDetails response.

    A missing field or unexpected type raises ValueError, so a SIS format change
    fails the fetch instead of being read as blank.
    """
    value = details
    for key in path:
        if not isinstance(value, dict) or key not in value:
            raise ValueError(
                f"SIS details for section {class_nbr} have an unexpected structure: missing {key}."
            )
        value = value[key]
    if not isinstance(value, types):
        raise ValueError(
            f"SIS details for section {class_nbr} have an unexpected structure: "
            f"{path[-1]} has unexpected type {type(value).__name__}."
        )
    return value


def catalog_description(details, class_nbr):
    """Return the description in a SIS ClassDetails response ("" if it has none)."""
    text = details_field(details, DESCRIPTION_PATH, OPTIONAL_TEXT, class_nbr)
    return text if text and text.strip() else ""


def class_attributes(details, class_nbr):
    """Return the attribute labels in a SIS ClassDetails response, one per line."""
    return details_field(details, ATTRIBUTES_PATH, TEXT, class_nbr).splitlines()
