from celery import shared_task
from tcf_website.models import Section
from django.utils import timezone
import requests

@shared_task
def update_enrollment_data():    
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
                section.enrollment_total = data['enrollment_total']
                section.enrollment_limit = data['enrollment_limit']
                section.waitlist_total = data['waitlist_total']
                section.waitlist_limit = data['waitlist_limit']
                section.save()
                updated_count += 1
                print(f"Updated section {section.sis_section_number}")
            else:
                print(f"No data found for section {section.sis_section_number}")
        except Exception as e:
            error_count += 1
            print(f"Error updating section {section.sis_section_number}: {str(e)}")

    print(f"Finished enrollment update at {timezone.now()}")
    print(f"Updated {updated_count} sections, encountered {error_count} errors.")

def fetch_section_data(section):
    url = (
        "https://sisuva.admin.virginia.edu/psc/ihprd/UVSS/SA/s/WEBLIB_HCX_CM.H_CLASS_SEARCH.FieldFormula.IScript_ClassSearch"
        f"?institution=UVA01&term={section.semester.number}&page=1&class_nbr={section.sis_section_number}"
    )
    response = requests.get(url, timeout=300)
    data = response.json()
    if data:
        section_data = data[0]
        return {
            "enrollment_total": section_data['enrollment_total'],
            "enrollment_limit": section_data['class_capacity'],
            "waitlist_total": section_data['wait_tot'],
            "waitlist_limit": section_data['wait_cap'],
        }
    return {}
