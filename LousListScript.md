# Lou's List Script
[UVA Lou's List](louslist.org) links individual courses to tCF course pages, and it requires a table mapping course IDs to the IDs in our URLs (mnemonic, number, database id). They are then fetched at https://thecourseforum.com/course/[course_id].

Run the following commands to generate a table for Lou's List using our database:

1. Open the psql terminal in the tCF database Docker container with this command*:
```
docker exec -it tcf_db psql -U tcf_django tcf_db
```

*This should work for Unix shells (Linux, MacOS) and both Powershell and CMD on Windows, but has been confirmed to not work on Git Bash for Windows.

2. In the psql shell, run the following:
```
COPY (
  SELECT S.mnemonic, C.number, C.id FROM
  (tcf_website_course C JOIN tcf_website_subdepartment S ON C.subdepartment_id = S.id)
)
TO '/tmp/lous.csv' DELIMITER ',' CSV HEADER;
```
This will create a file in the Docker container containing the relevant data at `/tmp/lous.csv`. 


1. Exit the psql shell with `\q` and copy the output file from the container to the repository root:
```
docker cp tcf_db:/tmp/lous.csv .
```
Feel free to run `cat lous.csv` to verify that the output is correct.


4. Send the CSV file to Professor Louis Bloomfield (lab3e@virginia.edu), creator of Lou's List!
