# tCF Developer Info

## Setup

1. Ensure your system has Node, Python, PostgreSQL, and Docker installed.
2. Build the project:
```console
$ docker compose up
```
<!-- TODO: windows? -->
<!-- TODO: remove wiki setup? -->
3. Populate the database:

```console
$ sh scripts/reset-db.sh
```

## Stack

The code stack is current standard technologies. They were chosen because they are robust and align with the stack that UVA students learn in courses.

- Python
- Django
- PostgreSQL
- Bootstrap 4
- Javascript (jQuery)
