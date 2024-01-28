## Site Update Guides

### Data migration plan from tCF 1.0 (total downtime: 2.5 hours)
1. Get latest copy of legacy db using `mysqldump` from DO instance.
2. Convert to sqlite using `legacy_db/mysql2sqlite`
    - Then put in `settings.py` as database `legacy`
3. `docker exec -it tcf_django bash` and then `python manage.py migrate_legacy_subdepartments`
4. `python manage.py load_semester ALL_DANGEROUS`
5. `python manage.py load_grades ALL_DANGEROUS`
6. `python manage.py migrate_legacy_reviews`
7. `docker exec tcf_db pg_dump -U tcf_django -Fc tcf_db > dump.sql`
8. Test
    - Maybe crawl tCF and check that all viewable reviews are on the new system.
9. Upload to DigitalOcean DB.
    - `PGPASSWORD=$DB_PASS pg_restore -U $DB_USER -h $DB_HOST -p 25060 -d $DB_NAME < dump.sql`
    - You may have to run this command 3 times.

### New semester update plan
1. Go into the `/tcf_website/management/commands/semester_data` directory. Edit `fetch_data.py` to run `download_semester()` on the semester(s) you want*. For example, if you wanted Fall 2020, you would add a line saying `download_semester(2020, 'fall')`.
2. Commit this updated data and push it into the repo; it needs to be on prod to update the DB (you could update locally, but what's the point?). 
3. On a prod environment (we've been using `heroku run bash --app thecourseforum-dev` because our prod/dev DBs are linked...but we probably won't have it be this way forever), run `python3 manage.py load_semester ${SEMESTER}`, where `${SEMESTER}` is the semester you're adding in the format `YEAR_SEASON` e.g. `2020_FALL`. 
4. You should be able to run this command as many times as you want, as it accounts for/skips over duplicates and will update sections with new instructors as necessary. Most courses will likely not change much, but this duplicate handling helps us deal with classes whose instructors change after we load the data the first time.
5. I think we have to run the `department_fixes` script too? But not sure about that one.
6. TODO: Consolidate this into one master script that we can run as a cron job on prod.

<sub>\* Yeah, this method really sucks; should probably improve it in the consolidation process</sub>

### Deploying to prod
Production deployments (i.e. the version of the site users see on thecourseforum.com) should be handled automatically by our CI (continuous integration system). As of the writing of this documentation, GitHub Actions is set up to autodeploy every time a build on the `master` branch passes. However, in the event that something fails, the manual deploy process is outlined [here](https://docs.google.com/document/d/1sPl1v4JrvicrgQluXvG9cR6GWPijC0hr7zAa3h3uE5E/edit#heading=h.9mo53b4db0s8). Just note that the environmental variables list in the doc may not be up-to-date, so remember to set them accordingly.
