# tCF Developer Info

Ensure your system has [Git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git), [git-lfs](https://git-lfs.com/), [Docker](https://docs.docker.com/install/), and [gdown](https://github.com/wkentaro/gdown) installed.

## Setup

1. Clone the project:

```bash
git clone https://github.com/thecourseforum/theCourseForum2.git
cd theCourseForum2
```

2. Setup environment variables

```bash
cp .env.example .env
```

3. Build the project

```bash
docker compose build --no-cache
```

4. Wait for the Django server to finish building (i.e. ` ✔ Service web  Built` is visible in stdout).
5. Download and place the [latest database backup](https://drive.google.com/drive/u/0/folders/1a7OkHkepOBWKiDou8nEhpAG41IzLi7mh) (should be named `latest.dump`) from Google Drive into `db/latest.dump` in your local repo.
6. Update the database:

```bash
./scripts/reset-db.sh
```
7. Start the server

```bash
docker compose up
```

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
