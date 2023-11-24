# Elasticsearch

As of the writing of this (10/21/21), tCF uses an Elasticsearch cluster on Elastic Cloud to handle the backend of our search. Why do we do this? Honestly, I'm not entirely sure. It seems kinda overkill for the scale of data we're working with, but the very first alums who worked on this version of the site thought it was a good idea, so here we are today. 

## How it works
The naming of various Elasticsearch services is a little confusing - our deployments have various instances running, including "Elasticsearch instances" (to be clear, the name of the searching service is now just called Elastic but they have a type of instance called Elasticsearch...why??). If you're only dealing with the search itself, don't bother with touching any of these settings; they should primarily be the responsibility of the VP of Infrastructure Engineering. What you care about is Enterprise Search (shown below) - then click the "Open" link to access the home page on the deployed instance.

![image](https://user-images.githubusercontent.com/55100084/138367801-c4267aa1-ec52-47df-a67c-5d2319569efe.png)

After that, click on "Launch App Search" and you'll be taken to the Engines page. An Elasticsearch engine stores JSON documents of a particular format (schema) and has configurable settings on how to prioritize various fields in the search algorithm. For example, when searching courses, matching the exact mnemonic (e.g. CS 2150) is more important than matching some string in the description. Since our Course and Instructor models have different schemas, we have two separate engines for each of them: `tcf-courses` and `tcf-instructors`. 

The way these engines are used is that our Django app makes GET requests to each engine's endpoint (defined by the environmental variables `ES_COURSE_SEARCH_ENDPOINT` and `ES_INSTRUCTOR_SEARCH_ENDPOINT`), the engines will search their documents with the passed query, and return the top matches. It's important to note that at this point what gets returned are *not* actual instances of the Course and Instructor models, but just a list of JSONs that have some fields matching up to instances of these models in our database.

## Updating Elasticsearch
Every semester, new courses are established, and we need to add them to our search DB or our users won't be able to find them. This is done by running the Django management command `index_elasticsearch` i.e. `python manage.py index_elasticsearch`. The command essentially takes every instance of Course and Instructor in the database, extracts several important fields into a JSON, and uploads batches of them via POST requests to the relevant engine. Obviously, this should be done after new semester data has been loaded.
