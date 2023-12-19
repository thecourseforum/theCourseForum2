# tCF Developer Info

## Setup

1. Ensure your system has [Git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git), Node, Python, PostgreSQL, and [Docker](https://docs.docker.com/install/) installed.
2. Download the `.env` secrets file in the project root from the [secrets repo](https://github.com/thecourseforum/tCF-Secrets/blob/master/.env).
- *__Note__*: the file should be named exactly `.env`, not `.env.txt` or `env.txt` - rename if necessary.
3. Clone then build the project:
```console
$ git clone https://github.com/thecourseforum/theCourseForum2.git && cd theCourseForum
$ docker compose up
```
4. Wait for the Django server to finish building (i.e. `tcf_django | Watching for file changes with StatReloader` is visible in stdout).
5. Download and place the [latest database backup](https://drive.google.com/drive/u/0/folders/1a7OkHkepOBWKiDou8nEhpAG41IzLi7mh) from Google Drive in the `db/` folder.
6. Update the database according to your operating system:

MacOS/Linux:
```console
$ sh scripts/reset-db.sh
```
Windows:
```console
$ scripts\reset-db.bat
```
7. Ensure the website is up running and functional at `localhost:8000`.

## [Useful Commands](docs/useful-commands.md)

## Common Issues

- Docker build error `=> CANCELED [internal] load build context`
  - This occurs because of a Windows compatibility issue with Docker. As of December 19, 2023, downgrade Docker to [version 4.19](https://docs.docker.com/desktop/release-notes/#4190), then re-build the project.

## Stack

The application stack is listed below. These technologies were chosen because they are robust and align with the stack that UVA students learn in courses.

- Python
- Django
- PostgreSQL
- Bootstrap 4
- Javascript (jQuery)
