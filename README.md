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

# Data migration plan
1. Get latest copy of legacy db using `mysqldump`
2. Convert to sqlite
3. Use django inspectdb
4. write a script to go through this data and add it to our new database
    - https://docs.djangoproject.com/en/3.0/topics/db/multi-db/

