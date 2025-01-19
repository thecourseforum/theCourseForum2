"""Tasks for updating enrollment data."""
import json
import requests
from django.utils import timezone
from celery import shared_task
from requests.exceptions import RequestException

from tcf_website.models import Section, SectionEnrollment


@shared_task
def update_enrollment_data():
    """Update enrollment data for all sections in the current semester."""
    current_semester = Section.objects.order_by('-semester__number').first().semester
    if not current_semester:
        return

    sections = Section.objects.filter(semester=current_semester)

    updated_count = 0
    error_count = 0

    for section in sections:
        try:
            data = fetch_section_data(section)
            if data:
                section_enrollment, created = SectionEnrollment.objects.get_or_create(
                    section=section
                )
                section_enrollment.enrollment_taken = data['enrollment_taken']
                section_enrollment.enrollment_limit = data['enrollment_limit']
                section_enrollment.waitlist_taken = data['waitlist_taken']
                section_enrollment.waitlist_limit = data['waitlist_limit']
                section_enrollment.save()
                updated_count += 1
                print(
                    f"{'Created' if created else 'Updated'} enrollment data for "
                    f"section {section.sis_section_number}"
                )
            else:
                print(f"No data found for section {section.sis_section_number}")
        except RequestException as e:
            error_count += 1
            print(f"Network error for section {section.sis_section_number}: {str(e)}")
        except json.JSONDecodeError as e:
            error_count += 1
            print(f"JSON parsing error for section {section.sis_section_number}: {str(e)}")
        except KeyError as e:
            error_count += 1
            print(f"Missing data for section {section.sis_section_number}: {str(e)}")
        except (ValueError, TypeError) as e:
            error_count += 1
            print(f"Data processing error for section {section.sis_section_number}: {str(e)}")

    print(f"Finished enrollment update at {timezone.now()}")
    print(f"Updated {updated_count} sections, encountered {error_count} errors.")


def fetch_section_data(section):
    """Fetch enrollment data for a given section from the UVA API."""
    url = (
        "https://sisuva.admin.virginia.edu/psc/ihprd/UVSS/SA/s/WEBLIB_HCX_CM."
        "H_CLASS_SEARCH.FieldFormula.IScript_ClassSearch"
        f"?institution=UVA01&term={section.semester.number}&page=1&"
        f"class_nbr={section.sis_section_number}"
    )
    response = requests.get(url, timeout=300)
    response.raise_for_status()
    data = response.json()
    if data and "classes" in data and data["classes"]:
        class_data = data["classes"][0]
        return {
            "enrollment_taken": class_data.get("enrollment_total", 0),
            "enrollment_limit": class_data.get("class_capacity", 0),
            "waitlist_taken": class_data.get("wait_tot", 0),
            "waitlist_limit": class_data.get("wait_cap", 0),
        }
    return {}
