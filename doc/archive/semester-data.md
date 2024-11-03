# Semster Data Overhaul Investigating

SIS maintains an internal API that it uses whenever you try to look at courses. By tracking the HTTP requests your browser makes with Developer Tools (F12 in Chrome, other browsers should have similar functionality), you can see what the endpoint is and make inferences on how to query data broadly.

## Loading all departments

```
https://sisuva.admin.virginia.edu/psc/ihprd/UVSS/SA/s/WEBLIB_HCX_CM.H_COURSE_CATALOG.FieldFormula.IScript_CatalogSubjects?institution=UVA01&x_acad_career=UGRD
```

![image](https://user-images.githubusercontent.com/55100084/202301312-3d970252-429f-420b-9dcd-e2e5747a52d3.png)

## Loading all classes in a department

![image](https://user-images.githubusercontent.com/55100084/201541326-6aa6f052-da14-4cde-87b3-65f78c948994.png)

```
https://sisuva.admin.virginia.edu/psc/ihprd/UVSS/SA/s/WEBLIB_HCX_CM.H_COURSE_CATALOG.FieldFormula.IScript_SubjectCourses?institution=UVA01&x_acad_career=UGRD&subject=CS
```

![image](https://user-images.githubusercontent.com/55100084/202313491-9e5638d8-03a5-43f1-9fc9-a7d2ad86ac74.png)

The important thing to note is that you can simply change `subject=CS` to whatever other department (e.g. `subject=MATH`) to get a list of JSON data for all classes in that (sub)department. It seems like you might need to change `x_acad_career` to something in order to get graduate-level classes, but that's a later problem.

## Loading Course Info

![image](https://user-images.githubusercontent.com/55100084/201541617-7418da43-a942-42e5-a2e8-ebcdbd91e820.png)

This will make this request:

```
https://sisuva.admin.virginia.edu/psc/ihprd/UVSS/SA/s/WEBLIB_HCX_CM.H_COURSE_CATALOG.FieldFormula.IScript_CatalogCourseDetails?institution=UVA01&course_id=006852&effdt=2020-05-01&x_acad_career=UGRD&crse_offer_nbr=1&use_catalog_print=Y
```

![image](https://user-images.githubusercontent.com/55100084/202313550-4eda0782-0376-437c-982f-c29aa0dfd043.png)

The important thing to note here is the `course_id` parameter in the request. This is **not** the same thing as the course ID column in our data (which probably corresponds to semester), but can be found in the JSON body for the department GET request under the key `crse_id` for each course.

Another important note: the `effdt` parameter stands for ["effective date"](http://peoplesoft.wikidot.com/effective-dates-sequence-status). It seems like changing this parameter shows you the data SIS would have provided on the given date, so this parameter should be the current date in our requests, in YYYY-MM-DD format.
