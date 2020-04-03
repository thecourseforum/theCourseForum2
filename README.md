# theCourseForum2
2020 Django rewrite of theCourseForum website

# Setup
1. Install docker and docker-compose
    - https://docs.docker.com/install/
    - https://docs.docker.com/compose/install/
2. `docker-compose up`

# Data migration plan

1. Get latest copy of legacy db using `mysqldump`
2. Convert to sqlite
3. Use django inspectdb
4. write a script to go through this data and add it to our new database


