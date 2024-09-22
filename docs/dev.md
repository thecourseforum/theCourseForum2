# tCF Developer Info

## Setup

1. Ensure your system has [Git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git), Node, Python, PostgreSQL, and [Docker](https://docs.docker.com/install/) installed.
2. Clone the project:

```console
$ git clone https://github.com/thecourseforum/theCourseForum2.git
$ cd theCourseForum
```

3. Download the `.env` secrets file from the [secrets repo](https://github.com/thecourseforum/tCF-env/blob/main/.env) and place it in the project root.

- _**Note**_: the file should be named exactly `.env`, not `.env.txt` or `env.txt` - rename if necessary.

4. Build the project

```console
$ docker compose build --no-cache # from scratch (only necessary the first time)
$ docker compose up
```

5. Wait for the Django server to finish building (i.e. `tcf_django | Watching for file changes with StatReloader` is visible in stdout).
6. Download and place the [latest database backup](https://drive.google.com/drive/u/0/folders/1a7OkHkepOBWKiDou8nEhpAG41IzLi7mh) from Google Drive into `db/latest.sql` in your local repo.
7. Update the database:

MacOS/Linux (or Windows, if you're using Git-Bash):

```console
$ sh scripts/reset-db.sh db/latest.sql
```

If you're on windows, open up `scripts/reset-db.sh` and run the commands manually (sorry)

8. Ensure the website is up, running, and functional at `localhost:8000`.

### VSCode Setup

When you open the project, VSCode may prompt you to install the recommended extensions for this project. Click yes and ensure that they are in your extension library. A list of the necessary libraries can be found [here](.././.vscode/extensions.json).

## [Useful Commands](useful-commands.md)

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
