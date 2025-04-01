"""Utility functions for enrollment data handling."""


def build_sis_api_url(section):
    """Build the SIS API URL for a given section.

    Args:
        section: Section object to build URL for

    Returns:
        str: The complete SIS API URL
    """
    return (
        "https://sisuva.admin.virginia.edu/psc/ihprd/UVSS/SA/s/WEBLIB_HCX_CM."
        "H_CLASS_SEARCH.FieldFormula.IScript_ClassSearch"
        f"?institution=UVA01&term={section.semester.number}&page=1&"
        f"class_nbr={section.sis_section_number}"
    )


def format_enrollment_update_message(section, section_enrollment):
    """Format a consistent enrollment update message.

    Args:
        section: Section object that was updated
        section_enrollment: SectionEnrollment object with the updated data

    Returns:
        str: Formatted message string
    """
    return (
        f"Updated section {section.sis_section_number} | "
        f"Enrollment: {section_enrollment.enrollment_taken}/"
        f"{section_enrollment.enrollment_limit} | "
        f"Waitlist: {section_enrollment.waitlist_taken}/"
        f"{section_enrollment.waitlist_limit}"
    )
