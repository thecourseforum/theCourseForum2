# theCourseForum2
2020 Django rewrite of theCourseForum website

# Setup
1. Install git, docker, and docker-compose
    - https://git-scm.com/book/en/v2/Getting-Started-Installing-Git
    - https://docs.docker.com/install/
    - https://docs.docker.com/compose/install/
2. `git clone https://github.com/thecourseforum/theCourseForum2.git`
3. Go into the `theCourseForum2/` folder and then run `docker-compose up`
4. Download a copy of the database from https://drive.google.com/open?id=1wEWgz_gAOd4fOnbiRw0AjOLg5DQrdj-5
    - put this into the `theCourseForum2/` folder
5. `docker exec tcf_db psql -U tcf_django tcf_db < april5.sql`
6. Go to http://localhost:8000 and make sure it works!

# Design Philosophies
- Thick models, thin views, thinner templates
    - most application logic should be in methods on model classes.
        - this ensures that the code can be reused easily anywhere the model is used
    - furthermore, you should avoid placing logic in templates.
        - e.g. don't filter lists in templates, filter them in the views.

- API-centric 

# Data migration plan from tCF 1.0 (total downtime: 2.5 hours)
1. Get latest copy of legacy db using `mysqldump` from DO instance.
2. Convert to sqlite using `legacy_db/mysql2sqlite`
    - Then put in `settings.py` as database `legacy`
3. `docker exec -it tcf_django bash` and then `python manage.py migrate_legacy_subdepartments`
4. `python manage.py load_all_semesters`
5. `python manage.py migrate_legacy_reviews`
6. `docker exec tcf_db pg_dump -U tcf_django tcf_db > new_db.sql`
7. Test
    - Maybe crawl tCF and check that all viewable reviews are on the new system.

# New semester update plan
1. `python manage.py update_semester 2021 january`
    - fetches CSV from lous list
    - loads section data into database
        - update courses with new course info if available
        - create new instructors if needed

