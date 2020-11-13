from django.core.management.base import BaseCommand, CommandError
from django.db import connections

from tqdm import tqdm
import traceback

from tcf_website.legacy_models import *
from tcf_website.models import *

import traceback


class Command(BaseCommand):
    help = 'Imports data from legacy database into default database'

    def migrate(
            self,
            legacy_class,
            new_class,
            field_map,
            unique_fields,
            reverse=False,
            after_func=None):

        def not_yet_created(obj):

            def get_or_call(old_field):
                if callable(old_field):
                    try:
                        return old_field(obj)
                    except BaseException:
                        return False
                return getattr(obj, old_field)

            return len(new_class.objects.filter(**{f"{new_field}__exact": get_or_call(
                old_field) for new_field, old_field in unique_fields.items()})) == 0

        if not reverse:
            objects = legacy_class.objects.using('legacy').all()
        else:
            objects = legacy_class.objects.using(
                'legacy').all().order_by('-pk')

        for obj in objects:
            if not_yet_created(obj):
                try:
                    new_obj = new_class()
                    for new_field_name, value_func in field_map.items():
                        old_val = value_func(obj)
                        if old_val:
                            setattr(new_obj, new_field_name, value_func(obj))
                    new_obj.save()
                    print(f"Created {new_obj}")

                    if after_func and callable(after_func):
                        after_func(obj, new_obj)

                except Exception as e:
                    print(f"Error migrating {type(obj).__name__} {obj}:")
                    print(e)
                    traceback.print_exc()

    def load_user(self, old_user):

        try:
            student = old_user.student
            grad_year = student.grad_year
        except BaseException:
            grad_year = None

        if not old_user.last_name:
            last_name = ""
        else:
            last_name = old_user.last_name

        computing_id = old_user.email.split("@")[0]

        try:
            return User.objects.get(computing_id=computing_id)
        except BaseException:
            pass

        user, created = User.objects.get_or_create(
            email=old_user.email,
            first_name=old_user.first_name,
            last_name=last_name,
            computing_id=computing_id,
            username=computing_id,
            graduation_year=grad_year,
        )

        return user

    def get_most_recent_semester(self, course, instructor, date):
        month = min(9, date.month)
        year = date.year % 100
        sem_number = int(f"1{year:02d}{month}")

        # sections from recent to least recent
        sections = Section.objects.filter(
            instructors=instructor,
            course=course,
        ).order_by("-semester__number")

        for section in sections:
            if section.semester.number <= sem_number:
                return section.semester

        if sections:
            return sections.last().semester

        return Semester.objects.order_by("number").first()

    def migrate_review(self, review):
        user = self.load_user(review.user)

        try:
            if not review.professor:
                return
        except BaseException:
            return

        try:
            if not review.course:
                return
        except BaseException:
            return

        try:
            instructor = Instructor.objects.get(
                last_name=review.professor.last_name,
                first_name=review.professor.first_name,
            )
        except KeyError:
            return

        course = Course.objects.get(
            number=review.course.course_number,
            subdepartment__mnemonic=review.course.subdepartment.mnemonic
        )

        amount_reading = min(
            20, review.amount_reading) if review.amount_reading else 0
        amount_writing = min(
            20, review.amount_writing) if review.amount_writing else 0
        amount_group = min(
            20, review.amount_group) if review.amount_group else 0
        amount_homework = min(
            20, review.amount_homework) if review.amount_homework else 0

        hours_per_week = amount_reading + amount_writing + amount_group + amount_homework

        try:
            semester = Semester.objects.get(number=review.semester.number)
        except Exception:
            semester = self.get_most_recent_semester(
                course, instructor, review.created_at)

        instructor_rating = min(5, round(
            review.professor_rating)) if review.professor_rating else 3
        difficulty = min(5, round(
            review.difficulty)) if review.difficulty else 3
        recommendability = min(5, round(
            review.recommend)) if review.recommend else 3
        enjoyability = min(5, round(
            review.enjoyability)) if review.enjoyability else 3

        r, created = Review.objects.get_or_create(
            text=review.comment,
            user=user,
            course=course,
            instructor=instructor,
            instructor_rating=instructor_rating,
            difficulty=difficulty,
            recommendability=recommendability,
            enjoyability=enjoyability,
            hours_per_week=hours_per_week,
            amount_reading=amount_reading,
            amount_writing=amount_writing,
            amount_group=amount_group,
            amount_homework=amount_homework,
            semester=semester,
            created=review.created_at,
            modified=review.created_at,
        )

        if not created:
            print("Review already created.")

        return r

    def migrate_reviews(self):
        for i in tqdm(range(0, self.reviews.count())):
            try:
                review = self.reviews[i]
            except Exception as e:
                print("Could not retrieve review!")
                print(e)

            try:
                self.migrate_review(review)
            except KeyError:
                print("WTF!?")
            except Exception as e:
                print(f"Problem migrationg {review}:")
                print(review.comment)
                print(e)

    def migrate_vote(self, vote):
        value = 0
        if vote.vote == 1:
            value = 1
        elif vote.vote == 0:
            value = -1

        user = self.load_user(vote.user)
        review_user = self.load_user(vote.review.user)

        try:
            review = Review.objects.get(
                user=review_user,
                created=vote.review.created_at,
                text=vote.review.comment,
            )
        except Review.DoesNotExist:
            print("TEST")
            review = self.migrate_review(vote.review)
        except Exception as e:
            print(e)
            print("Could not get or create review...")
            print(vote.review)
            return

        if not review:
            print("Could not get or create review...")
            print(vote.review)
            return

        Vote.objects.get_or_create(
            value=value,
            user=user,
            review=review,
        )

    def migrate_votes(self):
        for vote in tqdm(self.votes, total=self.votes.count()):
            self.migrate_vote(vote)

    def handle(self, *args, **options):

        self.schools = Schools.objects.using('legacy').all()
        self.departments = Departments.objects.using('legacy').all()
        self.subdepartments = Subdepartments.objects.using('legacy').all()
        self.courses = Courses.objects.using('legacy').all()
        self.sections = Sections.objects.using('legacy').all()
        self.professors = Professors.objects.using('legacy').all()
        self.users = Users.objects.using('legacy').all()
        self.students = Students.objects.using('legacy').all()
        self.reviews = Reviews.objects.using('legacy').all()
        self.votes = Votes.objects.using('legacy').all()
        self.semesters = Semesters.objects.using('legacy').all()

        UNKNOWN_SCHOOL, _ = School.objects.get_or_create(name='UNKNOWN')
        UNKNOWN_DEPT, _ = Department.objects.get_or_create(
            name='UNKNOWN', school=UNKNOWN_SCHOOL)

        self.migrate_reviews()

        self.migrate_votes()
