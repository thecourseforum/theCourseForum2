# Lou's List Script
[UVA Lou's List](louslist.org) links individual courses to tCF course pages, and it requires a table mapping course IDs to the IDs in our URLs (mnemonic, number, database id). They are then fetched at https://thecourseforum.com/course/[course_id].

Run the following commands to generate a table for Lou's List using our database:

0. Make sure your database is set up and not corrupted. If you didn't set up your database, 0 rows will be exported. If you changed `Course` or `Subdepartment` instances during local development, you should run `docker-compose down` and set it up again to make sure you don't export/send corrupted data.

1. Run the following command, which executes the file `app/export_mapping_table.sql` (relative to the DB container root) as the database user `tcf_django`:
    ```
    docker exec tcf_db psql -U tcf_django tcf_db -f app/export_mapping_table.sql
    ```
    - This will create a CSV file in the Docker container containing the relevant data at `/app/lous.csv`, or in other words, `theCourseForum2/db/lous.csv` in the host machine. 

2. Feel free to run `more db/lous.csv` on the host machine to verify that the output is correct.

3. Send the CSV file to Professor Louis Bloomfield (lab3e@virginia.edu), creator of Lou's List!
