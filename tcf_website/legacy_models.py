# pylint: skip-file
"""
Legacy models from tCF 1.0.

Only use these for data migration purposes.
(e.g. tcf_website/management/commands/migrate_*.py)
"""
# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or
# field names.
from django.db import models


class BookRequirements(models.Model):
    section_id = models.IntegerField()
    book_id = models.IntegerField()
    status = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'book_requirements'


class Books(models.Model):
    title = models.CharField(max_length=255, blank=True, null=True)
    author = models.CharField(max_length=255, blank=True, null=True)
    publisher = models.CharField(max_length=255, blank=True, null=True)
    edition = models.CharField(max_length=255, blank=True, null=True)
    binding = models.CharField(max_length=255, blank=True, null=True)
    isbn = models.CharField(max_length=255, blank=True, null=True)
    # This field type is a guess.
    bookstore_new_price = models.TextField(blank=True, null=True)
    # This field type is a guess.
    bookstore_used_price = models.TextField(blank=True, null=True)
    asin = models.TextField(blank=True, null=True)
    small_image_link = models.TextField(blank=True, null=True)
    medium_image_link = models.TextField(blank=True, null=True)
    large_image_link = models.TextField(blank=True, null=True)
    # This field type is a guess.
    amazon_official_new_price = models.TextField(blank=True, null=True)
    # This field type is a guess.
    amazon_official_used_price = models.TextField(blank=True, null=True)
    # This field type is a guess.
    amazon_merchant_new_price = models.TextField(blank=True, null=True)
    # This field type is a guess.
    amazon_merchant_used_price = models.TextField(blank=True, null=True)
    amazon_new_total = models.IntegerField(blank=True, null=True)
    amazon_used_total = models.IntegerField(blank=True, null=True)
    amazon_affiliate_link = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'books'


class BooksUsers(models.Model):
    book_id = models.IntegerField()
    user_id = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'books_users'


class Bugs(models.Model):
    url = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    email = models.CharField(max_length=255, blank=True, null=True)
    archived = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'bugs'


class CalendarSections(models.Model):
    section_id = models.IntegerField(blank=True, null=True)
    user_id = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'calendar_sections'


class Subdepartments(models.Model):
    id = models.IntegerField(primary_key=True, db_column="id")
    name = models.CharField(max_length=255, blank=True, null=True)
    mnemonic = models.CharField(max_length=255, blank=True, null=True)
    # created_at = models.DateTimeField()
    # updated_at = models.DateTimeField()

    def __str__(self):
        return f"{self.mnemonic} - {self.name}"

    class Meta:
        managed = False
        db_table = 'subdepartments'


class Semesters(models.Model):
    number = models.IntegerField(blank=True, null=True)
    season = models.CharField(max_length=255, blank=True, null=True)
    # max_digits and decimal_places have been guessed, as this database
    # handles decimal fields as float
    year = models.DecimalField(
        max_digits=10,
        decimal_places=5,
        blank=True,
        null=True)
    # created_at = models.DateTimeField()
    # updated_at = models.DateTimeField()

    def __str__(self):
        return f"{self.year:.0f} {self.season}"

    class Meta:
        managed = False
        db_table = 'semesters'


class Schools(models.Model):
    name = models.CharField(max_length=255, blank=True, null=True)
    # created_at = models.DateTimeField()
    # updated_at = models.DateTimeField()
    website = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'schools'


class Users(models.Model):
    email = models.CharField(max_length=255, blank=True, null=True)
    cellphone = models.CharField(max_length=255, blank=True, null=True)
    old_password = models.CharField(max_length=255, blank=True, null=True)
    # student_id = models.IntegerField(blank=True, null=True)
    student = models.ForeignKey(
        'Students',
        db_column='student_id',
        on_delete=models.CASCADE)
    # professor_id = models.IntegerField(blank=True, null=True)
    professor = models.ForeignKey(
        'Professors',
        db_column='professor_id',
        on_delete=models.CASCADE)
    subscribed_to_email = models.IntegerField(blank=True, null=True)
    # created_at = models.DateTimeField()
    # updated_at = models.DateTimeField()
    first_name = models.CharField(max_length=255, blank=True, null=True)
    last_name = models.CharField(max_length=255, blank=True, null=True)
    encrypted_password = models.CharField(max_length=255)
    reset_password_token = models.CharField(
        max_length=255, blank=True, null=True)
    # reset_password_sent_at = models.DateTimeField(blank=True, null=True)
    # remember_created_at = models.DateTimeField(blank=True, null=True)
    sign_in_count = models.IntegerField(blank=True, null=True)
    # current_sign_in_at = models.DateTimeField(blank=True, null=True)
    # last_sign_in_at = models.DateTimeField(blank=True, null=True)
    current_sign_in_ip = models.CharField(
        max_length=255, blank=True, null=True)
    last_sign_in_ip = models.CharField(max_length=255, blank=True, null=True)
    confirmation_token = models.CharField(
        max_length=255, blank=True, null=True)
    # confirmed_at = models.DateTimeField(blank=True, null=True)
    # confirmation_sent_at = models.DateTimeField(blank=True, null=True)
    unconfirmed_email = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"

    class Meta:
        managed = False
        db_table = 'users'


class Students(models.Model):
    # max_digits and decimal_places have been guessed, as this database
    # handles decimal fields as float
    grad_year = models.DecimalField(
        max_digits=10,
        decimal_places=5,
        blank=True,
        null=True)
    # user_id = models.IntegerField(blank=True, null=True)
    user = models.ForeignKey(
        Users,
        db_column='user_id',
        on_delete=models.CASCADE)
    # created_at = models.DateTimeField()
    # updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'students'


class Courses(models.Model):
    title = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    # max_digits and decimal_places have been guessed, as this database
    # handles decimal fields as float
    course_number = models.DecimalField(
        max_digits=10, decimal_places=5, blank=True, null=True)
    # subdepartment_id = models.IntegerField(blank=True, null=True)
    subdepartment = models.ForeignKey(
        Subdepartments,
        db_column='subdepartment_id',
        on_delete=models.CASCADE)
    # created_at = models.DateTimeField()
    # updated_at = models.DateTimeField()
    title_changed = models.IntegerField(blank=True, null=True)
    # last_taught_semester_id = models.IntegerField(blank=True, null=True)
    last_taught_semester = models.ForeignKey(
        Semesters,
        db_column='last_taught_semester_id',
        on_delete=models.CASCADE)

    def __str__(self):
        try:
            return f"{self.subdepartment.mnemonic} {self.course_number:.0f}"
        except Exception as e:
            return f"Error for course with number {self.course_number}: {e}"

    class Meta:
        managed = False
        db_table = 'courses'


class Sections(models.Model):
    sis_class_number = models.IntegerField(blank=True, null=True)
    section_number = models.IntegerField(blank=True, null=True)
    topic = models.CharField(max_length=255, blank=True, null=True)
    units = models.CharField(max_length=255, blank=True, null=True)
    capacity = models.IntegerField(blank=True, null=True)
    # created_at = models.DateTimeField()
    # updated_at = models.DateTimeField()
    section_type = models.CharField(max_length=255, blank=True, null=True)
    # course_id = models.IntegerField(blank=True, null=True)
    course = models.ForeignKey(
        Courses,
        db_column='course_id',
        on_delete=models.CASCADE)
    # semester_id = models.IntegerField(blank=True, null=True)
    semester = models.ForeignKey(
        Semesters,
        db_column='semester_id',
        on_delete=models.CASCADE)

    created_at = models.IntegerField(
        db_column='created_at', blank=True, null=True)
    updated_at = models.IntegerField(
        db_column='updated_at', blank=True, null=True)

    def __str__(self):
        return f"{self.course} {self.semester}"

    class Meta:
        managed = False
        db_table = 'sections'


class CoursesUsers(models.Model):
    # course_id = models.IntegerField(blank=True, null=True)
    # user_id = models.IntegerField(blank=True, null=True)

    course = models.ForeignKey(
        Courses,
        db_column='course_id',
        on_delete=models.CASCADE)
    user = models.ForeignKey(
        Users,
        db_column='user_id',
        on_delete=models.CASCADE)

    class Meta:
        managed = False
        db_table = 'courses_users'


class DayTimes(models.Model):
    day = models.CharField(max_length=255, blank=True, null=True)
    start_time = models.CharField(max_length=255, blank=True, null=True)
    end_time = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'day_times'


class DayTimesSections(models.Model):
    day_time_id = models.IntegerField(blank=True, null=True)
    section_id = models.IntegerField(blank=True, null=True)
    location_id = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'day_times_sections'


class Departments(models.Model):
    name = models.CharField(max_length=255, blank=True, null=True)
    # school_id = models.IntegerField(blank=True, null=True)
    school = models.ForeignKey(
        Schools,
        db_column='school_id',
        on_delete=models.CASCADE)
    # created_at = models.DateTimeField()
    # updated_at = models.DateTimeField()
#

    class Meta:
        managed = False
        db_table = 'departments'

    def __str__(self):
        return f"{self.name}"


class DepartmentsSubdepartments(models.Model):
    # department_id = models.IntegerField(blank=True, null=True)
    # subdepartment_id = models.IntegerField(blank=True, null=True)

    department = models.ForeignKey(
        Departments,
        db_column='department_id',
        on_delete=models.CASCADE)
    subdepartment = models.ForeignKey(
        Subdepartments,
        db_column='subdepartment_id',
        on_delete=models.CASCADE)

    class Meta:
        managed = False
        db_table = 'departments_subdepartments'


class Grades(models.Model):
    section_id = models.IntegerField(blank=True, null=True)
    semester_id = models.IntegerField(blank=True, null=True)
    # max_digits and decimal_places have been guessed, as this database
    # handles decimal fields as float
    gpa = models.DecimalField(
        max_digits=10,
        decimal_places=5,
        blank=True,
        null=True)
    count_a = models.IntegerField(blank=True, null=True)
    count_aminus = models.IntegerField(blank=True, null=True)
    count_bplus = models.IntegerField(blank=True, null=True)
    count_b = models.IntegerField(blank=True, null=True)
    count_bminus = models.IntegerField(blank=True, null=True)
    count_cplus = models.IntegerField(blank=True, null=True)
    count_c = models.IntegerField(blank=True, null=True)
    count_cminus = models.IntegerField(blank=True, null=True)
    count_dplus = models.IntegerField(blank=True, null=True)
    count_d = models.IntegerField(blank=True, null=True)
    count_dminus = models.IntegerField(blank=True, null=True)
    count_f = models.IntegerField(blank=True, null=True)
    count_drop = models.IntegerField(blank=True, null=True)
    count_withdraw = models.IntegerField(blank=True, null=True)
    count_other = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    count_aplus = models.IntegerField(blank=True, null=True)
    total = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'grades'


class Locations(models.Model):
    location = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'locations'


class Majors(models.Model):
    name = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'majors'


class ProfessorSalary(models.Model):
    staff_type = models.TextField(blank=True, null=True)
    assignment_organization = models.TextField(blank=True, null=True)
    annual_salary = models.IntegerField(blank=True, null=True)
    normal_hours = models.IntegerField(blank=True, null=True)
    working_title = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'professor_salary'


class Professors(models.Model):
    first_name = models.CharField(max_length=255, blank=True, null=True)
    last_name = models.CharField(max_length=255, blank=True, null=True)
    preferred_name = models.CharField(max_length=255, blank=True, null=True)
    email_alias = models.CharField(max_length=255, blank=True, null=True)
    # department_id = models.IntegerField(blank=True, null=True)
    department = models.ForeignKey(
        Departments,
        db_column='department_id',
        on_delete=models.CASCADE)
    # user_id = models.IntegerField(blank=True, null=True)
    user = models.ForeignKey(
        Users,
        db_column='user_id',
        on_delete=models.CASCADE)
    # created_at = models.DateTimeField()
    # updated_at = models.DateTimeField()
    middle_name = models.CharField(max_length=255, blank=True, null=True)
    classification = models.TextField(blank=True, null=True)
    department = models.TextField(blank=True, null=True)
    department_code = models.TextField(blank=True, null=True)
    primary_email = models.TextField(blank=True, null=True)
    office_phone = models.TextField(blank=True, null=True)
    office_address = models.TextField(blank=True, null=True)
    registered_email = models.TextField(blank=True, null=True)
    fax_phone = models.TextField(blank=True, null=True)
    title = models.TextField(blank=True, null=True)
    home_phone = models.TextField(blank=True, null=True)
    home_page = models.TextField(blank=True, null=True)
    mobile_phone = models.TextField(blank=True, null=True)
    professor_salary_id = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email_alias})"

    class Meta:
        managed = False
        db_table = 'professors'


class Reviews(models.Model):
    comment = models.TextField(blank=True, null=True)
    # course_professor_id = models.IntegerField(blank=True, null=True)
    # course_professor = models.ForeignKey(Professors, db_column='course_professor_id', on_delete=models.CASCADE)
    # student_id = models.IntegerField(blank=True, null=True)
    user = models.ForeignKey(
        Users,
        db_column='student_id',
        on_delete=models.CASCADE)
    # semester_id = models.IntegerField(blank=True, null=True)
    semester = models.ForeignKey(
        Semesters,
        db_column='semester_id',
        on_delete=models.CASCADE,
        null=True)
    created_at = models.DateTimeField()
    # updated_at = models.DateTimeField(null=True)
    # max_digits and decimal_places have been guessed, as this database
    # handles decimal fields as float
    professor_rating = models.DecimalField(
        max_digits=11, decimal_places=2, blank=True, null=True)
    enjoyability = models.IntegerField(blank=True, null=True)
    difficulty = models.IntegerField(blank=True, null=True)
    # max_digits and decimal_places have been guessed, as this database
    # handles decimal fields as float
    amount_reading = models.DecimalField(
        max_digits=11, decimal_places=2, blank=True, null=True)
    # max_digits and decimal_places have been guessed, as this database
    # handles decimal fields as float
    amount_writing = models.DecimalField(
        max_digits=11, decimal_places=2, blank=True, null=True)
    # max_digits and decimal_places have been guessed, as this database
    # handles decimal fields as float
    amount_group = models.DecimalField(
        max_digits=11, decimal_places=2, blank=True, null=True)
    # max_digits and decimal_places have been guessed, as this database
    # handles decimal fields as float
    amount_homework = models.DecimalField(
        max_digits=11, decimal_places=2, blank=True, null=True)
    only_tests = models.IntegerField(blank=True, null=True)
    recommend = models.IntegerField(blank=True, null=True)
    ta_name = models.CharField(max_length=255, blank=True, null=True)
    # course_id = models.IntegerField(blank=True, null=True)
    course = models.ForeignKey(
        Courses,
        db_column='course_id',
        on_delete=models.CASCADE)
    # professor_id = models.IntegerField(blank=True, null=True)
    professor = models.ForeignKey(
        Professors,
        db_column='professor_id',
        on_delete=models.CASCADE)
    deleted = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return f"Review by {self.user} for {self.course}, {self.professor} during {self.semester}"

    class Meta:
        managed = False
        db_table = 'reviews'


class Schedules(models.Model):
    name = models.CharField(max_length=255, blank=True, null=True)
    user_id = models.IntegerField(blank=True, null=True)
    flagged = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'schedules'


class SchedulesSections(models.Model):
    schedule_id = models.IntegerField()
    section_id = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'schedules_sections'


class SchemaMigrations(models.Model):
    version = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'schema_migrations'


class SectionProfessors(models.Model):
    # section_id = models.IntegerField(blank=True, null=True)
    # professor_id = models.IntegerField(blank=True, null=True)
    created_at = models.IntegerField(
        db_column='created_at', blank=True, null=True)
    updated_at = models.IntegerField(
        db_column='updated_at', blank=True, null=True)

    section = models.ForeignKey(
        Sections,
        db_column='section_id',
        on_delete=models.CASCADE)
    professor = models.ForeignKey(
        Professors,
        db_column='professor_id',
        on_delete=models.CASCADE)

    class Meta:
        managed = False
        db_table = 'section_professors'


class Settings(models.Model):
    var = models.CharField(max_length=255)
    value = models.TextField(blank=True, null=True)
    target_id = models.IntegerField()
    target_type = models.CharField(max_length=255)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'settings'


class Stats(models.Model):
    course_id = models.IntegerField(blank=True, null=True)
    professor_id = models.IntegerField(blank=True, null=True)
    # This field type is a guess.
    rating = models.TextField(blank=True, null=True)
    # This field type is a guess.
    difficulty = models.TextField(blank=True, null=True)
    # This field type is a guess.
    gpa = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'stats'


class StudentMajors(models.Model):
    student_id = models.IntegerField(blank=True, null=True)
    major_id = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'student_majors'


class TextbookTransactions(models.Model):
    seller_id = models.IntegerField()
    buyer_id = models.IntegerField(blank=True, null=True)
    book_id = models.IntegerField()
    price = models.IntegerField()
    condition = models.CharField(max_length=255)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    sold_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'textbook_transactions'


class Votes(models.Model):
    vote = models.IntegerField()
    review = models.ForeignKey(
        Reviews,
        db_column='voteable_id',
        on_delete=models.CASCADE)
    voteable_type = models.CharField(max_length=255)
    # voter_id = models.IntegerField(blank=True, null=True)
    user = models.ForeignKey(
        Users,
        db_column='voter_id',
        on_delete=models.CASCADE, null=True)
    voter_type = models.CharField(max_length=255, blank=True, null=True)
    # created_at = models.DateTimeField(blank=True, null=True)
    # updated_at = models.DateTimeField(blank=True, null=True)

    # def get_review(self):
    #     return Reviews.get(pk=self.review_id)

    def __str__(self):
        return f"Vote of value {self.vote} for {self.review} by {self.user}"

    class Meta:
        managed = False
        db_table = 'votes'
