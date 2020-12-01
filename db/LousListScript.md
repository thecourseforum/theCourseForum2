# Lou's List Script
[UVA Lou's List](louslist.org) links individual courses to tCF course pages, and it requires a table mapping course IDs to the IDs in our URLs (mnemonic, number, database id). They are then fetched at https://thecourseforum.com/course/[course_id].

Run the following commands to generate a table for Lou's List using our database:

0. Make sure you have your database set up correctly. It is likely that you ran `docker-compose down` to start with a clean slate.

1. Open the psql terminal in the tCF database Docker container with this command*:
    ```
    docker exec -it tcf_db psql -U tcf_django tcf_db -f app/export_mapping_table.sql
    ```
    - This will create a CSV file in the Docker container containing the relevant data at `/app/lous.csv`, or in other words, `theCourseForum2/db/lous.csv` in the host machine. 

    *This should work for Unix shells (Linux, MacOS) and both Powershell and CMD on Windows, but has been confirmed to not work on Git Bash for Windows.

2. Feel free to run `more db/lous.csv` on the host machine to verify that the output is correct.

3. Send the CSV file to Professor Louis Bloomfield (lab3e@virginia.edu), creator of Lou's List!
