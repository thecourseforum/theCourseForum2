from django.db.models import Max


def _move_m2m(through, owner_field, other_field, source_id, target_id):
    existing = through.objects.filter(**{owner_field: target_id}).values(other_field)
    through.objects.filter(
        **{owner_field: source_id, f"{other_field}__in": existing}
    ).delete()
    through.objects.filter(**{owner_field: source_id}).update(
        **{owner_field: target_id}
    )


def merge_instructor_into(apps, keep, other):
    Instructor = apps.get_model("tcf_website", "Instructor")
    Section = apps.get_model("tcf_website", "Section")
    _move_m2m(
        Section.instructors.through, "instructor_id", "section_id", other.id, keep.id
    )
    _move_m2m(
        Instructor.departments.through,
        "instructor_id",
        "department_id",
        other.id,
        keep.id,
    )
    for model_name in (
        "Review",
        "CourseInstructorGrade",
        "Question",
        "ScheduledCourse",
    ):
        apps.get_model("tcf_website", model_name).objects.filter(
            instructor_id=other.id
        ).update(instructor_id=keep.id)
    InstructorAlias = apps.get_model("tcf_website", "InstructorAlias")
    for alias in InstructorAlias.objects.filter(instructor_id=other.id):
        InstructorAlias.objects.get_or_create(
            instructor_id=keep.id,
            first_name=alias.first_name,
            last_name=alias.last_name,
        )
    InstructorAlias.objects.filter(instructor_id=other.id).delete()
    apps.get_model("tcf_website", "ReviewLLMSummary").objects.filter(
        instructor_id__in=[keep.id, other.id]
    ).delete()
    InstructorRedirect = apps.get_model("tcf_website", "InstructorRedirect")
    InstructorRedirect.objects.filter(instructor_id=other.id).update(
        instructor_id=keep.id
    )
    InstructorRedirect.objects.update_or_create(
        old_id=other.id, defaults={"instructor_id": keep.id}
    )
    keep.hidden = keep.hidden or other.hidden
    other.delete()


def merge_instructor_group(apps, ids, email):
    Instructor = apps.get_model("tcf_website", "Instructor")
    InstructorAlias = apps.get_model("tcf_website", "InstructorAlias")
    CourseInstructorGrade = apps.get_model("tcf_website", "CourseInstructorGrade")
    by_id = {
        row.id: row
        for row in Instructor.objects.filter(id__in=ids).annotate(
            latest=Max("section__semester__number")
        )
    }
    rows = [by_id[i] for i in ids if i in by_id]
    newest = max(rows, key=lambda row: (row.latest or 0, row.id))
    keep = rows[0]
    graded = set(
        CourseInstructorGrade.objects.filter(
            instructor_id__in=[row.id for row in rows]
        ).values_list("instructor_id", flat=True)
    )
    names = {
        (row.first_name, row.last_name)
        for row in rows
        if row.latest or row.id in graded
    }

    for other in rows[1:]:
        merge_instructor_into(apps, keep, other)

    keep.first_name = newest.first_name
    keep.last_name = newest.last_name
    keep.full_name = newest.full_name
    keep.email = email
    keep.save()

    for first_name, last_name in names - {(keep.first_name, keep.last_name)}:
        InstructorAlias.objects.get_or_create(
            instructor_id=keep.id, first_name=first_name, last_name=last_name
        )
    return keep
