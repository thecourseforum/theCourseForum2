COPY (
  SELECT S.mnemonic, C.number, C.id
  FROM tcf_website_course C
  JOIN tcf_website_subdepartment S
    ON C.subdepartment_id = S.id
)
TO '/app/lous.csv' DELIMITER ',' CSV HEADER;
