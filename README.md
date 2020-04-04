# theCourseForum2
2020 Django rewrite of theCourseForum website

# Setup
1. Install docker and docker-compose
    - https://docs.docker.com/install/
    - https://docs.docker.com/compose/install/
2. `docker-compose up`

# Design Philosophies
- Thick models, thin views, thinner templates
    - most application logic should be in methods on model classes.
        - this ensures that the code can be reused easily anywhere the model is used
    - furthermore, you should avoid placing logic in templates.
        - e.g. don't filter lists in templates, filter them in the views.

- API-centric 

# Data migration plan from tCF 1.0
1. Get latest copy of legacy db using `mysqldump`
2. Convert to sqlite
3. `python manage.py migrate_legacy_subdepartments`
4. `python manage.py load_all_semesters`
5. `python manage.py migrate_legacy_reviews`
6. Test

# New semester update plan
1. `python manage.py update_semester 2021 january`
    - fetches CSV from lous list
    - loads section data into database

