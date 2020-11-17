# Lou's List Script
[UVA Lou's List](louslist.org) links individual courses to tCF course pages, and it requires a table mapping course IDs to the IDs in our URLs (mnemonic, number, database id). They are then fetched at https://thecourseforum.com/course/[course_id].

Run the following commands to generate a table for Lou's List using our database:

1. Exec into the docker database container, then the psql shell.
```
docker-compose exec db bash
psql -U tcf_django tcf_db
```

2. In the psql shell, run the following:
```
COPY (
  SELECT S.mnemonic, C.number, C.id FROM
  (tcf_website_course C JOIN tcf_website_subdepartment S ON C.subdepartment_id = S.id)
)
TO '/tmp/lous.csv' DELIMITER ',' CSV HEADER;
```
Copying the file to the `/tmp` directory will allow write permissions.


3. Now copy the output file from the container to the repository root:
```
docker cp tcf_db:/tmp/lous.csv .
```
Feel free to run `cat lous.csv` to verify that the output is correct.


4. Send the CSV file to Professor Louis Bloomfield (lab3e@virginia.edu), creator of Lou's List!
