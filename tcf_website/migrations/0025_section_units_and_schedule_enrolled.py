# Section.units_min/max from catalog text; ScheduledCourse.enrolled_units (set only at add time in app).

import re

from django.db import migrations, models


def _int_from_text(text):
    t = (text or "").strip()
    if not t:
        return None
    try:
        return int(round(float(t)))
    except ValueError:
        return None


def _normalize_units(value):
    if value is None:
        return 0, 0
    s = str(value).strip()
    if not s:
        return 0, 0
    for ch in ("\u2013", "\u2014", "\u2212"):
        s = s.replace(ch, "-")

    parts = re.split(r"\s*-\s*", s, maxsplit=1)
    if len(parts) == 2:
        a, b = _int_from_text(parts[0]), _int_from_text(parts[1])
        if a is not None and b is not None:
            return min(a, b), max(a, b)

    one = _int_from_text(s)
    if one is not None:
        return one, one

    nums = re.findall(r"\d+\.?\d*|\.\d+", s)
    if len(nums) >= 2:
        a, b = _int_from_text(nums[0]), _int_from_text(nums[1])
        if a is not None and b is not None:
            return min(a, b), max(a, b)
    if len(nums) == 1:
        v = _int_from_text(nums[0])
        if v is not None:
            return v, v
    return 0, 0


def forwards_sections(apps, schema_editor):
    Section = apps.get_model("tcf_website", "Section")
    for sec in Section.objects.iterator():
        lo, hi = _normalize_units(sec.units)
        if sec.units_min != lo or sec.units_max != hi:
            sec.units_min = lo
            sec.units_max = hi
            sec.save(update_fields=["units_min", "units_max"])


def forwards_enrolled(apps, schema_editor):
    ScheduledCourse = apps.get_model("tcf_website", "ScheduledCourse")
    for sc in ScheduledCourse.objects.select_related("section").iterator():
        sec = sc.section
        sc.enrolled_units = (
            sec.units_max if sec.units_min < sec.units_max else sec.units_min
        )
        sc.save(update_fields=["enrolled_units"])


class Migration(migrations.Migration):

    dependencies = [
        ("tcf_website", "0024_schedule_semester"),
    ]

    operations = [
        migrations.AddField(
            model_name="section",
            name="units_min",
            field=models.IntegerField(default=0),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="section",
            name="units_max",
            field=models.IntegerField(default=0),
            preserve_default=False,
        ),
        migrations.RunPython(forwards_sections, migrations.RunPython.noop),
        migrations.AddField(
            model_name="scheduledcourse",
            name="enrolled_units",
            field=models.IntegerField(default=0),
            preserve_default=False,
        ),
        migrations.RunPython(forwards_enrolled, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="section",
            name="units_min",
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name="section",
            name="units_max",
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name="scheduledcourse",
            name="enrolled_units",
            field=models.IntegerField(default=0),
        ),
    ]
