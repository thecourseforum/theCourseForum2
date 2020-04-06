# See https://docs.djangoproject.com/en/3.0/topics/db/models/#organizing-models-in-a-package

from .auth import login, login_error, logout, collect_extra_info
from .index import index, about
from .browse import browse, department, course, course_instructor
from .review import new_review
from .profile import profile, reviews
